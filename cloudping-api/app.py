from chalice import Chalice, Response
from chalice.app import BadRequestError
from typing import Optional, Dict, List
import boto3
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key, Attr
import os

app = Chalice(app_name='cloudping-api')
dynamodb = boto3.resource('dynamodb')
latencies_table = dynamodb.Table(os.environ.get('LATENCIES_TABLE', 'cloudping_stored_avgs'))
ping_table = dynamodb.Table(os.environ.get('PING_TEST_TABLE', 'PingTest'))
regions_table = dynamodb.Table('cloudping_regions')

VALID_PERCENTILES = ['p_10', 'p_25', 'p_50', 'p_75', 'p_90', 'p_98', 'p_99', 'latency']
VALID_TIMEFRAMES = ['1D', '1W', '1M', '1Y']

def validate_params(percentile: Optional[str], timeframe: Optional[str]) -> None:
    """Validate input parameters."""
    if percentile and percentile not in VALID_PERCENTILES:
        raise BadRequestError(f"Invalid percentile. Must be one of: {', '.join(VALID_PERCENTILES)}")
    if timeframe and timeframe not in VALID_TIMEFRAMES:
        raise BadRequestError(f"Invalid timeframe. Must be one of: {', '.join(VALID_TIMEFRAMES)}")

@app.route('/latencies')
def get_latencies():
    """Get latency matrix for all or specific regions."""
    params = app.current_request.query_params or {}
    percentile = params.get('percentile', 'p_50')
    timeframe = params.get('timeframe', '1D')
    from_region = params.get('from')
    to_region = params.get('to')

    validate_params(percentile, timeframe)

    try:
        # Query DynamoDB for latencies
        if from_region and to_region:
            # Query for specific region pair
            response = latencies_table.query(
                KeyConditionExpression=Key('region_from').eq(from_region) & 
                                     Key('region_to').eq(to_region),
                FilterExpression=Attr('timeframe').eq(timeframe)
            )
        else:
            # Query for all regions
            response = latencies_table.scan(
                FilterExpression=Attr('timeframe').eq(timeframe)
            )

        # Process and format the data
        result = {
            "metadata": {
                "percentile": percentile,
                "timeframe": timeframe,
                "unit": "milliseconds"
            },
            "data": {}
        }

        # Transform the data into the matrix format
        for item in response.get('Items', []):
            from_reg = item['region_from']
            to_reg = item['region_to']
            if from_reg not in result['data']:
                result['data'][from_reg] = {}
            # Convert DynamoDB Decimal to float
            result['data'][from_reg][to_reg] = float(item[percentile])

        return Response(body=result,
                      headers={'Content-Type': 'application/json',
                              'Access-Control-Allow-Origin': '*'})

    except Exception as e:
        return Response(
            body={'error': str(e)},
            status_code=500,
            headers={'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'}
        )

@app.route('/history', api_key_required=True)
def get_history():
    """Get historical average latency data for specific region pairs."""
    params = app.current_request.query_params or {}
    
    # Required parameters
    from_region = params.get('from')
    to_region = params.get('to')
    if not from_region or not to_region:
        raise BadRequestError("Both 'from' and 'to' regions are required")

    # Parse date range
    end = params.get('end', datetime.utcnow().isoformat())
    # Default to 7 days if no start provided
    default_start = (datetime.fromisoformat(end.replace('Z', '')) - timedelta(days=7)).isoformat()
    start = params.get('start', default_start)

    try:
        # Query DynamoDB for historical data
        response = ping_table.query(
            IndexName='region-timestamp-index',
            KeyConditionExpression=
                Key('region').eq(from_region) & 
                Key('timestamp').between(start, end),
            FilterExpression=Attr('regionTo').eq(to_region),
            ProjectionExpression='#ts, #avg',
            ExpressionAttributeNames={
                '#ts': 'timestamp',
                '#avg': 'avg'
            }
        )

        # Process the data - note that items are already deserialized
        processed_data = [
            {
                'timestamp': item['timestamp'],  # Already a string
                'value': float(item['avg'])      # Convert to float
            }
            for item in response.get('Items', [])
        ]

        result = {
            "metadata": {
                "from": from_region,
                "to": to_region,
                "start": start,
                "end": end,
                "points": len(processed_data)
            },
            "data": processed_data
        }

        return Response(
            body=result,
            headers={
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'public, max-age=300'  # Cache for 5 minutes
            }
        )

    except Exception as e:
        return Response(
            body={'error': str(e)},
            status_code=500,
            headers={'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'}
        )

@app.route('/regions')
def get_regions():
    """Get list of available regions."""
    try:
        # Query DynamoDB for unique regions
        response = regions_table.query(
            IndexName='active_from-region-index',
            KeyConditionExpression=Key('active_from').eq('True'),
            ScanIndexForward=True
        )

        # Extract unique regions from the response
        regions = set()
        for item in response.get('Items', []):
            regions.add(item['region'])

        result = {
            "regions": sorted(list(regions))
        }

        return Response(body=result,
                      headers={'Content-Type': 'application/json',
                              'Access-Control-Allow-Origin': '*'})

    except Exception as e:
        return Response(
            body={'error': str(e)},
            status_code=500,
            headers={'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'}
        )

@app.route('/status')
def get_status():
    """Get API status and latest data timestamp."""
    try:
        # Query DynamoDB using region-timestamp-index with a high limit
        # and scan index forward false to get the latest timestamp
        response = ping_table.query(
            IndexName='region-timestamp-index',
            KeyConditionExpression=Key('region').eq('us-east-1'),  # Using us-east-1 as it's likely to have consistent data
            Limit=1,
            ScanIndexForward=False,  # This will get the most recent first
            ProjectionExpression='#ts',
            ExpressionAttributeNames={
                '#ts': 'timestamp'
            }
        )

        latest_timestamp = response['Items'][0]['timestamp'] if response['Items'] else None

        result = {
            "status": "healthy",
            "latest_update": latest_timestamp,
            "version": "1.0.0"
        }

        return Response(
            body=result,
            headers={
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'public, max-age=60'  # Cache for 1 minute
            }
        )

    except Exception as e:
        return Response(
            body={'error': str(e)},
            status_code=500,
            headers={
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        )
