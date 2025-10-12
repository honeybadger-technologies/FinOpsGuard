"""Unit tests for extended AWS Terraform parsing."""

import pytest
from finopsguard.parsers.terraform import parse_terraform_to_crmodel


class TestAWSExtendedParsing:
    """Test extended AWS resource parsing from Terraform HCL."""
    
    def test_parse_aws_lambda_function(self):
        """Test parsing AWS Lambda Function."""
        hcl = '''
resource "aws_lambda_function" "processor" {
  function_name = "data-processor"
  runtime       = "python3.11"
  memory_size   = 512
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        lambda_func = model.resources[0]
        assert lambda_func.type == 'aws_lambda_function'
        assert '512MB' in lambda_func.size
        assert 'python3.11' in lambda_func.size
        assert lambda_func.metadata['memory_mb'] == 512
    
    def test_parse_aws_s3_bucket(self):
        """Test parsing AWS S3 Bucket."""
        hcl = '''
resource "aws_s3_bucket" "data" {
  bucket        = "my-data-bucket"
  storage_class = "INTELLIGENT_TIERING"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        s3 = model.resources[0]
        assert s3.type == 'aws_s3_bucket'
        assert s3.size == 'INTELLIGENT_TIERING'
    
    def test_parse_aws_ecs_cluster(self):
        """Test parsing AWS ECS Cluster."""
        hcl = '''
resource "aws_ecs_cluster" "app" {
  name = "app-cluster"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        ecs = model.resources[0]
        assert ecs.type == 'aws_ecs_cluster'
        assert ecs.size == 'cluster'
    
    def test_parse_aws_ecs_service(self):
        """Test parsing AWS ECS Service."""
        hcl = '''
resource "aws_ecs_service" "web" {
  name            = "web-service"
  cluster         = aws_ecs_cluster.app.id
  desired_count   = 3
  launch_type     = "FARGATE"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        service = model.resources[0]
        assert service.type == 'aws_ecs_service'
        assert 'FARGATE' in service.size
        assert '3tasks' in service.size
        assert service.metadata['desired_count'] == 3
    
    def test_parse_aws_ecs_task_definition(self):
        """Test parsing AWS ECS Task Definition (Fargate)."""
        hcl = '''
resource "aws_ecs_task_definition" "app" {
  family                   = "app"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        task = model.resources[0]
        assert task.type == 'aws_ecs_task_definition'
        assert '1024cpu' in task.size
        assert '2048mb' in task.size
    
    def test_parse_aws_kinesis_stream(self):
        """Test parsing AWS Kinesis Stream."""
        hcl = '''
resource "aws_kinesis_stream" "events" {
  name             = "event-stream"
  shard_count      = 4
  retention_period = 24
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        kinesis = model.resources[0]
        assert kinesis.type == 'aws_kinesis_stream'
        assert '4shards' in kinesis.size
        assert kinesis.metadata['shard_count'] == 4
    
    def test_parse_aws_sns_topic(self):
        """Test parsing AWS SNS Topic."""
        hcl = '''
resource "aws_sns_topic" "alerts" {
  name = "system-alerts"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        sns = model.resources[0]
        assert sns.type == 'aws_sns_topic'
        assert sns.size == 'topic'
    
    def test_parse_aws_sqs_queue(self):
        """Test parsing AWS SQS Queue."""
        hcl = '''
resource "aws_sqs_queue" "standard" {
  name = "standard-queue"
}

resource "aws_sqs_queue" "fifo" {
  name       = "fifo-queue.fifo"
  fifo_queue = true
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 2
        
        queues = {r.name: r for r in model.resources}
        assert queues['standard'].size == 'standard'
        assert queues['fifo'].size == 'fifo'
    
    def test_parse_aws_step_functions(self):
        """Test parsing AWS Step Functions State Machine."""
        hcl = '''
resource "aws_sfn_state_machine" "workflow" {
  name     = "my-workflow"
  type     = "EXPRESS"
  role_arn = aws_iam_role.step_function.arn
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        sfn = model.resources[0]
        assert sfn.type == 'aws_sfn_state_machine'
        assert sfn.size == 'EXPRESS'
    
    def test_parse_aws_api_gateway(self):
        """Test parsing AWS API Gateway."""
        hcl = '''
resource "aws_apigatewayv2_api" "http_api" {
  name          = "http-api"
  protocol_type = "HTTP"
}

resource "aws_api_gateway_rest_api" "rest_api" {
  name = "rest-api"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 2
        
        apis = [r for r in model.resources if r.type == 'aws_api_gateway']
        assert len(apis) == 2
    
    def test_parse_aws_cloudfront(self):
        """Test parsing AWS CloudFront Distribution."""
        hcl = '''
resource "aws_cloudfront_distribution" "cdn" {
  price_class = "PriceClass_100"
  enabled     = true
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        cf = model.resources[0]
        assert cf.type == 'aws_cloudfront_distribution'
        assert cf.region == 'global'
        assert cf.size == 'PriceClass_100'
    
    def test_parse_aws_neptune_cluster(self):
        """Test parsing AWS Neptune Cluster."""
        hcl = '''
resource "aws_neptune_cluster" "graph" {
  cluster_identifier  = "graph-db"
  instance_class      = "db.r5.large"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        neptune = model.resources[0]
        assert neptune.type == 'aws_neptune_cluster'
        assert neptune.size == 'db.r5.large'
    
    def test_parse_aws_documentdb_cluster(self):
        """Test parsing AWS DocumentDB Cluster."""
        hcl = '''
resource "aws_docdb_cluster" "docdb" {
  cluster_identifier = "my-docdb-cluster"
  instance_class     = "db.t3.medium"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        docdb = model.resources[0]
        assert docdb.type == 'aws_docdb_cluster'
        assert docdb.size == 'db.t3.medium'
    
    def test_parse_aws_msk_cluster(self):
        """Test parsing AWS MSK (Kafka) Cluster."""
        hcl = '''
resource "aws_msk_cluster" "kafka" {
  cluster_name = "kafka-cluster"
  instance_type = "kafka.m5.large"
  number_of_broker_nodes = 3
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        msk = model.resources[0]
        assert msk.type == 'aws_msk_cluster'
        assert msk.size == 'kafka.m5.large'
    
    def test_parse_aws_emr_cluster(self):
        """Test parsing AWS EMR Cluster."""
        hcl = '''
resource "aws_emr_cluster" "hadoop" {
  name          = "hadoop-cluster"
  master_instance_type = "m5.xlarge"
  core_instance_type   = "m5.large"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        emr = model.resources[0]
        assert emr.type == 'aws_emr_cluster'
        assert emr.size == 'm5.xlarge'
    
    def test_parse_aws_glue(self):
        """Test parsing AWS Glue resources."""
        hcl = '''
resource "aws_glue_job" "etl" {
  name     = "etl-job"
  role_arn = aws_iam_role.glue.arn
}

resource "aws_glue_crawler" "s3_crawler" {
  name          = "s3-crawler"
  database_name = aws_glue_catalog_database.example.name
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 2
        
        glue_resources = [r for r in model.resources if r.type == 'aws_glue']
        assert len(glue_resources) == 2
    
    def test_parse_aws_athena(self):
        """Test parsing AWS Athena Workgroup."""
        hcl = '''
resource "aws_athena_workgroup" "analytics" {
  name = "analytics-workgroup"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        athena = model.resources[0]
        assert athena.type == 'aws_athena_workgroup'
        assert athena.size == 'workgroup'
    
    def test_parse_aws_apprunner(self):
        """Test parsing AWS App Runner Service."""
        hcl = '''
resource "aws_apprunner_service" "api" {
  service_name = "api-service"
  
  instance_configuration {
    cpu    = 2
    memory = 4
  }
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        apprunner = model.resources[0]
        assert apprunner.type == 'aws_apprunner_service'
        assert '2vCPU' in apprunner.size
        assert '4GB' in apprunner.size


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

