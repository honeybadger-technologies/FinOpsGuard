import client from 'prom-client';

export const register = new client.Registry();

// Default metrics
client.collectDefaultMetrics({ register });

export const checksTotal = new client.Counter({
  name: 'finops_checks_total',
  help: 'Total number of cost checks',
  labelNames: ['result', 'cloud'] as const,
});

export const checksDuration = new client.Histogram({
  name: 'finops_checks_duration_seconds',
  help: 'Duration of cost checks',
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60],
});

export const blocksTotal = new client.Counter({
  name: 'finops_blocks_total',
  help: 'Total number of blocking policy decisions',
});

export const recommendationsTotal = new client.Counter({
  name: 'finops_recommendations_total',
  help: 'Total number of recommendations emitted',
});

register.registerMetric(checksTotal);
register.registerMetric(checksDuration);
register.registerMetric(blocksTotal);
register.registerMetric(recommendationsTotal);

export async function metricsText(): Promise<string> {
  return register.metrics();
}

export {};