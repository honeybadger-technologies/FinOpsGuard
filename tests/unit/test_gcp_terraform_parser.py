"""
Unit tests for GCP Terraform parser integration
"""

from finopsguard.parsers.terraform import parse_terraform_to_crmodel


class TestGCPTerraformParser:
    """Test GCP resource parsing from Terraform HCL"""
    
    def test_parse_gcp_compute_instance(self):
        """Test parsing GCP Compute Engine instances"""
        hcl = '''
        provider "google" {
          region = "us-central1"
        }
        
        resource "google_compute_instance" "web_server" {
          machine_type = "e2-standard-4"
          zone = "us-central1-a"
          count = 2
        }
        '''
        
        result = parse_terraform_to_crmodel(hcl)
        
        assert len(result.resources) == 1
        resource = result.resources[0]
        assert resource.type == 'gcp_compute_instance'
        assert resource.name == 'web_server'
        assert resource.size == 'e2-standard-4'
        assert resource.region == 'us-central1'
        assert resource.count == 2
        assert resource.id == 'web_server-gce-us-central1'
    
    def test_parse_gcp_sql_database(self):
        """Test parsing GCP Cloud SQL instances"""
        hcl = '''
        provider "google" {
          region = "us-west1"
        }
        
        resource "google_sql_database_instance" "main_db" {
          database_version = "POSTGRES_13"
          settings {
            tier = "db-n1-standard-2"
          }
        }
        '''
        
        result = parse_terraform_to_crmodel(hcl)
        
        assert len(result.resources) == 1
        resource = result.resources[0]
        assert resource.type == 'gcp_sql_database_instance'
        assert resource.name == 'main_db'
        assert resource.size == 'db-n1-standard-2'
        assert resource.region == 'us-west1'
        assert resource.count == 1
        assert resource.id == 'main_db-sql-us-west1'
    
    def test_parse_gcp_storage_bucket(self):
        """Test parsing GCP Cloud Storage buckets"""
        hcl = '''
        resource "google_storage_bucket" "data_bucket" {
          name = "my-data-bucket"
          location = "US"
          count = 3
        }
        '''
        
        result = parse_terraform_to_crmodel(hcl)
        
        assert len(result.resources) == 1
        resource = result.resources[0]
        assert resource.type == 'gcp_storage_bucket'
        assert resource.name == 'data_bucket'
        assert resource.size == 'standard'
        assert resource.region == 'US'
        assert resource.count == 3
        assert resource.id == 'data_bucket-storage-US'
    
    def test_parse_gcp_container_cluster(self):
        """Test parsing GCP Kubernetes Engine clusters"""
        hcl = '''
        provider "google" {
          region = "europe-west1"
        }
        
        resource "google_container_cluster" "main_cluster" {
          name = "main-cluster"
          location = "europe-west1"
          enable_autopilot = true
        }
        '''
        
        result = parse_terraform_to_crmodel(hcl)
        
        assert len(result.resources) == 1
        resource = result.resources[0]
        assert resource.type == 'gcp_container_cluster'
        assert resource.name == 'main_cluster'
        assert resource.size == 'autopilot_cluster'
        assert resource.region == 'europe-west1'
        assert resource.count == 1
        assert resource.id == 'main_cluster-gke-europe-west1'
    
    def test_parse_gcp_cloud_run_service(self):
        """Test parsing GCP Cloud Run services"""
        hcl = '''
        resource "google_cloud_run_service" "api_service" {
          name = "api-service"
          location = "us-east1"
          count = 2
        }
        '''
        
        result = parse_terraform_to_crmodel(hcl)
        
        assert len(result.resources) == 1
        resource = result.resources[0]
        assert resource.type == 'gcp_cloud_run_service'
        assert resource.name == 'api_service'
        assert resource.size == 'serverless'
        assert resource.region == 'us-east1'
        assert resource.count == 2
        assert resource.id == 'api_service-run-us-east1'
    
    def test_parse_gcp_cloudfunctions_function(self):
        """Test parsing GCP Cloud Functions"""
        hcl = '''
        resource "google_cloudfunctions_function" "data_processor" {
          name = "data-processor"
          runtime = "python39"
          region = "asia-southeast1"
        }
        '''
        
        result = parse_terraform_to_crmodel(hcl)
        
        assert len(result.resources) == 1
        resource = result.resources[0]
        assert resource.type == 'gcp_cloudfunctions_function'
        assert resource.name == 'data_processor'
        assert resource.size == 'python39'
        assert resource.region == 'asia-southeast1'
        assert resource.count == 1
        assert resource.id == 'data_processor-functions-asia-southeast1'
    
    def test_parse_gcp_load_balancer(self):
        """Test parsing GCP Load Balancers"""
        hcl = '''
        resource "google_compute_global_forwarding_rule" "web_lb" {
          name = "web-load-balancer"
        }
        
        resource "google_compute_target_https_proxy" "web_https_proxy" {
          name = "web-https-proxy"
        }
        '''
        
        result = parse_terraform_to_crmodel(hcl)
        
        assert len(result.resources) == 2
        
        # Check global forwarding rule
        lb_resource = result.resources[0]
        assert lb_resource.type == 'gcp_load_balancer'
        assert lb_resource.name == 'web_lb'
        assert lb_resource.size == 'http_lb'
        assert lb_resource.id == 'web_lb-lb-us-central1'
        
        # Check HTTPS proxy
        https_resource = result.resources[1]
        assert https_resource.type == 'gcp_load_balancer'
        assert https_resource.name == 'web_https_proxy'
        assert https_resource.size == 'ssl_lb'
        assert https_resource.id == 'web_https_proxy-lb-us-central1'
    
    def test_parse_gcp_redis_instance(self):
        """Test parsing GCP Redis instances"""
        hcl = '''
        resource "google_redis_instance" "cache" {
          name = "main-cache"
          memory_size_gb = 8
          tier = "STANDARD_HA"
          region = "us-west2"
        }
        '''
        
        result = parse_terraform_to_crmodel(hcl)
        
        assert len(result.resources) == 1
        resource = result.resources[0]
        assert resource.type == 'gcp_redis_instance'
        assert resource.name == 'cache'
        assert resource.size == 'STANDARD_HA-8GB'
        assert resource.region == 'us-west2'
        assert resource.count == 1
        assert resource.id == 'cache-redis-us-west2'
    
    def test_parse_gcp_bigquery_dataset(self):
        """Test parsing GCP BigQuery datasets"""
        hcl = '''
        resource "google_bigquery_dataset" "analytics" {
          dataset_id = "analytics_data"
          location = "US"
        }
        '''
        
        result = parse_terraform_to_crmodel(hcl)
        
        assert len(result.resources) == 1
        resource = result.resources[0]
        assert resource.type == 'gcp_bigquery_dataset'
        assert resource.name == 'analytics'
        assert resource.size == 'standard'
        assert resource.region == 'US'
        assert resource.count == 1
        assert resource.id == 'analytics-bigquery-US'
    
    def test_parse_mixed_aws_gcp_resources(self):
        """Test parsing mixed AWS and GCP resources"""
        hcl = '''
        provider "aws" {
          region = "us-east-1"
        }
        
        provider "google" {
          region = "us-central1"
        }
        
        resource "aws_instance" "web" {
          instance_type = "t3.micro"
        }
        
        resource "google_compute_instance" "api" {
          machine_type = "e2-small"
          zone = "us-central1-a"
        }
        '''
        
        result = parse_terraform_to_crmodel(hcl)
        
        assert len(result.resources) == 2
        
        # Check AWS resource
        aws_resource = result.resources[0]
        assert aws_resource.type == 'aws_instance'
        assert aws_resource.region == 'us-east-1'
        assert aws_resource.size == 't3.micro'
        
        # Check GCP resource
        gcp_resource = result.resources[1]
        assert gcp_resource.type == 'gcp_compute_instance'
        assert gcp_resource.region == 'us-central1'
        assert gcp_resource.size == 'e2-small'
    
    def test_parse_zone_to_region_conversion(self):
        """Test that zones are converted to regions correctly"""
        hcl = '''
        resource "google_compute_instance" "test" {
          machine_type = "e2-micro"
          zone = "europe-west1-b"
        }
        '''
        
        result = parse_terraform_to_crmodel(hcl)
        
        assert len(result.resources) == 1
        resource = result.resources[0]
        assert resource.region == 'europe-west1'  # Zone converted to region
    
    def test_parse_default_gcp_region(self):
        """Test default GCP region when no provider or zone specified"""
        hcl = '''
        resource "google_compute_instance" "test" {
          machine_type = "e2-micro"
        }
        '''
        
        result = parse_terraform_to_crmodel(hcl)
        
        assert len(result.resources) == 1
        resource = result.resources[0]
        assert resource.region == 'us-central1'  # Default GCP region
    
    def test_parse_gcp_resources_with_count(self):
        """Test parsing GCP resources with count"""
        hcl = '''
        resource "google_compute_instance" "workers" {
          machine_type = "e2-medium"
          count = 5
        }
        '''
        
        result = parse_terraform_to_crmodel(hcl)
        
        assert len(result.resources) == 1
        resource = result.resources[0]
        assert resource.count == 5
        assert resource.size == 'e2-medium'
    
    def test_parse_complex_gcp_infrastructure(self):
        """Test parsing complex GCP infrastructure"""
        hcl = '''
        provider "google" {
          region = "us-central1"
        }
        
        resource "google_compute_instance" "web_servers" {
          machine_type = "e2-standard-2"
          count = 3
        }
        
        resource "google_sql_database_instance" "main_db" {
          database_version = "POSTGRES_13"
          settings {
            tier = "db-n1-standard-4"
          }
        }
        
        resource "google_container_cluster" "k8s_cluster" {
          name = "main-cluster"
          enable_autopilot = false
        }
        
        resource "google_storage_bucket" "data" {
          name = "app-data"
          location = "US"
        }
        
        resource "google_cloud_run_service" "api" {
          name = "api-service"
          location = "us-central1"
        }
        '''
        
        result = parse_terraform_to_crmodel(hcl)
        
        assert len(result.resources) == 5
        
        # Check all resource types are present
        resource_types = {r.type for r in result.resources}
        expected_types = {
            'gcp_compute_instance',
            'gcp_sql_database_instance',
            'gcp_container_cluster',
            'gcp_storage_bucket',
            'gcp_cloud_run_service'
        }
        assert resource_types == expected_types
        
        # Check counts and regions
        for resource in result.resources:
            assert resource.region == 'us-central1' or resource.region == 'US'
            if resource.type == 'gcp_compute_instance':
                assert resource.count == 3
            else:
                assert resource.count == 1
