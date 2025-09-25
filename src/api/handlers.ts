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

export async function checkCostImpact(_req: CheckRequest): Promise<CheckResponse> {
  return {
    estimated_monthly_cost: 0,
    estimated_first_week_cost: 0,
    breakdown_by_resource: [],
    risk_flags: [],
    recommendations: [],
    pricing_confidence: 'low',
    duration_ms: 1,
  };
}

export async function suggestOptimizations(_req: SuggestRequest): Promise<SuggestResponse> {
  return { suggestions: [] };
}

export async function evaluatePolicy(req: PolicyRequest): Promise<PolicyResponse> {
  return { status: 'pass', policy_id: req.policy_id, reason: 'stub' };
}

export async function getPriceCatalog(_req: PriceQuery): Promise<PriceCatalogResponse> {
  return { updated_at: new Date().toISOString(), pricing_confidence: 'low', items: [] };
}

export async function listRecentAnalyses(_req: ListQuery): Promise<ListResponse> {
  return { items: [] };
}
