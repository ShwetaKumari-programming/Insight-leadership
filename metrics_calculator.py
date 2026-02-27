"""
Metrics Calculator - Calculate specific business and performance metrics
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime, timedelta


class MetricsCalculator:
    """Calculate specific metrics from transaction data"""
    
    @staticmethod
    def calculate_error_rate(df: pd.DataFrame, time_bucket: str = 'D') -> pd.DataFrame:
        """
        Calculate error rate over time
        
        Returns:
            DataFrame with error rates over time
        """
        if 'success' not in df.columns:
            return None
        
        result = df.set_index('timestamp').resample(time_bucket).agg({
            'success': lambda x: (1 - x.mean()) * 100
        })
        result.columns = ['error_rate_percent']
        return result.reset_index()
    
    @staticmethod
    def calculate_latency_percentiles(df: pd.DataFrame, time_bucket: str = 'D') -> pd.DataFrame:
        """
        Calculate latency percentiles over time
        """
        if 'latency_ms' not in df.columns:
            return None
        
        def calc_percentiles(series):
            return pd.Series({
                'p50': series.quantile(0.50),
                'p95': series.quantile(0.95),
                'p99': series.quantile(0.99),
                'mean': series.mean()
            })
        
        result = df.set_index('timestamp').resample(time_bucket)['latency_ms'].apply(calc_percentiles)
        return result.reset_index()
    
    @staticmethod
    def calculate_throughput(df: pd.DataFrame, time_bucket: str = 'H') -> pd.DataFrame:
        """
        Calculate throughput (transactions per unit time)
        """
        result = df.set_index('timestamp').resample(time_bucket).size()
        result = result / pd.Timedelta(time_bucket).total_seconds()  # Convert to per-second
        return result.reset_index(name='throughput_tps')
    
    @staticmethod
    def calculate_availability(df: pd.DataFrame, time_bucket: str = 'D') -> pd.DataFrame:
        """
        Calculate availability (percentage of successful operations)
        """
        if 'success' not in df.columns:
            return None
        
        result = df.set_index('timestamp').resample(time_bucket).agg({
            'success': lambda x: x.mean() * 100
        })
        result.columns = ['availability_percent']
        return result.reset_index()
    
    @staticmethod
    def calculate_apdex(df: pd.DataFrame, satisfactory_threshold: float = 100, 
                       tolerable_threshold: float = 400, time_bucket: str = 'H') -> pd.DataFrame:
        """
        Calculate APDEX (Application Performance Index)
        
        APDEX = (Satisfied + (Tolerated/2)) / Total
        
        Args:
            df: Transaction data
            satisfactory_threshold: Response time threshold (ms) for satisfied users
            tolerable_threshold: Response time threshold (ms) for tolerable users
        """
        if 'latency_ms' not in df.columns:
            return None
        
        def calc_apdex(series):
            satisfied = (series <= satisfactory_threshold).sum()
            tolerated = ((series > satisfactory_threshold) & (series <= tolerable_threshold)).sum()
            total = len(series)
            
            if total == 0:
                return 0
            
            apdex = (satisfied + (tolerated / 2)) / total
            return apdex
        
        result = df.set_index('timestamp').resample(time_bucket)['latency_ms'].apply(calc_apdex)
        return result.reset_index(name='apdex_score')
    
    @staticmethod
    def calculate_mtbf(df: pd.DataFrame) -> float:
        """
        Calculate Mean Time Between Failures (MTBF)
        
        Returns:
            Average time (in seconds) between failures
        """
        if 'success' not in df.columns or 'timestamp' not in df.columns:
            return None
        
        failures = df[df['success'] == False].sort_values('timestamp')
        
        if len(failures) < 2:
            return float('inf')
        
        time_diffs = failures['timestamp'].diff().dt.total_seconds()
        return time_diffs.mean()
    
    @staticmethod
    def calculate_mttr(df: pd.DataFrame) -> float:
        """
        Calculate Mean Time To Recover (MTTR)
        
        Returns:
            Average duration (in seconds) of failure periods
        """
        if 'success' not in df.columns or 'timestamp' not in df.columns:
            return None
        
        df = df.sort_values('timestamp')
        df['state_change'] = df['success'].astype(int).diff().fillna(0)
        
        failure_starts = df[df['state_change'] == -1].index
        failure_ends = df[df['state_change'] == 1].index
        
        if len(failure_starts) == 0:
            return 0
        
        durations = []
        for start_idx in failure_starts:
            recovery_points = failure_ends[failure_ends > start_idx]
            if len(recovery_points) > 0:
                end_idx = recovery_points[0]
                duration = (df.loc[end_idx, 'timestamp'] - df.loc[start_idx, 'timestamp']).total_seconds()
                durations.append(duration)
        
        return np.mean(durations) if durations else 0
    
    @staticmethod
    def calculate_growth_rate(df: pd.DataFrame, metric: str, time_bucket: str = 'D') -> pd.DataFrame:
        """
        Calculate growth rate of a metric
        """
        daily = df.set_index('timestamp').resample(time_bucket)[metric].sum()
        growth = daily.pct_change() * 100
        
        result = pd.DataFrame({
            'timestamp': daily.index,
            metric: daily.values,
            'growth_rate_percent': growth.values
        })
        
        return result
    
    @staticmethod
    def calculate_user_engagement(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate user engagement metrics
        """
        if 'user_id' not in df.columns:
            return {}
        
        unique_users = df['user_id'].nunique()
        avg_actions_per_user = len(df) / unique_users
        
        user_activity = df.groupby('user_id').size()
        
        return {
            'total_unique_users': unique_users,
            'total_actions': len(df),
            'avg_actions_per_user': avg_actions_per_user,
            'active_users_today': df[df['timestamp'] >= datetime.now() - timedelta(days=1)]['user_id'].nunique(),
            'most_active_user': df['user_id'].value_counts().idxmax() if len(df) > 0 else None,
            'most_active_user_actions': df['user_id'].value_counts().max() if len(df) > 0 else 0
        }
    
    @staticmethod
    def calculate_revenue_metrics(df: pd.DataFrame, revenue_column: str = 'revenue') -> Dict[str, float]:
        """
        Calculate revenue metrics
        """
        if revenue_column not in df.columns:
            return {}
        
        return {
            'total_revenue': df[revenue_column].sum(),
            'avg_revenue': df[revenue_column].mean(),
            'median_revenue': df[revenue_column].median(),
            'max_revenue': df[revenue_column].max(),
            'min_revenue': df[revenue_column].min()
        }
    
    @staticmethod
    def calculate_all_metrics(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate all key metrics in one call
        
        Args:
            df: Transaction DataFrame
            
        Returns:
            Dictionary with all calculated metrics
        """
        if df is None or len(df) == 0:
            return {}
        
        metrics = {}
        
        # Failure/Success metrics
        if 'success' in df.columns:
            successful = df['success'].sum()
            total = len(df)
            metrics['failure_rate'] = ((total - successful) / total * 100) if total > 0 else 0
            metrics['success_rate'] = (successful / total * 100) if total > 0 else 0
        
        # Error type distribution (from real UPI data)
        if 'error_type' in df.columns:
            failed = df[df['transaction_status'] == 'Failure'] if 'transaction_status' in df.columns else df[~df['success']]
            error_dist = failed['error_type'].value_counts().to_dict()
            # Remove empty string keys
            error_dist = {k: v for k, v in error_dist.items() if k}
            metrics['error_type_distribution'] = error_dist
        elif 'status_code' in df.columns:
            error_dist = df[df['status_code'].isin([500, 502, 503, 504])]['status_code'].value_counts().to_dict()
            metrics['error_type_distribution'] = error_dist
        
        # Latency metrics
        if 'latency_ms' in df.columns:
            metrics['avg_latency'] = df['latency_ms'].mean()
            metrics['p50_latency'] = df['latency_ms'].quantile(0.50)
            metrics['p95_latency'] = df['latency_ms'].quantile(0.95)
            metrics['p99_latency'] = df['latency_ms'].quantile(0.99)
            metrics['max_latency'] = df['latency_ms'].max()
            metrics['min_latency'] = df['latency_ms'].min()
        
        # MTBF and MTTR
        metrics['mtbf'] = MetricsCalculator.calculate_mtbf(df)
        metrics['mttr'] = MetricsCalculator.calculate_mttr(df)
        
        # Total transactions
        metrics['total_transactions'] = len(df)
        
        return metrics
