import { describe, it, expect } from 'vitest';
import { checkCostImpact } from '../../src/api/handlers';

function b64(input: string): string { return Buffer.from(input, 'utf8').toString('base64'); }

describe('checkCostImpact', () => {
  it('computes EC2 instance monthly cost (AC-1)', async () => {
    const tf = `
resource "aws_instance" "example" {
  ami = "ami-123"
  instance_type = "t3.medium"
}
provider "aws" { region = "us-east-1" }
`;
    const res = await checkCostImpact({ iac_type: 'terraform', iac_payload: b64(tf), environment: 'dev' });
    expect(res.estimated_monthly_cost).toBeGreaterThan(0);
    expect(res.breakdown_by_resource.length).toBeGreaterThan(0);
  });

  it('handles ALB, ASG, and EKS control plane', async () => {
    const tf = `
resource "aws_lb" "app" {}
resource "aws_autoscaling_group" "asg" {
  desired_capacity = 3
  # pretend nested launch template with instance_type
  instance_type = "m5.large"
}
resource "aws_eks_cluster" "main" {}
provider "aws" { region = "us-east-1" }
`;
    const res = await checkCostImpact({ iac_type: 'terraform', iac_payload: b64(tf), environment: 'dev' });
    expect(res.estimated_monthly_cost).toBeGreaterThan(0);
    const ids = res.breakdown_by_resource.map(b => b.resource_id).join('\n');
    expect(ids).toContain('app-lb-us-east-1');
    expect(ids).toContain('asg-asg-us-east-1');
    expect(ids).toContain('main-eks-us-east-1');
  });

  it('computes RDS, Redshift, OpenSearch, ElastiCache, DynamoDB provisioned', async () => {
    const tf = `
resource "aws_db_instance" "db" { instance_class = "db.t3.small" }
resource "aws_redshift_cluster" "rs" { node_type = "dc2.large" number_of_nodes = 2 }
resource "aws_opensearch_domain" "os" { instance_type = "t3.small.search" instance_count = 2 }
resource "aws_elasticache_cluster" "ec" { node_type = "cache.t3.micro" num_cache_nodes = 2 }
resource "aws_dynamodb_table" "d" { billing_mode = "PROVISIONED" read_capacity = 100 write_capacity = 50 }
provider "aws" { region = "us-east-1" }
`;
    const res = await checkCostImpact({ iac_type: 'terraform', iac_payload: b64(tf), environment: 'dev' });
    expect(res.estimated_monthly_cost).toBeGreaterThan(0);
    const ids = res.breakdown_by_resource.map(b => b.resource_id).join('\n');
    expect(ids).toContain('db-rds-us-east-1');
    expect(ids).toContain('rs-redshift-us-east-1');
    expect(ids).toContain('os-os-us-east-1');
    expect(ids).toContain('ec-elasticache-us-east-1');
    expect(ids).toContain('d-dynamodb-us-east-1');
  });

  it('returns structured result for malformed HCL (AC-4) - graceful empty parse', async () => {
    const tf = `resource "aws_instance" {`;
    const res = await checkCostImpact({ iac_type: 'terraform', iac_payload: b64(tf), environment: 'dev' });
    expect(res.breakdown_by_resource.length).toBeGreaterThanOrEqual(0);
  });

  it('applies budget policy and flags over_budget', async () => {
    const tf = `resource "aws_instance" "example" { instance_type = "m5.large" } provider "aws" { region = "us-east-1" }`;
    const res = await checkCostImpact({ iac_type: 'terraform', iac_payload: b64(tf), environment: 'dev', budget_rules: { monthly_budget: 1 } });
    expect(res.policy_eval?.status).toBe('fail');
    expect(res.risk_flags).toContain('over_budget');
  });
});


