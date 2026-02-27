"""
Weekend analysis endpoints
"""
from fastapi import APIRouter
import pandas as pd
from data_utils import load_transaction_data

router = APIRouter()


@router.get("/api/metrics/weekend_analysis")
async def weekend_analysis():
    """
    Analyze weekend vs weekday transaction patterns.
    
    Returns:
    --------
    dict with:
    - summary: Weekend/weekday comparison metrics
    - weekend_data: Weekend-specific metrics
    - weekday_data: Weekday-specific metrics
    - comparative_insights: Key differences and patterns
    """
    df = load_transaction_data()
    
    # Separate weekend and weekday data
    weekend_df = df[df['is_weekend'] == True]
    weekday_df = df[df['is_weekend'] == False]
    
    def calculate_stats(data):
        """Calculate stats for a dataset"""
        total = len(data)
        failures = len(data[data['transaction_status'] == 'Failure'])
        success = total - failures
        failure_rate = (failures / total * 100) if total > 0 else 0
        
        # Calculate average latency
        avg_latency = data['latency_ms'].mean() if 'latency_ms' in data.columns else 0
        
        # Top error type
        failed_data = data[data['transaction_status'] == 'Failure']
        if len(failed_data) > 0 and 'error_type' in failed_data.columns:
            top_error = failed_data['error_type'].value_counts().idxmax()
        else:
            top_error = 'N/A'
        
        return {
            'total_transactions': int(total),
            'total_failures': int(failures),
            'total_success': int(success),
            'failure_rate': round(failure_rate, 2),
            'success_rate': round(100 - failure_rate, 2),
            'avg_latency_ms': round(avg_latency, 1),
            'top_error_type': top_error
        }
    
    weekend_stats = calculate_stats(weekend_df)
    weekday_stats = calculate_stats(weekday_df)
    
    # Calculate comparison metrics
    failure_rate_diff = weekend_stats['failure_rate'] - weekday_stats['failure_rate']
    latency_diff = weekend_stats['avg_latency_ms'] - weekday_stats['avg_latency_ms']
    
    # Error distribution comparison
    def get_error_distribution(data):
        """Get error distribution for a dataset"""
        error_map = {
            'timeout': 'NET_TIMEOUT',
            'payment_error': 'PAY_FAILED',
            'auth_failed': 'AUTH_ERR',
            'server_error': 'SERVER_ERR',
            'db_error': 'DB_CONN'
        }
        
        failed_data = data[data['transaction_status'] == 'Failure']
        total_failures = len(failed_data)
        
        if total_failures == 0:
            return []
        
        distribution = []
        for error_type, value_counts in failed_data['error_type'].value_counts().items():
            percentage = (value_counts / total_failures) * 100
            distribution.append({
                'error_code': error_map.get(error_type, 'UNKNOWN'),
                'error_type': error_type,
                'count': int(value_counts),
                'percentage': round(percentage, 2)
            })
        
        return sorted(distribution, key=lambda x: x['count'], reverse=True)
    
    weekend_errors = get_error_distribution(weekend_df)
    weekday_errors = get_error_distribution(weekday_df)
    
    # Generate insights
    insights = []
    
    # Failure rate insight
    if failure_rate_diff > 0:
        insights.append(
            f"📈 Weekends have {abs(failure_rate_diff):.2f}% HIGHER failure rate than weekdays "
            f"({weekend_stats['failure_rate']:.2f}% vs {weekday_stats['failure_rate']:.2f}%)"
        )
    elif failure_rate_diff < 0:
        insights.append(
            f"📉 Weekends have {abs(failure_rate_diff):.2f}% LOWER failure rate than weekdays "
            f"({weekend_stats['failure_rate']:.2f}% vs {weekday_stats['failure_rate']:.2f}%)"
        )
    else:
        insights.append(
            f"➖ Weekend and weekday failure rates are similar "
            f"({weekend_stats['failure_rate']:.2f}%)"
        )
    
    # Latency insight
    if latency_diff > 0:
        insights.append(
            f"⏱️ Weekends are SLOWER by {latency_diff:.0f}ms "
            f"({weekend_stats['avg_latency_ms']:.0f}ms vs {weekday_stats['avg_latency_ms']:.0f}ms)"
        )
    elif latency_diff < 0:
        insights.append(
            f"⚡ Weekends are FASTER by {abs(latency_diff):.0f}ms "
            f"({weekend_stats['avg_latency_ms']:.0f}ms vs {weekday_stats['avg_latency_ms']:.0f}ms)"
        )
    
    # Traffic insight
    total_trans = weekend_stats['total_transactions'] + weekday_stats['total_transactions']
    weekend_pct = (weekend_stats['total_transactions'] / total_trans) * 100
    insights.append(
        f"📊 Weekends account for {weekend_pct:.1f}% of traffic "
        f"({weekend_stats['total_transactions']:,} of {total_trans:,} transactions)"
    )
    
    # Most common error comparison
    if weekend_errors and weekday_errors:
        weekend_top = weekend_errors[0]
        weekday_top = weekday_errors[0]
        
        if weekend_top['error_code'] != weekday_top['error_code']:
            insights.append(
                f"🔴 Different top errors: Weekends {weekend_top['error_code']} vs Weekdays {weekday_top['error_code']}"
            )
        else:
            insights.append(
                f"🔴 Both periods dominated by {weekend_top['error_code']} "
                f"({weekend_top['percentage']:.1f}% vs {weekday_top['percentage']:.1f}%)"
            )
    
    return {
        'summary': {
            'comparison_metric': f"Weekend vs Weekday Analysis",
            'failure_rate_difference': round(failure_rate_diff, 2),
            'latency_difference_ms': round(latency_diff, 1),
            'weekend_is_worse': failure_rate_diff > 0
        },
        'weekend_data': weekend_stats,
        'weekday_data': weekday_stats,
        'weekend_error_distribution': weekend_errors,
        'weekday_error_distribution': weekday_errors,
        'comparative_insights': insights
    }
