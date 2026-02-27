"""
Pydantic type definitions for standardized analytics API responses.

This ensures type safety and validation across all endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime


# ============================================================================
# BASE RESPONSE TYPES
# ============================================================================

class AnalyticsResponse(BaseModel):
    """Base model for all analytics responses"""
    summary: Dict[str, Any] = Field(..., description="Key metrics summary")
    insights: List[str] = Field(..., description="Human-readable insights with emojis")

    class Config:
        json_schema_extra = {
            "example": {
                "summary": {"total_failures": 1086, "failure_rate": 10.86},
                "insights": ["📈 Insight 1", "📉 Insight 2"]
            }
        }


# ============================================================================
# FAILURE METRICS TYPES
# ============================================================================

class ErrorCodeEntry(BaseModel):
    """Single error code distribution entry"""
    error_code: str = Field(..., description="Error code (e.g., NET_TIMEOUT)")
    error_type: str = Field(..., description="Human-readable error type")
    count: int = Field(..., description="Number of occurrences")
    percentage: float = Field(..., description="Percentage of total failures")
    recommendation: str = Field(default="", description="Actionable recommendation")

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "NET_TIMEOUT",
                "error_type": "Network Timeout",
                "count": 420,
                "percentage": 38.2,
                "recommendation": "Improve retry logic and network stability"
            }
        }


class FailureSummary(BaseModel):
    """Summary for failure metrics"""
    total_failures: int
    failure_rate: float
    success_rate: float
    mtbf: str = Field(..., description="Mean Time Between Failures (e.g., '39 min')")
    total_transactions: int


class FailureMetricsResponse(BaseModel):
    """Response for /api/metrics/failures endpoint"""
    summary: FailureSummary
    error_distribution: List[ErrorCodeEntry] = Field(..., description="Error breakdown by code")
    failure_insights: List[str] = Field(..., description="Failure analysis insights")

    class Config:
        json_schema_extra = {
            "example": {
                "summary": {
                    "total_failures": 1086,
                    "failure_rate": 10.86,
                    "success_rate": 89.14,
                    "mtbf": "483 min",
                    "total_transactions": 10000
                },
                "error_distribution": [
                    {
                        "error_code": "NET_TIMEOUT",
                        "error_type": "Network Timeout",
                        "count": 420,
                        "percentage": 38.2,
                        "recommendation": "Improve retry logic"
                    }
                ],
                "failure_insights": ["⏱️ Failed transactions are 3.0x slower..."]
            }
        }


# ============================================================================
# WEEKEND ANALYSIS TYPES
# ============================================================================

class DayMetrics(BaseModel):
    """Metrics for a day period (weekend or weekday)"""
    total_transactions: int
    total_failures: int
    total_success: int
    failure_rate: float
    success_rate: float
    avg_latency_ms: float
    top_error_type: str


class WeekendSummary(BaseModel):
    """Summary for weekend vs weekday comparison"""
    comparison_metric: str = "Weekend vs Weekday Analysis"
    failure_rate_difference: float
    latency_difference_ms: float
    weekend_is_worse: bool


class WeekendAnalysisResponse(BaseModel):
    """Response for /api/metrics/weekend_analysis endpoint"""
    summary: WeekendSummary
    weekend_data: DayMetrics
    weekday_data: DayMetrics
    weekend_error_distribution: List[ErrorCodeEntry]
    weekday_error_distribution: List[ErrorCodeEntry]
    comparative_insights: List[str] = Field(..., description="Comparison insights")

    class Config:
        json_schema_extra = {
            "example": {
                "summary": {
                    "comparison_metric": "Weekend vs Weekday Analysis",
                    "failure_rate_difference": 1.06,
                    "latency_difference_ms": 1.5,
                    "weekend_is_worse": True
                },
                "weekend_data": {
                    "total_transactions": 1500,
                    "total_failures": 170,
                    "total_success": 1330,
                    "failure_rate": 11.33,
                    "success_rate": 88.67,
                    "avg_latency_ms": 67.3,
                    "top_error_type": "server_error"
                },
                "weekday_data": {
                    "total_transactions": 8500,
                    "total_failures": 916,
                    "total_success": 7584,
                    "failure_rate": 10.77,
                    "success_rate": 89.23,
                    "avg_latency_ms": 65.8,
                    "top_error_type": "timeout"
                },
                "weekend_error_distribution": [],
                "weekday_error_distribution": [],
                "comparative_insights": ["📈 Weekends have 1.06% HIGHER failure rate..."]
            }
        }


# ============================================================================
# TRENDS ANALYSIS TYPES
# ============================================================================

class DailyTrend(BaseModel):
    """Daily trend data"""
    date: str
    total_transactions: int
    failures: int
    failure_rate: float
    avg_latency_ms: float


class HourlyTrend(BaseModel):
    """Hourly trend data"""
    hour: int
    total_transactions: int
    failures: int
    failure_rate: float
    avg_latency_ms: float


class TrendsSummary(BaseModel):
    """Summary for trends analysis"""
    total_transactions: int
    total_failures: int
    overall_failure_rate: float
    trend_direction: str = Field(..., description="'worsening', 'improving', or 'stable'")
    days_analyzed: int
    hours_analyzed: int


class TrendsAnalysisResponse(BaseModel):
    """Response for /api/metrics/trends endpoint"""
    summary: TrendsSummary
    daily_trends: List[DailyTrend] = Field(..., description="Daily failure rate trends")
    hourly_trends: List[HourlyTrend] = Field(..., description="Hourly failure rate trends")
    peak_hour: Dict[str, Any] = Field(..., description="Hour with highest failure rate")
    best_hour: Dict[str, Any] = Field(..., description="Hour with lowest failure rate")
    trend_insights: List[str] = Field(..., description="Trend analysis insights")

    class Config:
        json_schema_extra = {
            "example": {
                "summary": {
                    "total_transactions": 10000,
                    "total_failures": 1086,
                    "overall_failure_rate": 10.86,
                    "trend_direction": "stable",
                    "days_analyzed": 365,
                    "hours_analyzed": 24
                },
                "daily_trends": [
                    {
                        "date": "2026-01-01",
                        "total_transactions": 50,
                        "failures": 5,
                        "failure_rate": 10.0,
                        "avg_latency_ms": 65.3
                    }
                ],
                "hourly_trends": [],
                "peak_hour": {},
                "best_hour": {},
                "trend_insights": ["📈 WORSENING: Failure rate increasing..."]
            }
        }


# ============================================================================
# PERFORMANCE ANALYSIS TYPES
# ============================================================================

class LatencyDistribution(BaseModel):
    """Latency percentile distribution"""
    min_ms: float
    max_ms: float
    mean_ms: float
    median_ms: float
    p50_ms: float
    p75_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float


class StatusPerformance(BaseModel):
    """Performance metrics by transaction status"""
    status: str = Field(..., description="'Success' or 'Failure'")
    count: int
    mean_ms: float
    median_ms: float
    p95_ms: float


class DevicePerformance(BaseModel):
    """Performance metrics by device type"""
    device: str
    count: int
    mean_ms: float
    p95_ms: float
    failure_rate: float


class NetworkPerformance(BaseModel):
    """Performance metrics by network type"""
    network: str
    count: int
    mean_ms: float
    p95_ms: float
    failure_rate: float


class PerformanceSummary(BaseModel):
    """Summary for performance analysis"""
    overall_mean_latency_ms: float
    overall_p95_latency_ms: float
    overall_p99_latency_ms: float
    success_vs_failure_ratio: float
    devices_analyzed: int
    networks_analyzed: int


class PerformanceAnalysisResponse(BaseModel):
    """Response for /api/metrics/performance endpoint"""
    summary: PerformanceSummary
    latency_distribution: LatencyDistribution
    success_performance: StatusPerformance
    failure_performance: StatusPerformance
    by_device: List[DevicePerformance]
    by_network: List[NetworkPerformance]
    performance_insights: List[str] = Field(..., description="Performance analysis insights")

    class Config:
        json_schema_extra = {
            "example": {
                "summary": {
                    "overall_mean_latency_ms": 65.8,
                    "overall_p95_latency_ms": 248.0,
                    "overall_p99_latency_ms": 347.0,
                    "success_vs_failure_ratio": 5.37,
                    "devices_analyzed": 3,
                    "networks_analyzed": 4
                },
                "latency_distribution": {
                    "min_ms": 10.0,
                    "max_ms": 499.0,
                    "mean_ms": 65.8,
                    "median_ms": 45.0,
                    "p50_ms": 45.0,
                    "p75_ms": 95.0,
                    "p90_ms": 180.0,
                    "p95_ms": 248.0,
                    "p99_ms": 347.0
                },
                "success_performance": {
                    "status": "Success",
                    "count": 8914,
                    "mean_ms": 45.0,
                    "median_ms": 42.0,
                    "p95_ms": 95.0
                },
                "failure_performance": {
                    "status": "Failure",
                    "count": 1086,
                    "mean_ms": 240.0,
                    "median_ms": 235.0,
                    "p95_ms": 347.0
                },
                "by_device": [],
                "by_network": [],
                "performance_insights": ["⚡ EXCELLENT: Average latency 65.8ms..."]
            }
        }


# ============================================================================
# RESPONSE TYPE UNION
# ============================================================================

AnalyticsEndpointResponse = Union[
    FailureMetricsResponse,
    WeekendAnalysisResponse,
    TrendsAnalysisResponse,
    PerformanceAnalysisResponse
]
