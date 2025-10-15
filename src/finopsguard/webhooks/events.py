"""
Webhook event service for cost anomaly detection
"""

import asyncio
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .storage import WebhookStore
from .delivery import WebhookDeliveryService
from ..database.models import Webhook
from ..types.webhook import WebhookEvent, WebhookEventType

logger = logging.getLogger(__name__)


class WebhookEventService:
    """Service for creating and sending webhook events"""
    
    def __init__(self):
        self.webhook_store = WebhookStore()
        self.delivery_service = WebhookDeliveryService()
    
    async def send_cost_anomaly_event(self, 
                                    analysis_data: Dict[str, Any],
                                    anomaly_details: Dict[str, Any],
                                    environment: str) -> None:
        """Send cost anomaly webhook event"""
        event_data = {
            'environment': environment,
            'analysis': analysis_data,
            'anomaly': anomaly_details,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        event = WebhookEvent(
            id=str(uuid.uuid4()),
            type=WebhookEventType.COST_ANOMALY,
            timestamp=datetime.now(timezone.utc),
            data=event_data
        )
        
        await self._send_event_to_webhooks(event)
    
    async def send_budget_exceeded_event(self,
                                       budget_limit: float,
                                       actual_cost: float,
                                       analysis_data: Dict[str, Any],
                                       environment: str) -> None:
        """Send budget exceeded webhook event"""
        event_data = {
            'environment': environment,
            'budget_limit': budget_limit,
            'actual_cost': actual_cost,
            'overage': actual_cost - budget_limit,
            'overage_percentage': ((actual_cost - budget_limit) / budget_limit) * 100,
            'analysis': analysis_data,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        event = WebhookEvent(
            id=str(uuid.uuid4()),
            type=WebhookEventType.BUDGET_EXCEEDED,
            timestamp=datetime.now(timezone.utc),
            data=event_data
        )
        
        await self._send_event_to_webhooks(event)
    
    async def send_policy_violation_event(self,
                                        policy_violations: List[Dict[str, Any]],
                                        analysis_data: Dict[str, Any],
                                        environment: str,
                                        violation_type: str = "blocking") -> None:
        """Send policy violation webhook event"""
        event_data = {
            'environment': environment,
            'violation_type': violation_type,
            'violations': policy_violations,
            'analysis': analysis_data,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        event = WebhookEvent(
            id=str(uuid.uuid4()),
            type=WebhookEventType.POLICY_VIOLATION,
            timestamp=datetime.now(timezone.utc),
            data=event_data
        )
        
        await self._send_event_to_webhooks(event)
    
    async def send_high_cost_resource_event(self,
                                          resource_data: Dict[str, Any],
                                          cost_threshold: float,
                                          analysis_data: Dict[str, Any],
                                          environment: str) -> None:
        """Send high cost resource webhook event"""
        event_data = {
            'environment': environment,
            'resource': resource_data,
            'cost_threshold': cost_threshold,
            'monthly_cost': resource_data.get('monthly_cost', 0),
            'analysis': analysis_data,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        event = WebhookEvent(
            id=str(uuid.uuid4()),
            type=WebhookEventType.HIGH_COST_RESOURCE,
            timestamp=datetime.now(timezone.utc),
            data=event_data
        )
        
        await self._send_event_to_webhooks(event)
    
    async def send_cost_spike_event(self,
                                  current_cost: float,
                                  previous_cost: float,
                                  spike_percentage: float,
                                  analysis_data: Dict[str, Any],
                                  environment: str) -> None:
        """Send cost spike webhook event"""
        event_data = {
            'environment': environment,
            'current_cost': current_cost,
            'previous_cost': previous_cost,
            'spike_percentage': spike_percentage,
            'cost_increase': current_cost - previous_cost,
            'analysis': analysis_data,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        event = WebhookEvent(
            id=str(uuid.uuid4()),
            type=WebhookEventType.COST_SPIKE,
            timestamp=datetime.now(timezone.utc),
            data=event_data
        )
        
        await self._send_event_to_webhooks(event)
    
    async def send_analysis_completed_event(self,
                                          analysis_data: Dict[str, Any],
                                          environment: str,
                                          duration_ms: int) -> None:
        """Send analysis completed webhook event"""
        event_data = {
            'environment': environment,
            'duration_ms': duration_ms,
            'analysis': analysis_data,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        event = WebhookEvent(
            id=str(uuid.uuid4()),
            type=WebhookEventType.ANALYSIS_COMPLETED,
            timestamp=datetime.now(timezone.utc),
            data=event_data
        )
        
        await self._send_event_to_webhooks(event)
    
    async def send_policy_created_event(self,
                                      policy_data: Dict[str, Any],
                                      created_by: str) -> None:
        """Send policy created webhook event"""
        event_data = {
            'policy': policy_data,
            'created_by': created_by,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        event = WebhookEvent(
            id=str(uuid.uuid4()),
            type=WebhookEventType.POLICY_CREATED,
            timestamp=datetime.now(timezone.utc),
            data=event_data
        )
        
        await self._send_event_to_webhooks(event)
    
    async def send_policy_updated_event(self,
                                      policy_data: Dict[str, Any],
                                      updated_by: str,
                                      changes: Dict[str, Any]) -> None:
        """Send policy updated webhook event"""
        event_data = {
            'policy': policy_data,
            'updated_by': updated_by,
            'changes': changes,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        event = WebhookEvent(
            id=str(uuid.uuid4()),
            type=WebhookEventType.POLICY_UPDATED,
            timestamp=datetime.now(timezone.utc),
            data=event_data
        )
        
        await self._send_event_to_webhooks(event)
    
    async def send_policy_deleted_event(self,
                                      policy_id: str,
                                      policy_name: str,
                                      deleted_by: str) -> None:
        """Send policy deleted webhook event"""
        event_data = {
            'policy_id': policy_id,
            'policy_name': policy_name,
            'deleted_by': deleted_by,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        event = WebhookEvent(
            id=str(uuid.uuid4()),
            type=WebhookEventType.POLICY_DELETED,
            timestamp=datetime.now(timezone.utc),
            data=event_data
        )
        
        await self._send_event_to_webhooks(event)
    
    async def _send_event_to_webhooks(self, event: WebhookEvent) -> None:
        """Send event to all subscribed webhooks"""
        try:
            # Get all webhooks subscribed to this event type
            webhooks = self.webhook_store.get_webhooks_for_event(event.type)
            
            if not webhooks:
                logger.debug(f"No webhooks subscribed to event type {event.type}")
                return
            
            logger.info(f"Sending {event.type} event to {len(webhooks)} webhooks")
            
            # Send to all webhooks concurrently
            tasks = []
            for webhook in webhooks:
                task = self.delivery_service.deliver_event(webhook, event)
                tasks.append(task)
            
            # Wait for all deliveries to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log results
            success_count = sum(1 for result in results if result is True)
            logger.info(f"Webhook delivery completed: {success_count}/{len(webhooks)} successful")
            
        except Exception as e:
            logger.error(f"Error sending webhook event {event.type}: {e}")
    
    async def detect_cost_anomalies(self, 
                                  current_analysis: Dict[str, Any],
                                  previous_analyses: List[Dict[str, Any]],
                                  environment: str) -> None:
        """Detect and send webhook events for cost anomalies"""
        try:
            current_cost = current_analysis.get('estimated_monthly_cost', 0)
            
            # Check for budget exceeded
            budget_limit = current_analysis.get('budget_limit')
            if budget_limit and current_cost > budget_limit:
                await self.send_budget_exceeded_event(
                    budget_limit=budget_limit,
                    actual_cost=current_cost,
                    analysis_data=current_analysis,
                    environment=environment
                )
            
            # Check for cost spike
            if previous_analyses:
                previous_cost = previous_analyses[0].get('estimated_monthly_cost', 0)
                if previous_cost > 0:
                    spike_percentage = ((current_cost - previous_cost) / previous_cost) * 100
                    
                    # Alert on spikes > 50%
                    if spike_percentage > 50:
                        await self.send_cost_spike_event(
                            current_cost=current_cost,
                            previous_cost=previous_cost,
                            spike_percentage=spike_percentage,
                            analysis_data=current_analysis,
                            environment=environment
                        )
            
            # Check for high-cost resources
            resource_breakdown = current_analysis.get('breakdown_by_resource', [])
            for resource in resource_breakdown:
                monthly_cost = resource.get('monthly_cost', 0)
                
                # Alert on resources > $1000/month
                if monthly_cost > 1000:
                    await self.send_high_cost_resource_event(
                        resource_data=resource,
                        cost_threshold=1000,
                        analysis_data=current_analysis,
                        environment=environment
                    )
            
            # Check for policy violations
            policy_eval = current_analysis.get('policy_eval')
            if policy_eval:
                blocking_violations = policy_eval.get('blocking_violations', [])
                advisory_violations = policy_eval.get('advisory_violations', [])
                
                if blocking_violations:
                    await self.send_policy_violation_event(
                        policy_violations=blocking_violations,
                        analysis_data=current_analysis,
                        environment=environment,
                        violation_type="blocking"
                    )
                
                if advisory_violations:
                    await self.send_policy_violation_event(
                        policy_violations=advisory_violations,
                        analysis_data=current_analysis,
                        environment=environment,
                        violation_type="advisory"
                    )
            
            # Send analysis completed event
            await self.send_analysis_completed_event(
                analysis_data=current_analysis,
                environment=environment,
                duration_ms=current_analysis.get('duration_ms', 0)
            )
            
        except Exception as e:
            logger.error(f"Error detecting cost anomalies: {e}")
