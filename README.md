# AWS Inter-Region Latency Monitoring

## Records inter-region latency over a TCP connection between all AWS regions.

### About this Project
Over time, as I've worked on global AWS deployments, I have often been faced with the question of which inter-region transactions will be faced with the most latency.
I have been able to find a lot of static examples of previous testing completed, or anecdotal thoughts based on a region's location. I haven't been able to find any kind of dynamic, consistently updated, latency monitoring.
The goal here is to provide a single source of truth for inter-region AWS region latency.

### How data is collected
* The latency test is performed using the Node.JS "tcp-ping" package (https://www.npmjs.com/package/tcp-ping). The tests are executed against the DynamoDB endpoint URL in each region, on TCP port 443.
* Every region performs a test every 6 hours (0000, 0600, 1200, 1800 UTC) by "pinging" every region's DynamoDB endpoint. The data is then stored in a DynamoDB database for later access.
* For regions with Lambda, the Node.JS code is stored in a Lambda function and executed by a CloudWatch Event calling the Lambda function at the specific times.
* For regions without Lambda, the Node.JS code runs on an EC2 instance, and is scheduled via a cron job every 6 hours. A Lambda function ensures that these EC2 instances are powered on 1 hour prior to test execution, and are shut down within 1 hour after the test executes.

### How to access the data
* Website: You can access a summary of the data at the following location:  https://www.cloudping.co. Note, the table on this page is based on the averages for tests performed in the previous 24-hours.
* API: Coming soon! API documentation is available here: https://www.cloudping.co/apidocs.

### Project Structure
* backend-apiFunction - the Lambda function which is executed whenever a request is made to the API to retrieve data.
* backend-monitorApp - the Node.JS code used on either Lambda or EC2 and executed every 6 hours to record latency data to DynamoDB.
* frontend-build - the front-end web application used for summarizing and displaying data pulled from the API. Uses the Vue.JS framework.

### TODO
* API access - both to raw data stored in DyanmoDB, as well as to specific queries used primarily by the web front-end.
* Graph showing latency over time for user selected parameters (between regions, specific timeframes, etc.)
* Refine the getLatestAvgs function in the API backend.
* Add city/location names whenever a region name is displayed (e.g. us-east-2 = Ohio)
* Alphabetize the regions in the table.
* Add API key

#### Additional Notes
This project is in no way associated with Amazon or AWS. If you wish to report any issues with the project, please use the "Issues" feature within GitHub.