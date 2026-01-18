"""
Account Region Manager for AWS European Sovereign Cloud (EUSC).

This Lambda function runs in the EUSC partition and is designed to automatically
enable new EUSC regions as they become available.

Note: The Account API (list_regions, enable_region) is not currently available
in EUSC. This function uses hardcoded regions as a fallback and will attempt
to use the Account API when it becomes available.
"""

from chalice import Chalice, Cron
import boto3
import logging
from datetime import datetime
from botocore.exceptions import ClientError

app = Chalice(app_name='account-region-manager-eusc')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Known EUSC regions - hardcoded since account:ListRegions is not available in EUSC
# Update this list as new EUSC regions become available
EUSC_REGIONS = [
    'eusc-de-east-1',
]


def get_account_id():
    """Get the current AWS account ID."""
    sts = boto3.client('sts')
    return sts.get_caller_identity()['Account']


def get_all_regions():
    """
    Get a list of all AWS regions in the current partition.

    Attempts to use EC2 DescribeRegions first, falls back to hardcoded
    regions if that's not available.
    """
    try:
        ec2 = boto3.client('ec2')
        regions = [region['RegionName'] for region in ec2.describe_regions(AllRegions=True)['Regions']]
        print(f"Retrieved {len(regions)} regions from EC2 API")
        return regions
    except ClientError as e:
        print(f"EC2 DescribeRegions not available, using hardcoded regions: {str(e)}")
        return EUSC_REGIONS.copy()


def get_region_status():
    """
    Get the status of all regions in the current partition.

    Attempts to use the Account API first, falls back to hardcoded regions
    if the API is not available (which is currently the case in EUSC).

    Returns a dict with region statuses and whether they're opt-in regions.
    """
    client = boto3.client('account')

    try:
        paginator = client.get_paginator('list_regions')
        page_iterator = paginator.paginate(
            RegionOptStatusContains=[
                'ENABLED', 'ENABLING', 'DISABLING', 'DISABLED', 'ENABLED_BY_DEFAULT',
            ]
        )
        region_status = {}

        for page in page_iterator:
            for region in page['Regions']:
                region_name = region['RegionName']
                status = region['RegionOptStatus']
                is_opt_in = True if status != "ENABLED_BY_DEFAULT" else False

                region_status[region_name] = {
                    'status': status,
                    'is_opt_in': is_opt_in
                }
        print("Successfully retrieved region status from Account API")
        return region_status
    except ClientError as e:
        print(f"Account API not available, using hardcoded regions: {str(e)}")
        # Fall back to hardcoded regions - assume all are enabled and opt-in
        return {
            region: {'status': 'ENABLED', 'is_opt_in': True}
            for region in EUSC_REGIONS
        }


def enable_region(region_name, region_info):
    """
    Enable a specific AWS region for the account if it's an opt-in region.

    Note: The Account API (enable_region) is not currently available in EUSC.
    This function will gracefully skip if the API is unavailable.

    Args:
        region_name: Name of the region
        region_info: Dict containing region status and opt-in information
    """
    if not region_info['is_opt_in']:
        print(f"Region {region_name} is not an opt-in region - no action needed")
        return True

    if region_info['status'] in ['ENABLED', 'ENABLED_BY_DEFAULT']:
        print(f"Region {region_name} is already enabled")
        return True

    if region_info['status'] == 'ENABLING':
        print(f"Region {region_name} is currently being enabled")
        return True

    client = boto3.client('account')

    try:
        client.enable_region(RegionName=region_name)
        print(f"Successfully initiated enable process for region: {region_name}")
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if 'RegionAlreadyEnabledException' in str(e):
            print(f"Region {region_name} is already enabled")
            return True
        elif 'RegionAlreadyInProgressException' in str(e):
            print(f"Region {region_name} is already being enabled")
            return True
        elif error_code == 'AccessDeniedException' or 'Unable to determine service' in str(e):
            print(f"Account API not available in EUSC - cannot enable region {region_name} programmatically")
            return False
        else:
            print(f"Error enabling region {region_name}: {str(e)}")
            return False


@app.schedule(Cron("*", "0", "*", "*", "?", "*"))
def check_and_enable_regions(event):
    """
    Scheduled task that runs daily to check for and enable new EUSC regions.
    """
    print(f"Starting EUSC region check at {datetime.now()}")

    try:
        # Get all available regions (in EUSC, this returns only EUSC regions)
        all_regions = get_all_regions()
        print(f"Found {len(all_regions)} total EUSC regions")

        # Get status of all regions
        region_status = get_region_status()
        print(f"Retrieved status for {len(region_status)} regions")

        # Process each region
        results = []
        for region in all_regions:
            if region not in region_status:
                print(f"No status information available for region {region}")
                continue

            region_info = region_status[region]

            # Check if region needs to be enabled
            if region_info['is_opt_in'] and region_info['status'] not in ['ENABLED', 'ENABLED_BY_DEFAULT', 'ENABLING']:
                success = enable_region(region, region_info)
                results.append({
                    'region': region,
                    'status': 'success' if success else 'failed',
                    'is_opt_in': region_info['is_opt_in'],
                    'current_status': region_info['status']
                })
            else:
                print(f"Region {region} does not need action (Status: {region_info['status']}, Opt-in: {region_info['is_opt_in']})")

        return {
            'statusCode': 200,
            'body': {
                'message': f"Processed {len(results)} EUSC regions that needed action",
                'results': results
            }
        }

    except Exception as e:
        error_msg = f"Unexpected error in check_and_enable_regions: {str(e)}"
        print(error_msg)
        return {
            'statusCode': 500,
            'body': error_msg
        }


if __name__ == "__main__":
    check_and_enable_regions(None)
