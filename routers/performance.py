"""
Performance and latency analysis endpoints
Deep analysis of UPI transactions (Jan-Dec 2024) with caching.
"""
from fastapi import APIRouter
import pandas as pd
import numpy as np
import time as _time
from data_utils import load_transaction_data

router = APIRouter()

# ── Module-level cache (5-minute TTL) ──────────────────────────────────────
_cache: dict = {"data": None, "ts": 0}
_CACHE_TTL = 300  # seconds


def _get_cached():
    if _cache["data"] is not None and (_time.time() - _cache["ts"]) < _CACHE_TTL:
        return _cache["data"]
    return None


def _set_cache(result):
    _cache["data"] = result
    _cache["ts"] = _time.time()


# ── Vectorised helpers ─────────────────────────────────────────────────────

def _group_perf(df, col, total, key_name, with_p95=False, top_n=None):
    """Vectorised group-by performance breakdown."""
    if col not in df.columns:
        return []

    agg_dict = {
        'count': (col, 'size'),
        'avg_latency': ('latency_ms', 'mean'),
        'success_sum': ('_success', 'sum'),
        'failure_sum': ('_fail', 'sum'),
    }
    if with_p95:
        agg_dict['p95_latency'] = ('latency_ms', lambda x: x.quantile(0.95))

    grp = df.groupby(col, observed=True).agg(**agg_dict).reset_index()
    grp['pct'] = (grp['count'] / total * 100).round(2)
    grp['avg_latency'] = grp['avg_latency'].round(2)
    grp['success_rate'] = (grp['success_sum'] / grp['count'] * 100).round(2)
    if with_p95:
        grp['p95_latency'] = grp['p95_latency'].round(2)
    grp = grp.sort_values('count', ascending=False)

    if top_n:
        grp = grp.head(top_n)

    rows = []
    for _, r in grp.iterrows():
        entry = {
            key_name: str(r[col]),
            'count': int(r['count']),
            'pct': float(r['pct']),
            'avg_latency': float(r['avg_latency']),
            'success_rate': float(r['success_rate']),
            'failure_count': int(r['failure_sum']),
        }
        if with_p95:
            entry['p95_latency'] = float(r['p95_latency'])
        rows.append(entry)
    return rows


# ── Main endpoint ──────────────────────────────────────────────────────────

