from chalice import Chalice, Cron
from timeit import default_timer as timer

import datetime
import socket
import signal
import boto3
import time
import sys

app = Chalice(app_name='ping_from_region')

def get_current_time():
    time = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + "Z"
    return time

def get_curr_region():
    my_session = boto3.session.Session()
    my_region = my_session.region_name
    return my_region

def get_regions():
    client = boto3.client('ec2')
    response = client.describe_regions()
    return response['Regions']

def getResults(failed, count, passed):
    """ Summarize Results """

    lRate = 0
    if failed != 0:
        lRate = failed / (count) * 100
        lRate = "%.2f" % lRate

    print("\nTCP Ping Results: Connections (Total/Pass/Fail): [{:}/{:}/{:}] (Failed: {:}%)".format((count), passed, failed, str(lRate)))
    # avg min max port region regionTo attempts address
    # results list: [{ "seq" "time"}]

def write_results(results):
    client = boto3.client('dynamodb', region_name="us-east-2")      # DynamoDB Table is always in us-east-2
    response = client.batch_write_item(
        RequestItems={
            'PingTest': results
        }
    )

app.schedule(Cron("0", "0,6,12,18", "*", "*", "?", "*"))
def ping(event):
    port = 443
    regions = get_regions()
    current_region = get_curr_region()
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
        endpoint = 'dynamodb.' + region_name + '.amazonaws.com'
        
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
                    "attempts": {"N": str(maxCount)},
                    "attemptsSuccess": {"N": str(passed)},
                    "results": {"L": details_list},
                    "timestamp": {"S": get_current_time()}
                }
            }
        })
        write_results(results)
