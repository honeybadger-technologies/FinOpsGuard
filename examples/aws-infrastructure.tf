# Example AWS Infrastructure
# Demonstrates comprehensive AWS resource support in FinOpsGuard

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# ============================================================================
# COMPUTE
# ============================================================================

# EC2 Instance
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"
  
  tags = {
    Name = "web-server"
  }
}

# Auto Scaling Group
resource "aws_autoscaling_group" "app" {
  name                = "app-asg"
  min_size            = 2
  max_size            = 10
  desired_capacity    = 3
  
  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }
}

resource "aws_launch_template" "app" {
  name          = "app-template"
  instance_type = "t3.large"
  image_id      = "ami-0c55b159cbfafe1f0"
}

# EKS Cluster
resource "aws_eks_cluster" "k8s" {
  name     = "app-cluster"
  role_arn = aws_iam_role.eks.arn
  
  vpc_config {
    subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  }
}

# Lambda Function
resource "aws_lambda_function" "processor" {
  function_name = "data-processor"
  role          = aws_iam_role.lambda.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  memory_size   = 1024
  timeout       = 300
  
  filename         = "function.zip"
  source_code_hash = filebase64sha256("function.zip")
}

# ECS Cluster
resource "aws_ecs_cluster" "app" {
  name = "app-cluster"
}

# ECS Service (Fargate)
resource "aws_ecs_service" "web" {
  name            = "web-service"
  cluster         = aws_ecs_cluster.app.id
  task_definition = aws_ecs_task_definition.web.arn
  desired_count   = 3
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets         = [aws_subnet.private_a.id]
    security_groups = [aws_security_group.ecs.id]
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "web" {
  family                   = "web"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"
  
  container_definitions = jsonencode([{
    name  = "web"
    image = "nginx:latest"
    portMappings = [{
      containerPort = 80
      protocol      = "tcp"
    }]
  }])
}

# App Runner Service
resource "aws_apprunner_service" "api" {
  service_name = "api-service"
  
  source_configuration {
    image_repository {
      image_identifier      = "public.ecr.aws/aws-containers/hello-app-runner:latest"
      image_repository_type = "ECR_PUBLIC"
    }
  }
  
  instance_configuration {
    cpu    = 2
    memory = 4
  }
}

# ============================================================================
# DATABASE
# ============================================================================

# RDS Instance
resource "aws_db_instance" "postgres" {
  identifier        = "app-database"
  engine            = "postgres"
  engine_version    = "14.7"
  instance_class    = "db.t3.large"
  allocated_storage = 100
  
  db_name  = "appdb"
  username = "admin"
  password = "P@ssw0rd1234!"
  
  skip_final_snapshot = true
}

# DynamoDB Table
resource "aws_dynamodb_table" "users" {
  name         = "users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "UserId"
  
  attribute {
    name = "UserId"
    type = "S"
  }
}

# Redshift Cluster
resource "aws_redshift_cluster" "analytics" {
  cluster_identifier = "analytics-cluster"
  database_name      = "analytics"
  master_username    = "admin"
  master_password    = "P@ssw0rd1234!"
  node_type          = "dc2.large"
  cluster_type       = "multi-node"
  number_of_nodes    = 3
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "app-cache"
  engine               = "redis"
  node_type            = "cache.t3.medium"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
}

# ElastiCache Redis Replication Group
resource "aws_elasticache_replication_group" "redis_cluster" {
  replication_group_id       = "redis-cluster"
  replication_group_description = "Redis cluster"
  node_type                  = "cache.m5.large"
  number_cache_clusters      = 3
  automatic_failover_enabled = true
}

# Neptune Graph Database
resource "aws_neptune_cluster" "graph" {
  cluster_identifier  = "graph-db"
  engine              = "neptune"
  skip_final_snapshot = true
}

resource "aws_neptune_cluster_instance" "graph" {
  cluster_identifier = aws_neptune_cluster.graph.id
  instance_class     = "db.r5.large"
}

# DocumentDB Cluster
resource "aws_docdb_cluster" "docdb" {
  cluster_identifier  = "docdb-cluster"
  engine              = "docdb"
  master_username     = "admin"
  master_password     = "P@ssw0rd1234!"
  skip_final_snapshot = true
}

resource "aws_docdb_cluster_instance" "docdb" {
  identifier         = "docdb-instance"
  cluster_identifier = aws_docdb_cluster.docdb.id
  instance_class     = "db.t3.medium"
}

# ============================================================================
# STORAGE
# ============================================================================

# S3 Bucket
resource "aws_s3_bucket" "data" {
  bucket = "finopsguard-data-bucket"
}

resource "aws_s3_bucket_storage_class" "data_ia" {
  bucket        = aws_s3_bucket.data.id
  storage_class = "INTELLIGENT_TIERING"
}

# ============================================================================
# NETWORKING
# ============================================================================

# Load Balancer
resource "aws_lb" "web" {
  name               = "web-lb"
  internal           = false
  load_balancer_type = "application"
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "cdn" {
  enabled = true
  price_class = "PriceClass_100"
  
  origin {
    domain_name = aws_s3_bucket.data.bucket_regional_domain_name
    origin_id   = "S3-origin"
  }
  
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-origin"
    viewer_protocol_policy = "redirect-to-https"
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }
  
  viewer_certificate {
    cloudfront_default_certificate = true
  }
  
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
}

# ============================================================================
# ANALYTICS & DATA
# ============================================================================

# Kinesis Stream
resource "aws_kinesis_stream" "events" {
  name             = "event-stream"
  shard_count      = 4
  retention_period = 24
  
  stream_mode_details {
    stream_mode = "PROVISIONED"
  }
}

# EMR Cluster
resource "aws_emr_cluster" "hadoop" {
  name          = "hadoop-cluster"
  release_label = "emr-6.10.0"
  service_role  = aws_iam_role.emr_service.arn
  
  master_instance_group {
    instance_type = "m5.xlarge"
  }
  
  core_instance_group {
    instance_type  = "m5.large"
    instance_count = 2
  }
}

# MSK (Managed Kafka)
resource "aws_msk_cluster" "kafka" {
  cluster_name           = "kafka-cluster"
  kafka_version          = "3.4.0"
  number_of_broker_nodes = 3
  
  broker_node_group_info {
    instance_type   = "kafka.m5.large"
    client_subnets  = [aws_subnet.private_a.id, aws_subnet.private_b.id]
    storage_info {
      ebs_storage_info {
        volume_size = 1000
      }
    }
  }
}

# Glue Job
resource "aws_glue_job" "etl" {
  name     = "etl-job"
  role_arn = aws_iam_role.glue.arn
  
  command {
    name            = "glueetl"
    script_location = "s3://my-bucket/scripts/etl.py"
  }
}

# Athena Workgroup
resource "aws_athena_workgroup" "analytics" {
  name = "analytics-workgroup"
  
  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true
    
    result_configuration {
      output_location = "s3://query-results-bucket/output"
    }
  }
}

