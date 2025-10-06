#!/bin/bash
# FinOpsGuard CI/CD Integration Script
# 
# This script provides a unified interface for integrating FinOpsGuard
# into various CI/CD platforms (GitHub Actions, GitLab CI, Jenkins, etc.)
#
# Usage:
#   ./finopsguard-cicd.sh [OPTIONS]
#
# Environment Variables:
#   FINOPSGUARD_URL           FinOpsGuard API URL (default: http://localhost:8080)
#   FINOPSGUARD_TOKEN         API authentication token
#   FINOPSGUARD_ENVIRONMENT   Environment name (default: dev)
#   FINOPSGUARD_MONTHLY_BUDGET Monthly budget limit (default: 100)
#   FINOPSGUARD_FAIL_ON_POLICY_VIOLATION Whether to fail on policy violations (default: true)
#   FINOPSGUARD_COMMENT_ON_PR Whether to comment on PR/MR (default: true)
#   FINOPSGUARD_OUTPUT_FORMAT Output format: text, json, junit (default: text)
#
# CI Platform Detection:
#   GITHUB_ACTIONS            Set automatically by GitHub Actions
#   GITLAB_CI                 Set automatically by GitLab CI
#   JENKINS                   Set automatically by Jenkins
#   CI                        Generic CI environment variable

set -euo pipefail

# Default values
FINOPSGUARD_URL="${FINOPSGUARD_URL:-http://localhost:8080}"
FINOPSGUARD_TOKEN="${FINOPSGUARD_TOKEN:-}"
FINOPSGUARD_ENVIRONMENT="${FINOPSGUARD_ENVIRONMENT:-dev}"
FINOPSGUARD_MONTHLY_BUDGET="${FINOPSGUARD_MONTHLY_BUDGET:-100}"
FINOPSGUARD_FAIL_ON_POLICY_VIOLATION="${FINOPSGUARD_FAIL_ON_POLICY_VIOLATION:-true}"
FINOPSGUARD_COMMENT_ON_PR="${FINOPSGUARD_COMMENT_ON_PR:-true}"
FINOPSGUARD_OUTPUT_FORMAT="${FINOPSGUARD_OUTPUT_FORMAT:-text}"

# Script options
VERBOSE=false
SKIP_COMMENT=false
SKIP_POLICY_CHECK=false
OUTPUT_FILE=""
WORK_DIR="."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[VERBOSE]${NC} $1"
    fi
}

# Help function
show_help() {
    cat << EOF
FinOpsGuard CI/CD Integration Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -w, --work-dir DIR      Working directory (default: .)
    -o, --output FILE       Output file for results
    -f, --format FORMAT     Output format: text, json, junit (default: text)
    --skip-comment          Skip posting comments to PR/MR
    --skip-policy-check     Skip policy evaluation
    --no-fail               Don't exit with error on policy violations

ENVIRONMENT VARIABLES:
    FINOPSGUARD_URL                    FinOpsGuard API URL
    FINOPSGUARD_TOKEN                  API authentication token
    FINOPSGUARD_ENVIRONMENT            Environment name
    FINOPSGUARD_MONTHLY_BUDGET         Monthly budget limit
    FINOPSGUARD_FAIL_ON_POLICY_VIOLATION Whether to fail on policy violations
    FINOPSGUARD_COMMENT_ON_PR          Whether to comment on PR/MR

EXAMPLES:
    # Basic usage
    $0

    # With custom settings
    $0 --work-dir /path/to/iac --format json --verbose

    # Skip commenting on PR
    $0 --skip-comment

    # Don't fail on policy violations
    $0 --no-fail

EXIT CODES:
    0   Success - no policy violations
    1   Policy violation detected (if fail_on_policy_violation=true)
    2   Infrastructure files not found
    3   FinOpsGuard API error
    4   Invalid configuration
    5   CI platform detection error

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -w|--work-dir)
                WORK_DIR="$2"
                shift 2
                ;;
            -o|--output)
                OUTPUT_FILE="$2"
                shift 2
                ;;
            -f|--format)
                FINOPSGUARD_OUTPUT_FORMAT="$2"
                shift 2
                ;;
            --skip-comment)
                SKIP_COMMENT=true
                shift
                ;;
            --skip-policy-check)
                SKIP_POLICY_CHECK=true
                shift
                ;;
            --no-fail)
                FINOPSGUARD_FAIL_ON_POLICY_VIOLATION=false
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 4
                ;;
        esac
    done
}

