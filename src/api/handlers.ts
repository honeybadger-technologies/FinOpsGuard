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
  return { ...sim, duration_ms };
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
