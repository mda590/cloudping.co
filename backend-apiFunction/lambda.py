############################################################################################
#### AWS Inter-Region Latency Monitoring
# Provides the API interface for the retrieval and manipulation of data from DynamoDB.
# The data stored contains TCP latency averages between AWS regions.
#
# @author Matt Adorjan
# @email matt@mattadorjan.com
# @github https://github.com/mda590/cloudping.co
############################################################################################

import boto3
from boto3.dynamodb.conditions import Key, Attr
import botocore
from time import gmtime, strftime, strptime, mktime
import datetime
import json
import numpy

ec2 = boto3.client('ec2')

ddb = boto3.client(
    'dynamodb',
    region_name='us-east-2'
)

def getPastTimestamp(daysAgo, weeksAgo):
    """Returns the timestamp for a requested time in the past.

    Takes a certain number of days and/or weeks ago and uses Python's
    date & time functions to return the timestamp for a time in the past.

    Timestamp format: Y-m-dTH:M:S.000Z (2016-12-12T03:15:32.032Z)

    Parameters
    -----------
    daysAgo : int
        Number of days ago for which a timestamp should be returned.
    weeksAgo : int
        Number of weeks ago for which a timestamp should be returned.

    Returns
    -----------
    string
        The calculated timestamp for today-however many days/weeks requested.

    """
    # Convert values to integer
    daysAgo = int(daysAgo)
    weeksAgo = int(weeksAgo)
    
    # Calculate the past timestamp using the requested days/weeks ago values.
    pastDate = datetime.datetime.now() - datetime.timedelta(days=daysAgo, weeks=weeksAgo)
    # Convert the calculated timestamp to unix time.
    pastUnix = mktime(strptime(str(pastDate), "%Y-%m-%d %H:%M:%S.%f"))
    # Convert the unix time into the correctly formatted timestamp. Return the timestamp.
    return datetime.datetime.utcfromtimestamp(pastUnix).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def getLatestAvgs(daysAgo, weeksAgo, keyCondOpr):
    """Returns a JSON object with the latest latency averages.

    Takes a certain number of days and/or weeks ago, as well as the type of query to execute
    (greater than or less than timestamp). It then returns latency averages for all regions
    to all regions for the specific time period.

    For example, if I request daysAgo=1, DynamoDB would be queried for all regions to all regions
    with a time period of yesterday thru today. This function then takes the averages returned,
    there will be 4 since the function runs 4 times per day, and then averages those 4 values.
    The result is then returned in a properly formatted JSON object.

    Parameters
    -----------
    daysAgo : int
        Number of days ago for which a timestamp should be returned.
    weeksAgo : int
        Number of weeks ago for which a timestamp should be returned.
    keyCondOpr: string
        The keyCond array defines the conditions for the queries executed against DDB.

    Returns
    -----------
    json object
        Formatted json object containing averages to be returned to API caller.

    """
    if(keyCondOpr == 'GT'):
        keyCondInd = 0
    elif(keyCondOpr == 'LT'):
        keyCondInd = 1
    else:
        keyCondInd = 0
    
    jsonResp = '['
    
    for regionToList in getRegions()['Regions']:
        response = queryDB_regionTimestamp(regionToList['RegionName'], getPastTimestamp(daysAgo, weeksAgo), keyCondInd)
        jsonResp = jsonResp + '{"region": "' + regionToList['RegionName'] + '","averages":['

        for region in getRegions()['Regions']:
            region_avgs = []

            for record in response['Items']:
                if(region['RegionName'] == record['regionTo']['S']):
                    region_avgs.append(round(float(record['avg']['N']), 2))
            
            prevDayAvg = round(float(numpy.average(region_avgs)), 2)

            jsonResp = jsonResp + '{"regionTo":"' + region['RegionName'] + '", "average":' + str(prevDayAvg) + '},'

        jsonResp = jsonResp.rstrip(',')
        jsonResp = jsonResp + ']},'

    jsonResp = jsonResp.rstrip(',')
    jsonResp = jsonResp + ']'
    jsonResp = json.loads(jsonResp)

    return jsonResp

