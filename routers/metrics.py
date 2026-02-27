"""
Metrics API routes for transaction analysis
"""
from fastapi import APIRouter
import pandas as pd
from data_utils import load_transaction_data


import time
router = APIRouter()

# Module-level cache for failure analysis
_failures_cache = {"data": None, "ts": 0}
_FAILURES_CACHE_TTL = 300  # seconds (5 minutes)

# Warm the cache at server startup
def _warm_failures_cache():
    try:
        _failures_cache["data"] = _compute_failure_analysis()
        _failures_cache["ts"] = time.time()
        print("[Failures] Cache warmed at startup.")
    except Exception as e:
        print(f"[Failures] Cache warm failed: {e}")

def _compute_failure_analysis():
    # ...existing code from failure_analysis() up to return {...}
    df = load_transaction_data()
    failed_df = df[df["transaction_status"] == "Failure"]
    total_failures = len(failed_df)
    total_transactions = len(df)
    failure_rate = (total_failures / total_transactions) * 100 if total_transactions > 0 else 0
    success_rate = 100 - failure_rate
    error_map = {
        "timeout": ("NET_TIMEOUT", "Network Timeout", "Improve retry logic and network stability"),
        "payment_error": ("PAY_FAILED", "Payment Gateway Failure", "Check payment gateway logs"),
        "auth_failed": ("AUTH_ERR", "Authentication Error", "Validate authentication tokens"),
        "server_error": ("SERVER_ERR", "Internal Server Error", "Inspect server logs and CPU usage"),
        "db_error": ("DB_CONN", "Database Connection Failure", "Verify DB connection pool")
    }
    error_distribution = []
    for reason, group in failed_df.groupby("error_type"):
        if reason and reason in error_map:
            code, error_type, recommendation = error_map[reason]
        else:
            code, error_type, recommendation = (
                "UNKNOWN",
                "Unknown Error",
                "Investigate application logs"
            )
        count = len(group)
        percentage = round((count / total_failures) * 100, 2) if total_failures > 0 else 0
        error_distribution.append({
            "error_code": code,
            "error_type": error_type,
            "count": int(count),
            "percentage": percentage,
            "recommendation": recommendation
        })
    error_distribution = sorted(error_distribution, key=lambda x: x['count'], reverse=True)
    insights = []
    if len(failed_df) > 0 and len(df[df["transaction_status"] == "Success"]) > 0:
        avg_failed_latency = failed_df["latency_ms"].mean()
        avg_success_latency = df[df["transaction_status"] == "Success"]["latency_ms"].mean()
        if avg_failed_latency > avg_success_latency:
            latency_ratio = round(avg_failed_latency / avg_success_latency, 1)
            insights.append(
                f"⏱️ Failed transactions have {latency_ratio}× higher latency than successful ones ({avg_failed_latency:.0f}ms vs {avg_success_latency:.0f}ms)."
            )
    if "is_peak_hour" in df.columns and len(failed_df) > 0:
        peak_failures = len(failed_df[failed_df["is_peak_hour"] == True])
        peak_total = len(df[df["is_peak_hour"] == True])
        peak_rate = (peak_failures / peak_total * 100) if peak_total > 0 else 0
        off_peak_failures = len(failed_df[failed_df["is_peak_hour"] == False])
        off_peak_total = len(df[df["is_peak_hour"] == False])
        off_peak_rate = (off_peak_failures / off_peak_total * 100) if off_peak_total > 0 else 0
        if peak_rate > off_peak_rate:
            insights.append(
                f"📈 Peak hours (9 AM - 6 PM) show {peak_rate:.1f}% failure rate vs {off_peak_rate:.1f}% off-hours."
            )
        else:
            insights.append(
                f"📉 Off-hours show {off_peak_rate:.1f}% failure rate vs {peak_rate:.1f}% during peak hours."
            )
    if "network_type" in df.columns and len(failed_df) > 0:
        network_stats = {}
        for network in df["network_type"].unique():
            network_df = df[df["network_type"] == network]
            network_failures = len(network_df[network_df["transaction_status"] == "Failure"])
            network_total = len(network_df)
            network_stats[network] = (network_failures / network_total * 100) if network_total > 0 else 0
        worst_network = max(network_stats, key=network_stats.get)
        best_network = min(network_stats, key=network_stats.get)
        insights.append(
            f"📡 {worst_network} network has {network_stats[worst_network]:.1f}% failure rate, highest among all networks ({best_network} has {network_stats[best_network]:.1f}%)."
        )
    if "is_weekend" in df.columns and len(failed_df) > 0:
        weekend_failures = len(failed_df[failed_df["is_weekend"] == True])
        weekend_total = len(df[df["is_weekend"] == True])
        weekend_rate = (weekend_failures / weekend_total * 100) if weekend_total > 0 else 0
        weekday_failures = len(failed_df[failed_df["is_weekend"] == False])
        weekday_total = len(df[df["is_weekend"] == False])
        weekday_rate = (weekday_failures / weekday_total * 100) if weekday_total > 0 else 0
        if weekend_rate > weekday_rate:
            insights.append(
                f"📅 Weekends show {weekend_rate:.1f}% failure rate vs {weekday_rate:.1f}% on weekdays."
            )
        else:
            insights.append(
                f"📅 Weekdays show {weekday_rate:.1f}% failure rate vs {weekend_rate:.1f}% on weekends."
            )
    if total_failures > 0 and "transaction_time" in df.columns:
        time_span = (df['transaction_time'].max() - df['transaction_time'].min()).total_seconds() / 60
        mtbf = int(time_span / total_failures)
        mtbf_str = f"{mtbf} min"
    else:
        mtbf_str = "N/A"
    return {
        "summary": {
            "total_failures": int(total_failures),
            "failure_rate": round(failure_rate, 2),
            "success_rate": round(success_rate, 2),
            "mtbf": mtbf_str,
            "total_transactions": int(total_transactions)
        },
        "error_distribution": error_distribution,
        "failure_insights": insights
    }

_warm_failures_cache()


@router.get("/api/metrics/failures")
async def failure_analysis():
    """
    Analyze transaction failures with detailed error distribution and insights.
    
    Returns:
    --------
    dict with:
    - summary: Total failures, failure rate, success rate
    - error_distribution: Breakdown by error code with recommendations
    - failure_insights: Key insights about failure patterns
    """
    # Serve from cache if fresh
    now = time.time()
    if _failures_cache["data"] is not None and (now - _failures_cache["ts"]) < _FAILURES_CACHE_TTL:
        return _failures_cache["data"]
    # Otherwise, recompute and update cache
    result = _compute_failure_analysis()
    _failures_cache["data"] = result
    _failures_cache["ts"] = now
    return result
