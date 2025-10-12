# Example GCP Infrastructure
# Demonstrates comprehensive GCP resource support in FinOpsGuard

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = "finopsguard-demo"
  region  = "us-central1"
}

# ============================================================================
# COMPUTE
# ============================================================================

# Compute Engine Instance
resource "google_compute_instance" "web" {
  name         = "web-server"
  machine_type = "n2-standard-4"
  zone         = "us-central1-a"
  
  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }
  
  network_interface {
    network = "default"
  }
}

# GKE Cluster
resource "google_container_cluster" "k8s" {
  name     = "app-cluster"
  location = "us-central1"
  
  initial_node_count = 3
  
  node_config {
    machine_type = "n1-standard-4"
    disk_size_gb = 100
  }
}

# GKE Autopilot Cluster
resource "google_container_cluster" "autopilot" {
  name     = "autopilot-cluster"
  location = "us-central1"
  
  enable_autopilot = true
}

# Persistent Disk
resource "google_compute_disk" "data" {
  name = "data-disk"
  type = "pd-ssd"
  zone = "us-central1-a"
  size = 500
}

# ============================================================================
# DATABASE & STORAGE
# ============================================================================

# Cloud SQL (PostgreSQL)
resource "google_sql_database_instance" "postgres" {
  name             = "postgres-instance"
  database_version = "POSTGRES_14"
  region           = "us-central1"
  
  settings {
    tier = "db-custom-4-16384"
  }
}

# Cloud SQL (MySQL)
resource "google_sql_database_instance" "mysql" {
  name             = "mysql-instance"
  database_version = "MYSQL_8_0"
  region           = "us-central1"
  
  settings {
    tier = "db-n1-standard-2"
  }
}

# Cloud Storage Bucket
resource "google_storage_bucket" "data" {
  name          = "finopsguard-data-bucket"
  location      = "US"
  storage_class = "STANDARD"
}

# Filestore Instance
resource "google_filestore_instance" "nfs" {
  name = "nfs-server"
  location = "us-central1-a"
  tier = "PREMIUM"
  
  file_shares {
    capacity_gb = 2560
    name        = "share1"
  }
  
  networks {
    network = "default"
    modes   = ["MODE_IPV4"]
  }
}

# Cloud Spanner Instance
resource "google_spanner_instance" "spanner" {
  name         = "spanner-instance"
  config       = "regional-us-central1"
  display_name = "Spanner Instance"
  num_nodes    = 2
}

# BigQuery Dataset
resource "google_bigquery_dataset" "analytics" {
  dataset_id                  = "analytics"
  friendly_name               = "Analytics Dataset"
  description                 = "Analytics data warehouse"
  location                    = "US"
  default_table_expiration_ms = 3600000
}

# ============================================================================
# SERVERLESS & CONTAINERS
# ============================================================================

# Cloud Run Service
resource "google_cloud_run_service" "api" {
  name     = "api-service"
  location = "us-central1"
  
  template {
    spec {
      containers {
        image = "gcr.io/cloudrun/hello"
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }
    }
  }
}

# Cloud Functions
resource "google_cloudfunctions_function" "processor" {
  name        = "data-processor"
  description = "Data processing function"
  runtime     = "python310"
  region      = "us-central1"
  
  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.functions.name
  source_archive_object = google_storage_bucket_object.function_zip.name
  trigger_http          = true
  entry_point           = "process_data"
}

# ============================================================================
# CACHING & MESSAGING
# ============================================================================

# Memorystore for Redis
resource "google_redis_instance" "cache" {
  name           = "app-cache"
  tier           = "STANDARD_HA"
  memory_size_gb = 5
  region         = "us-central1"
  
  authorized_network = google_compute_network.vpc.id
}

# Pub/Sub Topic
resource "google_pubsub_topic" "events" {
  name = "event-topic"
}

# ============================================================================
# NETWORKING
# ============================================================================

# Load Balancer Components
resource "google_compute_global_forwarding_rule" "lb" {
  name       = "global-lb"
  target     = google_compute_target_http_proxy.lb.id
  port_range = "80"
}

resource "google_compute_target_http_proxy" "lb" {
  name    = "lb-proxy"
  url_map = google_compute_url_map.lb.id
}

resource "google_compute_url_map" "lb" {
  name            = "lb-url-map"
  default_service = google_compute_backend_service.lb.id
}

resource "google_compute_backend_service" "lb" {
  name = "lb-backend"
  
  backend {
    group = google_compute_instance_group.web.id
  }
}

# Cloud Armor Security Policy
resource "google_compute_security_policy" "policy" {
  name = "security-policy"
  
  rule {
    action   = "deny(403)"
    priority = "1000"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["9.9.9.0/24"]
      }
    }
  }
  
  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
  }
}

# ============================================================================
# DATA ANALYTICS
# ============================================================================

# Dataflow Job
resource "google_dataflow_job" "pipeline" {
  name              = "data-pipeline"
  template_gcs_path = "gs://dataflow-templates/latest/Word_Count"
  temp_gcs_location = "gs://my-bucket/tmp"
  machine_type      = "n1-standard-2"
  max_workers       = 10
  region            = "us-central1"
}

# Dataproc Cluster
resource "google_dataproc_cluster" "spark" {
  name   = "spark-cluster"
  region = "us-central1"
  
  cluster_config {
    master_config {
      num_instances = 1
      machine_type  = "n1-standard-8"
      disk_config {
        boot_disk_size_gb = 100
      }
    }
    
    worker_config {
      num_instances = 4
      machine_type  = "n1-standard-4"
      disk_config {
        boot_disk_size_gb = 100
      }
    }
  }
}

# Cloud Composer (Managed Airflow)
resource "google_composer_environment" "airflow" {
  name   = "composer-env"
  region = "us-central1"
  
  config {
    node_count = 3
    
    node_config {
      network    = google_compute_network.vpc.id
      subnetwork = google_compute_subnetwork.composer.id
      machine_type = "n1-standard-4"
    }
    
    software_config {
      image_version = "composer-2-airflow-2"
    }
  }
}

# Vertex AI Workbench Instance
resource "google_notebooks_instance" "ml" {
  name         = "ml-notebook"
  location     = "us-west1-a"
  machine_type = "n1-standard-4"
  
  vm_image {
    project      = "deeplearning-platform-release"
    image_family = "tf-latest-cpu"
  }
}

# ============================================================================
# SUPPORTING RESOURCES
# ============================================================================

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "main-vpc"
  auto_create_subnetworks = false
}

# Subnetwork
resource "google_compute_subnetwork" "composer" {
  name          = "composer-subnet"
  ip_cidr_range = "10.2.0.0/16"
  region        = "us-central1"
  network       = google_compute_network.vpc.id
}

# Instance Group (for Load Balancer)
resource "google_compute_instance_group" "web" {
  name = "web-instance-group"
  zone = "us-central1-a"
  
  instances = [
    google_compute_instance.web.self_link
  ]
}

# Storage Bucket for Functions
resource "google_storage_bucket" "functions" {
  name     = "functions-source-bucket"
  location = "US"
}

resource "google_storage_bucket_object" "function_zip" {
  name   = "function-source.zip"
  bucket = google_storage_bucket.functions.name
  source = "function-source.zip"
}

