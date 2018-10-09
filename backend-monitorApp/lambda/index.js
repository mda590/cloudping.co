// 
// AWS Ping Test - Tests latency between regions of AWS.
// Matt Adorjan - matt@mattadorjan.com
// Lambda function
//

var AWS = require('aws-sdk');
var ddb = new AWS.DynamoDB({ region: 'us-east-2' });
var tcpp = require('tcp-ping');
var marshalItem = require('dynamodb-marshaler');

const regions = [
	'ap-northeast-1',   // Tokyo
	'ap-northeast-2',   // Seoul
	'ap-northeast-3',   // Osaka
	'ap-south-1',       // Mumbai
	'ap-southeast-1',   // Singapore
	'ap-southeast-2',   // Sydney
	'ca-central-1',     // Canada Central
	'eu-central-1',     // Frankfurt
	'eu-west-1',        // Ireland
	'eu-west-2',        // London
	'us-east-1',        // N Virginia
	'us-east-2',        // Ohio
	'us-west-1',        // N California
	'us-west-2',        // Oregon
	'sa-east-1',        // Brazil
];

const pingRegionAsync = function (region) {
	return new Promise((resolve, reject) => {
		const payload = { 
			address: `dynamodb.${region}.amazonaws.com`,
			port: 443,
			attempts: 5
		};

		tcpp.ping(payload, (err, data) => {
			if (err) reject(err);

			data['timestamp'] = new Date();
			data['regionTo'] = region;
			console.log(`ping ${region} took an average of ${data.avg}ms.`);
			resolve(data);
		});
	});
};

exports.handler = function (event, context) {
	// region where the requests are being generated

	// Use this with EC2
	//var region = "us-east-2";

	// Use this with Lambda
	var sourceRegion = context.invokedFunctionArn.substring(15, context.invokedFunctionArn.indexOf(":506"));

	Promise.all(regions.map(pingRegionAsync)).then(function (results) {
		const params = {
			RequestItems: {
				PingTest: results.map((result) => {
					result['region'] = sourceRegion;
					return {
						PutRequest: {
							Item: marshalItem.marshalJson(JSON.stringify(result));
						}
					};
				})
			}
		};
		ddb.batchWriteItem(params, function (err, data) {
			if (err) console.log(err, err.stack);                                     // an error occurred
			else console.log('Data successfully written to DynamoDB. See you soon!'); // successful
		});
	});
};
