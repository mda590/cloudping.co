"""
Store Region Status for AWS European Sovereign Cloud (EUSC).

This Lambda function runs in the EUSC partition (eusc-de-east-1) and writes
EUSC region information to the main AWS DynamoDB table (cloudping_regions_enhanced).

It uses cross-partition credentials stored in Secrets Manager to authenticate
to main AWS.

Note: The Account API (list_regions) is not available in EUSC, so regions are
hardcoded in the EUSC_REGIONS list. Update this list as new regions become available.
"""

from chalice import Chalice, Cron
import boto3
import json
import time
from datetime import datetime
from botocore.exceptions import ClientError

app = Chalice(app_name='store-region-status-eusc')

# EUSC-specific configuration
EUSC_HUB_REGION = 'eusc-de-east-1'
MAIN_AWS_DYNAMODB_REGION = 'us-east-2'
PING_FUNCTION_NAME = 'ping_from_region-eusc-ping'

# Known EUSC regions - hardcoded since account:ListRegions is not available in EUSC
# Update this list as new EUSC regions become available
EUSC_REGIONS = [
    'eusc-de-east-1',
]


def get_cross_partition_dynamodb_client():
    """
    Get a DynamoDB client for writing to main AWS from EUSC.

    This retrieves stored credentials from Secrets Manager to authenticate
    to main AWS.
    """
    # Get credentials from EUSC Secrets Manager
    secrets = boto3.client('secretsmanager')
    secret = secrets.get_secret_value(SecretId='cloudping/cross-partition-credentials')
    creds = json.loads(secret['SecretString'])

    return boto3.client(
        'dynamodb',
        region_name=MAIN_AWS_DYNAMODB_REGION,
        endpoint_url=f'https://dynamodb.{MAIN_AWS_DYNAMODB_REGION}.amazonaws.com',
        aws_access_key_id=creds['access_key_id'],
        aws_secret_access_key=creds['secret_access_key']
    )


def check_function_exists(region_name):
    """Check if the ping function exists in the specified EUSC region."""
    lambda_client = boto3.client('lambda', region_name=region_name)
    try:
        lambda_client.get_function_configuration(FunctionName=PING_FUNCTION_NAME)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return False
        print(f"Error checking function in {region_name}: {str(e)}")
        return False


def get_earliest_timestamp(dynamodb_client, region_name):
    """Get the earliest ping data timestamp for a region from PingTest table."""
    response = dynamodb_client.query(
        TableName='PingTest',
        IndexName='region-timestamp-index',
        KeyConditionExpression='#r = :region',
        ExpressionAttributeNames={'#r': 'region'},
        ExpressionAttributeValues={':region': {'S': region_name}},
        Limit=1,
        ScanIndexForward=True  # Ascending order (earliest first)
    )
    if response.get('Items'):
        return response['Items'][0]['timestamp']['S']
    return None


def get_latest_timestamp(dynamodb_client, region_name):
    """Get the most recent ping data timestamp for a region from PingTest table."""
    response = dynamodb_client.query(
        TableName='PingTest',
        IndexName='region-timestamp-index',
        KeyConditionExpression='#r = :region',
        ExpressionAttributeNames={'#r': 'region'},
        ExpressionAttributeValues={':region': {'S': region_name}},
        Limit=1,
        ScanIndexForward=False  # Descending order (latest first)
    )
    if response.get('Items'):
        return response['Items'][0]['timestamp']['S']
    return None


def chunk_list(lst, chunk_size):
    """Split a list into smaller chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def handle_unprocessed_items(client, unprocessed_items, max_retries=3):
    """Handle any unprocessed items with exponential backoff."""
    items = unprocessed_items
    retries = 0
    base_delay = 0.1  # 100ms

    while items and retries < max_retries:
        delay = base_delay * (2 ** retries)
        time.sleep(delay)

        try:
            response = client.batch_write_item(RequestItems=items)
            items = response.get('UnprocessedItems', {})
            retries += 1

            if items:
                print(f"Retry {retries}: {len(items)} items remaining")
        except Exception as e:
            print(f"Error during retry: {str(e)}")
            raise

    if items:
        print(f"Warning: {len(items)} items remained unprocessed after all retries")

    return items


def write_results(client, results):
    """Write results to DynamoDB with chunking and retry logic."""
    # Split into chunks of 25 (DynamoDB's limit)
    chunk_size = 25
    chunks = chunk_list(results, chunk_size)

    print(f"Split {len(results)} items into {len(chunks)} chunks")

    # Process each chunk
    for i, chunk in enumerate(chunks, 1):
        try:
            print(f"Processing chunk {i} of {len(chunks)}")
            response = client.batch_write_item(
                RequestItems={
                    'cloudping_regions_enhanced': chunk
                }
            )

            # Handle any unprocessed items
            if response.get('UnprocessedItems'):
                print("Handling unprocessed items...")
                unprocessed = handle_unprocessed_items(
                    client,
                    response['UnprocessedItems']
                )
                if unprocessed:
                    print(f"Warning: Some items in chunk {i} were not processed")

        except Exception as e:
            print(f"Error processing chunk {i}: {str(e)}")
            raise


@app.schedule(Cron("30", "0,6,12,18", "*", "*", "?", "*"))
def store(event):
    """
    Store EUSC region status to main AWS DynamoDB.

    This function runs every 6 hours (30 minutes after the hour to avoid
    overlap with the main AWS store_region_status) and writes EUSC region
    information to the cloudping_regions_enhanced table in main AWS.
    """
    print(f"Starting EUSC region status store at {datetime.now()}")

    try:
        # Get DynamoDB client for main AWS
        dynamodb = get_cross_partition_dynamodb_client()

        # Use hardcoded EUSC regions since account:ListRegions is not available
        enabled_regions = []
        current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + "Z"

        for region_name in EUSC_REGIONS:
            # Check if ping function exists in this region
            function_exists = check_function_exists(region_name)

            # Get timestamp data from PingTest table
            earliest_timestamp = get_earliest_timestamp(dynamodb, region_name)
            most_recent_timestamp = get_latest_timestamp(dynamodb, region_name)

            # EUSC regions are opt-in by default
            region_info = {
                "region_name": {"S": region_name},
                "partition": {"S": "aws-eusc"},
                "status": {"S": "ENABLED"},
                "is_opt_in": {"BOOL": True},
                "ping_function_exists": {"BOOL": function_exists},
                "earliest_data_timestamp": {"S": str(earliest_timestamp)},
                "most_recent_data_timestamp": {"S": str(most_recent_timestamp)},
            }
            print(f"Storing EUSC region info: {region_info}")

            enabled_regions.append({
                "PutRequest": {
                    "Item": region_info
                }
            })

        if enabled_regions:
            write_results(dynamodb, enabled_regions)
            print(f"Successfully stored {len(enabled_regions)} EUSC regions to main AWS DynamoDB")

        return {
            'statusCode': 200,
            'body': {
                'message': f"Stored {len(enabled_regions)} EUSC regions",
                'regions': [r['PutRequest']['Item']['region_name']['S'] for r in enabled_regions]
            }
        }

    except ClientError as e:
        error_msg = f"Error storing EUSC region status: {str(e)}"
        print(error_msg)
        return {
            'statusCode': 500,
            'body': {'error': error_msg}
        }

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        return {
            'statusCode': 500,
            'body': {'error': error_msg}
        }


if __name__ == "__main__":
    store(None)
