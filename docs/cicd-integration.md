# FinOpsGuard CI/CD Integration Guide

This guide explains how to integrate FinOpsGuard into your CI/CD pipelines to automatically check infrastructure costs and enforce cost governance policies.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [GitHub Actions Integration](#github-actions-integration)
- [GitLab CI Integration](#gitlab-ci-integration)
- [CLI Tool](#cli-tool)
- [Universal CI/CD Script](#universal-cicd-script)
- [Configuration](#configuration)
- [Exit Codes](#exit-codes)
- [Troubleshooting](#troubleshooting)
- [Examples](#examples)

## Overview

FinOpsGuard provides multiple integration options for CI/CD pipelines:

1. **GitHub Actions Workflow** - Ready-to-use workflow for GitHub repositories
2. **GitLab CI Template** - Reusable job template for GitLab CI/CD
3. **CLI Tool** - Command-line interface for any CI/CD platform
4. **Universal Script** - Bash script that works across all platforms

All integrations provide:
- ✅ **Automatic Infrastructure Detection** - Finds Terraform and Kubernetes files
- ✅ **Cost Analysis** - Estimates monthly and weekly costs
- ✅ **Policy Evaluation** - Enforces cost governance policies
- ✅ **PR/MR Comments** - Posts detailed results to pull/merge requests
- ✅ **Blocking Mode** - Can prevent deployments on policy violations
- ✅ **Multiple Output Formats** - Text, JSON, JUnit XML

## Quick Start

### 1. Set Up FinOpsGuard Server

First, ensure your FinOpsGuard server is running and accessible:

```bash
# Start FinOpsGuard server
python -m finopsguard.main

# Verify it's running
curl http://localhost:8080/healthz
```

### 2. Choose Your Integration Method

#### Option A: GitHub Actions (Recommended for GitHub repos)
Copy the workflow file from the examples directory to your repository:
```bash
cp examples/.github/workflows/finopsguard-check.yml your-repo/.github/workflows/
```

#### Option B: GitLab CI (Recommended for GitLab repos)
Copy the template from the examples directory and include it in your `.gitlab-ci.yml`:
```bash
cp examples/.gitlab/ci-templates/finopsguard.yml .gitlab/ci-templates/
```

```yaml
include:
  - local: '.gitlab/ci-templates/finopsguard.yml'

finopsguard_cost_check:
  extends: .finopsguard_cost_check
```

#### Option C: CLI Tool (Any CI/CD platform)
```bash
# Install and use the CLI
pip install -r requirements.txt
python -m finopsguard.cli.main check-cost
```

#### Option D: Universal Script (Any platform)
```bash
# Make executable and run
chmod +x scripts/finopsguard-cicd.sh
./scripts/finopsguard-cicd.sh
```

### 3. Configure Environment Variables

Set the required environment variables in your CI/CD platform:

```bash
FINOPSGUARD_URL=https://your-finopsguard-instance.com
FINOPSGUARD_TOKEN=your-api-token  # Optional
FINOPSGUARD_ENVIRONMENT=dev
FINOPSGUARD_MONTHLY_BUDGET=500
```

## GitHub Actions Integration

### Setup

1. Copy the workflow file from the examples directory to your repository:
```bash
cp examples/.github/workflows/finopsguard-check.yml .github/workflows/
```

2. Configure repository variables and secrets:
   - **Variables** (Settings → Secrets and variables → Actions → Variables):
     - `FINOPSGUARD_URL`: Your FinOpsGuard API URL
     - `FINOPSGUARD_ENVIRONMENT`: Environment name (dev/staging/prod)
     - `FINOPSGUARD_MONTHLY_BUDGET`: Monthly budget limit
   
   - **Secrets** (Settings → Secrets and variables → Actions → Secrets):
     - `FINOPSGUARD_TOKEN`: API authentication token (optional)

### Workflow Features

- **Triggers**: Pull requests and pushes to main branches
- **File Detection**: Automatically detects `.tf`, `.tfvars`, `.hcl`, `.yaml`, `.yml` files
- **PR Comments**: Posts detailed cost analysis results to pull requests
- **Blocking**: Fails the workflow on policy violations
- **Artifacts**: Saves analysis results as workflow artifacts

### Example Output

The workflow will post a comment like this on your pull request:

```markdown
## 💰 FinOpsGuard Cost Analysis

### 📊 Cost Summary
- **Estimated Monthly Cost**: $127.50
- **Estimated Weekly Cost**: $31.88
- **Environment**: dev
- **Monthly Budget**: $500

### 🛡️ Policy Evaluation
✅ **Status**: PASS

### 💡 Recommendations
- Consider using smaller instance types for development
- Enable spot instances for non-critical workloads

### 📋 Resource Breakdown
- **aws_instance** (t3.medium): $30.40/month
- **aws_rds_instance** (db.t3.micro): $12.41/month
```

## GitLab CI Integration

### Setup

1. Copy the CI template from the examples directory to your repository:
```bash
cp examples/.gitlab/ci-templates/finopsguard.yml .gitlab/ci-templates/
```

2. Include it in your `.gitlab-ci.yml`:
```yaml
include:
  - local: '.gitlab/ci-templates/finopsguard.yml'

variables:
  FINOPSGUARD_URL: "https://your-finopsguard-instance.com"
  FINOPSGUARD_TOKEN: $FINOPSGUARD_API_TOKEN
  FINOPSGUARD_ENVIRONMENT: "dev"
  FINOPSGUARD_MONTHLY_BUDGET: "500"

stages:
  - test

finopsguard_cost_check:
  extends: .finopsguard_cost_check

finopsguard_mr_comment:
  extends: .finopsguard_mr_comment
```

### Configuration

Set these variables in your GitLab project (Settings → CI/CD → Variables):

- `FINOPSGUARD_URL`: FinOpsGuard API URL
- `FINOPSGUARD_TOKEN`: API authentication token
- `FINOPSGUARD_ENVIRONMENT`: Environment name
- `FINOPSGUARD_MONTHLY_BUDGET`: Monthly budget limit

## CLI Tool

The FinOpsGuard CLI provides a command-line interface for cost checking and policy evaluation.

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Make CLI executable (optional)
chmod +x src/finopsguard/cli/main.py
```

### Usage

```bash
# Basic cost check
python -m finopsguard.cli.main check-cost

# With specific options
python -m finopsguard.cli.main check-cost \
  --directory /path/to/iac \
  --environment prod \
  --budget 1000 \
  --output json

# Policy evaluation only
python -m finopsguard.cli.main evaluate-policy \
  --environment staging

# List all policies
python -m finopsguard.cli.main list-policies

# Health check
python -m finopsguard.cli.main health
```

### Command Reference

| Command | Description | Options |
|---------|-------------|---------|
| `check-cost` | Check cost impact of infrastructure changes | `--directory`, `--files`, `--environment`, `--budget` |
| `evaluate-policy` | Evaluate policies against infrastructure | `--directory`, `--files`, `--environment` |
| `list-policies` | List all configured policies | None |
| `price-catalog` | Get price catalog information | `--service`, `--region` |
| `health` | Check FinOpsGuard service health | None |

## Universal CI/CD Script

The `finopsguard-cicd.sh` script provides a universal integration solution that works across all CI/CD platforms.

### Features

- **Platform Detection**: Automatically detects GitHub Actions, GitLab CI, Jenkins, etc.
- **Infrastructure Detection**: Finds Terraform and Kubernetes files
- **Multiple Output Formats**: Text, JSON, JUnit XML
- **PR/MR Comments**: Posts results to pull/merge requests
- **Flexible Configuration**: Environment variables and command-line options

### Usage

```bash
# Basic usage
./scripts/finopsguard-cicd.sh

# With options
./scripts/finopsguard-cicd.sh \
  --work-dir /path/to/iac \
  --format json \
  --output results.json \
  --verbose

# Skip commenting on PR
./scripts/finopsguard-cicd.sh --skip-comment

# Don't fail on policy violations
./scripts/finopsguard-cicd.sh --no-fail
```

### Options

| Option | Description |
|--------|-------------|
| `-h, --help` | Show help message |
| `-v, --verbose` | Enable verbose output |
| `-w, --work-dir DIR` | Working directory |
| `-o, --output FILE` | Output file for results |
| `-f, --format FORMAT` | Output format (text/json/junit) |
| `--skip-comment` | Skip posting comments to PR/MR |
| `--skip-policy-check` | Skip policy evaluation |
| `--no-fail` | Don't exit with error on policy violations |

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FINOPSGUARD_URL` | FinOpsGuard API URL | `http://localhost:8080` | Yes |
| `FINOPSGUARD_TOKEN` | API authentication token | None | No |
| `FINOPSGUARD_ENVIRONMENT` | Environment name | `dev` | No |
| `FINOPSGUARD_MONTHLY_BUDGET` | Monthly budget limit | `100` | No |
| `FINOPSGUARD_FAIL_ON_POLICY_VIOLATION` | Fail on policy violations | `true` | No |
| `FINOPSGUARD_COMMENT_ON_PR` | Comment on PR/MR | `true` | No |
| `FINOPSGUARD_OUTPUT_FORMAT` | Output format | `text` | No |

### Platform-Specific Variables

#### GitHub Actions
- `GITHUB_TOKEN`: GitHub API token (automatically provided)
- `GITHUB_PR_NUMBER`: Pull request number (automatically provided)

#### GitLab CI
- `GITLAB_TOKEN`: GitLab API token
- `CI_MERGE_REQUEST_IID`: Merge request IID (automatically provided)
- `CI_PROJECT_ID`: Project ID (automatically provided)

## Exit Codes

The CI/CD integrations use the following exit codes:

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success - no policy violations | Continue deployment |
| 1 | Policy violation detected | Block deployment (if `FAIL_ON_POLICY_VIOLATION=true`) |
| 2 | Infrastructure files not found | Skip cost check |
| 3 | FinOpsGuard API error | Block deployment |
| 4 | Invalid configuration | Block deployment |
| 5 | CI platform detection error | Block deployment |

## Troubleshooting

### Common Issues

#### 1. "FinOpsGuard service is not responding"

**Cause**: FinOpsGuard server is not running or not accessible.

**Solution**:
```bash
# Check if server is running
curl http://localhost:8080/healthz

# Start the server
python -m finopsguard.main

# Check logs for errors
tail -f finopsguard.log
```

#### 2. "No infrastructure files found"

**Cause**: No Terraform or Kubernetes files detected in the repository.

**Solution**:
- Ensure you have `.tf`, `.tfvars`, `.hcl`, `.yaml`, or `.yml` files
- Check the working directory with `--work-dir` option
- Use `--files` option to specify specific files

#### 3. "Policy evaluation failed"

**Cause**: Infrastructure changes violate configured policies.

**Solution**:
- Review the policy violation details in the output
- Adjust your infrastructure configuration
- Update policies in the FinOpsGuard admin UI
- Use `--no-fail` option to continue despite violations

#### 4. "Authentication failed"

**Cause**: Invalid or missing API token.

**Solution**:
- Verify `FINOPSGUARD_TOKEN` is set correctly
- Check token permissions in FinOpsGuard admin UI
- Ensure token is not expired

#### 5. "Comment posting failed"

**Cause**: Unable to post comments to PR/MR.

**Solution**:
- Verify CI platform tokens are set correctly
- Check repository permissions
- Use `--skip-comment` option to disable commenting

### Debug Mode

Enable verbose output for detailed debugging:

```bash
# CLI tool
python -m finopsguard.cli.main check-cost --verbose

# Universal script
./scripts/finopsguard-cicd.sh --verbose
```

### Logs

Check the following logs for troubleshooting:

- **FinOpsGuard Server**: Application logs from the server process
- **CI/CD Platform**: Platform-specific logs (GitHub Actions, GitLab CI, etc.)
- **Integration Scripts**: Output from verbose mode

## Examples

### Example 1: GitHub Actions with Custom Budget

```yaml
name: FinOpsGuard Cost Check

on:
  pull_request:
    paths: ['**/*.tf', '**/*.yaml']

jobs:
  cost-check:
    runs-on: ubuntu-latest
    env:
      FINOPSGUARD_URL: https://finopsguard.company.com
      FINOPSGUARD_TOKEN: ${{ secrets.FINOPSGUARD_TOKEN }}
      FINOPSGUARD_ENVIRONMENT: staging
      FINOPSGUARD_MONTHLY_BUDGET: 2000
    steps:
      - uses: actions/checkout@v4
      - name: FinOpsGuard Cost Check
        run: |
          curl -fsSL https://raw.githubusercontent.com/your-org/finopsguard/main/scripts/finopsguard-cicd.sh | bash
```

### Example 2: GitLab CI with Multiple Environments

```yaml
stages:
  - cost-check

variables:
  FINOPSGUARD_URL: "https://finopsguard.company.com"
  FINOPSGUARD_TOKEN: $FINOPSGUARD_API_TOKEN

.cost_check_template:
  extends: .finopsguard_cost_check
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'

cost_check_dev:
  extends: .cost_check_template
  variables:
    FINOPSGUARD_ENVIRONMENT: "dev"
    FINOPSGUARD_MONTHLY_BUDGET: "500"

cost_check_staging:
  extends: .cost_check_template
  variables:
    FINOPSGUARD_ENVIRONMENT: "staging"
    FINOPSGUARD_MONTHLY_BUDGET: "2000"
  rules:
    - if: '$CI_COMMIT_BRANCH == "staging"'

cost_check_prod:
  extends: .cost_check_template
  variables:
    FINOPSGUARD_ENVIRONMENT: "prod"
    FINOPSGUARD_MONTHLY_BUDGET: "10000"
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
```

### Example 3: Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    environment {
        FINOPSGUARD_URL = 'https://finopsguard.company.com'
        FINOPSGUARD_TOKEN = credentials('finopsguard-token')
        FINOPSGUARD_ENVIRONMENT = 'dev'
        FINOPSGUARD_MONTHLY_BUDGET = '1000'
    }
    
    stages {
        stage('Cost Check') {
            steps {
                script {
                    sh '''
                        curl -fsSL https://raw.githubusercontent.com/your-org/finopsguard/main/scripts/finopsguard-cicd.sh | bash
                    '''
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'finopsguard_response.json', fingerprint: true
        }
    }
}
```

### Example 4: Azure DevOps Pipeline

```yaml
trigger:
- main

pool:
  vmImage: 'ubuntu-latest'

variables:
  FINOPSGUARD_URL: 'https://finopsguard.company.com'
  FINOPSGUARD_ENVIRONMENT: 'dev'
  FINOPSGUARD_MONTHLY_BUDGET: '1000'

steps:
- task: Bash@3
  inputs:
    targetType: 'inline'
    script: |
      curl -fsSL https://raw.githubusercontent.com/your-org/finopsguard/main/scripts/finopsguard-cicd.sh | bash
  env:
    FINOPSGUARD_TOKEN: $(finopsguard-token)

- task: PublishTestResults@2
  inputs:
    testResultsFiles: 'finopsguard_report.xml'
    testRunTitle: 'FinOpsGuard Cost Check'
  condition: always()
```

---

For more information, visit the [FinOpsGuard documentation](https://github.com/your-org/finopsguard) or contact the FinOps team.
