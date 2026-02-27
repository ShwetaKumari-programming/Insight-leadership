"""
Weekend vs Weekday Analysis
Specialized analysis for comparing weekend and weekday performance
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta


class WeekendAnalyzer:
    """Analyze differences between weekend and weekday performance"""
    
    @staticmethod
    def filter_weekend_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter to only weekend data (Saturday=5, Sunday=6)
        
        Args:
            df: DataFrame with timestamp column
            
        Returns:
            DataFrame with only weekend records
        """
        if 'timestamp' not in df.columns:
            return None
        
        df_copy = df.copy()
        df_copy['day_of_week'] = pd.to_datetime(df_copy['timestamp']).dt.dayofweek
        weekend_mask = df_copy['day_of_week'] >= 5  # 5=Saturday, 6=Sunday
        
        return df_copy[weekend_mask]
    
    @staticmethod
    def filter_weekday_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter to only weekday data (Monday-Friday)
        
        Args:
            df: DataFrame with timestamp column
            
        Returns:
            DataFrame with only weekday records
        """
        if 'timestamp' not in df.columns:
            return None
        
        df_copy = df.copy()
        df_copy['day_of_week'] = pd.to_datetime(df_copy['timestamp']).dt.dayofweek
        weekday_mask = df_copy['day_of_week'] < 5  # 0-4 = Monday-Friday
        
        return df_copy[weekday_mask]
    
    @staticmethod
    def compare_failure_rates(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compare failure rates between weekend and weekday
        
        Args:
            df: DataFrame with success column
            
        Returns:
            Dictionary with comparison statistics
        """
        if 'success' not in df.columns:
            return None
        
        # Filter data
        weekend_df = WeekendAnalyzer.filter_weekend_data(df)
        weekday_df = WeekendAnalyzer.filter_weekday_data(df)
        
        # Calculate failure rates
        weekend_failures = 1 - weekend_df['success'].mean()
        weekday_failures = 1 - weekday_df['success'].mean()
        
        # Calculate counts
        weekend_total = len(weekend_df)
        weekday_total = len(weekday_df)
        weekend_failed = (~weekend_df['success']).sum()
        weekday_failed = (~weekday_df['success']).sum()
        
        # Calculate difference
        failure_diff = weekend_failures - weekday_failures
        failure_ratio = weekend_failures / weekday_failures if weekday_failures > 0 else 0
        
        return {
            'weekend': {
                'failure_rate_percent': weekend_failures * 100,
                'total_transactions': weekend_total,
                'failed_count': weekend_failed,
                'successful_count': weekend_total - weekend_failed,
                'success_rate_percent': (1 - weekend_failures) * 100
            },
            'weekday': {
                'failure_rate_percent': weekday_failures * 100,
                'total_transactions': weekday_total,
                'failed_count': weekday_failed,
                'successful_count': weekday_total - weekday_failed,
                'success_rate_percent': (1 - weekday_failures) * 100
            },
            'comparison': {
                'absolute_difference_percent': failure_diff * 100,
                'relative_difference_percent': (failure_ratio - 1) * 100,
                'weekend_vs_weekday_ratio': failure_ratio,
                'insight': WeekendAnalyzer._generate_insight(failure_diff, failure_ratio)
            }
        }
    
    @staticmethod
    def analyze_failure_root_causes(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze root causes of failures with breakdown
        
        Args:
            df: DataFrame with error_code or status columns
            
        Returns:
            Dictionary with root cause analysis
        """
        if 'success' not in df.columns:
            return None
        
        # Filter failures
        failures = df[df['success'] == False]
        
        if len(failures) == 0:
            return {
                'total_failures': 0,
                'root_causes': {},
                'message': 'No failures found'
            }
        
        # Extract root causes by error code
        root_causes = {}
        
        if 'error_code' in failures.columns:
            error_counts = failures['error_code'].value_counts().to_dict()
            root_causes = error_counts
        
        # Calculate percentages
        total_failures = len(failures)
        root_causes_percent = {
            code: (count / total_failures * 100) 
            for code, count in root_causes.items()
        }
        
        return {
            'total_failures': total_failures,
            'root_causes_by_count': root_causes,
            'root_causes_by_percent': root_causes_percent,
            'top_cause': max(root_causes, key=root_causes.get) if root_causes else None,
            'top_cause_percent': max(root_causes_percent.values()) if root_causes_percent else 0
        }
    
    @staticmethod
    def analyze_weekend_vs_weekday_causes(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compare root causes between weekend and weekday
        
        Args:
            df: DataFrame with timestamp, success, and error_code columns
            
        Returns:
            Dictionary with comparative root cause analysis
        """
        weekend_df = WeekendAnalyzer.filter_weekend_data(df)
        weekday_df = WeekendAnalyzer.filter_weekday_data(df)
        
        weekend_causes = WeekendAnalyzer.analyze_failure_root_causes(weekend_df)
        weekday_causes = WeekendAnalyzer.analyze_failure_root_causes(weekday_df)
        
        # Compare which errors are more common in weekend
        weekend_errors = set(weekend_causes.get('root_causes_by_count', {}).keys())
        weekday_errors = set(weekday_causes.get('root_causes_by_count', {}).keys())
        
        weekend_specific = weekend_errors - weekday_errors
        weekday_specific = weekday_errors - weekend_errors
        
        return {
            'weekend': {
                'total_failures': weekend_causes['total_failures'],
                'root_causes': weekend_causes['root_causes_by_count'],
                'root_causes_percent': weekend_causes['root_causes_by_percent'],
                'top_cause': weekend_causes['top_cause']
            },
            'weekday': {
                'total_failures': weekday_causes['total_failures'],
                'root_causes': weekday_causes['root_causes_by_count'],
                'root_causes_percent': weekday_causes['root_causes_by_percent'],
                'top_cause': weekday_causes['top_cause']
            },
            'differences': {
                'errors_unique_to_weekend': list(weekend_specific),
                'errors_unique_to_weekday': list(weekday_specific),
                'common_errors': list(weekend_errors & weekday_errors)
            }
        }
    
    @staticmethod
    def detailed_weekend_failure_report(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive weekend failure report
        
        Args:
            df: Full transaction DataFrame
            
        Returns:
            Detailed report with all analysis
        """
        weekend_df = WeekendAnalyzer.filter_weekend_data(df)
        
        if len(weekend_df) == 0:
            return {'error': 'No weekend data found'}
        
        # Get all metrics
        failure_comparison = WeekendAnalyzer.compare_failure_rates(df)
        root_cause_comparison = WeekendAnalyzer.analyze_weekend_vs_weekday_causes(df)
        
        # Analyze by component if available
        component_analysis = {}
        if 'component' in weekend_df.columns:
            component_analysis = WeekendAnalyzer._analyze_by_component(weekend_df)
        
        # Analyze by region if available
        region_analysis = {}
        if 'region' in weekend_df.columns:
            region_analysis = WeekendAnalyzer._analyze_by_region(weekend_df)
        
        # Timeline analysis
        timeline_analysis = WeekendAnalyzer._analyze_weekend_timeline(weekend_df)
        
        return {
            'summary': {
                'total_weekend_transactions': len(weekend_df),
                'weekend_failure_rate': failure_comparison['weekend']['failure_rate_percent'],
                'weekday_failure_rate': failure_comparison['weekday']['failure_rate_percent'],
                'increase_percent': failure_comparison['comparison']['absolute_difference_percent'],
                'increase_ratio': f"{failure_comparison['comparison']['weekend_vs_weekday_ratio']:.2f}x"
            },
            'failure_comparison': failure_comparison,
            'root_cause_comparison': root_cause_comparison,
            'component_analysis': component_analysis,
            'region_analysis': region_analysis,
            'timeline_analysis': timeline_analysis,
            'insights': WeekendAnalyzer._generate_detailed_insights(failure_comparison, root_cause_comparison)
        }
    
    @staticmethod
    def _analyze_by_component(df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze failures by component"""
        if 'component' not in df.columns or 'success' not in df.columns:
            return {}
        
        result = {}
        for component in df['component'].unique():
            component_df = df[df['component'] == component]
            failure_rate = (1 - component_df['success'].mean()) * 100
            
            result[component] = {
                'total_transactions': len(component_df),
                'failure_rate_percent': failure_rate,
                'failure_count': (~component_df['success']).sum()
            }
        
        return result
    
    @staticmethod
    def _analyze_by_region(df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze failures by region"""
        if 'region' not in df.columns or 'success' not in df.columns:
            return {}
        
        result = {}
        for region in df['region'].unique():
            region_df = df[df['region'] == region]
            failure_rate = (1 - region_df['success'].mean()) * 100
            
            result[region] = {
                'total_transactions': len(region_df),
                'failure_rate_percent': failure_rate,
                'failure_count': (~region_df['success']).sum()
            }
        
        return result
    
    @staticmethod
    def _analyze_weekend_timeline(df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze failure timeline across weekend"""
        df_copy = df.copy()
        df_copy['hour'] = pd.to_datetime(df_copy['timestamp']).dt.hour
        df_copy['day_name'] = pd.to_datetime(df_copy['timestamp']).dt.day_name()
        
        timeline = {}
        for day in df_copy['day_name'].unique():
            day_df = df_copy[df_copy['day_name'] == day]
            
            hourly = {}
            for hour in sorted(day_df['hour'].unique()):
                hour_df = day_df[day_df['hour'] == hour]
                failure_rate = (1 - hour_df['success'].mean()) * 100 if 'success' in hour_df.columns else 0
                
                hourly[f"{hour:02d}:00"] = {
                    'transactions': len(hour_df),
                    'failure_rate_percent': failure_rate
                }
            
            timeline[day] = hourly
        
        return timeline
    
    @staticmethod
    def _generate_insight(failure_diff: float, failure_ratio: float) -> str:
        """Generate insight message"""
        if failure_diff > 0.1:
            return f"🔴 CRITICAL: Weekend failures are {failure_ratio:.1f}x higher than weekdays"
        elif failure_diff > 0.05:
            return f"🟠 WARNING: Weekend failures are {failure_ratio:.1f}x higher than weekdays"
        elif failure_diff > 0.01:
            return f"🟡 NOTICE: Weekend failures are slightly elevated ({failure_ratio:.1f}x)"
        else:
            return "🟢 Good: Weekend and weekday failure rates are similar"
    
    @staticmethod
    def _generate_detailed_insights(failure_comp: Dict, cause_comp: Dict) -> List[str]:
        """Generate detailed insights from analysis"""
        insights = []
        
        weekend_rate = failure_comp['weekend']['failure_rate_percent']
        weekday_rate = failure_comp['weekday']['failure_rate_percent']
        ratio = failure_comp['comparison']['weekend_vs_weekday_ratio']
        
        # Insight 1: Overall trend
        if ratio > 2:
            insights.append(f"⚠️ Weekend failures are {ratio:.1f}x higher - this is a significant issue")
        elif ratio > 1.5:
            insights.append(f"Weekend failures are elevated at {ratio:.1f}x the weekday rate")
        elif ratio < 0.8:
            insights.append(f"Interestingly, weekends are more stable than weekdays")
        
        # Insight 2: Root causes
        weekend_top = cause_comp['weekend']['top_cause']
        if weekend_top:
            insights.append(f"Top failure cause on weekends: Error {weekend_top} ({cause_comp['weekend']['root_causes_percent'].get(weekend_top, 0):.1f}%)")
        
        # Insight 3: Component-specific issues
        if 'component_analysis' in cause_comp:
            insights.append("Failure patterns vary by system component")
        
        # Insight 4: Action recommendation
        if ratio > 2:
            insights.append("🔧 RECOMMENDED ACTION: Investigate weekend-specific configurations or load patterns")
        elif ratio > 1.5:
            insights.append("🔧 RECOMMENDED ACTION: Monitor weekend performance and prepare contingency plans")
        
        return insights


# Global analyzer instance
weekend_analyzer = WeekendAnalyzer()
