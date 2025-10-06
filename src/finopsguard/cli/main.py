#!/usr/bin/env python3
"""
FinOpsGuard CLI Tool for CI/CD Integration

This CLI tool provides command-line access to FinOpsGuard functionality,
making it easy to integrate cost checking into CI/CD pipelines.
"""

import argparse
import base64
import json
import os
import sys
import glob
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests


class FinOpsGuardCLI:
    """Command-line interface for FinOpsGuard"""
    
    def __init__(self, base_url: str = None, token: str = None):
        self.base_url = base_url or os.environ.get('FINOPSGUARD_URL', 'http://localhost:8080')
        self.token = token or os.environ.get('FINOPSGUARD_TOKEN')
        self.headers = {
            'Content-Type': 'application/json'
        }
        if self.token:
            self.headers['Authorization'] = f'Bearer {self.token}'
    
    def check_cost_impact(self, 
                         iac_type: str,
                         iac_files: List[str],
                         environment: str = 'dev',
                         monthly_budget: float = 100.0,
                         fail_on_policy_violation: bool = True) -> Dict[str, Any]:
        """Check cost impact of infrastructure changes"""
        
        # Combine file contents
        iac_content = ""
        for file_path in iac_files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    iac_content += f"\n# File: {file_path}\n{f.read()}\n"
        
        # Encode as base64
        payload = base64.b64encode(iac_content.encode()).decode()
        
        # Prepare request
        request_data = {
            "iac_type": iac_type,
            "iac_payload": payload,
            "environment": environment,
            "budget_rules": {
                "monthly_budget": monthly_budget
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/mcp/checkCostImpact",
                headers=self.headers,
                json=request_data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error calling FinOpsGuard API: {e}", file=sys.stderr)
            sys.exit(1)
    
    def evaluate_policy(self, 
                       iac_type: str,
                       iac_files: List[str],
                       environment: str = 'dev') -> Dict[str, Any]:
        """Evaluate policies against infrastructure changes"""
        
        # Combine file contents
        iac_content = ""
        for file_path in iac_files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    iac_content += f"\n# File: {file_path}\n{f.read()}\n"
        
        # Encode as base64
        payload = base64.b64encode(iac_content.encode()).decode()
        
        # Prepare request
        request_data = {
            "iac_type": iac_type,
            "iac_payload": payload,
            "environment": environment
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/mcp/evaluatePolicy",
                headers=self.headers,
                json=request_data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error calling FinOpsGuard API: {e}", file=sys.stderr)
            sys.exit(1)
    
    def get_price_catalog(self, service: str = None, region: str = None) -> Dict[str, Any]:
        """Get price catalog information"""
        request_data = {}
        if service:
            request_data["service"] = service
        if region:
            request_data["region"] = region
        
        try:
            response = requests.post(
                f"{self.base_url}/mcp/getPriceCatalog",
                headers=self.headers,
                json=request_data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error calling FinOpsGuard API: {e}", file=sys.stderr)
            sys.exit(1)
    
    def list_policies(self) -> Dict[str, Any]:
        """List all policies"""
        try:
            response = requests.get(
                f"{self.base_url}/mcp/policies",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error calling FinOpsGuard API: {e}", file=sys.stderr)
            sys.exit(1)
    
    def health_check(self) -> bool:
        """Check if FinOpsGuard service is healthy"""
        try:
            response = requests.get(f"{self.base_url}/healthz", timeout=10)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException:
            return False


def find_infrastructure_files(directory: str = ".") -> tuple[str, List[str]]:
    """Find infrastructure files and determine type"""
    directory = Path(directory)
    
    # Terraform files
    tf_patterns = ["**/*.tf", "**/*.tfvars", "**/*.hcl"]
    tf_files = []
    for pattern in tf_patterns:
        tf_files.extend(glob.glob(str(directory / pattern), recursive=True))
    
    # Filter out .terraform directory
    tf_files = [f for f in tf_files if '.terraform' not in f]
    
    # Kubernetes files
    k8s_patterns = ["**/*.yaml", "**/*.yml"]
    k8s_files = []
    for pattern in k8s_patterns:
        k8s_files.extend(glob.glob(str(directory / pattern), recursive=True))
    
    # Filter for Kubernetes-specific files
    k8s_keywords = ['kubernetes', 'k8s', 'deployment', 'service', 'configmap', 'secret', 'ingress']
    k8s_files = [f for f in k8s_files 
                 if any(keyword in f.lower() for keyword in k8s_keywords)]
    
    # Determine type and files
    if tf_files:
        return "terraform", tf_files[:10]  # Limit to 10 files
    elif k8s_files:
        return "kubernetes", k8s_files[:10]  # Limit to 10 files
    else:
        return None, []


def format_cost_output(result: Dict[str, Any], output_format: str = "text") -> str:
    """Format cost analysis output"""
    if output_format == "json":
        return json.dumps(result, indent=2)
    
    # Text format
    output = []
    output.append("💰 FinOpsGuard Cost Analysis")
    output.append("=" * 50)
    
    # Cost summary
    monthly_cost = result.get('estimated_monthly_cost', 0)
    weekly_cost = result.get('estimated_first_week_cost', 0)
    output.append(f"📊 Cost Summary:")
    output.append(f"  Monthly Cost: ${monthly_cost:.2f}")
    output.append(f"  Weekly Cost: ${weekly_cost:.2f}")
    
    # Risk flags
    risk_flags = result.get('risk_flags', [])
    if risk_flags:
        output.append(f"\n⚠️  Risk Flags:")
        for flag in risk_flags:
            output.append(f"  - {flag}")
    
    # Policy evaluation
    policy_eval = result.get('policy_eval', {})
    if policy_eval:
        status = policy_eval.get('status', 'unknown')
        emoji = "✅" if status == "pass" else "❌"
        output.append(f"\n🛡️  Policy Evaluation:")
        output.append(f"  {emoji} Status: {status.upper()}")
        if policy_eval.get('message'):
            output.append(f"  Message: {policy_eval['message']}")
    
    # Recommendations
    recommendations = result.get('recommendations', [])
    if recommendations:
        output.append(f"\n💡 Recommendations:")
        for rec in recommendations:
            output.append(f"  - {rec}")
    
    # Resource breakdown
    breakdown = result.get('breakdown_by_resource', [])
    if breakdown:
        output.append(f"\n📋 Resource Breakdown:")
        for resource in breakdown:
            cost = resource.get('estimated_monthly_cost', 0)
            size = resource.get('size', 'N/A')
            output.append(f"  - {resource['type']} ({size}): ${cost:.2f}/month")
    
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="FinOpsGuard CLI - Cost-aware guardrails for IaC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check cost impact of current directory
  finopsguard check-cost
  
  # Check with specific budget and environment
  finopsguard check-cost --budget 500 --environment prod
  
  # Evaluate policies only
  finopsguard evaluate-policy
  
  # Get price catalog
  finopsguard price-catalog --service ec2 --region us-east-1
  
  # List all policies
  finopsguard list-policies
  
Environment Variables:
  FINOPSGUARD_URL     FinOpsGuard API URL (default: http://localhost:8080)
  FINOPSGUARD_TOKEN   API authentication token
        """
    )
    
    parser.add_argument('--url', default=None,
                       help='FinOpsGuard API URL')
    parser.add_argument('--token', default=None,
                       help='API authentication token')
    parser.add_argument('--output', choices=['text', 'json'], default='text',
                       help='Output format')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Check cost command
    check_parser = subparsers.add_parser('check-cost', help='Check cost impact')
    check_parser.add_argument('--directory', '-d', default='.',
                             help='Directory to scan for infrastructure files')
    check_parser.add_argument('--files', nargs='+',
                             help='Specific files to analyze')
    check_parser.add_argument('--type', choices=['terraform', 'kubernetes'],
                             help='Infrastructure type (auto-detected if not specified)')
    check_parser.add_argument('--environment', '-e', default='dev',
                             help='Environment name')
    check_parser.add_argument('--budget', type=float, default=100.0,
                             help='Monthly budget limit')
    check_parser.add_argument('--no-fail', action='store_true',
                             help='Do not exit with error on policy violation')
    
    # Evaluate policy command
    policy_parser = subparsers.add_parser('evaluate-policy', help='Evaluate policies')
    policy_parser.add_argument('--directory', '-d', default='.',
                              help='Directory to scan for infrastructure files')
    policy_parser.add_argument('--files', nargs='+',
                              help='Specific files to analyze')
    policy_parser.add_argument('--type', choices=['terraform', 'kubernetes'],
                              help='Infrastructure type (auto-detected if not specified)')
    policy_parser.add_argument('--environment', '-e', default='dev',
                              help='Environment name')
    
    # Price catalog command
    price_parser = subparsers.add_parser('price-catalog', help='Get price catalog')
    price_parser.add_argument('--service',
                             help='Service name (e.g., ec2, rds)')
    price_parser.add_argument('--region',
                             help='AWS region')
    
    # List policies command
    subparsers.add_parser('list-policies', help='List all policies')
    
    # Health check command
    subparsers.add_parser('health', help='Check service health')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize CLI
    cli = FinOpsGuardCLI(args.url, args.token)
    
    try:
        if args.command == 'check-cost':
            # Determine files to analyze
            if args.files:
                files = args.files
                iac_type = args.type or 'terraform'  # Default assumption
            else:
                iac_type, files = find_infrastructure_files(args.directory)
                if not files:
                    print("No infrastructure files found", file=sys.stderr)
                    sys.exit(1)
            
            if args.verbose:
                print(f"Analyzing {iac_type} files: {files}")
            
            # Run cost check
            result = cli.check_cost_impact(
                iac_type=iac_type,
                iac_files=files,
                environment=args.environment,
                monthly_budget=args.budget,
                fail_on_policy_violation=not args.no_fail
            )
            
            # Output results
            print(format_cost_output(result, args.output))
            
            # Check for policy violations
            policy_eval = result.get('policy_eval', {})
            if policy_eval.get('status') == 'fail' and not args.no_fail:
                print("\n❌ Policy evaluation failed - exiting with error", file=sys.stderr)
                sys.exit(1)
        
        elif args.command == 'evaluate-policy':
            # Determine files to analyze
            if args.files:
                files = args.files
                iac_type = args.type or 'terraform'  # Default assumption
            else:
                iac_type, files = find_infrastructure_files(args.directory)
                if not files:
                    print("No infrastructure files found", file=sys.stderr)
                    sys.exit(1)
            
            if args.verbose:
                print(f"Evaluating policies for {iac_type} files: {files}")
            
            # Run policy evaluation
            result = cli.evaluate_policy(
                iac_type=iac_type,
                iac_files=files,
                environment=args.environment
            )
            
            # Output results
            if args.output == 'json':
                print(json.dumps(result, indent=2))
            else:
                print("🛡️ Policy Evaluation Results")
                print("=" * 40)
                print(f"Status: {result.get('overall_status', 'unknown').upper()}")
                
                blocking_violations = result.get('blocking_violations', [])
                if blocking_violations:
                    print(f"\n❌ Blocking Violations ({len(blocking_violations)}):")
                    for violation in blocking_violations:
                        print(f"  - {violation.get('policy_name', 'Unknown')}: {violation.get('reason', 'No reason')}")
                
                advisory_violations = result.get('advisory_violations', [])
                if advisory_violations:
                    print(f"\n⚠️ Advisory Violations ({len(advisory_violations)}):")
                    for violation in advisory_violations:
                        print(f"  - {violation.get('policy_name', 'Unknown')}: {violation.get('reason', 'No reason')}")
                
                passed_policies = result.get('passed_policies', [])
                if passed_policies:
                    print(f"\n✅ Passed Policies ({len(passed_policies)}):")
                    for policy_id in passed_policies:
                        print(f"  - {policy_id}")
            
            # Exit with error if there are blocking violations
            if result.get('blocking_violations'):
                sys.exit(1)
        
        elif args.command == 'price-catalog':
            result = cli.get_price_catalog(args.service, args.region)
            print(format_cost_output(result, args.output))
        
        elif args.command == 'list-policies':
            result = cli.list_policies()
            if args.output == 'json':
                print(json.dumps(result, indent=2))
            else:
                policies = result.get('policies', [])
                print(f"📋 FinOpsGuard Policies ({len(policies)})")
                print("=" * 40)
                for policy in policies:
                    status = "✅ Enabled" if policy.get('enabled') else "❌ Disabled"
                    print(f"• {policy.get('name', 'Unnamed')} - {status}")
                    print(f"  ID: {policy.get('id')}")
                    print(f"  Description: {policy.get('description', 'No description')}")
                    print()
        
        elif args.command == 'health':
            if cli.health_check():
                print("✅ FinOpsGuard service is healthy")
            else:
                print("❌ FinOpsGuard service is not responding", file=sys.stderr)
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        if args.verbose:
            import traceback
            traceback.print_exc()
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
