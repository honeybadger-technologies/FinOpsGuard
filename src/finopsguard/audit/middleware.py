"""Audit logging middleware for FastAPI."""

import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..types.audit import AuditEventType, AuditSeverity
from .logger import get_audit_logger

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic audit logging of API requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log audit event.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Extract request details
        method = request.method
        path = request.url.path
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Extract user info (if available from auth)
        user_id = getattr(request.state, "user_id", None)
        username = getattr(request.state, "username", None)
        user_role = getattr(request.state, "user_role", None)
        
        # Process request
        response = None
        success = True
        error_message = None
        
        try:
            response = await call_next(request)
            success = response.status_code < 400
            
        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(f"Request error: {e}")
            raise
            
        finally:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log audit event (skip health checks and metrics)
            if not self._should_skip_logging(path):
                audit_logger = get_audit_logger()
                
                audit_logger.log_event(
                    event_type=AuditEventType.API_REQUEST,
                    action=f"{method} {path}",
                    user_id=user_id,
                    username=username,
                    user_role=user_role,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_id=request_id,
                    success=success,
                    error_message=error_message,
                    http_method=method,
                    http_path=path,
                    http_status=response.status_code if response else 500,
                    severity=self._get_severity(response.status_code if response else 500),
                    compliance_tags=["api_access"],
                    metadata={
                        "duration_ms": duration_ms,
                        "query_params": dict(request.query_params) if request.query_params else {}
                    }
                )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check X-Forwarded-For header (proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to client host
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _should_skip_logging(self, path: str) -> bool:
        """Determine if path should be skipped for audit logging."""
        skip_paths = [
            "/healthz",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/static/"
        ]
        
        for skip_path in skip_paths:
            if path.startswith(skip_path):
                return True
        
        return False
    
    def _get_severity(self, status_code: int) -> AuditSeverity:
        """Determine severity from HTTP status code."""
        if status_code >= 500:
            return AuditSeverity.ERROR
        elif status_code >= 400:
            return AuditSeverity.WARNING
        else:
            return AuditSeverity.INFO

