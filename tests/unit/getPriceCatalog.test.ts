import { describe, it, expect } from 'vitest';
import { getPriceCatalog } from '../../src/api/handlers';

describe('getPriceCatalog', () => {
  it('lists EC2 prices with no filters', async () => {
    const res = await getPriceCatalog({ cloud: 'aws', region: undefined, instance_types: undefined });
    expect(res.items.length).toBeGreaterThan(0);
  });

  it('filters by region', async () => {
    const res = await getPriceCatalog({ cloud: 'aws', region: 'us-east-1', instance_types: undefined });
    expect(res.items.length).toBeGreaterThan(0);
    for (const it of res.items) expect(it.region).toBe('us-east-1');
  });

  it('filters by instance types', async () => {
    const res = await getPriceCatalog({ cloud: 'aws', region: 'us-east-1', instance_types: ['t3.medium'] });
    expect(res.items.length).toBe(1);
    expect(res.items[0].sku).toContain('t3.medium');
  });
});


