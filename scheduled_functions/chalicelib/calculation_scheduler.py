import boto3
import json
import sys

session = boto3.Session()
dynamodb = session.resource('dynamodb', region_name="us-east-2")
regions_table_enhanced = dynamodb.Table('cloudping_regions_enhanced')
stored_avgs_table = dynamodb.Table('cloudping_stored_avgs')
lambda_client = session.client('lambda', region_name="us-east-2")

def is_region_active(region_object):
    status = region_object["status"]
    function_exists = region_object["ping_function_exists"]
    earliest_data_timestamp = region_object["earliest_data_timestamp"]

    if status in ["ENABLED", "ENABLED_BY_DEFAULT"] and \
        function_exists and earliest_data_timestamp is not "None":
        return True
    return False

def schedule(calc_func_name):
    timeframes_to_store = ['1D', '1W', '1M', '1Y']

    regions_enhanced_response = regions_table_enhanced.scan()

    for region in regions_enhanced_response['Items']:
        region_id = region['region_name']
        region_active = is_region_active(region)

        if region_active:
            for timeframe in timeframes_to_store:
                print(region_id, region_active, timeframe)
                # Invoke Lambda function
                lambda_response = lambda_client.invoke(
                    FunctionName=calc_func_name,
                    InvocationType='RequestResponse',
                    LogType='None',
                    Payload=json.dumps({
                        'region': region_id,
                        'execution_source': 'scheduled',
                        'latency_range': timeframe
                    })
                )
                if lambda_response['StatusCode'] != 200:
                    print(lambda_response['FunctionError'], lambda_response['StatusCode'])
                    sys.exit(1)
                calculated_averages = res_json = json.loads(lambda_response['Payload'].read().decode("utf-8"))

                # Store data received back in DynamoDB
                for avg in calculated_averages[region_id]:
                    region_to = avg['region_to']
                    avg_latency = avg['avg_latency']
                    
                    item = {
                        "index": "{}_{}_{}".format(region_id, region_to, timeframe),
                        "region_from": region_id,
                        "timeframe": timeframe,
                        "region_to": region_to,
                        "latency": avg_latency,
                        "p_10": avg['p_10'],
                        "p_25": avg['p_25'],
                        "p_50": avg['p_50'],
                        "p_75": avg['p_75'],
                        "p_90": avg['p_90'],
                        "p_98": avg['p_98'],
                        "p_99": avg['p_99']
                    }
                    
                    try:
                        response = stored_avgs_table.put_item(
                            Item=item
                        )
                    except:
                        print("An error occurred with the following item:")
                        print(item)
                        print(response)

    return {
        "message": "Function execution completed successfully.",
        "event": calc_func_name
    }

if __name__ == "__main__":
    schedule("scheduled_functions-prod-calculate_avgs")