# Detect CI platform
detect_ci_platform() {
    local platform="unknown"
    
    if [ -n "${GITHUB_ACTIONS:-}" ]; then
        platform="github_actions"
        log_verbose "Detected GitHub Actions"
    elif [ -n "${GITLAB_CI:-}" ]; then
        platform="gitlab_ci"
        log_verbose "Detected GitLab CI"
    elif [ -n "${JENKINS_URL:-}" ]; then
        platform="jenkins"
        log_verbose "Detected Jenkins"
    elif [ -n "${CI:-}" ]; then
        platform="generic_ci"
        log_verbose "Detected generic CI environment"
    else
        platform="local"
        log_verbose "Running in local environment"
    fi
    
    echo "$platform"
}

# Find infrastructure files
find_infrastructure_files() {
    local work_dir="$1"
    local iac_type=""
    local iac_files=""
    
    log_verbose "Scanning directory: $work_dir"
    
    # Find Terraform files
    local tf_files
    tf_files=$(find "$work_dir" -name "*.tf" -o -name "*.tfvars" -o -name "*.hcl" 2>/dev/null | grep -v ".terraform" | head -10)
    
    if [ -n "$tf_files" ]; then
        iac_type="terraform"
        iac_files="$tf_files"
        log_verbose "Found Terraform files: $tf_files"
    else
        # Find Kubernetes files
        local k8s_files
        k8s_files=$(find "$work_dir" -name "*.yaml" -o -name "*.yml" 2>/dev/null | grep -E "(kubernetes|k8s|deployment|service|configmap|secret)" | head -10)
        
        if [ -n "$k8s_files" ]; then
            iac_type="kubernetes"
            iac_files="$k8s_files"
            log_verbose "Found Kubernetes files: $k8s_files"
        fi
    fi
    
    if [ -z "$iac_type" ]; then
        log_warning "No infrastructure files found in $work_dir"
        return 1
    fi
    
    echo "$iac_type|$iac_files"
}

# Prepare infrastructure content
prepare_iac_content() {
    local iac_type="$1"
    local iac_files="$2"
    local content=""
    
    log_verbose "Preparing infrastructure content for type: $iac_type"
    
    for file in $iac_files; do
        if [ -f "$file" ]; then
            log_verbose "Processing file: $file"
            content="$content$(echo -e "\n# File: $file\n$(cat "$file")\n")"
        fi
    done
    
    # Encode as base64
    echo "$content" | base64 -w 0
}

# Call FinOpsGuard API
call_finopsguard_api() {
    local endpoint="$1"
    local payload="$2"
    local response_file="$3"
    
    local headers="Content-Type: application/json"
    if [ -n "$FINOPSGUARD_TOKEN" ]; then
        headers="$headers"$'\n'"Authorization: Bearer $FINOPSGUARD_TOKEN"
    fi
    
    log_verbose "Calling FinOpsGuard API: $FINOPSGUARD_URL$endpoint"
    
    local http_code
    http_code=$(curl -s -w "%{http_code}" \
        -X POST "$FINOPSGUARD_URL$endpoint" \
        -H "$headers" \
        -d "$payload" \
        -o "$response_file")
    
    log_verbose "HTTP response code: $http_code"
    
    if [ "$http_code" != "200" ]; then
        log_error "FinOpsGuard API call failed with HTTP $http_code"
        if [ -f "$response_file" ]; then
            log_error "Response: $(cat "$response_file")"
        fi
        return 1
    fi
    
    return 0
}

