"""
Background tasks for webhook processing
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta

from .delivery import WebhookDeliveryService

logger = logging.getLogger(__name__)


class WebhookTaskService:
    """Background task service for webhook processing"""
    
    def __init__(self):
        self.delivery_service = WebhookDeliveryService()
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start_retry_processor(self, interval_seconds: int = 60):
        """Start the background webhook retry processor"""
        if self._running:
            logger.warning("Webhook retry processor is already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._retry_processor_loop(interval_seconds))
        logger.info(f"Started webhook retry processor with {interval_seconds}s interval")
    
    async def stop_retry_processor(self):
        """Stop the background webhook retry processor"""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped webhook retry processor")
    
    async def _retry_processor_loop(self, interval_seconds: int):
        """Main loop for processing webhook retries"""
        while self._running:
            try:
                # Process pending deliveries
                success_count = await self.delivery_service.retry_pending_deliveries()
                
                if success_count > 0:
                    logger.info(f"Processed {success_count} webhook retries")
                
                # Clean up old deliveries (daily)
                if datetime.utcnow().hour == 2:  # Run cleanup at 2 AM
                    try:
                        cleaned_count = await self.delivery_service.cleanup_old_deliveries()
                        if cleaned_count > 0:
                            logger.info(f"Cleaned up {cleaned_count} old webhook deliveries")
                    except Exception as e:
                        logger.error(f"Error cleaning up old deliveries: {e}")
                
                # Wait for next iteration
                await asyncio.sleep(interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in webhook retry processor: {e}")
                await asyncio.sleep(interval_seconds)  # Wait before retrying
    
    async def process_immediate_retries(self):
        """Process immediate retries without waiting for the next interval"""
        try:
            success_count = await self.delivery_service.retry_pending_deliveries()
            logger.info(f"Processed {success_count} immediate webhook retries")
            return success_count
        except Exception as e:
            logger.error(f"Error processing immediate retries: {e}")
            return 0


# Global task service instance
_webhook_task_service: Optional[WebhookTaskService] = None


def get_webhook_task_service() -> WebhookTaskService:
    """Get the global webhook task service instance"""
    global _webhook_task_service
    if _webhook_task_service is None:
        _webhook_task_service = WebhookTaskService()
    return _webhook_task_service


async def start_webhook_background_tasks():
    """Start webhook background tasks"""
    task_service = get_webhook_task_service()
    await task_service.start_retry_processor()


async def stop_webhook_background_tasks():
    """Stop webhook background tasks"""
    task_service = get_webhook_task_service()
    await task_service.stop_retry_processor()
