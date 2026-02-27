"""
Analytics Engine - Core Pandas-based analytics operations
Performs all calculations in memory without SQL
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta


class AnalyticsEngine:
    """Core analytics engine using Pandas for in-memory analysis"""
    
    def __init__(self):
        """Initialize analytics engine"""
        self.transactions_df = None
        self.metrics_df = None
        self.user_activity_df = None
        self.last_loaded = None
    
    def load_data(self, transactions_df: pd.DataFrame, metrics_df: Optional[pd.DataFrame] = None,
                  user_activity_df: Optional[pd.DataFrame] = None):
        """
        Load data into memory
        
        Args:
            transactions_df: Transaction data
            metrics_df: Hourly metrics data
            user_activity_df: User activity data
        """
        self.transactions_df = transactions_df.copy()
        self.metrics_df = metrics_df.copy() if metrics_df is not None else None
        self.user_activity_df = user_activity_df.copy() if user_activity_df is not None else None
        self.last_loaded = datetime.now()
    
    # ===== Filtering Operations =====
    
    def filter_by_time_range(self, df: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Filter data by time range"""
        mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
        return df[mask]
    
    def filter_by_metric(self, df: pd.DataFrame, metric: str, min_val: float = None, 
                        max_val: float = None) -> pd.DataFrame:
        """Filter data by metric value range"""
        if min_val is not None:
            df = df[df[metric] >= min_val]
        if max_val is not None:
            df = df[df[metric] <= max_val]
        return df
    
    def filter_by_category(self, df: pd.DataFrame, column: str, values: List[str]) -> pd.DataFrame:
        """Filter data by categorical values"""
        return df[df[column].isin(values)]
    
    def filter_successful(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter to only successful transactions"""
        return df[df['success'] == True]
    
    def filter_failures(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter to only failed transactions"""
        return df[df['success'] == False]
    
    # ===== Grouping & Aggregation =====
    
    def group_by_time_bucket(self, df: pd.DataFrame, bucket: str = 'D') -> pd.DataFrame:
        """
        Group by time bucket
        
        Args:
            df: DataFrame
            bucket: 'H' (hourly), 'D' (daily), 'W' (weekly), 'M' (monthly)
        """
        return df.groupby(pd.Grouper(key='timestamp', freq=bucket))
    
    def group_and_count(self, df: pd.DataFrame, column: str) -> pd.Series:
        """Group by column and count"""
        return df.groupby(column).size().sort_values(ascending=False)
    
    def group_and_aggregate(self, df: pd.DataFrame, group_by: str, 
                           agg_dict: Dict[str, str]) -> pd.DataFrame:
        """
        Group by column and apply aggregations
        
        Args:
            df: DataFrame
            group_by: Column to group by
            agg_dict: Dictionary of {column: aggregation_function}
        """
        return df.groupby(group_by).agg(agg_dict)
    
    # ===== Trend Analysis =====
    
    def calculate_trend(self, df: pd.DataFrame, metric: str, time_bucket: str = 'D') -> pd.DataFrame:
        """
        Calculate trend for a metric over time
        
        Args:
            df: DataFrame with timestamp
            metric: Metric column name
            time_bucket: Time grouping ('H', 'D', 'W', 'M')
        """
        result = df.set_index('timestamp').resample(time_bucket)[metric].agg(['mean', 'sum', 'count', 'std'])
        result['trend'] = result['mean'].diff()
        result['pct_change'] = result['mean'].pct_change() * 100
        return result.reset_index()
    
    def detect_trend_direction(self, values: List[float]) -> str:
        """
        Detect if trend is going up, down, or flat
        
        Returns: 'up', 'down', or 'flat'
        """
        if len(values) < 2:
            return 'flat'
        
        # Calculate linear regression slope
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        if abs(slope) < 0.01 * np.std(values):
            return 'flat'
        elif slope > 0:
            return 'up'
        else:
            return 'down'
    
    def calculate_moving_average(self, df: pd.DataFrame, metric: str, window: int = 7) -> pd.Series:
        """Calculate moving average"""
        return df[metric].rolling(window=window).mean()
    
    # ===== Comparison & Statistical Analysis =====
    
    def compare_periods(self, df: pd.DataFrame, metric: str, period1_start: datetime, 
                       period1_end: datetime, period2_start: datetime, period2_end: datetime) -> Dict[str, Any]:
        """
        Compare a metric between two time periods
        
        Returns:
            Dictionary with comparison statistics
        """
        p1 = self.filter_by_time_range(df, period1_start, period1_end)
        p2 = self.filter_by_time_range(df, period2_start, period2_end)
        
        p1_mean = p1[metric].mean()
        p2_mean = p2[metric].mean()
        
        change = p2_mean - p1_mean
        pct_change = (change / p1_mean * 100) if p1_mean != 0 else 0
        
        return {
            'period1_mean': p1_mean,
            'period1_median': p1[metric].median(),
            'period1_std': p1[metric].std(),
            'period1_count': len(p1),
            'period2_mean': p2_mean,
            'period2_median': p2[metric].median(),
            'period2_std': p2[metric].std(),
            'period2_count': len(p2),
            'absolute_change': change,
            'percent_change': pct_change,
            'direction': 'increased' if change > 0 else 'decreased' if change < 0 else 'unchanged'
        }
    
    def distribution_analysis(self, df: pd.DataFrame, metric: str) -> Dict[str, Any]:
        """
        Analyze distribution of a metric
        """
        data = df[metric].dropna()
        
        return {
            'count': len(data),
            'mean': data.mean(),
            'median': data.median(),
            'std': data.std(),
            'min': data.min(),
            'max': data.max(),
            'q25': data.quantile(0.25),
            'q50': data.quantile(0.50),
            'q75': data.quantile(0.75),
            'q95': data.quantile(0.95),
            'q99': data.quantile(0.99),
            'skewness': data.skew(),
            'kurtosis': data.kurtosis()
        }
    
    def correlation_analysis(self, df: pd.DataFrame, metrics: List[str]) -> pd.DataFrame:
        """
        Calculate correlation between metrics
        """
        return df[metrics].corr()
    
    # ===== Anomaly Detection =====
    
    def detect_anomalies(self, df: pd.DataFrame, metric: str, threshold_std: float = 2.0) -> pd.DataFrame:
        """
        Detect anomalies using standard deviation
        
        Args:
            df: DataFrame
            metric: Metric column
            threshold_std: Number of standard deviations for outlier detection
        """
        mean = df[metric].mean()
        std = df[metric].std()
        
        upper_bound = mean + (threshold_std * std)
        lower_bound = mean - (threshold_std * std)
        
        df['is_anomaly'] = (df[metric] > upper_bound) | (df[metric] < lower_bound)
        df['anomaly_score'] = np.abs((df[metric] - mean) / std)
        
        return df
    
    # ===== Failure Analysis =====
    
    def failure_rate_analysis(self, df: pd.DataFrame, time_bucket: str = 'D') -> pd.DataFrame:
        """
        Calculate failure rate over time
        """
        # Add success column if not exists
        if 'success' not in df.columns:
            return None
        
        result = df.set_index('timestamp').resample(time_bucket).agg({
            'success': ['sum', 'count']
        })
        
        result.columns = ['successful', 'total']
        result['failure_count'] = result['total'] - result['successful']
        result['failure_rate'] = (result['failure_count'] / result['total'] * 100)
        result['success_rate'] = (result['successful'] / result['total'] * 100)
        
        return result.reset_index()
    
    def failure_root_causes(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        Analyze failure root causes
        """
        failures = self.filter_failures(df)
        
        if 'error_code' in failures.columns:
            return failures['error_code'].value_counts().to_dict()
        return {}
    
    # ===== Summary Statistics =====
    
    def get_summary_stats(self, df: pd.DataFrame, metric: str) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        return {
            'total': df[metric].sum(),
            'count': len(df),
            'mean': df[metric].mean(),
            'median': df[metric].median(),
            'min': df[metric].min(),
            'max': df[metric].max(),
            'std': df[metric].std()
        }
    
    def breakdown_by_category(self, df: pd.DataFrame, metric: str, category: str) -> Dict[str, float]:
        """Break down metric by category"""
        return df.groupby(category)[metric].sum().to_dict()
    
    # ===== Performance Metrics =====
    
    def percentile_analysis(self, df: pd.DataFrame, metric: str) -> Dict[str, float]:
        """Calculate percentiles for a metric"""
        return {
            'p50': df[metric].quantile(0.50),
            'p75': df[metric].quantile(0.75),
            'p90': df[metric].quantile(0.90),
            'p95': df[metric].quantile(0.95),
            'p99': df[metric].quantile(0.99),
            'p999': df[metric].quantile(0.999)
        }


# Global analytics instance
analytics_engine = AnalyticsEngine()