# OpenSearch Domain
resource "aws_opensearch_domain" "search" {
  domain_name    = "search-domain"
  engine_version = "OpenSearch_2.5"
  
  cluster_config {
    instance_type  = "t3.medium.search"
    instance_count = 3
  }
  
  ebs_options {
    ebs_enabled = true
    volume_size = 100
  }
}

# ============================================================================
# MESSAGING & INTEGRATION
# ============================================================================

# SNS Topic
resource "aws_sns_topic" "alerts" {
  name = "system-alerts"
}

# SQS Queue (Standard)
resource "aws_sqs_queue" "tasks" {
  name                      = "task-queue"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 345600
}

# SQS Queue (FIFO)
resource "aws_sqs_queue" "orders" {
  name                        = "orders.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
}

# Step Functions State Machine
resource "aws_sfn_state_machine" "workflow" {
  name     = "order-workflow"
  role_arn = aws_iam_role.sfn.arn
  type     = "EXPRESS"
  
  definition = jsonencode({
    StartAt = "ProcessOrder"
    States = {
      ProcessOrder = {
        Type = "Task"
        Resource = aws_lambda_function.processor.arn
        End = true
      }
    }
  })
}

# API Gateway REST API
resource "aws_api_gateway_rest_api" "api" {
  name        = "rest-api"
  description = "REST API"
}

# API Gateway HTTP API (v2)
resource "aws_apigatewayv2_api" "http_api" {
  name          = "http-api"
  protocol_type = "HTTP"
}

# ============================================================================
# SUPPORTING RESOURCES (for reference)
# ============================================================================

# VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  
  tags = {
    Name = "main-vpc"
  }
}

# Subnets
resource "aws_subnet" "public_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
}

resource "aws_subnet" "public_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"
}

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "us-east-1a"
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = "us-east-1b"
}

# Security Group
resource "aws_security_group" "ecs" {
  name   = "ecs-sg"
  vpc_id = aws_vpc.main.id
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# IAM Roles
resource "aws_iam_role" "eks" {
  name = "eks-cluster-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role" "lambda" {
  name = "lambda-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role" "glue" {
  name = "glue-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "glue.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role" "sfn" {
  name = "step-functions-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "states.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role" "emr_service" {
  name = "emr-service-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "elasticmapreduce.amazonaws.com"
      }
    }]
  })
}

