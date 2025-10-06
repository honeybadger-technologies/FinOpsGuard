# Test Terraform infrastructure for FinOpsGuard CI/CD testing
terraform {
  required_version = ">= 1.0"
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

# Test EC2 instance
resource "aws_instance" "test_instance" {
  ami           = "ami-0c02fb55956c7d316"
  instance_type = "t3.medium"
  
  tags = {
    Name        = "test-instance"
    Environment = "dev"
    Project     = "finopsguard-test"
  }
}

# Test RDS instance
resource "aws_db_instance" "test_database" {
  identifier = "test-db"
  
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = "db.t3.micro"
  
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type         = "gp2"
  
  db_name  = "testdb"
  username = "admin"
  password = "password123"  # In real usage, use secrets manager
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = true
  
  tags = {
    Name        = "test-database"
    Environment = "dev"
    Project     = "finopsguard-test"
  }
}

# Test Elastic Load Balancer
resource "aws_lb" "test_lb" {
  name               = "test-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.lb_sg.id]
  subnets            = ["subnet-12345678", "subnet-87654321"]  # Replace with actual subnet IDs
  
  enable_deletion_protection = false
  
  tags = {
    Name        = "test-load-balancer"
    Environment = "dev"
    Project     = "finopsguard-test"
  }
}

resource "aws_security_group" "lb_sg" {
  name_prefix = "test-lb-sg"
  vpc_id      = "vpc-12345678"  # Replace with actual VPC ID
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name        = "test-lb-security-group"
    Environment = "dev"
    Project     = "finopsguard-test"
  }
}
