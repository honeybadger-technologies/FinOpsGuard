"""Tests for Ansible parser functionality."""

import pytest
import yaml
from finopsguard.parsers.ansible import parse_ansible_to_crmodel, get_ansible_default_regions


class TestAnsibleParser:
    """Test Ansible parser functionality."""
    
    def test_parse_aws_ec2_instance(self):
        """Test parsing AWS EC2 instance from Ansible playbook."""
        playbook = """
        - hosts: localhost
          vars:
            aws_region: us-east-1
          tasks:
            - name: Create EC2 instance
              ec2_instance:
                name: web-server
                instance_type: t3.medium
                image_id: ami-0c55b159cbfafe1f0
                region: us-east-1
                tags:
                  Environment: production
                  Name: web-server
        """
        
        model = parse_ansible_to_crmodel(playbook)
        
        assert len(model.resources) == 1
        resource = model.resources[0]
        assert resource.type == 'aws_instance'
        assert resource.name == 'Create EC2 instance'
        assert resource.region == 'us-east-1'
        assert resource.size == 't3.medium'
        assert resource.count == 1
        assert resource.tags['Environment'] == 'production'
        assert resource.tags['Name'] == 'web-server'
        assert resource.metadata['module'] == 'ec2_instance'
        assert resource.metadata['image_id'] == 'ami-0c55b159cbfafe1f0'
    
    def test_parse_aws_autoscaling_group(self):
        """Test parsing AWS Auto Scaling Group from Ansible playbook."""
        playbook = """
        - hosts: localhost
          tasks:
            - name: Create Auto Scaling Group
              ec2_asg:
                name: app-asg
                launch_template:
                  instance_type: t3.large
                desired_capacity: 3
                min_size: 2
                max_size: 10
                region: us-west-2
        """
        
        model = parse_ansible_to_crmodel(playbook)
        
        assert len(model.resources) == 1
        resource = model.resources[0]
        assert resource.type == 'aws_autoscaling_group'
        assert resource.name == 'Create Auto Scaling Group'
        assert resource.region == 'us-west-2'
        assert resource.size == 't3.large'
        assert resource.count == 3
        assert resource.metadata['module'] == 'ec2_asg'
        assert resource.metadata['min_size'] == 2
        assert resource.metadata['max_size'] == 10
    
    def test_parse_aws_lambda_function(self):
        """Test parsing AWS Lambda function from Ansible playbook."""
        playbook = """
        - hosts: localhost
          tasks:
            - name: Create Lambda function
              lambda_function:
                name: data-processor
                runtime: python3.11
                handler: index.handler
                memory_size: 1024
                timeout: 300
                region: eu-west-1
        """
        
        model = parse_ansible_to_crmodel(playbook)
        
        assert len(model.resources) == 1
        resource = model.resources[0]
        assert resource.type == 'aws_lambda_function'
        assert resource.name == 'Create Lambda function'
        assert resource.region == 'eu-west-1'
        assert resource.size == '1024MB-python3.11'
        assert resource.count == 1
        assert resource.metadata['module'] == 'lambda_function'
        assert resource.metadata['handler'] == 'index.handler'
        assert resource.metadata['timeout'] == 300
    
    def test_parse_aws_rds_instance(self):
        """Test parsing AWS RDS instance from Ansible playbook."""
        playbook = """
        - hosts: localhost
          tasks:
            - name: Create RDS instance
              rds_instance:
                name: app-database
                engine: postgres
                engine_version: "14.7"
                instance_class: db.t3.large
                allocated_storage: 100
                region: us-central-1
        """
        
        model = parse_ansible_to_crmodel(playbook)
        
        assert len(model.resources) == 1
        resource = model.resources[0]
        assert resource.type == 'aws_db_instance'
        assert resource.name == 'Create RDS instance'
        assert resource.region == 'us-central-1'
        assert resource.size == 'db.t3.large'
        assert resource.count == 1
        assert resource.metadata['module'] == 'rds_instance'
        assert resource.metadata['engine'] == 'postgres'
        assert resource.metadata['allocated_storage'] == 100
    
    def test_parse_gcp_compute_instance(self):
        """Test parsing GCP Compute Engine instance from Ansible playbook."""
        playbook = """
        - hosts: localhost
          vars:
            gcp_region: us-central1
          tasks:
            - name: Create GCP instance
              gcp_compute_instance:
                name: web-server
                machine_type: n1-standard-2
                zone: us-central1-a
                image: projects/ubuntu-os-cloud/global/images/ubuntu-2004-focal-v20230101
        """
        
        model = parse_ansible_to_crmodel(playbook)
        
        assert len(model.resources) == 1
        resource = model.resources[0]
        assert resource.type == 'google_compute_instance'
        assert resource.name == 'Create GCP instance'
        assert resource.region == 'us-central1'
        assert resource.size == 'n1-standard-2'
        assert resource.count == 1
        assert resource.metadata['module'] == 'gcp_compute_instance'
        assert resource.metadata['zone'] == 'us-central1-a'
    
    def test_parse_gcp_gke_cluster(self):
        """Test parsing GCP GKE cluster from Ansible playbook."""
        playbook = """
        - hosts: localhost
          tasks:
            - name: Create GKE cluster
              gcp_container_cluster:
                name: app-cluster
                zone: us-central1-a
                cluster_version: "1.24"
                initial_node_count: 3
                node_config:
                  machine_type: e2-medium
                  disk_size_gb: 100
        """
        
        model = parse_ansible_to_crmodel(playbook)
        
        assert len(model.resources) == 1
        resource = model.resources[0]
        assert resource.type == 'google_container_cluster'
        assert resource.name == 'Create GKE cluster'
        assert resource.region == 'us-central1'
        assert resource.size == 'e2-medium'
        assert resource.count == 3
        assert resource.metadata['module'] == 'gcp_container_cluster'
        assert resource.metadata['cluster_version'] == '1.24'
        assert resource.metadata['num_nodes'] == 3
    
    def test_parse_gcp_cloud_function(self):
        """Test parsing GCP Cloud Function from Ansible playbook."""
        playbook = """
        - hosts: localhost
          tasks:
            - name: Create Cloud Function
              gcp_cloudfunctions_function:
                name: data-processor
                runtime: python39
                entry_point: process_data
                memory: 512
                timeout: 60
                region: us-central1
        """
        
        model = parse_ansible_to_crmodel(playbook)
        
        assert len(model.resources) == 1
        resource = model.resources[0]
        assert resource.type == 'google_cloudfunctions_function'
        assert resource.name == 'Create Cloud Function'
        assert resource.region == 'us-central1'
        assert resource.size == '512MB-python39'
        assert resource.count == 1
        assert resource.metadata['module'] == 'gcp_cloudfunctions_function'
        assert resource.metadata['entry_point'] == 'process_data'
        assert resource.metadata['runtime'] == 'python39'
    
    def test_parse_azure_virtual_machine(self):
        """Test parsing Azure Virtual Machine from Ansible playbook."""
        playbook = """
        - hosts: localhost
          tasks:
            - name: Create Azure VM
              azure_rm_virtualmachine:
                name: web-server
                resource_group: my-resource-group
                vm_size: Standard_B2s
                image:
                  offer: UbuntuServer
                  publisher: Canonical
                  sku: "18.04-LTS"
                  version: latest
                location: eastus
        """
        
        model = parse_ansible_to_crmodel(playbook)
        
        assert len(model.resources) == 1
        resource = model.resources[0]
        assert resource.type == 'azurerm_virtual_machine'
        assert resource.name == 'Create Azure VM'
        assert resource.region == 'eastus'
        assert resource.size == 'Standard_B2s'
        assert resource.count == 1
        assert resource.metadata['module'] == 'azure_rm_virtualmachine'
        assert resource.metadata['resource_group'] == 'my-resource-group'
    
    def test_parse_azure_aks_cluster(self):
        """Test parsing Azure AKS cluster from Ansible playbook."""
        playbook = """
        - hosts: localhost
          tasks:
            - name: Create AKS cluster
              azure_rm_aks:
                name: app-cluster
                resource_group: my-resource-group
                location: westus2
                dns_prefix: app-cluster
                kubernetes_version: "1.24.0"
                agent_pool_profiles:
                  - name: default
                    count: 2
                    vm_size: Standard_D2s_v3
        """
        
        model = parse_ansible_to_crmodel(playbook)
        
        assert len(model.resources) == 1
        resource = model.resources[0]
        assert resource.type == 'azurerm_kubernetes_cluster'
        assert resource.name == 'Create AKS cluster'
        assert resource.region == 'westus2'
        assert resource.size == 'Standard_D2s_v3'
        assert resource.count == 2
        assert resource.metadata['module'] == 'azure_rm_aks'
        assert resource.metadata['dns_prefix'] == 'app-cluster'
    
    def test_parse_multiple_tasks(self):
        """Test parsing multiple tasks in a single playbook."""
        playbook = """
        - hosts: localhost
          tasks:
            - name: Create EC2 instance
              ec2_instance:
                instance_type: t3.micro
                region: us-east-1
            
            - name: Create RDS instance
              rds_instance:
                instance_class: db.t3.small
                engine: mysql
                region: us-east-1
                
            - name: Create S3 bucket
              s3_bucket:
                name: my-bucket
                region: us-east-1
        """
        
        model = parse_ansible_to_crmodel(playbook)
        
        assert len(model.resources) == 3
        
        # Check EC2 instance
        ec2_resource = next(r for r in model.resources if r.type == 'aws_instance')
        assert ec2_resource.size == 't3.micro'
        
        # Check RDS instance
        rds_resource = next(r for r in model.resources if r.type == 'aws_db_instance')
        assert rds_resource.size == 'db.t3.small'
        
        # Check S3 bucket
        s3_resource = next(r for r in model.resources if r.type == 'aws_s3_bucket')
        assert s3_resource.size == 'standard'
    
    def test_parse_handlers(self):
        """Test parsing handlers in addition to tasks."""
        playbook = """
        - hosts: localhost
          tasks:
            - name: Create EC2 instance
              ec2_instance:
                instance_type: t3.micro
                region: us-east-1
              notify: restart service
          
          handlers:
            - name: restart service
              service:
                name: my-service
                state: restarted
        """
        
        model = parse_ansible_to_crmodel(playbook)
        
        # Should only parse the EC2 instance, not the service handler
        assert len(model.resources) == 1
        assert model.resources[0].type == 'aws_instance'
    
    def test_parse_playbook_variables(self):
        """Test parsing with playbook-level variables."""
        playbook = """
        - hosts: localhost
          vars:
            aws_region: us-west-2
            instance_type: t3.large
          tasks:
            - name: Create EC2 instance
              ec2_instance:
                instance_type: "{{ instance_type }}"
                region: "{{ aws_region }}"
        """
        
        model = parse_ansible_to_crmodel(playbook)
        
        assert len(model.resources) == 1
        resource = model.resources[0]
        assert resource.region == 'us-west-2'
        assert resource.size == 't3.large'
    
    def test_parse_invalid_yaml(self):
        """Test parsing invalid YAML content."""
        invalid_yaml = """
        - hosts: localhost
          tasks:
            - name: Invalid task
              ec2_instance:
                instance_type: t3.micro
                region: us-east-1
            invalid: yaml: content
        """
        
        model = parse_ansible_to_crmodel(invalid_yaml)
        
        # Should return empty model for invalid YAML
        assert len(model.resources) == 0
    
    def test_parse_unsupported_module(self):
        """Test parsing unsupported Ansible modules."""
        playbook = """
        - hosts: localhost
          tasks:
            - name: Install package
              package:
                name: nginx
                state: present
            
            - name: Create EC2 instance
              ec2_instance:
                instance_type: t3.micro
                region: us-east-1
        """
        
        model = parse_ansible_to_crmodel(playbook)
        
        # Should only parse the EC2 instance, ignore the package module
        assert len(model.resources) == 1
        assert model.resources[0].type == 'aws_instance'
    
    def test_get_default_regions(self):
        """Test extracting default regions from playbook content."""
        playbook = """
        - hosts: localhost
          vars:
            aws_region: us-east-1
            gcp_region: us-central1
            azure_location: eastus
          tasks:
            - name: Create resources
              debug:
                msg: "Creating resources"
        """
        
        regions = get_ansible_default_regions(playbook)
        
        assert regions['aws'] == 'us-east-1'
        assert regions['gcp'] == 'us-central1'
        assert regions['azure'] == 'eastus'
    
    def test_empty_playbook(self):
        """Test parsing empty playbook."""
        playbook = """
        - hosts: localhost
          tasks: []
        """
        
        model = parse_ansible_to_crmodel(playbook)
        
        assert len(model.resources) == 0
    
    def test_playbook_without_tasks(self):
        """Test parsing playbook without tasks."""
        playbook = """
        - hosts: localhost
          vars:
            my_var: value
        """
        
        model = parse_ansible_to_crmodel(playbook)
        
        assert len(model.resources) == 0
