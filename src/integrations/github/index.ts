import type { CheckResponse } from '../../types/api';

export interface GithubRepoRef {
  owner: string;
  repo: string;
}

export interface GithubAuth {
  token: string; // GitHub token with repo:scope
}

export interface PostPrCommentParams extends GithubRepoRef, GithubAuth {
  pull_number: number;
  body: string;
}

export async function postPrComment(params: PostPrCommentParams): Promise<void> {
  const { owner, repo, pull_number, body, token } = params;
  const url = `https://api.github.com/repos/${owner}/${repo}/issues/${pull_number}/comments`;
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      'User-Agent': 'finopsguard-mcp',
      Accept: 'application/vnd.github+json',
    },
    body: JSON.stringify({ body }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`GitHub comment failed: ${res.status} ${text}`);
  }
}

export function formatCheckResponseMarkdown(title: string, response: CheckResponse): string {
  const lines: string[] = [];
  lines.push(`### ${title}`);
  lines.push('');
  lines.push(`- Estimated monthly: $${response.estimated_monthly_cost.toFixed(2)}`);
  lines.push(`- First week: $${response.estimated_first_week_cost.toFixed(2)}`);
  lines.push(`- Pricing confidence: ${response.pricing_confidence}`);
  if (response.policy_eval) {
    lines.push(`- Policy: ${response.policy_eval.status}${response.policy_eval.policy_id ? ` (${response.policy_eval.policy_id})` : ''}`);
  }
  lines.push('');
  lines.push('<details><summary>Breakdown</summary>');
  lines.push('');
  lines.push('| Resource | Monthly | Notes |');
  lines.push('|---|---:|---|');
  for (const item of response.breakdown_by_resource) {
    const notes = (item.notes ?? []).join('; ');
    lines.push(`| ${item.resource_id} | $${item.monthly_cost.toFixed(2)} | ${notes} |`);
  }
  lines.push('</details>');
  if (response.recommendations?.length) {
    lines.push('');
    lines.push('#### Recommendations');
    for (const r of response.recommendations) {
      const savings = r.estimated_savings_monthly ? ` (save ~$${r.estimated_savings_monthly.toFixed(2)}/mo)` : '';
      lines.push(`- ${r.description}${savings}`);
    }
  }
  return lines.join('\n');
}

export {};
