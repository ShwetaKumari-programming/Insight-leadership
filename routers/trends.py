"""
Trends and forecasting endpoints
Analyzes UPI transactions (Jan-Dec 2024) for anomaly detection,
trend analysis, and forecasting.

Performance-optimized: uses vectorized pandas operations and module-level
caching so the heavy computation runs only once.
"""
from fastapi import APIRouter
import pandas as pd
import numpy as np
import time
from data_utils import load_transaction_data


router = APIRouter()

# Warm the trends cache at server startup
def _warm_trends_cache():
    try:
        df = load_transaction_data()
        result = _build_full_response(df)
        _cache["data"] = result
        _cache["ts"] = time.time()
        print("[Trends] Cache warmed at startup.")
    except Exception as e:
        print(f"[Trends] Cache warm failed: {e}")

_warm_trends_cache()

# ── Module-level cache ─────────────────────────────────────────────────
_cache = {"data": None, "ts": 0}
_CACHE_TTL = 300  # seconds – rebuild every 5 minutes


def _groupby_stats(df: pd.DataFrame, group_col: str, total: int) -> pd.DataFrame:
    """
    Vectorised groupby helper.  Returns a DataFrame with
    txn_count, total_amount, avg_amount, failures, failure_rate, pct.
    """
    agg = df.groupby(group_col, observed=True).agg(
        txn_count=('_fail', 'count'),
        total_amount=('amount', 'sum'),
        avg_amount=('amount', 'mean'),
        failures=('_fail', 'sum'),
    ).reset_index()
    agg['failure_rate'] = (agg['failures'] / agg['txn_count'] * 100).round(2)
    agg['pct'] = (agg['txn_count'] / total * 100).round(1)
    agg['total_amount'] = agg['total_amount'].round(0)
    agg['avg_amount'] = agg['avg_amount'].round(0)
    return agg


