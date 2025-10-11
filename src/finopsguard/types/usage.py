"""Usage data types and models for FinOpsGuard."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class UsageMetric(BaseModel):
    """Single usage metric datapoint."""
    
    timestamp: datetime
    value: float
    unit: str
    metric_name: str
    dimensions: Dict[str, str] = Field(default_factory=dict)


class ResourceUsage(BaseModel):
    """Usage data for a specific resource."""
    
    resource_id: str
    resource_type: str  # e.g., "ec2", "rds", "gcs_bucket"
    region: str
    cloud_provider: str  # aws, gcp, azure
    
    # Time range
    start_time: datetime
    end_time: datetime
    
    # Metrics collected
    metrics: List[UsageMetric] = Field(default_factory=list)
    
    # Summary statistics
    avg_cpu_utilization: Optional[float] = None
    avg_memory_utilization: Optional[float] = None
    avg_network_in_gb: Optional[float] = None
    avg_network_out_gb: Optional[float] = None
    avg_disk_read_gb: Optional[float] = None
    avg_disk_write_gb: Optional[float] = None
    
    # Additional metadata
    tags: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CostUsageRecord(BaseModel):
    """Historical cost and usage record from billing APIs."""
    
    # Time period
    date: datetime
    start_time: datetime
    end_time: datetime
    
    # Cost information
    cost: float
    currency: str = "USD"
    
    # Usage information
    usage_amount: float
    usage_unit: str
    
    # Resource identification
    service: str  # e.g., "AmazonEC2", "CloudSQL"
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    region: Optional[str] = None
    
    # Grouping dimensions
    dimensions: Dict[str, str] = Field(default_factory=dict)
    
    # Tags and metadata
    tags: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UsageSummary(BaseModel):
    """Summary of usage data over a time period."""
    
    cloud_provider: str
    resource_type: str
    region: Optional[str] = None
    
    # Time range
    start_time: datetime
    end_time: datetime
    
    # Total counts
    total_resources: int = 0
    
    # Cost summary
    total_cost: float = 0.0
    average_cost_per_resource: float = 0.0
    
    # Usage summary
    total_usage: float = 0.0
    average_usage: float = 0.0
    usage_unit: str = "hours"
    
    # Resource utilization averages
    avg_cpu_utilization: Optional[float] = None
    avg_memory_utilization: Optional[float] = None
    
    # Detailed records
    records: List[CostUsageRecord] = Field(default_factory=list)
    resources: List[ResourceUsage] = Field(default_factory=list)
    
    # Confidence and data quality
    confidence: str = "high"  # high, medium, low
    data_completeness: float = 1.0  # 0.0 to 1.0


class UsageQuery(BaseModel):
    """Query parameters for fetching usage data."""
    
    cloud_provider: str  # aws, gcp, azure
    
    # Time range (required)
    start_time: datetime
    end_time: datetime
    
    # Resource filtering
    resource_ids: Optional[List[str]] = None
    resource_types: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    
    # Metric filtering
    metric_names: Optional[List[str]] = None
    
    # Tag filtering
    tags: Optional[Dict[str, str]] = None
    
    # Aggregation
    granularity: str = "DAILY"  # HOURLY, DAILY, MONTHLY
    group_by: Optional[List[str]] = None  # e.g., ["service", "region"]
    
    # Limits
    max_results: int = 1000

