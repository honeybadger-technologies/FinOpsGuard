"""Parsers module for FinOpsGuard"""

from .terraform import parse_terraform_to_crmodel
from .aws_tf_parser import parse_aws_resource, get_aws_default_region
from .gcp_tf_parser import parse_gcp_resource, get_gcp_default_region
from .azure_tf_parser import parse_azure_resource, get_azure_default_location

__all__ = [
    "parse_terraform_to_crmodel",
    "parse_aws_resource",
    "parse_gcp_resource",
    "parse_azure_resource",
    "get_aws_default_region",
    "get_gcp_default_region",
    "get_azure_default_location",
]

