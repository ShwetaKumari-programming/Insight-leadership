"""
Trend Analyzer - Advanced trend analysis and pattern detection
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from scipy import stats


class TrendAnalyzer:
    """Analyze trends and patterns in data"""
    
    @staticmethod
    def analyze_weekly_pattern(df: pd.DataFrame, metric: str) -> Dict[str, Any]:
        """
        Analyze how metric varies by day of week
        """
        if 'timestamp' not in df.columns:
            return {}
        
        df_copy = df.copy()
        df_copy['day_of_week'] = pd.to_datetime(df_copy['timestamp']).dt.day_name()
        
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        pattern = df_copy.groupby('day_of_week')[metric].agg(['mean', 'std', 'count'])
        pattern = pattern.reindex(day_order)
        
        return {
            'pattern': pattern.to_dict(),
            'peak_day': pattern['mean'].idxmax(),
            'lowest_day': pattern['mean'].idxmin(),
            'peak_value': pattern['mean'].max(),
            'lowest_value': pattern['mean'].min()
        }
    
    @staticmethod
    def analyze_hourly_pattern(df: pd.DataFrame, metric: str) -> Dict[str, Any]:
        """
        Analyze how metric varies by hour of day
        """
        if 'timestamp' not in df.columns:
            return {}
        
        df_copy = df.copy()
        df_copy['hour'] = pd.to_datetime(df_copy['timestamp']).dt.hour
        
        pattern = df_copy.groupby('hour')[metric].agg(['mean', 'std', 'count'])
        
        return {
            'pattern': pattern.to_dict(),
            'peak_hour': pattern['mean'].idxmax(),
            'lowest_hour': pattern['mean'].idxmin(),
            'peak_value': pattern['mean'].max(),
            'lowest_value': pattern['mean'].min(),
            'business_hours_vs_offhours_ratio': (
                pattern.loc[8:18, 'mean'].mean() / pattern.loc[[0,1,2,3,4,5,6,7,19,20,21,22,23], 'mean'].mean()
                if len(pattern.loc[8:18]) > 0 else 0
            )
        }
    
    @staticmethod
    def forecast_next_period(df: pd.DataFrame, metric: str, time_bucket: str = 'D', 
                            periods: int = 7) -> List[Dict[str, Any]]:
        """
        Simple forecast for next period using exponential smoothing
        
        Args:
            df: DataFrame with time series
            metric: Metric to forecast
            time_bucket: Time grouping
            periods: Number of periods to forecast
        """
        # Aggregate data by time bucket
        ts = df.set_index('timestamp').resample(time_bucket)[metric].mean()
        
        # Exponential smoothing
        from scipy.stats import linregress
        
        x = np.arange(len(ts))
        y = ts.values
        
        # Fit linear regression
        slope, intercept, r_value, p_value, std_err = linregress(x, y)
        
        # Forecast
        forecast = []
        last_index = len(ts)
        last_date = ts.index[-1]
        
        for i in range(1, periods + 1):
            predicted_value = slope * (last_index + i) + intercept
            
            # Calculate next date based on time bucket
            if time_bucket == 'D':
                next_date = last_date + timedelta(days=i)
            elif time_bucket == 'H':
                next_date = last_date + timedelta(hours=i)
            else:
                next_date = last_date + timedelta(days=i)
            
            forecast.append({
                'date': next_date,
                'predicted_value': predicted_value,
                'confidence': r_value ** 2,
                'period': i
            })
        
        return forecast
    
    @staticmethod
    def seasonal_decomposition(df: pd.DataFrame, metric: str, period: int = 7) -> Dict[str, Any]:
        """
        Perform seasonal decomposition
        """
        from statsmodels.tsa.seasonal import seasonal_decompose
        
        ts = df.set_index('timestamp')[metric].asfreq('D')
        
        if len(ts) < 2 * period:
            return {'error': 'Insufficient data for seasonal decomposition'}
        
        try:
            decomposition = seasonal_decompose(ts, model='additive', period=period)
            
            return {
                'trend': decomposition.trend.to_dict(),
                'seasonal': decomposition.seasonal.to_dict(),
                'residual': decomposition.resid.to_dict(),
                'seasonal_strength': 1 - (decomposition.resid.var() / decomposition.seasonal.var()),
                'trend_strength': 1 - (decomposition.resid.var() / decomposition.trend.var())
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def detect_change_points(df: pd.DataFrame, metric: str) -> List[Dict[str, Any]]:
        """
        Detect change points in time series
        """
        ts = df.set_index('timestamp')[metric].resample('D').mean()
        
        # Calculate rolling mean and std
        rolling_mean = ts.rolling(window=7).mean()
        rolling_std = ts.rolling(window=7).std()
        
        # Detect points where value deviates significantly
        change_points = []
        threshold = 2.0  # Standard deviations
        
        for i in range(len(ts)):
            if i < 7:
                continue
            
            z_score = abs((ts.iloc[i] - rolling_mean.iloc[i]) / rolling_std.iloc[i])
            
            if z_score > threshold:
                change_points.append({
                    'date': ts.index[i],
                    'value': ts.iloc[i],
                    'z_score': z_score,
                    'severity': 'high' if z_score > 3 else 'medium' if z_score > 2.5 else 'low'
                })
        
        return change_points
    
    @staticmethod
    def compare_metric_trends(df: pd.DataFrame, metric1: str, metric2: str) -> Dict[str, Any]:
        """
        Compare trends of two metrics
        """
        ts1 = df.set_index('timestamp').resample('D')[metric1].mean()
        ts2 = df.set_index('timestamp').resample('D')[metric2].mean()
        
        # Normalize for comparison
        ts1_normalized = (ts1 - ts1.mean()) / ts1.std()
        ts2_normalized = (ts2 - ts2.mean()) / ts2.std()
        
        # Calculate correlation
        correlation = ts1_normalized.corr(ts2_normalized)
        
        # Fit trends
        x = np.arange(len(ts1))
        slope1, _, _, _, _ = stats.linregress(x, ts1_normalized.values)
        slope2, _, _, _, _ = stats.linregress(x, ts2_normalized.values)
        
        return {
            'correlation': correlation,
            'metric1_trend': 'up' if slope1 > 0 else 'down' if slope1 < 0 else 'flat',
            'metric2_trend': 'up' if slope2 > 0 else 'down' if slope2 < 0 else 'flat',
            'metric1_slope': slope1,
            'metric2_slope': slope2,
            'trends_aligned': (slope1 * slope2) > 0
        }
    
    @staticmethod
    def calculate_volatility(df: pd.DataFrame, metric: str, window: int = 7) -> pd.DataFrame:
        """
        Calculate volatility (standard deviation) over time
        """
        ts = df.set_index('timestamp').resample('D')[metric].mean()
        volatility = ts.rolling(window=window).std()
        
        result = pd.DataFrame({
            'timestamp': ts.index,
            'value': ts.values,
            'volatility': volatility.values
        })
        
        return result
    
    @staticmethod
    def identify_anomalies_zscore(df: pd.DataFrame, metric: str, threshold: float = 3.0) -> List[Dict[str, Any]]:
        """
        Identify anomalies using Z-score method
        """
        mean = df[metric].mean()
        std = df[metric].std()
        
        df_copy = df.copy()
        df_copy['z_score'] = (df_copy[metric] - mean) / std
        df_copy['is_anomaly'] = abs(df_copy['z_score']) > threshold
        
        anomalies = df_copy[df_copy['is_anomaly']][['timestamp', metric, 'z_score']]
        
        return anomalies.to_dict('records')


# Global trend analyzer instance
trend_analyzer = TrendAnalyzer()
