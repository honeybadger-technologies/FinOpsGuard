"""Parsers module for FinOpsGuard"""

from .terraform import parse_terraform_to_crmodel
from .aws_tf_parser import parse_aws_resource, get_aws_default_region
from .gcp_tf_parser import parse_gcp_resource, get_gcp_default_region
from .azure_tf_parser import parse_azure_resource, get_azure_default_location

from .ansible import parse_ansible_to_crmodel, get_ansible_default_regions
from .aws_ansible_parser import parse_aws_ansible_task
from .gcp_ansible_parser import parse_gcp_ansible_task
from .azure_ansible_parser import parse_azure_ansible_task

__all__ = [
    # Terraform parsers
    "parse_terraform_to_crmodel",
    "parse_aws_resource",
    "parse_gcp_resource",
    "parse_azure_resource",
    "get_aws_default_region",
    "get_gcp_default_region",
    "get_azure_default_location",
    # Ansible parsers
    "parse_ansible_to_crmodel",
    "parse_aws_ansible_task",
    "parse_gcp_ansible_task",
    "parse_azure_ansible_task",
    "get_ansible_default_regions",
]

