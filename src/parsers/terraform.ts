import type { CanonicalResource, CanonicalResourceModel } from '../types/models';

// Minimal heuristic Terraform parser for MVP
// Extracts aws instance type, region, count from a simple HCL string
export function parseTerraformToCRModel(hclText: string): CanonicalResourceModel {
  const resources: CanonicalResource[] = [];

  const regionMatchGlobal = hclText.match(/provider\s+"aws"\s*\{[^}]*region\s*=\s*"([a-z0-9-]+)"/i);
  const defaultRegion = regionMatchGlobal?.[1] ?? 'us-east-1';

  // Extract resource blocks
  const resourceRegex = /resource\s+"([^"]+)"\s+"([^"]+)"\s*\{([\s\S]*?)\}/g;
  let match: RegExpExecArray | null;
  while ((match = resourceRegex.exec(hclText)) !== null) {
    const [, rType, rName, body] = match;
    const name = rName;
    const regionMatch = body.match(/region\s*=\s*"([a-z0-9-]+)"/i);
    const region = regionMatch?.[1] ?? defaultRegion;
    const countMatch = body.match(/count\s*=\s*([0-9]+)/i);
    const count = countMatch ? parseInt(countMatch[1], 10) : 1;

    if (rType === 'aws_instance') {
      const instMatch = body.match(/instance_type\s*=\s*"([a-z0-9.\-]+)"/i);
      const instanceType = instMatch?.[1] ?? 't3.micro';
      resources.push({
        id: `${name}-${instanceType}-${region}`,
        type: 'aws_instance',
        name,
        region,
        size: instanceType,
        count,
        tags: {},
        metadata: {},
      });
      continue;
    }

    if (rType === 'aws_lb' || rType === 'aws_alb' || rType === 'aws_lb_listener') {
      resources.push({
        id: `${name}-lb-${region}`,
        type: 'aws_lb',
        name,
        region,
        size: 'application',
        count,
        tags: {},
        metadata: {},
      });
      continue;
    }

    if (rType === 'aws_autoscaling_group') {
      const desired = body.match(/desired_capacity\s*=\s*([0-9]+)/i);
      const launchType = body.match(/instance_type\s*=\s*"([a-z0-9.\-]+)"/i);
      const instanceType = launchType?.[1] ?? 't3.medium';
      const desiredCount = desired ? parseInt(desired[1], 10) : count;
      resources.push({
        id: `${name}-asg-${region}`,
        type: 'aws_asg',
        name,
        region,
        size: instanceType,
        count: desiredCount,
        tags: {},
        metadata: {},
      });
      continue;
    }

    if (rType === 'aws_eks_cluster') {
      resources.push({
        id: `${name}-eks-${region}`,
        type: 'aws_eks_cluster',
        name,
        region,
        size: 'control_plane',
        count,
        tags: {},
        metadata: {},
      });
      continue;
    }

    // RDS instance
    if (rType === 'aws_db_instance') {
      const cl = body.match(/instance_class\s*=\s*"([a-z0-9.\-]+)"/i)?.[1] ?? 'db.t3.micro';
      resources.push({
        id: `${name}-rds-${region}`,
        type: 'aws_rds_instance',
        name,
        region,
        size: cl,
        count,
        tags: {},
        metadata: {},
      });
      continue;
    }

    // Redshift cluster
    if (rType === 'aws_redshift_cluster') {
      const nodeType = body.match(/node_type\s*=\s*"([a-z0-9.\-]+)"/i)?.[1] ?? 'dc2.large';
      const nodes = body.match(/number_of_nodes\s*=\s*([0-9]+)/i);
      const numNodes = nodes ? parseInt(nodes[1], 10) : 1;
      resources.push({
        id: `${name}-redshift-${region}`,
        type: 'aws_redshift_cluster',
        name,
        region,
        size: nodeType,
        count: numNodes,
        tags: {},
        metadata: {},
      });
      continue;
    }

    // OpenSearch domain
    if (rType === 'aws_opensearch_domain') {
      const inst = body.match(/instance_type\s*=\s*"([a-z0-9.\-]+)"/i)?.[1] ?? 't3.small.search';
      const instCount = body.match(/instance_count\s*=\s*([0-9]+)/i);
      const replicas = instCount ? parseInt(instCount[1], 10) : 1;
      resources.push({
        id: `${name}-os-${region}`,
        type: 'aws_opensearch',
        name,
        region,
        size: inst,
        count: replicas,
        tags: {},
        metadata: {},
      });
      continue;
    }

    // ElastiCache cluster/replication group (approximate nodes)
    if (rType === 'aws_elasticache_cluster') {
      const nodeType = body.match(/node_type\s*=\s*"([a-z0-9.\-]+)"/i)?.[1] ?? 'cache.t3.micro';
      const nodes = body.match(/num_cache_nodes\s*=\s*([0-9]+)/i);
      const numNodes = nodes ? parseInt(nodes[1], 10) : 1;
      resources.push({
        id: `${name}-elasticache-${region}`,
        type: 'aws_elasticache',
        name,
        region,
        size: nodeType,
        count: numNodes,
        tags: {},
        metadata: {},
      });
      continue;
    }
    if (rType === 'aws_elasticache_replication_group') {
      const nodeType = body.match(/node_type\s*=\s*"([a-z0-9.\-]+)"/i)?.[1] ?? 'cache.t3.micro';
      const replicas = body.match(/replicas_per_node_group\s*=\s*([0-9]+)/i);
      const shardCount = body.match(/num_node_groups\s*=\s*([0-9]+)/i);
      const countNodes = (replicas ? parseInt(replicas[1], 10) : 0) + 1;
      const total = (shardCount ? parseInt(shardCount[1], 10) : 1) * countNodes;
      resources.push({
        id: `${name}-elasticache-rg-${region}`,
        type: 'aws_elasticache',
        name,
        region,
        size: nodeType,
        count: total,
        tags: {},
        metadata: {},
      });
      continue;
    }

    // DynamoDB table (bill pay-per-request or provisioned capacity)
    if (rType === 'aws_dynamodb_table') {
      const billing = body.match(/billing_mode\s*=\s*"([A-Z_]+)"/i)?.[1] ?? 'PAY_PER_REQUEST';
      const read = body.match(/read_capacity\s*=\s*([0-9]+)/i);
      const write = body.match(/write_capacity\s*=\s*([0-9]+)/i);
      resources.push({
        id: `${name}-dynamodb-${region}`,
        type: 'aws_dynamodb_table',
        name,
        region,
        size: billing.toUpperCase(),
        count: 1,
        tags: {},
        metadata: {
          read_capacity: read ? parseInt(read[1], 10) : undefined,
          write_capacity: write ? parseInt(write[1], 10) : undefined,
        },
      });
      continue;
    }
  }

  return { resources };
}


