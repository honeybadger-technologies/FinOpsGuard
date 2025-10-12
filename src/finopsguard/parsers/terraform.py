"""
Terraform HCL parser for multi-cloud infrastructure.

Orchestrates cloud-specific parsers for AWS, GCP, and Azure.
Extracts resource types, regions, and configuration from HCL strings.
"""

import re
from typing import List

from ..types.models import CanonicalResource, CanonicalResourceModel
from .aws_tf_parser import parse_aws_resource, get_aws_default_region
from .gcp_tf_parser import parse_gcp_resource, get_gcp_default_region
from .azure_tf_parser import parse_azure_resource, get_azure_default_location


def parse_terraform_to_crmodel(hcl_text: str) -> CanonicalResourceModel:
    """
    Parse Terraform HCL text into canonical resource model.
    
    Supports multi-cloud infrastructure across AWS, GCP, and Azure.
    
    Args:
        hcl_text: Terraform HCL content
        
    Returns:
        CanonicalResourceModel with parsed resources
        
    Example:
        >>> hcl = '''
        ... resource "aws_instance" "web" {
        ...   instance_type = "t3.micro"
        ... }
        ... '''
        >>> model = parse_terraform_to_crmodel(hcl)
        >>> print(model.resources[0].type)
        'aws_instance'
    """
    resources: List[CanonicalResource] = []
    
    # Extract default regions/locations from provider blocks
    aws_default_region = get_aws_default_region(hcl_text)
    gcp_default_region = get_gcp_default_region(hcl_text)
    azure_default_location = get_azure_default_location(hcl_text)
    
    # Extract resource blocks using regex
    resource_regex = re.compile(
        r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{([\s\S]*?)\}',
        re.MULTILINE
    )
    
    for match in resource_regex.finditer(hcl_text):
        resource_type, resource_name, resource_body = match.groups()
        
        # Extract count parameter (applies to all resources)
        count_match = re.search(r'count\s*=\s*([0-9]+)', resource_body, re.IGNORECASE)
        count = int(count_match.group(1)) if count_match else 1
        
        # Route to appropriate cloud parser based on resource type prefix
        resource = None
        
        if resource_type.startswith('aws_'):
            resource = parse_aws_resource(
                resource_type,
                resource_name,
                resource_body,
                aws_default_region,
                count
            )
        
        elif resource_type.startswith('google_'):
            resource = parse_gcp_resource(
                resource_type,
                resource_name,
                resource_body,
                gcp_default_region,
                count
            )
        
        elif resource_type.startswith('azurerm_'):
            resource = parse_azure_resource(
                resource_type,
                resource_name,
                resource_body,
                azure_default_location,
                count
            )
        
        # Add to resources list if successfully parsed
        if resource:
            resources.append(resource)
    
    return CanonicalResourceModel(resources=resources)
