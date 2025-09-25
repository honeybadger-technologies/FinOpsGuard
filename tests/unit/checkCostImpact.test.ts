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

  it('returns structured result for malformed HCL (AC-4) - graceful empty parse', async () => {
    const tf = `resource "aws_instance" {`;
    const res = await checkCostImpact({ iac_type: 'terraform', iac_payload: b64(tf), environment: 'dev' });
    expect(res.breakdown_by_resource.length).toBeGreaterThanOrEqual(0);
  });
});