def getQueryResults(regionTo, regionFrom, daysAgo, weeksAgo, keyCondOpr):
    """Returns a JSON object with the requested averages.

    Takes a certain number of days and/or weeks ago, the type of query to execute
    (greater than or less than timestamp), and the region pair (to and from) for which to return averages.
    All averages will be returned for the specific time period defined in the query.

    Parameters
    -----------
    regionTo : string
        Region which is the ping destination to return results for.
    regionFrom : string
        Region which is the source of the ping to return results for.
    daysAgo : int
        Number of days ago for which a timestamp should be returned.
    weeksAgo : int
        Number of weeks ago for which a timestamp should be returned.
    keyCondOpr: string
        The keyCond array defines the conditions for the queries executed against DDB.

    Returns
    -----------
    json object
        Formatted json object containing averages to be returned to API caller.

    """
    if(keyCondOpr == 'GT'):
        keyCondInd = 0
    elif(keyCondOpr == 'LT'):
        keyCondInd = 1
    else:
        keyCondInd = 0

    response = queryDB_regionTimestamp(regionFrom, getPastTimestamp(daysAgo, weeksAgo), keyCondInd)
    jsonResp = '{"regionFrom":"' + regionFrom + '", "regionTo":"' + regionTo + '", "averages": ['

    for record in response['Items']:
        if(regionTo == record['regionTo']['S']):
            jsonResp = jsonResp + '{"timestamp":"' + record['timestamp']['S'] + '", "average":"' + str(round(float(record['avg']['N']), 2)) + '"},'

    jsonResp = jsonResp.rstrip(',')
    jsonResp = jsonResp + ']}'
    jsonResp = json.loads(jsonResp)

    return jsonResp

def getRegions():
    """
        Calls the AWS EC2 API to get the current list of AWS regions.
        Returns the list as a JSON object.
    """
    response = ec2.describe_regions()
    return response

def queryDB_regionTimestamp(regionName, timestamp, keyCondInd):
    """Performs a query against the DynamoDB table for latency information.

    When a query is required against the DynamoDB table where latency data is stored,
    this function will be called. The query will be executed and a JSON object will be returned
    in DynamoDB format.

    The query is executed against the 'region-timestamp-index' GSI. This uses the region
    as the PK and a timestamp as a hash key, so we can perform GT, LT, etc. operations against it.

    Parameters
    -----------
    regionName : string
        The name of the region to be used in the query.
    timestamp: string
        The timestamp to be used in the query.
    keyCondInd: int
        The keyCond array defines the conditions for the queries executed against DDB.
        0 = GT operation for timestamp
        1 = LT operation for timestamp

    Returns
    -----------
    json object
        JSON object containing the query results.

    """ 
    keyCond = ['#R = :regionVal AND #T > :timestampVal', 
                '#R = :regionVal AND #T < :timestampVal']
    
    response = ddb.query(
        TableName='PingTest',
        IndexName='region-timestamp-index',
        KeyConditionExpression=keyCond[keyCondInd],
        ExpressionAttributeNames={"#R":"region", "#T":"timestamp"},
        ExpressionAttributeValues={ ":regionVal":{"S":regionName}, ":timestampVal":{"S":timestamp}}
    )

    return response

def error_handler(error):
    """Returns a JSON string containing information on an error.

    When an error is encountered during execution, this function will be called to
    return a properly formatted error message, including pertinent information for that error.

    In general HTTP codes, are defined using the following:
        200 - OK, 400 - Bad Request (client), 500 - Internal Server Error (server)

    Parameters
    -----------
    error : object
        The original error object created when the error was encountered.

    Returns
    -----------
    json string
        The error message in a properly formatted json string.
        This is built using the build_error_json() function.

    """ 
    if error.response['Error']['Code'] == 'KeyError':
        return build_error_json('KeyError', '', 'Requested Key was not found.', 400)
    elif error.response['Error']['Code'] == 'NameError':
        return build_error_json('NameError', '', 'Requested Name was not found.', 400)
    else:
        return build_error_json('UnknownError', '', "Unexpected error: %s" % error, 400)

