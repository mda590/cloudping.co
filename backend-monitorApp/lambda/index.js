// 
// AWS Ping Test - Tests latency between regions of AWS.
// Matt Adorjan - matt@mattadorjan.com
// Lambda function
//

var AWS = require('aws-sdk');
var ddb = new AWS.DynamoDB({ region: 'us-east-2' });
var tcpp = require('tcp-ping');
var marshalItem = require('dynamodb-marshaler');
var params;

exports.handler = function (event, context) {
	// region where the requests are being generated

	// Use this with EC2
	//var region = "us-east-2";

	// Use this with Lambda
	var region = context.invokedFunctionArn.substring(15, context.invokedFunctionArn.indexOf(":506"));

	// us-east-1 (N Virginia)
	tcpp.ping({ address: 'dynamodb.us-east-1.amazonaws.com', port: 443, attempts: 5 }, function (err, data) {
		data["region"] = region;
		data["timestamp"] = new Date();
		data["regionTo"] = "us-east-1";
		params = { 'RequestItems': { 'PingTest': [{ 'PutRequest': { Item: marshalItem.marshalJson(JSON.stringify(data)) } }] } };
		console.log(region + ' to ' + data["regionTo"] + ' added to request.');

		// us-east-2 (Ohio)
		tcpp.ping({ address: 'dynamodb.us-east-2.amazonaws.com', port: 443, attempts: 5 }, function (err, data) {
			data["region"] = region;
			data["timestamp"] = new Date();
			data["regionTo"] = "us-east-2"
			params.RequestItems.PingTest.push({ 'PutRequest': { Item: marshalItem.marshalJson(JSON.stringify(data)) } });
			console.log(region + ' to ' + data["regionTo"] + ' added to request.');

			// us-west-1 (N California)
			tcpp.ping({ address: 'dynamodb.us-west-1.amazonaws.com', port: 443, attempts: 5 }, function (err, data) {
				data["region"] = region;
				data["timestamp"] = new Date();
				data["regionTo"] = "us-west-1"
				params.RequestItems.PingTest.push({ 'PutRequest': { Item: marshalItem.marshalJson(JSON.stringify(data)) } });
				console.log(region + ' to ' + data["regionTo"] + ' added to request.');

				// us-west-2 (Oregon)
				tcpp.ping({ address: 'dynamodb.us-west-2.amazonaws.com', port: 443, attempts: 5 }, function (err, data) {
					data["region"] = region;
					data["timestamp"] = new Date();
					data["regionTo"] = "us-west-2";
					params.RequestItems.PingTest.push({ 'PutRequest': { Item: marshalItem.marshalJson(JSON.stringify(data)) } });
					console.log(region + ' to ' + data["regionTo"] + ' added to request.');

					// ap-south-1 (Mumbai)
					tcpp.ping({ address: 'dynamodb.ap-south-1.amazonaws.com', port: 443, attempts: 5 }, function (err, data) {
						data["region"] = region;
						data["timestamp"] = new Date();
						data["regionTo"] = "ap-south-1"
						params.RequestItems.PingTest.push({ 'PutRequest': { Item: marshalItem.marshalJson(JSON.stringify(data)) } });
						console.log(region + ' to ' + data["regionTo"] + ' added to request.');

						// ap-northeast-2 (Seoul)
						tcpp.ping({ address: 'dynamodb.ap-northeast-2.amazonaws.com', port: 443, attempts: 5 }, function (err, data) {
							data["region"] = region;
							data["timestamp"] = new Date();
							data["regionTo"] = "ap-northeast-2"
							params.RequestItems.PingTest.push({ 'PutRequest': { Item: marshalItem.marshalJson(JSON.stringify(data)) } });
							console.log(region + ' to ' + data["regionTo"] + ' added to request.');

							// ap-southeast-1 (Singapore)
							tcpp.ping({ address: 'dynamodb.ap-southeast-1.amazonaws.com', port: 443, attempts: 5 }, function (err, data) {
								data["region"] = region;
								data["timestamp"] = new Date();
								data["regionTo"] = "ap-southeast-1";
								params.RequestItems.PingTest.push({ 'PutRequest': { Item: marshalItem.marshalJson(JSON.stringify(data)) } });
								console.log(region + ' to ' + data["regionTo"] + ' added to request.');

								// ap-southeast-2 (Sydney)
								tcpp.ping({ address: 'dynamodb.ap-southeast-2.amazonaws.com', port: 443, attempts: 5 }, function (err, data) {
									data["region"] = region;
									data["timestamp"] = new Date();
									data["regionTo"] = "ap-southeast-2"
									params.RequestItems.PingTest.push({ 'PutRequest': { Item: marshalItem.marshalJson(JSON.stringify(data)) } });
									console.log(region + ' to ' + data["regionTo"] + ' added to request.');

									// ap-northeast-1 (Tokyo)
									tcpp.ping({ address: 'dynamodb.ap-northeast-1.amazonaws.com', port: 443, attempts: 5 }, function (err, data) {
										data["region"] = region;
										data["timestamp"] = new Date();
										data["regionTo"] = "ap-northeast-1"
										params.RequestItems.PingTest.push({ 'PutRequest': { Item: marshalItem.marshalJson(JSON.stringify(data)) } });
										console.log(region + ' to ' + data["regionTo"] + ' added to request.');

										// eu-central-1 (Frankfurt)
										tcpp.ping({ address: 'dynamodb.eu-central-1.amazonaws.com', port: 443, attempts: 5 }, function (err, data) {
											data["region"] = region;
											data["timestamp"] = new Date();
											data["regionTo"] = "eu-central-1";
											params.RequestItems.PingTest.push({ 'PutRequest': { Item: marshalItem.marshalJson(JSON.stringify(data)) } });
											console.log(region + ' to ' + data["regionTo"] + ' added to request.');

											// eu-west-1 (Ireland)
											tcpp.ping({ address: 'dynamodb.eu-west-1.amazonaws.com', port: 443, attempts: 5 }, function (err, data) {
												data["region"] = region;
												data["timestamp"] = new Date();
												data["regionTo"] = "eu-west-1"
												params.RequestItems.PingTest.push({ 'PutRequest': { Item: marshalItem.marshalJson(JSON.stringify(data)) } });
												console.log(region + ' to ' + data["regionTo"] + ' added to request.');

												// ca-central-1 (Canada Central)
												tcpp.ping({ address: 'dynamodb.ca-central-1.amazonaws.com', port: 443, attempts: 5 }, function (err, data) {
													data["region"] = region;
													data["timestamp"] = new Date();
													data["regionTo"] = "ca-central-1"
													params.RequestItems.PingTest.push({ 'PutRequest': { Item: marshalItem.marshalJson(JSON.stringify(data)) } });
													console.log(region + ' to ' + data["regionTo"] + ' added to request.');

													// eu-west-2 (London)
													tcpp.ping({ address: 'dynamodb.eu-west-2.amazonaws.com', port: 443, attempts: 5 }, function (err, data) {
														data["region"] = region;
														data["timestamp"] = new Date();
														data["regionTo"] = "eu-west-2"
														params.RequestItems.PingTest.push({ 'PutRequest': { Item: marshalItem.marshalJson(JSON.stringify(data)) } });
														console.log(region + ' to ' + data["regionTo"] + ' added to request.');

														// sa-east-1 (Brazil)
														tcpp.ping({ address: 'dynamodb.sa-east-1.amazonaws.com', port: 443, attempts: 5 }, function (err, data) {
															data["region"] = region;
															data["timestamp"] = new Date();
															data["regionTo"] = "sa-east-1"
															params.RequestItems.PingTest.push({ 'PutRequest': { Item: marshalItem.marshalJson(JSON.stringify(data)) } });
															console.log(region + ' to ' + data["regionTo"] + ' added to request.');

															// put new test results into DynamoDB
															ddb.batchWriteItem(params, function (err, data) {
																if (err) console.log(err, err.stack); 				// an error occurred
																else console.log('Data successfully written to DynamoDB. See you soon!');           	// successful response
															});
														});
													});
												});
											});
										});
									});
								});
							});
						});
					});
				});
			});
		});
	});
};