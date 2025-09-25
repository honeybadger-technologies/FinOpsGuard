// MCP request/response types per section 8
import { CanonicalResourceModel, Recommendation, PolicyEvaluation, PricingConfidence } from './models';

export type IaCType = 'terraform' | 'helm' | 'k8s' | 'pulumi';

export interface CheckRequest {
  iac_type: IaCType;
  iac_payload: string; // base64 tarball or inline
  environment: 'dev' | 'staging' | 'prod';
  budget_rules?: {
    monthly_budget?: number;
    max_per_resource?: number;
  };
  options?: {
    prefer_spot?: boolean;
    max_execution_secs?: number;
  };
}

export interface ResourceBreakdownItem {
  resource_id: string;
  monthly_cost: number;
  notes?: string[];
}

export interface CheckResponse {
  estimated_monthly_cost: number;
  estimated_first_week_cost: number;
  breakdown_by_resource: ResourceBreakdownItem[];
  risk_flags: string[];
  recommendations: Recommendation[];
  policy_eval?: PolicyEvaluation;
  pricing_confidence: PricingConfidence;
  duration_ms: number;
}

export interface SuggestRequest {
  iac_type?: IaCType;
  resources?: CanonicalResourceModel['resources'];
}

export interface SuggestResponse {
  suggestions: Recommendation[];
}

export interface PolicyRequest {
  iac_type: IaCType;
  iac_payload: string;
  policy_id: string;
  mode?: 'advisory' | 'blocking';
}

export interface PolicyResponse extends PolicyEvaluation {}

export interface PriceQuery {
  cloud: 'aws' | 'gcp' | 'azure';
  region?: string;
  instance_types?: string[];
}

export interface PriceCatalogResponse {
  updated_at: string; // ISO timestamp
  pricing_confidence: PricingConfidence;
  items: Array<{
    sku: string;
    description?: string;
    region: string;
    unit: 'hour' | 'month' | 'gb-month' | 'requests';
    price: number;
    attributes?: Record<string, string>;
  }>;
}

export interface ListQuery {
  limit?: number;
  after?: string; // cursor
}

export interface ListResponse {
  items: Array<{
    request_id: string;
    started_at: string;
    duration_ms: number;
    summary: string;
  }>;
  next_cursor?: string;
}
