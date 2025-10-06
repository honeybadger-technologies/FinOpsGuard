"""
GitLab Merge Request Comment Integration for FinOpsGuard

This module provides functionality to post cost analysis results
as comments on GitLab merge requests.
"""

import os
import json
from typing import Dict, Any, Optional
import gitlab


class GitLabMRCommenter:
    """Handle posting comments to GitLab merge requests"""
    
    def __init__(self, token: str = None, url: str = None, project_id: str = None):
        self.token = token or os.environ.get('GITLAB_TOKEN')
        self.url = url or os.environ.get('CI_SERVER_URL', 'https://gitlab.com')
        self.project_id = project_id or os.environ.get('CI_PROJECT_ID')
        
        if not self.token:
            raise ValueError("GitLab token is required")
        if not self.project_id:
            raise ValueError("GitLab project ID is required")
        
        # Initialize GitLab client
        self.gl = gitlab.Gitlab(self.url, private_token=self.token)
        self.project = self.gl.projects.get(self.project_id)
    
    def post_cost_analysis_comment(self, 
                                 mr_iid: int,
                                 analysis_result: Dict[str, Any],
                                 environment: str = 'dev',
                                 monthly_budget: float = 100.0) -> bool:
        """Post cost analysis results as an MR comment"""
        
        comment_body = self._format_cost_analysis_comment(
            analysis_result, environment, monthly_budget
        )
        
        return self._post_comment(mr_iid, comment_body)
    
    def post_policy_evaluation_comment(self,
                                     mr_iid: int,
                                     policy_result: Dict[str, Any]) -> bool:
        """Post policy evaluation results as an MR comment"""
        
        comment_body = self._format_policy_evaluation_comment(policy_result)
        
        return self._post_comment(mr_iid, comment_body)
    
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
    
    def _post_comment(self, mr_iid: int, body: str) -> bool:
        """Post a comment to a GitLab merge request"""
        
        try:
            mr = self.project.mergerequests.get(mr_iid)
            mr.notes.create({'body': body})
            return True
        except Exception as e:
            print(f"Error posting comment to GitLab MR: {e}", file=sys.stderr)
            return False
    
    def update_existing_comment(self, comment_id: int, body: str) -> bool:
        """Update an existing comment"""
        
        try:
            note = self.project.notes.get(comment_id, noteable_type='merge_request')
            note.body = body
            note.save()
            return True
        except Exception as e:
            print(f"Error updating GitLab comment: {e}", file=sys.stderr)
            return False
    
    def find_finopsguard_comments(self, mr_iid: int) -> list:
        """Find existing FinOpsGuard comments on an MR"""
        
        try:
            mr = self.project.mergerequests.get(mr_iid)
            notes = mr.notes.list()
            
            # Filter for FinOpsGuard comments
            finopsguard_comments = []
            for note in notes:
                if "FinOpsGuard" in note.body:
                    finopsguard_comments.append({
                        'id': note.id,
                        'body': note.body,
                        'created_at': note.created_at
                    })
            
            return finopsguard_comments
        except Exception as e:
            print(f"Error fetching GitLab comments: {e}", file=sys.stderr)
            return []


def main():
    """Command-line interface for GitLab MR commenting"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Post FinOpsGuard results to GitLab MR")
    parser.add_argument('--mr-iid', type=int, required=True,
                       help='Merge request IID')
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
        commenter = GitLabMRCommenter()
        
        if args.analysis_file:
            with open(args.analysis_file, 'r') as f:
                analysis_result = json.load(f)
            
            success = commenter.post_cost_analysis_comment(
                args.mr_iid, analysis_result, args.environment, args.budget
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
                args.mr_iid, policy_result
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
