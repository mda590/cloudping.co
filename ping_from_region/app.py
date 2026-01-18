from chalice import Chalice, Cron
from timeit import default_timer as timer

import datetime
import socket
import signal
import boto3
import json
import time
import sys

app = Chalice(app_name='ping_from_region')

# Cross-partition utilities (inlined to avoid packaging issues with Chalice)

def get_current_partition():
    """Detect the AWS partition from the current region."""
    region = boto3.session.Session().region_name
    if region and region.startswith('eusc-'):
        return 'aws-eusc'
    return 'aws'


def get_dns_suffix(partition=None):
    """Get the DNS suffix for the given partition."""
    if partition is None:
        partition = get_current_partition()
    return 'amazonaws.eu' if partition == 'aws-eusc' else 'amazonaws.com'


def get_cross_partition_dynamodb_client(region='us-east-2'):
    """
    Get a DynamoDB client for writing to main AWS from any partition.

    When running in EUSC, this retrieves stored credentials from Secrets Manager
    to authenticate to main AWS. When running in main AWS, it uses the IAM role.
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


def get_current_time():
    time = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + "Z"
    return time


def get_curr_region():
    my_session = boto3.session.Session()
    my_region = my_session.region_name
    return my_region


def get_regions():
    """
    Get all regions from both partitions via DynamoDB.

    This reads from the cloudping_regions_enhanced table which contains
    regions from both main AWS and EUSC partitions.
    """
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


def getResults(failed, count, passed):
    """ Summarize Results """

    lRate = 0
    if failed != 0:
        lRate = failed / (count) * 100
        lRate = "%.2f" % lRate

    print("\nTCP Ping Results: Connections (Total/Pass/Fail): [{:}/{:}/{:}] (Failed: {:}%)".format((count), passed, failed, str(lRate)))
    # avg min max port region regionTo attempts address
    # results list: [{ "seq" "time"}]


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
    # Use cross-partition client to write to main AWS DynamoDB
    client = get_cross_partition_dynamodb_client(region='us-east-2')

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
                    'PingTest': chunk
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


@app.schedule(Cron("0", "0,6,12,18", "*", "*", "?", "*"))
def ping(event):
    port = 443
    regions = get_regions()
    current_region = get_curr_region()
    current_partition = get_current_partition()
    results = []

    for region in regions:
        # CloudPing Counters and Lists
        times_list = []
        details_list = []

        # Pass/Fail counters
        failed = 0

        # Default to 4 connections max
        maxCount = 5
        count = 0
        passed = 0

        region_name = region['RegionName']
        target_partition = region.get('partition', 'aws')

        # Build partition-aware endpoint
        dns_suffix = get_dns_suffix(target_partition)
        endpoint = f'dynamodb.{region_name}.{dns_suffix}'

        # Loop while less than max count or until Ctrl-C caught
        while count < maxCount:

            # Increment Counter
            count += 1

            success = False

            # New Socket
            s = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)

            # 1sec Timeout
            s.settimeout(1)

            # Start a timer
            s_start = timer()

            # Try to Connect
            try:
                s.connect((endpoint, int(port)))
                s.shutdown(socket.SHUT_RD)
                success = True

            # Connection Timed Out
            except socket.timeout:
                print("Connection timed out!")
                failed += 1
            except OSError as e:
                print("OS Error:", e)
                failed += 1

            # Stop Timer
            s_stop = timer()
            s_runtime = "%.2f" % (1000 * (s_stop - s_start))

            if success:
                times_list.append(float(s_runtime))
                details_list.append({"M": {"seq": {"N": str((count-1))}, "time": {"N": str(float(s_runtime))}}})
                print("Connected to %s[%s]: tcp_seq=%s time=%s ms" % (endpoint, port, (count-1), s_runtime))
                passed += 1

            # Sleep for 1sec
            if count < maxCount:
                time.sleep(1)

        # Output Results when maxCount reached
        getResults(failed, count, passed)

        # Build the output data to be stored in DynamoDB
        if times_list:  # Only store results if we had successful connections
            minimum = min(times_list)
            maximum = max(times_list)
            add = sum(times_list)
            length = len(times_list)
            average = add / length
            results.append({
                "PutRequest": {
                    "Item": {
                        "avg": {"N": str(average)},
                        "min": {"N": str(minimum)},
                        "max": {"N": str(maximum)},
                        "port": {"N": str(port)},
                        "address": {"S": endpoint},
                        "region": {"S": current_region},
                        "regionTo": {"S": region_name},
                        "partition": {"S": current_partition},
                        "partitionTo": {"S": target_partition},
                        "attempts": {"N": str(maxCount)},
                        "attemptsSuccess": {"N": str(passed)},
                        "results": {"L": details_list},
                        "timestamp": {"S": get_current_time()}
                    }
                }
            })

    if results:
        write_results(results)
