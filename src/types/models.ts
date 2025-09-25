// Canonical Resource Model and shared types
export interface CanonicalResource {
  id: string;
  type: string;
  name: string;
  region: string;
  size: string;
  count: number;
  tags?: Record<string, string>;
  metadata?: Record<string, unknown>;
}

export interface CanonicalResourceModel {
  resources: CanonicalResource[];
}

export type PricingConfidence = 'high' | 'medium' | 'low';

export interface Recommendation {
  id: string;
  type: 'right_size' | 'spot' | 'reserved' | 'autoscale' | 'other';
  description: string;
  estimated_savings_monthly?: number;
}

export interface PolicyEvaluation {
  status: 'pass' | 'fail';
  policy_id?: string;
  reason?: string;
}
