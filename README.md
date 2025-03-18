# CloudPing.co

CloudPing records inter-region latency over TCP connections between all AWS regions in real-time, providing a continuously updated, reliable source of truth for AWS region-to-region latency metrics.

## About

When building global AWS deployments, knowing which inter-region transactions will face the most latency is crucial for system design. While static examples and anecdotal guidance based on geographic location exist, CloudPing.co offers a dynamic, consistently updated latency monitoring service that tracks real-world performance between all AWS regions.

## Architecture

CloudPing.co consists of several microservices working together:

## Components

### 1. Frontend (`cloudping-frontend-njs/`)

A Next.js application that provides an interactive user interface for viewing latency data.

- Modern responsive design with Tailwind CSS
- Interactive latency matrix with filtering capabilities
- Visualization tools to help understand region relationships
- Supports viewing different time periods (daily, weekly, monthly, yearly)
- Ability to filter regions and view by percentiles (P50, P90, etc.)

### 2. API Service (`cloudping-api/`)

A serverless API built with AWS Chalice that provides endpoints for accessing latency data.

- RESTful endpoints for retrieving latency information
- Support for filtering by region, timeframe, and percentile
- Historical data access with API key authentication
- Provides region status information

### 3. Ping Functions (`ping_from_region/`)

Lambda functions deployed to each AWS region that measure TCP latency to all other regions.

- Runs every 6 hours in each active AWS region
- Measures TCP connection time to AWS service endpoints
- Records raw results in DynamoDB for historical tracking
- Stores detailed round-trip information for analysis

### 4. Scheduled Functions (`scheduled_functions/`)

Background tasks that process raw ping data to calculate statistics and summaries.

- Calculates daily, weekly, monthly, and annual averages
- Computes percentiles (P10, P25, P50, P75, P90, P98, P99)
- Stores aggregated data in DynamoDB tables
- Updates region status information

### 5. Ping Function Deployer (`ping-function-deployer/`)

Automated deployment service that ensures ping functions exist in all AWS regions.

- Automatically deploys ping functions to new regions
- Updates function code when changes are made
- Sets up appropriate CloudWatch Event Rules for scheduling
- Maintains consistent monitoring across the AWS global infrastructure

### 6. Account Region Manager (`account-region-manager/`)

Service that monitors and enables new AWS regions automatically.

- Checks for newly available AWS regions
- Automatically enables opt-in regions for the account
- Ensures CloudPing.co expands to cover new regions as they launch
- Maintains region status information

### Database Structure

CloudPing.co uses Amazon DynamoDB for data storage:

- `PingTest` - Raw data from all region-to-region pings
- `cloudping_regions` - Configuration data for all AWS regions
- `cloudping_stored_avgs` - Processed averages and percentiles used by the frontend

## Local Development

### Prerequisites

- Python 3.9+
- Node.js 18+
- AWS CLI configured with appropriate credentials
- Docker (optional, for container-based development)

### Setting Up the Frontend

```bash
# Navigate to the frontend directory
cd cloudping-frontend-njs

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at http://localhost:3000

### Setting Up the API

```bash
# Navigate to the API directory
cd cloudping-api

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run local API server
chalice local
```

The API will be available at http://localhost:8000

### Testing Ping Functions

```bash
# Navigate to the ping function directory
cd ping_from_region

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the function locally
python -c "from app import ping; ping({})"
```

### Setting Up Scheduled Functions

```bash
# Navigate to the scheduled functions directory
cd scheduled_functions

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run individual functions
python -c "from chalicelib.calculate_avgs import calculate; calculate({})"
```

## Deployment

The Lambda functions are deployed with AWS Chalice:

```bash
# Example: Deploy ping functions
cd ping_from_region
chalice deploy --stage prod
```

The frontend is deployed as a Docker container in AWS Fargate:

```bash
# Build and deploy the frontend
cd cloudping-frontend-njs
docker build -t cloudping-frontend .
```

## Future Enhancements

- Enhanced API access for raw data and custom queries
- Interactive graphs showing latency trends over time
- Support for GovCloud and China regions
- Additional cloud providers beyond AWS

## Contributing

Contributions to CloudPing.co are welcome! If you'd like to help improve the project, please feel free to submit pull requests or open issues.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions or feedback, please contact [matt@ma.dev](mailto:matt@ma.dev).