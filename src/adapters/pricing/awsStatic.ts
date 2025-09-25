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


