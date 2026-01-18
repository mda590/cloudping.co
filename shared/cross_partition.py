"""
Cross-partition utilities for AWS European Sovereign Cloud (EUSC) integration.

This module provides utilities for:
- Detecting the current AWS partition (aws or aws-eusc)
- Building partition-aware endpoints
- Creating DynamoDB clients that can write across partitions
"""

import boto3
import json


def get_current_partition():
    """
    Detect the AWS partition from the current region.

    Returns:
        str: 'aws-eusc' if running in European Sovereign Cloud, 'aws' otherwise
    """
    region = boto3.session.Session().region_name
    if region and region.startswith('eusc-'):
        return 'aws-eusc'
    return 'aws'


def get_dns_suffix(partition=None):
    """
    Get the DNS suffix for the given partition.

    Args:
        partition: The AWS partition ('aws' or 'aws-eusc').
                   If None, detects from current region.

    Returns:
        str: 'amazonaws.eu' for EUSC, 'amazonaws.com' for main AWS
    """
    if partition is None:
        partition = get_current_partition()
    return 'amazonaws.eu' if partition == 'aws-eusc' else 'amazonaws.com'


def get_arn_partition(partition=None):
    """
    Get the ARN partition prefix for the given partition.

    Args:
        partition: The AWS partition ('aws' or 'aws-eusc').
                   If None, detects from current region.

    Returns:
        str: 'aws-eusc' for EUSC, 'aws' for main AWS
    """
    if partition is None:
        partition = get_current_partition()
    return partition


def build_endpoint(service, region, partition=None):
    """
    Build a partition-aware endpoint URL for an AWS service.

    Args:
        service: The AWS service name (e.g., 'dynamodb', 'lambda')
        region: The AWS region name
        partition: The AWS partition. If None, infers from region name.

    Returns:
        str: The endpoint URL (e.g., 'dynamodb.us-east-2.amazonaws.com')
    """
    if partition is None:
        # Infer partition from region name
        partition = 'aws-eusc' if region.startswith('eusc-') else 'aws'

    dns_suffix = get_dns_suffix(partition)
    return f"{service}.{region}.{dns_suffix}"


def get_cross_partition_dynamodb_client(region='us-east-2'):
    """
    Get a DynamoDB client for writing to main AWS from any partition.

    When running in EUSC, this retrieves stored credentials from Secrets Manager
    to authenticate to main AWS. When running in main AWS, it uses the IAM role.

    Args:
        region: The target region in main AWS (default: us-east-2)

    Returns:
        boto3 DynamoDB client configured to write to main AWS
    """
    partition = get_current_partition()

    if partition == 'aws':
        # In main AWS - use IAM role
        return boto3.client('dynamodb', region_name=region)

    # In EUSC - use stored credentials from Secrets Manager
    secrets = boto3.client('secretsmanager')
    secret = secrets.get_secret_value(SecretId='cloudping/cross-partition-credentials')
    creds = json.loads(secret['SecretString'])

    return boto3.client(
        'dynamodb',
        region_name=region,
        endpoint_url=f'https://dynamodb.{region}.amazonaws.com',
        aws_access_key_id=creds['access_key_id'],
        aws_secret_access_key=creds['secret_access_key']
    )


def get_regions_from_dynamodb(dynamodb_client=None):
    """
    Get all regions from both partitions via DynamoDB.

    This reads from the cloudping_regions_enhanced table which contains
    regions from both main AWS and EUSC partitions.

    Args:
        dynamodb_client: Optional DynamoDB client. If None, creates one.

    Returns:
        list: List of dicts with 'RegionName' and 'partition' keys
    """
    if dynamodb_client is None:
        dynamodb_client = get_cross_partition_dynamodb_client()

    response = dynamodb_client.scan(TableName='cloudping_regions_enhanced')

    regions = []
    for item in response.get('Items', []):
        status = item.get('status', {}).get('S', '')
        if status in ['ENABLED', 'ENABLED_BY_DEFAULT']:
            regions.append({
                'RegionName': item['region_name']['S'],
                'partition': item.get('partition', {'S': 'aws'})['S']
            })

    # Handle pagination
    while 'LastEvaluatedKey' in response:
        response = dynamodb_client.scan(
            TableName='cloudping_regions_enhanced',
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        for item in response.get('Items', []):
            status = item.get('status', {}).get('S', '')
            if status in ['ENABLED', 'ENABLED_BY_DEFAULT']:
                regions.append({
                    'RegionName': item['region_name']['S'],
                    'partition': item.get('partition', {'S': 'aws'})['S']
                })

    return regions
