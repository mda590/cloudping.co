"""
Shared utilities for cloudping cross-partition operations.
"""

from .cross_partition import (
    get_current_partition,
    get_dns_suffix,
    get_arn_partition,
    build_endpoint,
    get_cross_partition_dynamodb_client,
    get_regions_from_dynamodb,
)

__all__ = [
    'get_current_partition',
    'get_dns_suffix',
    'get_arn_partition',
    'build_endpoint',
    'get_cross_partition_dynamodb_client',
    'get_regions_from_dynamodb',
]
