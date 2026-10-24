import boto3
import time
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

# DynamoDB Table is always in us-east-2
client = boto3.client('dynamodb', region_name="us-east-2")

# SSM in us-east-1 publishes the authoritative long name for every region in
# every partition, EUSC included, so new regions pick up a display name without
# anyone maintaining a list of them.
SSM_LONG_NAME_REGION = 'us-east-1'
LONG_NAME_PATH = '/aws/service/global-infrastructure/regions/{}/longName'

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

def get_region_long_names(region_names):
    """Map region codes to their AWS long names, e.g. eu-south-2 -> Europe (Spain).

    Returns {} if SSM cannot be reached, and omits any region SSM does not know
    about: a missing long name costs a tooltip in the UI, not the whole run.
    """
    long_names = {}

    try:
        ssm = boto3.client('ssm', region_name=SSM_LONG_NAME_REGION)

        # get_parameters accepts at most 10 names per call
        for batch in chunk_list(list(region_names), 10):
            response = ssm.get_parameters(
                Names=[LONG_NAME_PATH.format(region) for region in batch]
            )

            for param in response['Parameters']:
                # /aws/service/global-infrastructure/regions/<code>/longName
                long_names[param['Name'].split('/')[-2]] = param['Value']

            if response.get('InvalidParameters'):
                print(f"No long name in SSM for: {response['InvalidParameters']}")

    except Exception as e:
        print(f"Warning: could not load region long names from SSM: {str(e)}")

    return long_names

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

        # Collect the region list first so the long names can be resolved in a
        # single batch of SSM calls rather than one per region.
        regions = [
            (region['RegionName'], region['RegionOptStatus'])
            for page in page_iterator
            for region in page['Regions']
        ]
        long_names = get_region_long_names(region_name for region_name, _ in regions)

        for region_name, status in regions:
            is_opt_in = True if status != "ENABLED_BY_DEFAULT" else False

            try:
                function_exists = check_function_exists(region_name)
            except Exception as e:
                print(f"Warning: could not check function in {region_name}: {e}")
                function_exists = False

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

            # Omitted when SSM has no name for the region, so consumers can tell
            # "unknown" apart from a region genuinely named after its code.
            if region_name in long_names:
                region_info['region_long_name'] = {"S": long_names[region_name]}

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