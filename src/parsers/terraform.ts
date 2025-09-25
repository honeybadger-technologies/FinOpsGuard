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
  }

  return { resources };
}


