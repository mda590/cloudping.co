#!/bin/bash

REGIONS = aws ec2 describe-regions \
    --all-regions \
    --query "Regions[].{Name:RegionName}" \
    --output text

for region in REGIONS
do
    export AWS_DEFAULT_REGION=$region
    chalice deploy --stage prod
done
