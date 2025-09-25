import express from 'express';
import { checkCostImpact, evaluatePolicy, getPriceCatalog, listRecentAnalyses, suggestOptimizations } from './handlers';
import { metricsText } from '../metrics';
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

export const app = express();
app.use(express.json({ limit: '10mb' }));

function nowIso() { return new Date().toISOString(); }

app.post('/mcp/checkCostImpact', async (req, res) => {
  try {
    const body = req.body as CheckRequest;
    const response: CheckResponse = await checkCostImpact(body);
    res.json(response);
  } catch (e) {
    const err = (e as Error).message;
    if (err === 'invalid_request' || err === 'invalid_payload_encoding') {
      return res.status(400).json({ error: err });
    }
    return res.status(500).json({ error: 'internal_error' });
  }
});

app.post('/mcp/suggestOptimizations', async (req, res) => {
  const body = req.body as SuggestRequest;
  const response: SuggestResponse = await suggestOptimizations(body);
  res.json(response);
});

app.post('/mcp/evaluatePolicy', async (req, res) => {
  const body = req.body as PolicyRequest;
  const response: PolicyResponse = await evaluatePolicy(body);
  res.json(response);
});

app.post('/mcp/getPriceCatalog', async (req, res) => {
  const body = req.body as PriceQuery;
  const response: PriceCatalogResponse = await getPriceCatalog(body);
  res.json(response);
});

app.post('/mcp/listRecentAnalyses', async (req, res) => {
  const body = req.body as ListQuery;
  const response: ListResponse = await listRecentAnalyses(body);
  res.json(response);
});

app.get('/healthz', (_req, res) => {
  res.status(200).json({ status: 'ok', now: nowIso() });
});

app.get('/metrics', async (_req, res) => {
  try {
    const text = await metricsText();
    res.set('Content-Type', 'text/plain');
    res.send(text);
  } catch {
    res.status(500).json({ error: 'metrics_unavailable' });
  }
});

const port = process.env.PORT ? Number(process.env.PORT) : 8080;
export function startServer() {
  return app.listen(port, () => {
    console.log(`FinOpsGuard MCP listening on :${port}`);
  });
}

if (process.env.NODE_ENV === 'development' || process.env.NODE_ENV === 'production') {
  startServer();
}
