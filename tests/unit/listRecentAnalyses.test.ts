import { describe, it, expect } from 'vitest';
import { checkCostImpact, listRecentAnalyses } from '../../src/api/handlers';

function b64(s: string) { return Buffer.from(s, 'utf8').toString('base64'); }

describe('listRecentAnalyses', () => {
  it('returns recent analyses with limit and cursor', async () => {
    const tf = `resource "aws_instance" "a" { instance_type = "t3.micro" } provider "aws" { region = "us-east-1" }`;
    // create a few analyses
    for (let i = 0; i < 5; i++) {
      await checkCostImpact({ iac_type: 'terraform', iac_payload: b64(tf), environment: 'dev' });
    }
    const first = await listRecentAnalyses({ limit: 3 });
    expect(first.items.length).toBe(3);
    const second = await listRecentAnalyses({ limit: 3, after: first.items[first.items.length - 1].started_at });
    expect(second.items.length).toBeGreaterThan(0);
  });
});


