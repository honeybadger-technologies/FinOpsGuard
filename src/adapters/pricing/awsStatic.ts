import type { PricingConfidence } from '../../types/models';

type PriceKey = `${string}:${string}`; // `${region}:${instanceType}`

const ON_DEMAND_HOURLY_USD: Record<PriceKey, number> = {
  'us-east-1:t3.micro': 0.0104,
  'us-east-1:t3.medium': 0.0416,
  'us-east-1:m5.large': 0.096,
  'us-east-1:c7g.large': 0.072,
};

// Simplified monthly costs for LB/EKS control plane, etc.
export const MONTHLY_FLAT_USD = {
  aws_lb_application: 18, // very rough placeholder
  aws_eks_cluster_control_plane: 73, // EKS control plane approx per month
};

// Naive static hourly prices (very rough placeholders) for select services
export const HOURLY_SERVICE_USD = {
  rds: {
    'us-east-1:db.t3.micro': 0.017,
    'us-east-1:db.t3.small': 0.034,
  },
  redshift: {
    'us-east-1:dc2.large': 0.25,
  },
  opensearch: {
    'us-east-1:t3.small.search': 0.036,
  },
  elasticache: {
    'us-east-1:cache.t3.micro': 0.017,
  },
  dynamodb_provisioned: {
    read_capacity_hour: 0.00013, // per RCU-hour
    write_capacity_hour: 0.00065, // per WCU-hour
  },
};

export interface InstancePrice {
  hourly_usd: number;
  monthly_usd: number;
  pricing_confidence: PricingConfidence;
}

export function getAwsEc2OnDemandPrice(region: string, instanceType: string): InstancePrice {
  const key = `${region}:${instanceType}` as PriceKey;
  const hourly = ON_DEMAND_HOURLY_USD[key];
  if (hourly === undefined) {
    // default fallback
    return { hourly_usd: 0.1, monthly_usd: 0.1 * 730, pricing_confidence: 'low' };
  }
  return { hourly_usd: hourly, monthly_usd: hourly * 730, pricing_confidence: 'high' };
}

export function listAwsEc2OnDemand(region?: string, instanceTypes?: string[]) {
  const items: Array<{ sku: string; region: string; unit: 'hour'; price: number; description: string }> = [];
  for (const [key, price] of Object.entries(ON_DEMAND_HOURLY_USD)) {
    const [r, it] = key.split(':');
    if (region && r !== region) continue;
    if (instanceTypes && instanceTypes.length > 0 && !instanceTypes.includes(it)) continue;
    items.push({
      sku: `aws_ec2_${it}_ondemand_${r}`,
      region: r,
      unit: 'hour',
      price,
      description: `EC2 ${it} on-demand in ${r}`,
    });
  }
  return items;
}


