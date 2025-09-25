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
  if (!req || !req.iac_type || !req.iac_payload) {
    throw new Error('invalid_request');
  }
  let crModel;
  if (req.iac_type === 'terraform') {
    let decoded = '';
    try {
      decoded = Buffer.from(req.iac_payload, 'base64').toString('utf8');
    } catch {
      throw new Error('invalid_payload_encoding');
    }
    crModel = parseTerraformToCRModel(decoded);
  } else {
    crModel = { resources: [] };
  }
  const sim = simulateCost(crModel);
  const duration_ms = Date.now() - start;
  const response = { ...sim, duration_ms };

  // Apply simple budget rule if provided
  const monthlyBudget = req.budget_rules?.monthly_budget;
  if (typeof monthlyBudget === 'number') {
    if (response.estimated_monthly_cost > monthlyBudget) {
      if (!response.risk_flags.includes('over_budget')) response.risk_flags.push('over_budget');
      response.policy_eval = {
        status: 'fail',
        policy_id: 'monthly_budget',
        reason: `Estimated ${response.estimated_monthly_cost.toFixed(2)} exceeds budget ${monthlyBudget.toFixed(2)}`,
      };
    } else {
      response.policy_eval = { status: 'pass', policy_id: 'monthly_budget', reason: 'within budget' };
    }
  }
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
