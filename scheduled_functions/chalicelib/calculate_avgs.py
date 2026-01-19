from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timedelta

import boto3
import decimal
import json
import numpy as np
import sys

def get_curr_region():
    my_session = boto3.session.Session()
    my_region = my_session.region_name
    return my_region

def calculate(event):
    session = boto3.Session()
    dynamodb = session.resource('dynamodb', region_name=get_curr_region())
    table = dynamodb.Table('PingTest')

    try:
        region_name = event['region']
    except:
        print('Must define "region" in the payload passed to this function.')
        sys.exit(1)

    try:
        execution_source = event['execution_source']
    except:
        print('Must define "execution_source" in the payload passed to this function.')
        sys.exit(1)
    
    try:
        latency_range = event['latency_range']
    except:
        print('Must define "latency_range" in the payload passed to this function.')
        sys.exit(1)

    range_start = ''
    range_end = ''
    if latency_range == 'RANGE':
        range_start = event['custom_range']['range_start_timestamp']
        range_end = event['custom_range']['range_end_timestamp']

    timestamp_query_map = {
        '1D': Key('timestamp').gte((datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")),
        '1W': Key('timestamp').gte((datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")),
        '1M': Key('timestamp').gte((datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")),
        '1Y': Key('timestamp').gte((datetime.now() - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")),
        'MTD': Key('timestamp').gte(datetime(datetime.today().year, datetime.today().month, 1).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
        'YTD': Key('timestamp').gte(datetime(datetime.today().year, 1, 1).strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
        'RANGE': Key('timestamp').between(range_start, range_end)
    }

    regions_to_avg = {}
    response = table.query(
        IndexName='region-timestamp-index',
        KeyConditionExpression=Key('region').eq(region_name) & timestamp_query_map[latency_range]
    )

    for i in response['Items']:
        if i['regionTo'] not in regions_to_avg:
            regions_to_avg[i['regionTo']] = []
        regions_to_avg[i['regionTo']].append(i['avg'])
    while 'LastEvaluatedKey' in response:
        response = table.query(
            IndexName='region-timestamp-index',
            KeyConditionExpression=Key('region').eq(region_name) & timestamp_query_map[latency_range],
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        # Loop through all of the different latencies returned for the time period requested
        # Group the latencies all together in a JSON object
        # Object ends up looking like regions_to_avg = {'region_name': ['latency1', 'latency2', 'latency3'], 'region_name': ['latency1', 'latency2']}
        for i in response['Items']:
            if i['regionTo'] not in regions_to_avg:
                regions_to_avg[i['regionTo']] = []
            regions_to_avg[i['regionTo']].append(i['avg'])

    # Loop through the regions_to_avg JSON object
    # Take all of the different latencies for each region and average them
    # Store the results in the avgs_to_return JSON object
    avgs_to_return = {region_name: []}
    for region in regions_to_avg:
        a = np.array([float(l) for l in regions_to_avg[region]])
        p_10 = np.percentile(a, 10)
        p_25 = np.percentile(a, 25)
        p_50 = np.percentile(a, 50)
        p_75 = np.percentile(a, 75)
        p_90 = np.percentile(a, 90)
        p_98 = np.percentile(a, 98)
        p_99 = np.percentile(a, 99)
        avg = sum(regions_to_avg[region]) / len(regions_to_avg[region])
        print(p_25, p_50, p_90, p_98, p_99)
        avgs_to_return[region_name].append(
            {
                "region_to": region,
                "avg_latency": str(avg),
                "p_10": str(p_10),
                "p_25": str(p_25),
                "p_50": str(p_50),
                "p_75": str(p_75),
                "p_90": str(p_90),
                "p_98": str(p_98),
                "p_99": str(p_99)
            }
        )

    print(json.dumps(avgs_to_return))
    return avgs_to_return

if __name__ == "__main__":
    event = {
        'region': "us-west-2",
        'execution_source': 'scheduled',
        'latency_range': '1D'
    }
    calculate(event)