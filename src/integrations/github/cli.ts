#!/usr/bin/env node
import { postPrComment, formatCheckResponseMarkdown } from './index';

type Args = Record<string, string>;

function parseArgs(argv: string[]): Args {
  const out: Args = {};
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const key = a.slice(2);
      const val = argv[i + 1];
      out[key] = val;
      i++;
    }
  }
  return out;
}

async function main() {
  const args = parseArgs(process.argv);
  const owner = args.owner || process.env.GITHUB_REPOSITORY?.split('/')[0];
  const repo = args.repo || process.env.GITHUB_REPOSITORY?.split('/')[1];
  const pull = args.pr || process.env.PR_NUMBER;
  const token = args.token || process.env.GITHUB_TOKEN;
  const url = (args.url || process.env.FINOPSGUARD_URL || 'http://localhost:8080') + '/mcp/checkCostImpact';
  const iacFile = args['iac-file'];
  const iacType = (args['iac-type'] || 'terraform') as 'terraform' | 'helm' | 'k8s' | 'pulumi';
  const environment = (args.environment || 'dev') as 'dev' | 'staging' | 'prod';

  if (!owner || !repo || !pull || !token || !iacFile) {
    console.error('Missing required arguments: --owner --repo --pr --token --iac-file [--url] [--iac-type] [--environment]');
    process.exit(2);
  }

  const fs = await import('node:fs');
  const payload = fs.readFileSync(iacFile);
  const b64 = Buffer.from(payload).toString('base64');

  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ iac_type: iacType, iac_payload: b64, environment }),
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`checkCostImpact failed: ${resp.status} ${text}`);
  }
  const json = await resp.json();
  const body = formatCheckResponseMarkdown('FinOpsGuard Check', json);
  await postPrComment({ owner, repo, pull_number: Number(pull), token, body });
  // eslint-disable-next-line no-console
  console.log('Posted FinOpsGuard summary to PR #' + pull);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});


