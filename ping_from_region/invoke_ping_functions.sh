#!/bin/bash

REGIONS=$(aws ec2 describe-regions \
    --query "Regions[].RegionName" \
    --output text)

FUNCTION_NAME="ping_from_region-prod-ping"

# Write payload to temp file
PAYLOAD_FILE=$(mktemp)
cat > "$PAYLOAD_FILE" << 'EOF'
{
  "id": "cdc73f9d-aea9-11e3-9d5a-835b769c0d9c",
  "detail-type": "Scheduled Event",
  "source": "aws.events",
  "account": "123456789012",
  "time": "1970-01-01T00:00:00Z",
  "region": "us-east-1",
  "resources": [
    "arn:aws:events:us-east-1:123456789012:rule/ExampleRule"
  ],
  "detail": {},
  "version": "2.0"
}
EOF

for region in $REGIONS; do
    echo "Invoking in $region..."
    aws lambda invoke \
        --function-name "$FUNCTION_NAME" \
        --region "$region" \
        --invocation-type Event \
        --cli-binary-format raw-in-base64-out \
        --payload "file://$PAYLOAD_FILE" \
        --no-cli-pager \
        /dev/null 2>&1 && echo "  Success" || echo "  Not deployed or error"
done

rm -f "$PAYLOAD_FILE"