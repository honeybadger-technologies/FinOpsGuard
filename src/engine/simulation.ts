import type { CanonicalResourceModel } from '../types/models';
import type { CheckResponse, ResourceBreakdownItem } from '../types/api';
import { getAwsEc2OnDemandPrice, MONTHLY_FLAT_USD } from '../adapters/pricing/awsStatic';

export function simulateCost(crModel: CanonicalResourceModel): Omit<CheckResponse, 'policy_eval'> {
  const breakdown: ResourceBreakdownItem[] = [];
  let totalMonthly = 0;
  for (const r of crModel.resources) {
    if (r.type === 'aws_instance') {
      const price = getAwsEc2OnDemandPrice(r.region, r.size);
      const monthly = price.monthly_usd * r.count;
      totalMonthly += monthly;
      breakdown.push({ resource_id: r.id, monthly_cost: monthly, notes: [] });
      continue;
    }
    if (r.type === 'aws_lb') {
      const monthly = MONTHLY_FLAT_USD.aws_lb_application * r.count;
      totalMonthly += monthly;
      breakdown.push({ resource_id: r.id, monthly_cost: monthly, notes: [] });
      continue;
    }
    if (r.type === 'aws_asg') {
      const price = getAwsEc2OnDemandPrice(r.region, r.size);
      const monthly = price.monthly_usd * r.count;
      totalMonthly += monthly;
      breakdown.push({ resource_id: r.id, monthly_cost: monthly, notes: [] });
      continue;
    }
    if (r.type === 'aws_eks_cluster') {
      const monthly = MONTHLY_FLAT_USD.aws_eks_cluster_control_plane * r.count;
      totalMonthly += monthly;
      breakdown.push({ resource_id: r.id, monthly_cost: monthly, notes: [] });
      continue;
    }
  }

  const estimated_first_week_cost = totalMonthly / 4.345; // approx 1 week of month

  return {
    estimated_monthly_cost: Number(totalMonthly.toFixed(2)),
    estimated_first_week_cost: Number(estimated_first_week_cost.toFixed(2)),
    breakdown_by_resource: breakdown,
    risk_flags: [],
    recommendations: [],
    pricing_confidence: 'high',
    duration_ms: 1,
  };
}