# Parse API response
parse_api_response() {
    local response_file="$1"
    local monthly_cost
    local weekly_cost
    local risk_flags
    local policy_status
    local policy_message
    
    if [ ! -f "$response_file" ]; then
        log_error "Response file not found: $response_file"
        return 1
    fi
    
    # Extract key metrics using Python
    monthly_cost=$(python3 -c "
import sys, json
try:
    with open('$response_file', 'r') as f:
        data = json.load(f)
    print(data.get('estimated_monthly_cost', 0))
except:
    print(0)
" 2>/dev/null || echo "0")
    
    weekly_cost=$(python3 -c "
import sys, json
try:
    with open('$response_file', 'r') as f:
        data = json.load(f)
    print(data.get('estimated_first_week_cost', 0))
except:
    print(0)
" 2>/dev/null || echo "0")
    
    risk_flags=$(python3 -c "
import sys, json
try:
    with open('$response_file', 'r') as f:
        data = json.load(f)
    flags = data.get('risk_flags', [])
    print(','.join(flags) if flags else '')
except:
    print('')
" 2>/dev/null || echo "")
    
    policy_status=$(python3 -c "
import sys, json
try:
    with open('$response_file', 'r') as f:
        data = json.load(f)
    policy = data.get('policy_eval', {})
    print(policy.get('status', 'unknown'))
except:
    print('unknown')
" 2>/dev/null || echo "unknown")
    
    policy_message=$(python3 -c "
import sys, json
try:
    with open('$response_file', 'r') as f:
        data = json.load(f)
    policy = data.get('policy_eval', {})
    print(policy.get('message', ''))
except:
    print('')
" 2>/dev/null || echo "")
    
    echo "$monthly_cost|$weekly_cost|$risk_flags|$policy_status|$policy_message"
}

# Format output
format_output() {
    local format="$1"
    local response_file="$2"
    local monthly_cost="$3"
    local weekly_cost="$4"
    local risk_flags="$5"
    local policy_status="$6"
    local policy_message="$7"
    
    case "$format" in
        json)
            if [ -f "$response_file" ]; then
                cat "$response_file"
            else
                echo '{"error": "No response data"}'
            fi
            ;;
        junit)
            generate_junit_xml "$response_file" "$policy_status" "$policy_message"
            ;;
        text|*)
            generate_text_output "$monthly_cost" "$weekly_cost" "$risk_flags" "$policy_status" "$policy_message"
            ;;
    esac
}

# Generate text output
generate_text_output() {
    local monthly_cost="$1"
    local weekly_cost="$2"
    local risk_flags="$3"
    local policy_status="$4"
    local policy_message="$5"
    
    echo "💰 FinOpsGuard Cost Analysis"
    echo "=============================="
    echo "📊 Cost Summary:"
    echo "  Monthly Cost: \$${monthly_cost}"
    echo "  Weekly Cost: \$${weekly_cost}"
    echo "  Environment: $FINOPSGUARD_ENVIRONMENT"
    echo "  Monthly Budget: \$${FINOPSGUARD_MONTHLY_BUDGET}"
    echo ""
    
    if [ -n "$risk_flags" ]; then
        echo "⚠️  Risk Flags:"
        IFS=',' read -ra FLAGS <<< "$risk_flags"
        for flag in "${FLAGS[@]}"; do
            echo "  - $flag"
        done
        echo ""
    fi
    
    echo "🛡️  Policy Evaluation:"
    if [ "$policy_status" = "pass" ]; then
        echo "  ✅ Status: PASS"
    else
        echo "  ❌ Status: FAIL"
    fi
    
    if [ -n "$policy_message" ]; then
        echo "  Message: $policy_message"
    fi
    echo ""
}

# Generate JUnit XML
generate_junit_xml() {
    local response_file="$1"
    local policy_status="$2"
    local policy_message="$3"
    
    local test_name="FinOpsGuard Cost Check"
    local test_status="passed"
    local test_message=""
    
    if [ "$policy_status" = "fail" ]; then
        test_status="failed"
        test_message="$policy_message"
    fi
    
    cat << EOF
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="FinOpsGuard" tests="1" failures="0" errors="0" time="0.0">
  <testcase name="$test_name" classname="FinOpsGuard.CostCheck" time="0.0">
EOF
    
    if [ "$test_status" = "failed" ]; then
        cat << EOF
    <failure message="$test_message" type="PolicyViolation">
      Policy evaluation failed: $test_message
    </failure>
EOF
    fi
    
    cat << EOF
  </testcase>
</testsuite>
EOF
}

# Post comment to PR/MR
post_comment() {
    local platform="$1"
    local response_file="$2"
    local pr_number="${3:-}"
    local mr_iid="${4:-}"
    
    if [ "$SKIP_COMMENT" = true ]; then
        log_verbose "Skipping PR/MR comment (--skip-comment specified)"
        return 0
    fi
    
    if [ ! -f "$response_file" ]; then
        log_warning "No response file available for commenting"
        return 1
    fi
    
    case "$platform" in
        github_actions)
            if [ -n "$pr_number" ]; then
                post_github_comment "$response_file" "$pr_number"
            else
                log_verbose "No PR number available for GitHub Actions"
            fi
            ;;
        gitlab_ci)
            if [ -n "$mr_iid" ]; then
                post_gitlab_comment "$response_file" "$mr_iid"
            else
                log_verbose "No MR IID available for GitLab CI"
            fi
            ;;
        *)
            log_verbose "Commenting not supported for platform: $platform"
            ;;
    esac
}

