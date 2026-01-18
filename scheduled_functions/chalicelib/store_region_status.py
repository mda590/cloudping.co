import boto3
import time
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

# DynamoDB Table is always in us-east-2
client = boto3.client('dynamodb', region_name="us-east-2")

def chunk_list(lst, chunk_size):
    """Split a list into smaller chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def handle_unprocessed_items(client, unprocessed_items, max_retries=3):
    """Handle any unprocessed items with exponential backoff"""
    items = unprocessed_items
    retries = 0
    base_delay = 0.1  # 100ms

    while items and retries < max_retries:
        # Exponential backoff
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

def write_results(results):
    """Write results to DynamoDB with chunking and retry logic"""
    
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

def check_function_exists(region_name):
    lambda_client = boto3.client('lambda', region_name=region_name)
    try:
        source_config = lambda_client.get_function_configuration(
            FunctionName="ping_from_region-prod-ping"
        )
    except ClientError as e:
        print(f"Error getting source function configuration: {str(e)}")
        return False
    return True

def get_earliest_timestamp(region_name):
    dynamodb = boto3.resource('dynamodb', region_name="us-east-2")
    table = dynamodb.Table('PingTest')
    
    response = table.query(
        IndexName='region-timestamp-index',
        KeyConditionExpression=Key('region').eq(region_name),
        Limit=1,  # We only need the first item
        ScanIndexForward=True  # True for ascending order (earliest first)
    )
    
    if response['Items']:
        return response['Items'][0]['timestamp']
    return None

def get_latest_timestamp(region_name):
    dynamodb = boto3.resource('dynamodb', region_name="us-east-2")
    table = dynamodb.Table('PingTest')
    
    response = table.query(
        IndexName='region-timestamp-index',
        KeyConditionExpression=Key('region').eq(region_name),
        Limit=1,  # We only need the first item
        ScanIndexForward=False  # False for descending order (latest first)
    )
    
    if response['Items']:
        return response['Items'][0]['timestamp']
    return None

def store():
    """
    Get the status of all regions, separating them into opt-in and default regions.
    Returns a dict with region statuses and whether they're opt-in regions.
    """
    client = boto3.client('account')

    try:
        paginator = client.get_paginator('list_regions')
        page_iterator = paginator.paginate()
        enabled_regions = []
        
        for page in page_iterator:
            for region in page['Regions']:
                region_name = region['RegionName']
                status = region['RegionOptStatus']
                is_opt_in = True if status != "ENABLED_BY_DEFAULT" else False
                function_exists = check_function_exists(region_name)
                earliest_timestamp = get_earliest_timestamp(region_name)
                most_recent_timestamp = get_latest_timestamp(region_name)

                region_info = {
                    "region_name": {"S": region_name},
                    "partition": {"S": "aws"},
                    'status': {"S": status},
                    'is_opt_in': {"BOOL": is_opt_in},
                    'ping_function_exists': {"BOOL": function_exists},
                    'earliest_data_timestamp': {"S": str(earliest_timestamp)},
                    'most_recent_data_timestamp': {"S": str(most_recent_timestamp)},
                }
                print("Storing region info:", region_info)

                enabled_regions.append({
                    "PutRequest": {
                        "Item": region_info
                    }
                })

        write_results(enabled_regions)

    except ClientError as e:
        print(f"Error getting region status: {str(e)}")
        return {}
    
if __name__ == "__main__":
    store()