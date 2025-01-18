from chalice import Chalice, Cron
import boto3
import json
import hashlib
import os
import urllib.request
from datetime import datetime
from botocore.exceptions import ClientError

app = Chalice(app_name='ping-function-deployer')

def get_enabled_regions():
    """Get list of enabled regions in the account."""
    account_client = boto3.client('account')
    try:
        paginator = account_client.get_paginator('list_regions')
        page_iterator = paginator.paginate()
        enabled_regions = []

        for page in page_iterator:
            for region in page['Regions']:
                if region['RegionOptStatus'] in ['ENABLED', 'ENABLED_BY_DEFAULT']:
                    enabled_regions.append(region['RegionName'])
        return enabled_regions
    except ClientError as e:
        print(f"Error getting regions: {str(e)}")
        return []

def get_function_code_hash(lambda_client, function_name):
    """Get hash of the function's code."""
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        code_location = response['Code']['Location']
        
        # Download the code
        import urllib.request
        with urllib.request.urlopen(code_location) as f:
            code_content = f.read()
            
        # Calculate SHA256 hash
        return hashlib.sha256(code_content).hexdigest()
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return None
        raise e

def create_or_update_event_rule(events_client, function_name, function_arn):
    """Create or update EventBridge rule for the Lambda function."""
    rule_name = f"{function_name}-schedule"
    
    try:
        # Create or update the rule
        events_client.put_rule(
            Name=rule_name,
            ScheduleExpression="cron(0 0,6,12,18 * * ? *)",
            State='ENABLED',
            Description=f'Schedule for {function_name}'
        )

        # Add permission for EventBridge to invoke Lambda
        lambda_client = boto3.client('lambda', region_name=events_client.meta.region_name)
        try:
            lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=f"{function_name}-EventBridge",
                Action='lambda:InvokeFunction',
                Principal='events.amazonaws.com',
                SourceArn=f"arn:aws:events:{events_client.meta.region_name}:{boto3.client('sts').get_caller_identity()['Account']}:rule/{rule_name}"
            )
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceConflictException':
                raise e

        # Add the target
        events_client.put_targets(
            Rule=rule_name,
            Targets=[{
                'Id': f"{function_name}-target",
                'Arn': function_arn
            }]
        )
        
        print(f"Successfully set up event rule in {events_client.meta.region_name}")
        return True
        
    except Exception as e:
        print(f"Error setting up event rule in {events_client.meta.region_name}: {str(e)}")
        return False

def deploy_lambda(source_function_name, target_function_name, region):
    """Deploy or update Lambda function in specified region."""
    # Get source function details from current region
    source_lambda = boto3.client('lambda')
    
    try:
        source_config = source_lambda.get_function_configuration(
            FunctionName=source_function_name
        )
    except ClientError as e:
        print(f"Error getting source function configuration: {str(e)}")
        return False
        
    # Create Lambda client for target region
    target_lambda = boto3.client('lambda', region_name=region)
    
    # Get source function code hash
    source_hash = get_function_code_hash(source_lambda, source_function_name)
    if not source_hash:
        print(f"Could not get source function code hash")
        return False
        
    try:
        # Check if function exists in target region
        target_hash = get_function_code_hash(target_lambda, target_function_name)
        function_updated = False
        
        if target_hash is None:
            # Function doesn't exist, create it
            print(f"Creating new function in {region}")
            
            # Get the function code
            code_response = source_lambda.get_function(FunctionName=source_function_name)
            code_location = code_response['Code']['Location']
            
            # Create the function
            response = target_lambda.create_function(
                FunctionName=target_function_name,
                Runtime=source_config['Runtime'],
                Role=source_config['Role'],  # Make sure this role exists in target region
                Handler=source_config['Handler'],
                Code={'ZipFile': urllib.request.urlopen(code_location).read()},
                Description=f"Deployed from {source_function_name} on {datetime.now().isoformat()}",
                Timeout=source_config['Timeout'],
                MemorySize=source_config['MemorySize'],
                Environment=source_config.get('Environment', {'Variables': {}}),
                Tags={
                    'SourceFunction': source_function_name,
                    'DeploymentTime': datetime.now().isoformat(),
                    'application': 'cloudping',
                    'component': 'ping_from_region'
                }
            )
            function_arn = response['FunctionArn']
            function_updated = True
            print(f"Successfully created function in {region}")
            
        elif target_hash != source_hash:
            # Function exists but code is different, update it
            print(f"Updating existing function in {region}")
            
            # Get the function code
            code_response = source_lambda.get_function(FunctionName=source_function_name)
            code_location = response['Code']['Location']
            
            # Update function code
            target_lambda.update_function_code(
                FunctionName=target_function_name,
                ZipFile=urllib.request.urlopen(code_location).read()
            )
            
            # Update configuration
            response = target_lambda.update_function_configuration(
                FunctionName=target_function_name,
                Runtime=source_config['Runtime'],
                Role=source_config['Role'],
                Handler=source_config['Handler'],
                Description=f"Updated from {source_function_name} on {datetime.now().isoformat()}",
                Timeout=source_config['Timeout'],
                MemorySize=source_config['MemorySize'],
                Environment=source_config.get('Environment', {'Variables': {}})
            )
            function_arn = response['FunctionArn']
            function_updated = True
            print(f"Successfully updated function in {region}")
        
        else:
            print(f"Function in {region} is up to date")
            response = target_lambda.get_function_configuration(FunctionName=target_function_name)
            function_arn = response['FunctionArn']
        
        # Set up or update EventBridge rule
        events_client = boto3.client('events', region_name=region)
        if not create_or_update_event_rule(events_client, target_function_name, function_arn):
            print(f"Warning: Failed to set up event rule in {region}")
            
        return True
            
    except ClientError as e:
        print(f"Error deploying to {region}: {str(e)}")
        return False

@app.schedule(Cron("0", "5,11,17,23", "*", "*", "?", "*"))
def deploy(event):
    """
    Main handler for deploying Lambda functions across regions.
    
    Expected event format:
    {
        "source_function_name": "name-of-source-function",
        "target_function_name": "name-to-deploy-as",
        "skip_regions": ["region1", "region2"]  # optional
    }
    """
    try:
        source_function = "ping_from_region-prod-ping"
        target_function = "ping_from_region-prod-ping"
        skip_regions = ["us-east-2"]
        
        # Get enabled regions
        regions = get_enabled_regions()
        print(f"Found {len(regions)} enabled regions")
        
        results = {}
        for region in regions:
            if region in skip_regions:
                print(f"Skipping {region} as requested")
                continue

            print(f"Processing region {region}")
            success = deploy_lambda(source_function, target_function, region)
            results[region] = 'SUCCESS' if success else 'FAILED'

        return {
            'statusCode': 200,
            'body': {
                'message': f"Processed {len(regions)} regions",
                'results': results
            }
        }
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        return {
            'statusCode': 500,
            'body': {'error': error_msg}
        }
    
if __name__ == "__main__":
    deploy(None)