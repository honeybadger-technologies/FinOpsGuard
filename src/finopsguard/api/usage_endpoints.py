"""API endpoints for usage integration."""

import logging
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from finopsguard.adapters.usage import get_usage_factory
from finopsguard.types.usage import (
    ResourceUsage,
    CostUsageRecord,
    UsageSummary,
    UsageQuery
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/usage", tags=["usage"])


# Request/Response models
class ResourceUsageRequest(BaseModel):
    """Request to get resource usage metrics."""
    cloud_provider: str = Field(..., description="Cloud provider (aws, gcp, azure)")
    resource_id: str = Field(..., description="Resource identifier")
    resource_type: str = Field(..., description="Resource type (ec2, gce_instance, virtual_machine)")
    start_time: datetime = Field(..., description="Start of time range")
    end_time: datetime = Field(..., description="End of time range")
    region: Optional[str] = Field(None, description="Cloud region")
    metrics: Optional[List[str]] = Field(None, description="Specific metrics to fetch")


class CostUsageRequest(BaseModel):
    """Request to get cost and usage data."""
    cloud_provider: str = Field(..., description="Cloud provider (aws, gcp, azure)")
    start_time: datetime = Field(..., description="Start of time range")
    end_time: datetime = Field(..., description="End of time range")
    granularity: str = Field("DAILY", description="Time granularity (HOURLY, DAILY, MONTHLY)")
    group_by: Optional[List[str]] = Field(None, description="Dimensions to group by (service, region, etc.)")


class UsageAvailabilityResponse(BaseModel):
    """Response for usage availability check."""
    enabled: bool
    aws_available: bool
    gcp_available: bool
    azure_available: bool


# Endpoints
@router.get("/availability", response_model=UsageAvailabilityResponse)
def check_usage_availability():
    """
    Check if usage integration is available for each cloud provider.
    
    Returns availability status for AWS, GCP, and Azure usage integrations.
    """
    factory = get_usage_factory()
    
    return UsageAvailabilityResponse(
        enabled=factory.enabled,
        aws_available=factory.is_available("aws"),
        gcp_available=factory.is_available("gcp"),
        azure_available=factory.is_available("azure")
    )


@router.post("/resource", response_model=ResourceUsage)
def get_resource_usage(request: ResourceUsageRequest):
    """
    Get usage metrics for a specific cloud resource.
    
    Fetches metrics like CPU utilization, network traffic, and disk I/O
    from CloudWatch (AWS), Cloud Monitoring (GCP), or Azure Monitor.
    
    Args:
        request: Resource usage request parameters
        
    Returns:
        ResourceUsage object with metrics and summary statistics
        
    Raises:
        HTTPException: If usage integration is not available or request fails
    """
    factory = get_usage_factory()
    
    if not factory.enabled:
        raise HTTPException(
            status_code=503,
            detail="Usage integration is not enabled. Set USAGE_INTEGRATION_ENABLED=true"
        )
    
    if not factory.is_available(request.cloud_provider):
        raise HTTPException(
            status_code=503,
            detail=f"Usage integration not available for {request.cloud_provider}"
        )
    
    try:
        usage = factory.get_resource_usage(
            cloud_provider=request.cloud_provider,
            resource_id=request.resource_id,
            resource_type=request.resource_type,
            start_time=request.start_time,
            end_time=request.end_time,
            region=request.region,
            metrics=request.metrics
        )
        
        if usage is None:
            raise HTTPException(
                status_code=404,
                detail=f"No usage data found for resource {request.resource_id}"
            )
        
        return usage
        
    except Exception as e:
        logger.error(f"Error fetching resource usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cost", response_model=List[CostUsageRecord])
def get_cost_usage(request: CostUsageRequest):
    """
    Get historical cost and usage data from billing APIs.
    
    Fetches cost data from AWS Cost Explorer, GCP Cloud Billing,
    or Azure Cost Management.
    
    Args:
        request: Cost usage request parameters
        
    Returns:
        List of cost usage records
        
    Raises:
        HTTPException: If usage integration is not available or request fails
    """
    factory = get_usage_factory()
    
    if not factory.enabled:
        raise HTTPException(
            status_code=503,
            detail="Usage integration is not enabled. Set USAGE_INTEGRATION_ENABLED=true"
        )
    
    if not factory.is_available(request.cloud_provider):
        raise HTTPException(
            status_code=503,
            detail=f"Usage integration not available for {request.cloud_provider}"
        )
    
    try:
        records = factory.get_cost_usage(
            cloud_provider=request.cloud_provider,
            start_time=request.start_time,
            end_time=request.end_time,
            granularity=request.granularity,
            group_by=request.group_by
        )
        
        if records is None:
            raise HTTPException(
                status_code=404,
                detail="No cost data found for the specified time range"
            )
        
        return records
        
    except Exception as e:
        logger.error(f"Error fetching cost usage data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summary", response_model=UsageSummary)
def get_usage_summary(query: UsageQuery):
    """
    Get usage summary for a query.
    
    Combines resource metrics and cost data to provide a comprehensive
    usage summary with statistics and insights.
    
    Args:
        query: Usage query parameters
        
    Returns:
        Usage summary with aggregated statistics
        
    Raises:
        HTTPException: If usage integration is not available or request fails
    """
    factory = get_usage_factory()
    
    if not factory.enabled:
        raise HTTPException(
            status_code=503,
            detail="Usage integration is not enabled. Set USAGE_INTEGRATION_ENABLED=true"
        )
    
    if not factory.is_available(query.cloud_provider):
        raise HTTPException(
            status_code=503,
            detail=f"Usage integration not available for {query.cloud_provider}"
        )
    
    try:
        summary = factory.get_usage_summary(query)
        
        if summary is None:
            raise HTTPException(
                status_code=404,
                detail="Could not generate usage summary"
            )
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating usage summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/example/{cloud_provider}")
def get_usage_example(
    cloud_provider: str,
    days: int = Query(7, ge=1, le=90, description="Number of days to look back")
):
    """
    Get example usage data for the last N days.
    
    Convenience endpoint that fetches recent cost data for a cloud provider.
    
    Args:
        cloud_provider: Cloud provider (aws, gcp, azure)
        days: Number of days to look back (1-90)
        
    Returns:
        Cost usage records for the specified time range
    """
    factory = get_usage_factory()
    
    if not factory.enabled:
        raise HTTPException(
            status_code=503,
            detail="Usage integration is not enabled"
        )
    
    if not factory.is_available(cloud_provider):
        raise HTTPException(
            status_code=503,
            detail=f"Usage integration not available for {cloud_provider}"
        )
    
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        records = factory.get_cost_usage(
            cloud_provider=cloud_provider,
            start_time=start_time,
            end_time=end_time,
            granularity="DAILY",
            group_by=["service"]
        )
        
        if not records:
            return {
                "message": f"No usage data available for {cloud_provider} in the last {days} days",
                "records": []
            }
        
        total_cost = sum(r.cost for r in records)
        
        return {
            "cloud_provider": cloud_provider,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "days": days
            },
            "summary": {
                "total_cost": total_cost,
                "currency": "USD",
                "record_count": len(records)
            },
            "records": records[:50]  # Limit to 50 records
        }
        
    except Exception as e:
        logger.error(f"Error fetching usage example: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache")
def clear_usage_cache():
    """
    Clear the usage data cache.
    
    Forces fresh data to be fetched from cloud APIs on the next request.
    
    Returns:
        Success message
    """
    factory = get_usage_factory()
    factory.clear_cache()
    
    return {
        "message": "Usage cache cleared successfully"
    }