# Post GitHub comment
post_github_comment() {
    local response_file="$1"
    local pr_number="$2"
    
    log_verbose "Posting comment to GitHub PR #$pr_number"
    
    # This would typically be done by the GitHub Actions workflow
    # using the github-script action, but we can prepare the data here
    echo "$(cat "$response_file")" > finopsguard_response.json
    log_info "FinOpsGuard response saved to finopsguard_response.json for GitHub Actions"
}

# Post GitLab comment
post_gitlab_comment() {
    local response_file="$1"
    local mr_iid="$2"
    
    log_verbose "Posting comment to GitLab MR !$mr_iid"
    
    # This would typically be done by the GitLab CI job
    # using the GitLab API, but we can prepare the data here
    echo "$(cat "$response_file")" > finopsguard_response.json
    log_info "FinOpsGuard response saved to finopsguard_response.json for GitLab CI"
}

# Main function
main() {
    local platform
    local infra_info
    local iac_type
    local iac_files
    local iac_payload
    local response_file
    local parsed_response
    local monthly_cost
    local weekly_cost
    local risk_flags
    local policy_status
    local policy_message
    
    # Parse arguments
    parse_args "$@"
    
    # Change to work directory
    if [ "$WORK_DIR" != "." ] && [ -d "$WORK_DIR" ]; then
        cd "$WORK_DIR"
        log_verbose "Changed to work directory: $WORK_DIR"
    fi
    
    # Detect CI platform
    platform=$(detect_ci_platform)
    log_info "Running on platform: $platform"
    
    # Find infrastructure files
    log_info "Scanning for infrastructure files..."
    if ! infra_info=$(find_infrastructure_files "$PWD"); then
        log_warning "No infrastructure files found - skipping cost check"
        exit 2
    fi
    
    IFS='|' read -r iac_type iac_files <<< "$infra_info"
    log_info "Found $iac_type infrastructure files"
    
    # Prepare infrastructure content
    log_info "Preparing infrastructure content..."
    iac_payload=$(prepare_iac_content "$iac_type" "$iac_files")
    
    # Prepare request payload
    local request_payload
    request_payload=$(python3 -c "
import json
import sys

payload = {
    'iac_type': sys.argv[1],
    'iac_payload': sys.argv[2],
    'environment': sys.argv[3],
    'budget_rules': {
        'monthly_budget': float(sys.argv[4])
    }
}

print(json.dumps(payload))
" "$iac_type" "$iac_payload" "$FINOPSGUARD_ENVIRONMENT" "$FINOPSGUARD_MONTHLY_BUDGET")
    
    # Create temporary response file
    response_file=$(mktemp)
    trap "rm -f $response_file" EXIT
    
    # Call FinOpsGuard API
    log_info "Calling FinOpsGuard cost check API..."
    if ! call_finopsguard_api "/mcp/checkCostImpact" "$request_payload" "$response_file"; then
        log_error "Failed to call FinOpsGuard API"
        exit 3
    fi
    
    log_success "FinOpsGuard cost check completed successfully"
    
    # Parse response
    parsed_response=$(parse_api_response "$response_file")
    IFS='|' read -r monthly_cost weekly_cost risk_flags policy_status policy_message <<< "$parsed_response"
    
    log_info "Monthly cost: \$${monthly_cost}"
    log_info "Weekly cost: \$${weekly_cost}"
    log_info "Policy status: $policy_status"
    
    # Generate output
    if [ -n "$OUTPUT_FILE" ]; then
        format_output "$FINOPSGUARD_OUTPUT_FORMAT" "$response_file" "$monthly_cost" "$weekly_cost" "$risk_flags" "$policy_status" "$policy_message" > "$OUTPUT_FILE"
        log_info "Output written to: $OUTPUT_FILE"
    else
        format_output "$FINOPSGUARD_OUTPUT_FORMAT" "$response_file" "$monthly_cost" "$weekly_cost" "$risk_flags" "$policy_status" "$policy_message"
    fi
    
    # Post comment to PR/MR
    local pr_number="${GITHUB_PR_NUMBER:-}"
    local mr_iid="${CI_MERGE_REQUEST_IID:-}"
    post_comment "$platform" "$response_file" "$pr_number" "$mr_iid"
    
    # Check policy status and exit accordingly
    if [ "$policy_status" = "fail" ] && [ "$FINOPSGUARD_FAIL_ON_POLICY_VIOLATION" = "true" ]; then
        log_error "Policy evaluation failed - exiting with error"
        exit 1
    fi
    
    log_success "FinOpsGuard CI/CD integration completed successfully"
    exit 0
}

# Run main function
main "$@"
