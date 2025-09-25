import type {
  CheckRequest,
  CheckResponse,
  SuggestRequest,
  SuggestResponse,
  PolicyRequest,
  PolicyResponse,
  PriceQuery,
  PriceCatalogResponse,
  ListQuery,
  ListResponse,
} from '../types/api';
import { parseTerraformToCRModel } from '../parsers/terraform';
import { simulateCost } from '../engine/simulation';
import { listAwsEc2OnDemand } from '../adapters/pricing/awsStatic';
import { addAnalysis, listAnalyses } from '../storage/analyses';

export async function checkCostImpact(req: CheckRequest): Promise<CheckResponse> {
  const start = Date.now();
  let crModel;
  if (req.iac_type === 'terraform') {
    crModel = parseTerraformToCRModel(Buffer.from(req.iac_payload, 'base64').toString('utf8'));
  } else {
    crModel = { resources: [] };
  }
  const sim = simulateCost(crModel);
  const duration_ms = Date.now() - start;
  const response = { ...sim, duration_ms };
  addAnalysis({
    request_id: `${start}`,
    started_at: new Date(start).toISOString(),
    duration_ms,
    summary: `monthly=${response.estimated_monthly_cost.toFixed(2)} resources=${response.breakdown_by_resource.length}`,
  });
  return response;
}

export async function suggestOptimizations(_req: SuggestRequest): Promise<SuggestResponse> {
  return { suggestions: [] };
}

export async function evaluatePolicy(req: PolicyRequest): Promise<PolicyResponse> {
  return { status: 'pass', policy_id: req.policy_id, reason: 'stub' };
}

export async function getPriceCatalog(_req: PriceQuery): Promise<PriceCatalogResponse> {
  const items = listAwsEc2OnDemand(_req.region, _req.instance_types).map((i) => ({
    sku: i.sku,
    description: i.description,
    region: i.region,
    unit: 'hour' as const,
    price: i.price,
    attributes: {},
  }));
  return {
    updated_at: new Date().toISOString(),
    pricing_confidence: items.length > 0 ? 'high' : 'low',
    items,
  };
}

export async function listRecentAnalyses(req: ListQuery): Promise<ListResponse> {
  const { items, next_cursor } = listAnalyses(req.limit ?? 20, req.after);
  return { items, next_cursor };
}
