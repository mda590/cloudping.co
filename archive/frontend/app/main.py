from boto3.dynamodb.conditions import Key, Attr
from flask import Flask, render_template, request, redirect, url_for

import boto3
import json

app = Flask(__name__)

try:
    # Used for development
    session = boto3.Session(profile_name='mda2')
except:
    # Used when running on AWS, when above profile name is not found
    session = boto3.Session()
dynamodb = session.resource('dynamodb', region_name='us-east-2')

def get_enabled_regions():
    table = dynamodb.Table('cloudping_regions')
    response = table.query(
        IndexName='active_from-region-index',
        KeyConditionExpression=Key('active_from').eq('True'),
        ScanIndexForward=True
    )

    return response['Items']

def get_enabled_regions_to():
    table = dynamodb.Table('cloudping_regions')
    response = table.query(
        IndexName='active_to-region-index',
        KeyConditionExpression=Key('active_to').eq('True'),
        ScanIndexForward=True
    )

    return response['Items']

def get_dynamodb_data(timeframe):
    table = dynamodb.Table('cloudping_stored_avgs')
    response = table.scan(
        FilterExpression=Key('timeframe').eq(timeframe.upper())
    )

    return response['Items']

@app.route('/')
def home():
    return redirect(url_for('grid'))

@app.route('/grid', defaults={'show_data': 'p_50', 'timeframe': '1D'})
@app.route("/grid/<show_data>/timeframe/<timeframe>")
def grid(show_data, timeframe):
    return_data = {}
    enabled_regions = get_enabled_regions()
    enabled_regions_to = get_enabled_regions_to()

    data = get_dynamodb_data(timeframe)

    for item in data:
        item_split = item['index'].split("_")
        region_from = item_split[0]
        region_to = item_split[1]
        timeframe = item_split[2]

        if region_from not in return_data:
            return_data[region_from] = {}
        if region_to not in return_data[region_from]:
            return_data[region_from][region_to] = {}

        return_data[region_from][region_to] = {
            'region_from': region_from,
            'region_from_name': '',
            'region_to': region_to,
            'region_to_name': '',
            'latency': round(float(item['latency']), 2),
            'p_10': round(float(item['p_10']), 2),
            'p_25': round(float(item['p_25']), 2),
            'p_50': round(float(item['p_50']), 2),
            'p_75': round(float(item['p_75']), 2),
            'p_90': round(float(item['p_90']), 2),
            'p_98': round(float(item['p_98']), 2),
            'p_99': round(float(item['p_99']), 2),
        }

    return render_template(
        'index.html',
        title='Home', 
        values=return_data,
        regions_from=enabled_regions,
        regions_to=enabled_regions_to,
        show_data=show_data,
        selected_percentile=show_data,
        selected_timeframe=timeframe
    )

@app.route('/about')
def about():
    enabled_regions = get_enabled_regions()
    return render_template('about.html', title='About CloudPing', regions_from=enabled_regions)

@app.route('/provider/<provider>')
def provider(provider):
    return provider

@app.route('/detail/<provider>/<region_from>/<region_to>')
def region_to_region(provider, region_from, region_to):
    return provider, region_from, region_to

if __name__ == '__main__':
    app.run(debug=True)