def _build_full_response(df: pd.DataFrame) -> dict:
    """
    Build the ENTIRE trends response from the raw DataFrame.
    All heavy work happens here; the result is cached.
    """
    total = len(df)

    # Pre-compute helper columns once
    df = df.copy()
    df['transaction_time'] = pd.to_datetime(df['transaction_time'])
    df['_fail'] = (df['transaction_status'] == 'Failure').astype(int)
    df['date'] = df['transaction_time'].dt.date

    # ═══════════════════════════════════════════════════════════════════
    # 1) Daily aggregation (vectorised)
    # ═══════════════════════════════════════════════════════════════════
    daily = df.groupby('date').agg(
        total_transactions=('_fail', 'count'),
        failures=('_fail', 'sum'),
        avg_latency_ms=('latency_ms', 'mean'),
    ).reset_index()
    daily['failure_rate'] = (daily['failures'] / daily['total_transactions'] * 100).round(2)
    daily['avg_latency_ms'] = daily['avg_latency_ms'].round(1)
    daily['date'] = daily['date'].astype(str)

    daily_stats = daily.to_dict('records')
    daily_rates = daily['failure_rate'].tolist()

    # ═══════════════════════════════════════════════════════════════════
    # 2) Hourly aggregation (vectorised)
    # ═══════════════════════════════════════════════════════════════════
    hourly_stats = []
    if 'hour' in df.columns:
        hourly = df.groupby('hour').agg(
            total_transactions=('_fail', 'count'),
            failures=('_fail', 'sum'),
            avg_latency_ms=('latency_ms', 'mean'),
        ).reset_index()
        hourly['failure_rate'] = (hourly['failures'] / hourly['total_transactions'] * 100).round(2)
        hourly['avg_latency_ms'] = hourly['avg_latency_ms'].round(1)
        hourly['hour'] = hourly['hour'].astype(int)
        hourly_stats = hourly.to_dict('records')

    # ═══════════════════════════════════════════════════════════════════
    # 3) Core statistics & trend detection
    # ═══════════════════════════════════════════════════════════════════
    total_transactions = total
    total_failures = int(df['_fail'].sum())
    overall_failure_rate = (total_failures / total_transactions * 100) if total_transactions > 0 else 0
    avg_daily_rate = float(np.mean(daily_rates)) if daily_rates else 0
    volatility = float(np.std(daily_rates)) if len(daily_rates) > 1 else 0

    if len(daily_rates) > 7:
        x = np.arange(len(daily_rates))
        coeffs = np.polyfit(x, daily_rates, 1)
        slope = float(coeffs[0])
        y_pred = np.polyval(coeffs, x)
        ss_res = np.sum((np.array(daily_rates) - y_pred) ** 2)
        ss_tot = np.sum((np.array(daily_rates) - np.mean(daily_rates)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        confidence = max(0.5, min(0.98, 0.6 + abs(r_squared) * 0.35))
    else:
        slope = 0
        confidence = 0.5

    if slope > 0.01:
        trend = 'increasing'
    elif slope < -0.01:
        trend = 'decreasing'
    else:
        trend = 'stable'

    if len(daily_rates) > 7:
        forecast_7d = round(float(np.mean(daily_rates[-7:])) + slope * 7, 2)
    else:
        forecast_7d = round(avg_daily_rate, 2)

    # ═══════════════════════════════════════════════════════════════════
    # 4) Anomaly detection (vectorised)
    # ═══════════════════════════════════════════════════════════════════
    mean_rate = daily['failure_rate'].mean()
    std_rate = daily['failure_rate'].std()
    threshold_2 = mean_rate + 2 * std_rate
    threshold_25 = mean_rate + 2.5 * std_rate
    threshold_3 = mean_rate + 3 * std_rate

    anom_mask = daily['failure_rate'] > threshold_2
    anom_df = daily[anom_mask].copy()
    anom_df['deviation'] = (anom_df['failure_rate'] - mean_rate).round(2)
    anom_df['expected'] = round(mean_rate, 2)
    anom_df['severity'] = np.where(
        anom_df['failure_rate'] > threshold_3, '🔴 Critical',
        np.where(anom_df['failure_rate'] > threshold_25, '🟠 High', '🟡 Medium')
    )
    anom_df = anom_df.sort_values('failure_rate', ascending=False)
    anomaly_list = []
    for _, r in anom_df.iterrows():
        anomaly_list.append({
            'date': r['date'],
            'failure_rate': round(r['failure_rate'], 2),
            'expected': r['expected'],
            'deviation': f"+{r['deviation']}",
            'severity': r['severity'],
            'total_txns': int(r['total_transactions']),
            'failed_txns': int(r['failures']),
        })

    # Volume anomalies
    mean_vol = daily['total_transactions'].mean()
    std_vol = daily['total_transactions'].std()
    high_vol = mean_vol + 2 * std_vol
    low_vol = mean_vol - 2 * std_vol
    vol_spikes = daily[daily['total_transactions'] > high_vol]
    vol_drops = daily[daily['total_transactions'] < low_vol]
    volume_anomalies = []
    for _, r in vol_spikes.iterrows():
        volume_anomalies.append({
            'date': r['date'], 'volume': int(r['total_transactions']),
            'expected': int(round(mean_vol)),
            'deviation': f"+{int(r['total_transactions'] - mean_vol)}",
            'type': '📈 Spike'
        })
    for _, r in vol_drops.iterrows():
        volume_anomalies.append({
            'date': r['date'], 'volume': int(r['total_transactions']),
            'expected': int(round(mean_vol)),
            'deviation': str(int(r['total_transactions'] - mean_vol)),
            'type': '📉 Drop'
        })

    # ═══════════════════════════════════════════════════════════════════
    # 5) Volume analysis – all vectorised
    # ═══════════════════════════════════════════════════════════════════
    volume_analysis = {}

    # Hourly volume
    if 'hour' in df.columns:
        h = _groupby_stats(df, 'hour', total)
        h = h.sort_values('hour')
        h['hour'] = h['hour'].astype(int)
        h['label'] = h['hour'].apply(lambda x: f"{x:02d}:00\u2013{x+1:02d}:00")
        volume_analysis['hourly'] = h[['hour', 'label', 'txn_count', 'total_amount',
                                        'avg_amount', 'failures', 'failure_rate']].to_dict('records')

    # Transaction type
    if 'transaction_type' in df.columns:
        t = _groupby_stats(df, 'transaction_type', total)
        t = t.sort_values('txn_count', ascending=False)
        t = t.rename(columns={'transaction_type': 'type'})
        volume_analysis['transaction_types'] = t[['type', 'txn_count', 'pct', 'total_amount',
                                                    'avg_amount', 'failures', 'failure_rate']].to_dict('records')

    # Merchant category
    if 'category' in df.columns:
        c = _groupby_stats(df, 'category', total)
        c = c.sort_values('txn_count', ascending=False)
        volume_analysis['categories'] = c[['category', 'txn_count', 'pct', 'total_amount',
                                            'avg_amount', 'failures', 'failure_rate']].to_dict('records')

    # States (top 10)
    if 'state' in df.columns:
        s = _groupby_stats(df, 'state', total)
        s = s.sort_values('txn_count', ascending=False).head(10)
        volume_analysis['states'] = s[['state', 'txn_count', 'pct', 'total_amount',
                                        'avg_amount', 'failures', 'failure_rate']].to_dict('records')

    # Banks
    if 'sender_bank' in df.columns:
        b = _groupby_stats(df, 'sender_bank', total)
        b = b.sort_values('txn_count', ascending=False)
        b = b.rename(columns={'sender_bank': 'bank'})
        volume_analysis['banks'] = b[['bank', 'txn_count', 'pct', 'total_amount',
                                       'avg_amount', 'failures', 'failure_rate']].to_dict('records')

    # Network
    if 'network_type' in df.columns:
        n = _groupby_stats(df, 'network_type', total)
        n = n.sort_values('txn_count', ascending=False)
        n = n.rename(columns={'network_type': 'network'})
        volume_analysis['networks'] = n[['network', 'txn_count', 'pct', 'total_amount',
                                          'failures', 'failure_rate']].to_dict('records')

    # Device
    if 'device_type' in df.columns:
        d = _groupby_stats(df, 'device_type', total)
        d = d.sort_values('txn_count', ascending=False)
        d = d.rename(columns={'device_type': 'device'})
        volume_analysis['devices'] = d[['device', 'txn_count', 'pct', 'total_amount',
                                         'failures', 'failure_rate']].to_dict('records')

    # Amount range distribution
    if 'amount' in df.columns:
        bins = [0, 100, 500, 1000, 2000, 5000, 10000, 50000]
        labels = ['₹0–100', '₹101–500', '₹501–1K', '₹1K–2K', '₹2K–5K', '₹5K–10K', '₹10K–50K']
        df['_amount_range'] = pd.cut(df['amount'], bins=bins, labels=labels)
        ar = df.groupby('_amount_range', observed=True).agg(
            txn_count=('_fail', 'count'),
            failures=('_fail', 'sum'),
        ).reset_index()
        ar = ar.rename(columns={'_amount_range': 'range'})
        ar['range'] = ar['range'].astype(str)
        ar['pct'] = (ar['txn_count'] / total * 100).round(1)
        ar['failure_rate'] = (ar['failures'] / ar['txn_count'] * 100).round(2)
        volume_analysis['amount_distribution'] = ar.to_dict('records')

    # Day of week
    dow_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    if 'day_of_week' in df.columns:
        dw = _groupby_stats(df, 'day_of_week', total)
        dw = dw.sort_values('day_of_week')
        dw['day'] = dw['day_of_week'].apply(lambda x: dow_names[int(x)])
        volume_analysis['day_of_week'] = dw[['day', 'txn_count', 'total_amount',
                                              'avg_amount', 'failures', 'failure_rate']].to_dict('records')

    # Weekend vs weekday
    if 'is_weekend' in df.columns:
        ww = df.groupby('is_weekend').agg(
            txn_count=('_fail', 'count'),
            total_amount=('amount', 'sum'),
            avg_amount=('amount', 'mean'),
            failures=('_fail', 'sum'),
        ).reset_index()
        ww['failure_rate'] = (ww['failures'] / ww['txn_count'] * 100).round(2)
        ww['total_amount'] = ww['total_amount'].round(0)
        ww['avg_amount'] = ww['avg_amount'].round(0)
        weekday_row = ww[ww['is_weekend'] == False].iloc[0] if len(ww[ww['is_weekend'] == False]) else None
        weekend_row = ww[ww['is_weekend'] == True].iloc[0] if len(ww[ww['is_weekend'] == True]) else None
        volume_analysis['weekend_vs_weekday'] = {
            'weekday': {
                'txn_count': int(weekday_row['txn_count']) if weekday_row is not None else 0,
                'total_amount': float(weekday_row['total_amount']) if weekday_row is not None else 0,
                'avg_amount': float(weekday_row['avg_amount']) if weekday_row is not None else 0,
                'failures': int(weekday_row['failures']) if weekday_row is not None else 0,
                'failure_rate': float(weekday_row['failure_rate']) if weekday_row is not None else 0,
            },
            'weekend': {
                'txn_count': int(weekend_row['txn_count']) if weekend_row is not None else 0,
                'total_amount': float(weekend_row['total_amount']) if weekend_row is not None else 0,
                'avg_amount': float(weekend_row['avg_amount']) if weekend_row is not None else 0,
                'failures': int(weekend_row['failures']) if weekend_row is not None else 0,
                'failure_rate': float(weekend_row['failure_rate']) if weekend_row is not None else 0,
            }
        }

    # Peak vs off-peak
    if 'is_peak_hour' in df.columns:
        pp = df.groupby('is_peak_hour').agg(
            txn_count=('_fail', 'count'),
            total_amount=('amount', 'sum'),
            failures=('_fail', 'sum'),
        ).reset_index()
        pp['failure_rate'] = (pp['failures'] / pp['txn_count'] * 100).round(2)
        pp['pct'] = (pp['txn_count'] / total * 100).round(1)
        pp['total_amount'] = pp['total_amount'].round(0)
        peak_row = pp[pp['is_peak_hour'] == True].iloc[0] if len(pp[pp['is_peak_hour'] == True]) else None
        off_row = pp[pp['is_peak_hour'] == False].iloc[0] if len(pp[pp['is_peak_hour'] == False]) else None
        volume_analysis['peak_vs_offpeak'] = {
            'peak': {
                'label': 'Peak (9AM–6PM)',
                'txn_count': int(peak_row['txn_count']) if peak_row is not None else 0,
                'pct': float(peak_row['pct']) if peak_row is not None else 0,
                'total_amount': float(peak_row['total_amount']) if peak_row is not None else 0,
                'failures': int(peak_row['failures']) if peak_row is not None else 0,
                'failure_rate': float(peak_row['failure_rate']) if peak_row is not None else 0,
            },
            'offpeak': {
                'label': 'Off-Peak',
                'txn_count': int(off_row['txn_count']) if off_row is not None else 0,
                'pct': float(off_row['pct']) if off_row is not None else 0,
                'total_amount': float(off_row['total_amount']) if off_row is not None else 0,
                'failures': int(off_row['failures']) if off_row is not None else 0,
                'failure_rate': float(off_row['failure_rate']) if off_row is not None else 0,
            }
        }

    # Volume summary
    total_amount = float(df['amount'].sum()) if 'amount' in df.columns else 0
    volume_analysis['summary'] = {
        'total_transactions': total,
        'total_amount': round(total_amount),
        'avg_daily_volume': round(total / 365, 1),
        'avg_daily_amount': round(total_amount / 365),
        'avg_txn_amount': round(total_amount / total) if total > 0 else 0,
    }

    # ═══════════════════════════════════════════════════════════════════
    # 6) Monthly breakdown (vectorised)
    # ═══════════════════════════════════════════════════════════════════
    df['_month'] = df['transaction_time'].dt.to_period('M')
    monthly = df.groupby('_month').agg(
        total_transactions=('_fail', 'count'),
        failures=('_fail', 'sum'),
        fraud_count=('fraud_flag', 'sum') if 'fraud_flag' in df.columns else ('_fail', lambda x: 0),
    ).reset_index()
    monthly['failure_rate'] = (monthly['failures'] / monthly['total_transactions'] * 100).round(2)
    monthly['_month'] = monthly['_month'].astype(str)
    monthly = monthly.rename(columns={'_month': 'month'})
    monthly_stats = monthly.to_dict('records')

    # ═══════════════════════════════════════════════════════════════════
    # 7) Peak / Best hours + Insights
    # ═══════════════════════════════════════════════════════════════════
    peak_hour = max(hourly_stats, key=lambda x: x['failure_rate']) if hourly_stats else {}
    best_hour = min(hourly_stats, key=lambda x: x['failure_rate']) if hourly_stats else {}

    insights = []
    if trend == 'increasing':
        insights.append(f"📈 WORSENING: Failure rate trending upward (slope {slope:.4f}% per day)")
    elif trend == 'decreasing':
        insights.append(f"📉 IMPROVING: Failure rate trending downward (slope {slope:.4f}% per day)")
    else:
        insights.append(f"➖ STABLE: Failure rate stable around {avg_daily_rate:.2f}%")

    if peak_hour and best_hour:
        ph = peak_hour['hour']
        bh = best_hour['hour']
        insights.append(
            f"⏰ Peak failure hour: {ph}:00–{(ph+1):02d}:00 ({peak_hour['failure_rate']:.2f}%), "
            f"Best hour: {bh}:00–{(bh+1):02d}:00 ({best_hour['failure_rate']:.2f}%)"
        )

    if volatility > 5:
        insights.append(f"⚠️ HIGH VOLATILITY: σ = {volatility:.2f}% – inconsistent system behavior")
    elif volatility > 2:
        insights.append(f"📊 MODERATE VOLATILITY: σ = {volatility:.2f}%")
    else:
        insights.append(f"✅ LOW VOLATILITY: σ = {volatility:.2f}% – consistent performance")

    insights.append(f"🔍 {len(anomaly_list)} failure-rate anomalies detected across {len(daily_stats)} days")
    insights.append(f"📊 {len(volume_anomalies)} volume anomalies detected (unusual transaction counts)")

    if len(daily_stats) >= 14:
        recent_7 = daily_rates[-7:]
        older_7 = daily_rates[-14:-7]
        recent_avg = np.mean(recent_7)
        older_avg = np.mean(older_7)
        change = recent_avg - older_avg
        if change > 0.5:
            insights.append(f"📈 Last 7 days WORSE: {recent_avg:.2f}% vs prior {older_avg:.2f}% (↑{change:.2f}%)")
        elif change < -0.5:
            insights.append(f"📉 Last 7 days BETTER: {recent_avg:.2f}% vs prior {older_avg:.2f}% (↓{abs(change):.2f}%)")
        else:
            insights.append(f"➖ Last 7 days STABLE: {recent_avg:.2f}% vs prior {older_avg:.2f}%")

    # ═══════════════════════════════════════════════════════════════════
    # 8) Final response
    # ═══════════════════════════════════════════════════════════════════
    return {
        'metrics': {
            'trend': trend,
            'confidence': round(confidence, 2),
            'forecast_7d': forecast_7d,
            'current_rate': round(overall_failure_rate, 2),
            'volatility': round(volatility, 2),
            'anomalies': len(anomaly_list),
            'anomaly_list': anomaly_list,
            'volume_anomalies': volume_anomalies,
            'volume_anomaly_count': len(volume_anomalies),
            'volume_analysis': volume_analysis,
            'total_transactions': int(total_transactions),
            'total_failures': int(total_failures),
            'days_analyzed': len(daily_stats),
            'monthly_stats': monthly_stats,
        },
        'summary': {
            'total_transactions': int(total_transactions),
            'total_failures': int(total_failures),
            'overall_failure_rate': round(overall_failure_rate, 2),
            'trend_direction': trend,
            'days_analyzed': len(daily_stats),
            'hours_analyzed': len(hourly_stats)
        },
        'daily_trends': daily_stats,
        'hourly_trends': hourly_stats,
        'peak_hour': peak_hour,
        'best_hour': best_hour,
        'trend_insights': insights
    }


@router.get("/api/metrics/trends")
async def trends_analysis():
    """
    Comprehensive trend analysis with anomaly detection on UPI
    transactions (Jan–Dec 2024).

    Uses module-level caching – the heavy computation runs once and is
    reused for subsequent requests within the TTL window.
    """
    now = time.time()
    if _cache["data"] is not None and (now - _cache["ts"]) < _CACHE_TTL:
        return _cache["data"]

    df = load_transaction_data()
    result = _build_full_response(df)

    _cache["data"] = result
    _cache["ts"] = time.time()
    return result
