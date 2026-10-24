import os
import logging
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SITE_URL = "https://cloudping.co"
STALE_THRESHOLD_HOURS = 24


def check_site_reachable():
    """Check if cloudping.co returns HTTP 200."""
    try:
        req = Request(SITE_URL, method="GET")
        with urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                return None
            return f"Site returned HTTP {resp.status}"
    except HTTPError as e:
        return f"Site returned HTTP {e.code}"
    except URLError as e:
        return f"Site unreachable: {e.reason}"
    except Exception as e:
        return f"Site check failed: {str(e)}"


def check_data_staleness():
    """Check if any active region has data older than 24 hours."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
    table = dynamodb.Table("cloudping_regions_enhanced")

    response = table.scan()
    regions = response["Items"]

    now = datetime.now(timezone.utc)
    threshold = now - timedelta(hours=STALE_THRESHOLD_HOURS)
    stale_regions = []

    for region in regions:
        status = region.get("status", "")
        has_function = region.get("ping_function_exists", False)

        if status not in ("ENABLED", "ENABLED_BY_DEFAULT"):
            continue
        if not has_function:
            continue

        most_recent = region.get("most_recent_data_timestamp")
        if not most_recent:
            stale_regions.append(
                f"  - {region['region_name']}: no data timestamp"
            )
            continue

        # Timestamps are ISO 8601 with Z suffix
        ts = datetime.fromisoformat(most_recent.replace("Z", "+00:00"))
        if ts < threshold:
            age_hours = (now - ts).total_seconds() / 3600
            stale_regions.append(
                f"  - {region['region_name']}: last data {age_hours:.1f}h ago ({most_recent})"
            )

    if stale_regions:
        return "Stale data detected in regions:\n" + "\n".join(stale_regions)
    return None


def check_and_alert():
    """Run all checks and send SNS alert if any fail."""
    problems = []

    site_issue = check_site_reachable()
    if site_issue:
        logger.warning(f"Site check failed: {site_issue}")
        problems.append(f"SITE DOWN: {site_issue}")

    data_issue = check_data_staleness()
    if data_issue:
        logger.warning(f"Data staleness issue: {data_issue}")
        problems.append(f"STALE DATA:\n{data_issue}")

    if not problems:
        logger.info("All checks passed")
        return

    topic_arn = os.environ.get("ALERT_SNS_TOPIC_ARN")
    if not topic_arn:
        logger.error("ALERT_SNS_TOPIC_ARN not set, cannot send alert")
        return

    subject = "CloudPing Alert"
    message = "CloudPing monitoring detected issues:\n\n" + "\n\n".join(problems)

    sns = boto3.client("sns", region_name="us-east-2")
    sns.publish(
        TopicArn=topic_arn,
        Subject=subject,
        Message=message,
    )
    logger.info(f"Alert sent: {len(problems)} issue(s)")
