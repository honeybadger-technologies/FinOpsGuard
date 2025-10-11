"""
GitHub PR Comment Integration for FinOpsGuard

This module provides functionality to post cost analysis results
as comments on GitHub pull requests.
"""

import os
import sys
import json
from typing import Dict, Any
import requests


class GitHubPRCommenter:
    """Handle posting comments to GitHub pull requests"""
    
    def __init__(self, token: str = None, repo: str = None):
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.repo = repo or os.environ.get('GITHUB_REPOSITORY')
        
        if not self.token:
            raise ValueError("GitHub token is required")
        if not self.repo:
            raise ValueError("GitHub repository is required")
        
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def post_cost_analysis_comment(self, 
                                 pr_number: int,
                                 analysis_result: Dict[str, Any],
                                 environment: str = 'dev',
                                 monthly_budget: float = 100.0) -> bool:
        """Post cost analysis results as a PR comment"""
        
        comment_body = self._format_cost_analysis_comment(
            analysis_result, environment, monthly_budget
        )
        
        return self._post_comment(pr_number, comment_body)
    
    def post_policy_evaluation_comment(self,
                                     pr_number: int,
                                     policy_result: Dict[str, Any]) -> bool:
        """Post policy evaluation results as a PR comment"""
        
        comment_body = self._format_policy_evaluation_comment(policy_result)
        
        return self._post_comment(pr_number, comment_body)
    
    def _format_cost_analysis_comment(self,
                                    analysis_result: Dict[str, Any],
                                    environment: str,
                                    monthly_budget: float) -> str:
        """Format cost analysis results into a comment"""
        
        monthly_cost = analysis_result.get('estimated_monthly_cost', 0)
        weekly_cost = analysis_result.get('estimated_first_week_cost', 0)
        risk_flags = analysis_result.get('risk_flags', [])
        policy_eval = analysis_result.get('policy_eval', {})
        recommendations = analysis_result.get('recommendations', [])
        breakdown = analysis_result.get('breakdown_by_resource', [])
        
        comment = "## 💰 FinOpsGuard Cost Analysis\n\n"
        
        # Cost Summary
        comment += "### 📊 Cost Summary\n"
        comment += f"- **Estimated Monthly Cost**: ${monthly_cost:.2f}\n"
        comment += f"- **Estimated Weekly Cost**: ${weekly_cost:.2f}\n"
        comment += f"- **Environment**: {environment}\n"
        comment += f"- **Monthly Budget**: ${monthly_budget:.2f}\n\n"
        
        # Risk Flags
        if risk_flags:
            comment += "### ⚠️ Risk Flags\n"
            for flag in risk_flags:
                comment += f"- `{flag}`\n"
            comment += "\n"
        
        # Policy Evaluation
        if policy_eval:
            status = policy_eval.get('status', 'unknown')
            emoji = "✅" if status == 'pass' else "❌"
            comment += "### 🛡️ Policy Evaluation\n"
            comment += f"{emoji} **Status**: {status.upper()}\n"
            if policy_eval.get('message'):
                comment += f"**Message**: {policy_eval['message']}\n"
            comment += "\n"
        
        # Recommendations
        if recommendations:
            comment += "### 💡 Recommendations\n"
            for rec in recommendations:
                comment += f"- {rec}\n"
            comment += "\n"
        
        # Resource Breakdown
        if breakdown:
            comment += "### 📋 Resource Breakdown\n"
            for resource in breakdown:
                cost = resource.get('estimated_monthly_cost', 0)
                size = resource.get('size', 'N/A')
                comment += f"- **{resource['type']}** ({size}): ${cost:.2f}/month\n"
            comment += "\n"
        
        comment += "---\n"
        comment += "*Powered by [FinOpsGuard](https://github.com/your-org/finopsguard)*\n"
        
        return comment
    
    def _format_policy_evaluation_comment(self,
                                        policy_result: Dict[str, Any]) -> str:
        """Format policy evaluation results into a comment"""
        
        overall_status = policy_result.get('overall_status', 'unknown')
        blocking_violations = policy_result.get('blocking_violations', [])
        advisory_violations = policy_result.get('advisory_violations', [])
        passed_policies = policy_result.get('passed_policies', [])
        
        status_emoji = "✅" if overall_status == 'pass' else "❌"
        
        comment = "## 🛡️ FinOpsGuard Policy Evaluation\n\n"
        comment += f"### Overall Status: {status_emoji} {overall_status.upper()}\n\n"
        
        # Blocking Violations
        if blocking_violations:
            comment += "### ❌ Blocking Violations\n"
            comment += "These violations will prevent deployment:\n\n"
            for violation in blocking_violations:
                policy_name = violation.get('policy_name', 'Unknown Policy')
                reason = violation.get('reason', 'No reason provided')
                comment += f"- **{policy_name}**: {reason}\n"
            comment += "\n"
        
        # Advisory Violations
        if advisory_violations:
            comment += "### ⚠️ Advisory Violations\n"
            comment += "These violations should be reviewed but won't block deployment:\n\n"
            for violation in advisory_violations:
                policy_name = violation.get('policy_name', 'Unknown Policy')
                reason = violation.get('reason', 'No reason provided')
                comment += f"- **{policy_name}**: {reason}\n"
            comment += "\n"
        
        # Passed Policies
        if passed_policies:
            comment += "### ✅ Passed Policies\n"
            comment += f"The following {len(passed_policies)} policies passed evaluation:\n\n"
            for policy_id in passed_policies:
                comment += f"- `{policy_id}`\n"
            comment += "\n"
        
        comment += "---\n"
        comment += "*Powered by [FinOpsGuard](https://github.com/your-org/finopsguard)*\n"
        
        return comment
    
    def _post_comment(self, pr_number: int, body: str) -> bool:
        """Post a comment to a GitHub pull request"""
        
        url = f"https://api.github.com/repos/{self.repo}/issues/{pr_number}/comments"
        
        data = {
            "body": body
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error posting comment to GitHub PR: {e}", file=sys.stderr)
            return False
    
    def update_existing_comment(self, comment_id: int, body: str) -> bool:
        """Update an existing comment"""
        
        url = f"https://api.github.com/repos/{self.repo}/issues/comments/{comment_id}"
        
        data = {
            "body": body
        }
        
        try:
            response = requests.patch(url, headers=self.headers, json=data)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error updating GitHub comment: {e}", file=sys.stderr)
            return False
    
    def find_finopsguard_comments(self, pr_number: int) -> list:
        """Find existing FinOpsGuard comments on a PR"""
        
        url = f"https://api.github.com/repos/{self.repo}/issues/{pr_number}/comments"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            comments = response.json()
            
            # Filter for FinOpsGuard comments
            finopsguard_comments = []
            for comment in comments:
                if "FinOpsGuard" in comment.get('body', ''):
                    finopsguard_comments.append({
                        'id': comment['id'],
                        'body': comment['body'],
                        'created_at': comment['created_at']
                    })
            
            return finopsguard_comments
        except requests.exceptions.RequestException as e:
            print(f"Error fetching GitHub comments: {e}", file=sys.stderr)
            return []


def main():
    """Command-line interface for GitHub PR commenting"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Post FinOpsGuard results to GitHub PR")
    parser.add_argument('--pr-number', type=int, required=True,
                       help='Pull request number')
    parser.add_argument('--analysis-file', 
                       help='JSON file containing cost analysis results')
    parser.add_argument('--policy-file',
                       help='JSON file containing policy evaluation results')
    parser.add_argument('--environment', default='dev',
                       help='Environment name')
    parser.add_argument('--budget', type=float, default=100.0,
                       help='Monthly budget')
    
    args = parser.parse_args()
    
    try:
        commenter = GitHubPRCommenter()
        
        if args.analysis_file:
            with open(args.analysis_file, 'r') as f:
                analysis_result = json.load(f)
            
            success = commenter.post_cost_analysis_comment(
                args.pr_number, analysis_result, args.environment, args.budget
            )
            
            if success:
                print("✅ Cost analysis comment posted successfully")
            else:
                print("❌ Failed to post cost analysis comment")
                sys.exit(1)
        
        elif args.policy_file:
            with open(args.policy_file, 'r') as f:
                policy_result = json.load(f)
            
            success = commenter.post_policy_evaluation_comment(
                args.pr_number, policy_result
            )
            
            if success:
                print("✅ Policy evaluation comment posted successfully")
            else:
                print("❌ Failed to post policy evaluation comment")
                sys.exit(1)
        
        else:
            print("Error: Either --analysis-file or --policy-file is required")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
