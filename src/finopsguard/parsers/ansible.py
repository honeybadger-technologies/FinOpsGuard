"""
Ansible YAML parser for multi-cloud infrastructure.

Orchestrates cloud-specific parsers for AWS, GCP, and Azure.
Extracts resource types, regions, and configuration from Ansible playbooks.
"""

import re
import yaml
from typing import List, Dict, Any, Optional

from ..types.models import CanonicalResource, CanonicalResourceModel
from .aws_ansible_parser import parse_aws_ansible_task, get_aws_default_region
from .gcp_ansible_parser import parse_gcp_ansible_task, get_gcp_default_region
from .azure_ansible_parser import parse_azure_ansible_task, get_azure_default_location


def _resolve_jinja2_variables(value: Any, task_vars: Dict[str, Any]) -> Any:
    """
    Resolve simple Jinja2 template variables in a value.
    
    Args:
        value: Value that may contain Jinja2 variables
        task_vars: Task variables to use for substitution
        
    Returns:
        Value with variables resolved
    """
    if isinstance(value, str) and '{{' in value:
        # Extract variable name and try to resolve from task_vars
        var_match = re.search(r'\{\{\s*([^}]+)\s*\}\}', value)
        if var_match:
            var_name = var_match.group(1).strip()
            return task_vars.get(var_name, value)
    return value


def parse_ansible_to_crmodel(playbook_content: str) -> CanonicalResourceModel:
    """
    Parse Ansible playbook YAML into canonical resource model.
    
    Supports multi-cloud infrastructure across AWS, GCP, and Azure.
    
    Args:
        playbook_content: Ansible playbook YAML content
        
    Returns:
        CanonicalResourceModel with parsed resources
        
    Example:
        >>> yaml_content = '''
        ... - hosts: localhost
        ...   tasks:
        ...     - name: Create EC2 instance
        ...       ec2_instance:
        ...         instance_type: t3.micro
        ...         region: us-east-1
        ... '''
        >>> model = parse_ansible_to_crmodel(yaml_content)
        >>> print(model.resources[0].type)
        'ec2_instance'
    """
    resources: List[CanonicalResource] = []
    
    try:
        # Parse YAML content
        playbook_data = yaml.safe_load(playbook_content)
        
        # Handle both single playbook and list of playbooks
        if isinstance(playbook_data, list):
            playbooks = playbook_data
        else:
            playbooks = [playbook_data]
        
        # Extract default regions/locations from playbook variables
        aws_default_region = get_aws_default_region(playbook_content)
        gcp_default_region = get_gcp_default_region(playbook_content)
        azure_default_location = get_azure_default_location(playbook_content)
        
        # Process each playbook
        for playbook in playbooks:
            if not isinstance(playbook, dict):
                continue
                
            # Extract variables from playbook level
            playbook_vars = playbook.get('vars', {})
            
            # Process tasks in each playbook
            tasks = playbook.get('tasks', [])
            for task in tasks:
                if not isinstance(task, dict):
                    continue
                    
                resource = _parse_task_to_resource(
                    task,
                    playbook_vars,
                    aws_default_region,
                    gcp_default_region,
                    azure_default_location
                )
                
                if resource:
                    resources.append(resource)
            
            # Process handlers
            handlers = playbook.get('handlers', [])
            for handler in handlers:
                if not isinstance(handler, dict):
                    continue
                    
                resource = _parse_task_to_resource(
                    handler,
                    playbook_vars,
                    aws_default_region,
                    gcp_default_region,
                    azure_default_location
                )
                
                if resource:
                    resources.append(resource)
    
    except yaml.YAMLError as e:
        # If YAML parsing fails, return empty model
        print(f"Warning: Failed to parse Ansible YAML: {e}")
        return CanonicalResourceModel(resources=[])
    
    return CanonicalResourceModel(resources=resources)


def _parse_task_to_resource(
    task: Dict[str, Any],
    playbook_vars: Dict[str, Any],
    aws_default_region: str,
    gcp_default_region: str,
    azure_default_location: str
) -> Optional[CanonicalResource]:
    """
    Parse an individual Ansible task into a canonical resource.
    
    Args:
        task: Ansible task dictionary
        playbook_vars: Playbook-level variables
        aws_default_region: Default AWS region
        gcp_default_region: Default GCP region
        azure_default_location: Default Azure location
        
    Returns:
        CanonicalResource if parsed, None if not supported
    """
    task_name = task.get('name', 'unnamed')
    
    # Merge playbook variables with task variables
    task_vars = {**playbook_vars, **task.get('vars', {})}
    
    # Find the first module that we can parse
    for module_name, module_params in task.items():
        if module_name in ['name', 'vars', 'when', 'loop', 'register', 'tags']:
            continue
        
        # Resolve variables in module parameters
        resolved_params = {}
        for key, value in module_params.items():
            resolved_params[key] = _resolve_jinja2_variables(value, task_vars)
            
        # AWS modules
        if module_name.startswith('ec2_') or module_name.startswith('aws_') or module_name in ['lambda_function', 'rds_instance', 'rds', 's3_bucket', 'aws_s3']:
            return parse_aws_ansible_task(
                module_name,
                resolved_params,
                task_name,
                task_vars,
                aws_default_region
            )
        
        # GCP modules
        elif module_name.startswith('gcp_') or module_name.startswith('gce_'):
            return parse_gcp_ansible_task(
                module_name,
                resolved_params,
                task_name,
                task_vars,
                gcp_default_region
            )
        
        # Azure modules
        elif module_name.startswith('azure_') or module_name.startswith('azurerm_'):
            return parse_azure_ansible_task(
                module_name,
                resolved_params,
                task_name,
                task_vars,
                azure_default_location
            )
    
    return None


def get_ansible_default_regions(content: str) -> Dict[str, str]:
    """
    Extract default regions/locations from Ansible playbook content.
    
    Args:
        content: Ansible playbook YAML content
        
    Returns:
        Dictionary with default regions for each cloud provider
    """
    return {
        'aws': get_aws_default_region(content),
        'gcp': get_gcp_default_region(content),
        'azure': get_azure_default_location(content)
    }