@router.get("/api/performance")
async def performance_analysis():
    """
    Comprehensive performance analysis of UPI transactions.
    Cached for 5 minutes. Returns format expected by performance.js.
    """
    cached = _get_cached()
    if cached:
        return cached

    df = load_transaction_data()
    if df.empty or 'latency_ms' not in df.columns:
        return {"message": "No data yet"}

    total = len(df)
    latencies = df['latency_ms'].astype(float)

    # Pre-compute boolean columns once
    df['_success'] = (df['transaction_status'] == 'Success').astype(int)
    df['_fail'] = (df['transaction_status'] == 'Failure').astype(int)

    total_success = int(df['_success'].sum())
    total_failures = int(df['_fail'].sum())
    success_rate_val = round(total_success / total * 100, 2)
    failure_rate_val = round(100 - success_rate_val, 2)

    # ── Latency statistics ─────────────────────────────────────────────
    avg_lat = round(float(latencies.mean()), 2)
    median_lat = round(float(latencies.median()), 2)
    p95_lat = round(float(latencies.quantile(0.95)), 2)
    p99_lat = round(float(latencies.quantile(0.99)), 2)
    max_lat = round(float(latencies.max()), 2)
    min_lat = round(float(latencies.min()), 2)
    std_lat = round(float(latencies.std()), 2)

    # ── Throughput ─────────────────────────────────────────────────────
    throughput = 0.0
    if 'transaction_time' in df.columns:
        ts = pd.to_datetime(df['transaction_time'])
        span = (ts.max() - ts.min()).total_seconds()
        throughput = round(total / span * 60, 2) if span > 0 else 0.0

    # ── APDEX ──────────────────────────────────────────────────────────
    satisfied = int((latencies < 200).sum())
    tolerating = int(((latencies >= 200) & (latencies <= 500)).sum())
    apdex = round((satisfied + tolerating / 2) / total, 2)

    fast_count = satisfied
    moderate_count = tolerating
    slow_count = int((latencies > 500).sum())

    # ── Analysis object ────────────────────────────────────────────────
    analysis = {}

    # Device performance (with p95)
    analysis['device_performance'] = _group_perf(
        df, 'device_type', total, 'device', with_p95=True)

    # Network performance (with p95)
    analysis['network_performance'] = _group_perf(
        df, 'network_type', total, 'network', with_p95=True)

    # Category performance
    analysis['category_performance'] = _group_perf(
        df, 'category', total, 'category')

    # Bank performance (top 10)
    analysis['bank_performance'] = _group_perf(
        df, 'sender_bank', total, 'bank', top_n=10)

    # State performance (top 10)
    analysis['state_performance'] = _group_perf(
        df, 'state', total, 'state', top_n=10)

    # Age group performance
    if 'age_group' in df.columns:
        ag = df.groupby('age_group', observed=True).agg(
            count=('age_group', 'size'),
            avg_latency=('latency_ms', 'mean'),
            success_sum=('_success', 'sum'),
        ).reset_index()
        ag['pct'] = (ag['count'] / total * 100).round(2)
        ag['avg_latency'] = ag['avg_latency'].round(2)
        ag['success_rate'] = (ag['success_sum'] / ag['count'] * 100).round(2)
        ag = ag.sort_values('count', ascending=False)
        analysis['age_group_performance'] = [
            {'age_group': str(r['age_group']), 'count': int(r['count']),
             'pct': float(r['pct']), 'avg_latency': float(r['avg_latency']),
             'success_rate': float(r['success_rate'])}
            for _, r in ag.iterrows()
        ]

    # Hourly performance
    if 'hour' in df.columns:
        hg = df.groupby('hour', observed=True).agg(
            count=('hour', 'size'),
            avg_latency=('latency_ms', 'mean'),
            success_sum=('_success', 'sum'),
            failure_sum=('_fail', 'sum'),
        ).reset_index().sort_values('hour')
        hg['success_rate'] = (hg['success_sum'] / hg['count'] * 100).round(2)
        hg['avg_latency'] = hg['avg_latency'].round(2)

        hourly_perf = [
            {'hour': int(r['hour']), 'count': int(r['count']),
             'avg_latency': float(r['avg_latency']),
             'success_rate': float(r['success_rate']),
             'failure_count': int(r['failure_sum'])}
            for _, r in hg.iterrows()
        ]
        analysis['hourly_performance'] = hourly_perf

        # Peak vs off-peak
        pk = hg[hg['hour'].between(9, 21)]
        op = hg[~hg['hour'].between(9, 21)]
        if not pk.empty and not op.empty:
            pk_total = int(pk['count'].sum())
            op_total = int(op['count'].sum())
            pk_avg = round(float((pk['avg_latency'] * pk['count']).sum() / pk_total), 2)
            op_avg = round(float((op['avg_latency'] * op['count']).sum() / op_total), 2)
            analysis['peak_vs_offpeak'] = {
                'peak_transactions': pk_total, 'peak_avg_latency': pk_avg,
                'offpeak_transactions': op_total, 'offpeak_avg_latency': op_avg,
            }

    # Weekend vs weekday
    if 'is_weekend' in df.columns:
        wk_wd = {}
        for val, label in [(True, 'weekend'), (False, 'weekday')]:
            mask = df['is_weekend'] == val
            if not mask.any():
                continue
            sub = df[mask]
            wk_wd[label] = {
                'count': int(mask.sum()),
                'avg_latency': round(float(sub['latency_ms'].mean()), 2),
                'success_rate': round(float(sub['_success'].mean() * 100), 2),
                'failure_count': int(sub['_fail'].sum()),
            }
        analysis['weekend_vs_weekday'] = wk_wd

    # Fraud analysis
    if 'fraud_flag' in df.columns:
        fraud_count = int(df['fraud_flag'].sum())
        analysis['fraud_analysis'] = {
            'total_flagged': fraud_count,
            'fraud_rate_pct': round(fraud_count / total * 100, 3),
            'clean_transactions': total - fraud_count,
        }

    # Health assessment
    if apdex >= 0.94:
        h_status, h_color = 'EXCELLENT', 'green'
        h_msg = f"System performance is excellent. APDEX score of {apdex} across {total:,} transactions indicates outstanding user experience."
    elif apdex >= 0.85:
        h_status, h_color = 'GOOD', 'green'
        h_msg = f"System performance is good. APDEX of {apdex} across {total:,} transactions shows reliable service."
    elif apdex >= 0.70:
        h_status, h_color = 'FAIR', 'orange'
        h_msg = f"System performance needs attention. APDEX of {apdex} across {total:,} transactions indicates some user friction."
    else:
        h_status, h_color = 'POOR', 'red'
        h_msg = f"System performance is degraded. APDEX of {apdex} across {total:,} transactions requires immediate action."

    analysis['health_assessment'] = {
        'status': h_status, 'color': h_color, 'message': h_msg,
        'total_transactions': total, 'total_success': total_success,
        'total_failures': total_failures, 'failure_rate': failure_rate_val,
    }

    # ── Build response ─────────────────────────────────────────────────
    result = {
        'average_latency': avg_lat,
        'p95_latency': p95_lat,
        'p99_latency': p99_lat,
        'max_latency': max_lat,
        'min_latency': min_lat,
        'median_latency': median_lat,
        'std_latency': std_lat,
        'throughput': throughput,
        'success_rate': success_rate_val,
        'failure_rate': failure_rate_val,
        'total_transactions': total,
        'total_success': total_success,
        'total_failures': total_failures,
        'apdex': apdex,
        'analysis': analysis,
        'latency_distribution': [
            {'metric': 'Fast (<200ms)', 'value': fast_count,
             'pct': round(fast_count / total * 100, 2),
             'status': 'Healthy', 'trend': 'Stable'},
            {'metric': 'Moderate (200-500ms)', 'value': moderate_count,
             'pct': round(moderate_count / total * 100, 2),
             'status': 'Warning', 'trend': 'Increasing'},
            {'metric': 'Slow (>500ms)', 'value': slow_count,
             'pct': round(slow_count / total * 100, 2),
             'status': 'Critical', 'trend': 'Degrading'},
        ],
    }

    # Clean up temp columns
    df.drop(columns=['_success', '_fail'], inplace=True, errors='ignore')

    _set_cache(result)
    return result


# Keep the old router path as an alias
@router.get("/api/metrics/performance")
async def performance_metrics_alias():
    return await performance_analysis()