def build_error_json(errorCode, errorType, message, httpCode):
    """Builds the error json string.

    When an error is encountered during execution, this function is called by the error_handler
    function to build a properly formatted json string error.

    Parameters
    -----------
    errorCode : string
        The original error code created when the error was encountered.
    errorType : string
        Reserved for future use.
    message : string
        More details about the error which should be included in the error object returned.
    httpCode : int
        The 3 digit HTTP code associated with this error. (200, 300, 400)

    Returns
    -----------
    json string
        The error message in a properly formatted json string.

    """     
    
    # Build the JSON string using the inputs to the function.
    jsonResp = '{"errorType":"' + errorType + '", "errorCode":"' + errorCode + '", "httpCode":"' + httpCode + '", "message":"' + message + '"}'

    # Properly format the error object into JSON
    jsonResp = json.loads(jsonResp)
    # Convert the properly formatted JSON object back to a string, and pretty-print it for return.
    jsonResp = json.dumps(jsonResp, indent=2)

    return jsonResp

def lambda_handler(event, context):
    """Main function called by Lambda during execution.

    This function provides the backend for the API which will be called whenever information
    is requested from the AWS Inter-Region Latency API.

    This function checks the resource path which was called, as well as the HTTP method
    and then accesses the requested data from the API.

    Parameters
    -----------
    event : object
        All of the event payload generated by the API, as well as any message
        to be passed into the function.
    context : object
        Lambda context information.

    Returns
    -----------
    object
        Either an error message, or the data requested when making a call to the API.

    """     

    # Ensure that the resource path is included in the message from the API.
    # If not, throw an error. This is required for further execution.
    try:
        resourcePath = event['context']['resource-path']
    except botocore.exceptions.ClientError as e:
        return error_handler(e)

    # Ensure that the http method is included in the message from the API.
    # If not, throw an error. This is required for further execution.
    try:
        httpMethod = event['context']['http-method']
    except botocore.exceptions.ClientError as e:
        return error_handler(e)

    if(resourcePath == '/getlatestavgs'):
        return getLatestAvgs(1, 0, 'GT')

    elif(resourcePath == '/averages'):
        return getLatestAvgs(1, 0, 'GT')

    elif(resourcePath == '/averages/day'):
        return getLatestAvgs(1, 0, 'GT')

    elif(resourcePath == '/averages/day/{numdays}'):
        try:
            numDays = event['params']['path']['numdays']
        except botocore.exceptions.ClientError as e:
            return error_handler(e)

        return getLatestAvgs(numDays, 0, 'GT')

    elif(resourcePath == '/averages/week'):
        return getLatestAvgs(0, 1, 'GT')

    elif(resourcePath == '/averages/week/{numweeks}'):
        try:
            numWeeks = event['params']['path']['numweeks']
        except botocore.exceptions.ClientError as e:
            return error_handler(e)

        return getLatestAvgs(0, numWeeks, 'GT')

    elif(resourcePath == '/averages/month'):
        return getLatestAvgs(0, 4, 'GT')

    elif(resourcePath == '/averages/month/{nummonths}'):
        try:
            numMonths = event['params']['path']['nummonths']
        except botocore.exceptions.ClientError as e:
            return error_handler(e)

        return getLatestAvgs(0, numMonths*4, 'GT')

    elif(resourcePath == '/query' and httpMethod == 'POST'):
        try:
            query = event['body-json']
        except botocore.exceptions.ClientError as e:
            return error_handler(e)

        return getQueryResults(query['regionTo'], query['regionFrom'], query['daysAgo'], query['weeksAgo'], query['condOpr'])
        
    else:
        return 'No functionality is available for that request.'