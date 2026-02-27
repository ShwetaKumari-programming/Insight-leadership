"""
Entity Extraction - Extract entities like time, metrics, and values from queries
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re


class EntityExtractor:
    """Extract entities from natural language queries"""
    
    def __init__(self):
        """Initialize entity patterns and keywords"""
        self.time_keywords = {
            'today': 0,
            'yesterday': -1,
            'tomorrow': 1,
            'last week': -7,
            'last weekend': -2,  # Relative to current day
            'this week': 0,
            'next week': 7,
            'last month': -30,
            'this month': 0,
            'next month': 30,
            'last quarter': -90,
            'this quarter': 0,
            'next quarter': 90,
            'last year': -365,
            'this year': 0,
            'next year': 365,
            'past 24 hours': -1,
            'past week': -7,
            'past month': -30,
            'past quarter': -90,
            'past year': -365
        }
        
        self.metric_keywords = {
            # Performance Metrics
            'latency': ['latency', 'response time', 'lag', 'delay'],
            'throughput': ['throughput', 'requests per second', 'rps', 'qps'],
            'cpu_usage': ['cpu', 'cpu usage', 'cpu load', 'processor'],
            'memory_usage': ['memory', 'ram', 'memory usage', 'heap'],
            'disk_usage': ['disk', 'disk usage', 'storage', 'space'],
            
            # Reliability Metrics
            'error_rate': ['error rate', 'error %', 'failure rate', 'failures'],
            'availability': ['availability', 'uptime', 'downtime', 'up'],
            'success_rate': ['success rate', 'success %', 'passed'],
            
            # Business Metrics
            'revenue': ['revenue', 'income', 'sales', 'profit'],
            'users': ['users', 'customers', 'visitors', 'traffic'],
            'conversion': ['conversion', 'conversion rate', 'ctr'],
            'churn': ['churn', 'churn rate', 'retention'],
            
            # Other
            'count': ['count', 'number', 'total', 'amount'],
            'time': ['time', 'duration', 'period']
        }
        
        self.system_components = {
            'database': ['database', 'db', 'postgres', 'mysql', 'mongodb', 'elasticsearch'],
            'api': ['api', 'endpoint', 'service', 'microservice'],
            'frontend': ['frontend', 'ui', 'web', 'client', 'browser'],
            'backend': ['backend', 'server', 'application'],
            'cache': ['cache', 'redis', 'memcached'],
            'queue': ['queue', 'message queue', 'kafka', 'rabbitmq'],
            'network': ['network', 'bandwidth', 'latency', 'connection']
        }
    
    def extract(self, query: str) -> Dict[str, any]:
        """
        Extract all entities from query
        
        Args:
            query: User's natural language query
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {}
        
        # Extract metrics
        metrics = self.extract_metrics(query)
        if metrics:
            entities['metrics'] = metrics
        
        # Extract system components
        components = self.extract_components(query)
        if components:
            entities['components'] = components
        
        # Extract numeric values
        values = self.extract_numbers(query)
        if values:
            entities['values'] = values
        
        # Extract comparisons
        comparisons = self.extract_comparisons(query)
        if comparisons:
            entities['comparisons'] = comparisons
        
        return entities
    
    def extract_time_reference(self, query: str) -> Optional[str]:
        """
        Extract time reference from query
        
        Args:
            query: User's natural language query
            
        Returns:
            Time reference as string or None
        """
        query_lower = query.lower()
        
        # Check for exact matches
        for time_ref in sorted(self.time_keywords.keys(), key=len, reverse=True):
            if time_ref in query_lower:
                return time_ref
        
        # Check for relative time patterns
        relative_patterns = [
            (r'(\d+)\s*(?:day|days|d)', 'past {0} days'),
            (r'(\d+)\s*(?:hour|hours|h)', 'past {0} hours'),
            (r'(\d+)\s*(?:week|weeks|w)', 'past {0} weeks'),
            (r'(\d+)\s*(?:month|months|m)(?!in)', 'past {0} months')
        ]
        
        for pattern, template in relative_patterns:
            match = re.search(pattern, query_lower)
            if match:
                return template.format(match.group(1))
        
        return None
    
    def extract_metrics(self, query: str) -> List[str]:
        """
        Extract metric names from query
        
        Args:
            query: User's natural language query
            
        Returns:
            List of extracted metrics
        """
        query_lower = query.lower()
        found_metrics = []
        
        for metric, keywords in self.metric_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    found_metrics.append(metric)
                    break
        
        return list(set(found_metrics))  # Remove duplicates
    
    def extract_components(self, query: str) -> List[str]:
        """
        Extract system components from query
        
        Args:
            query: User's natural language query
            
        Returns:
            List of extracted components
        """
        query_lower = query.lower()
        found_components = []
        
        for component, keywords in self.system_components.items():
            for keyword in keywords:
                if keyword in query_lower:
                    found_components.append(component)
                    break
        
        return list(set(found_components))  # Remove duplicates
    
    def extract_numbers(self, query: str) -> List[Dict]:
        """
        Extract numeric values and their context from query
        
        Args:
            query: User's natural language query
            
        Returns:
            List of numbers with their context
        """
        numbers = []
        
        # Pattern for numbers with optional units
        pattern = r'(\d+(?:\.\d+)?)\s*(%|ms|seconds?|minutes?|hours?|days?)?'
        
        for match in re.finditer(pattern, query):
            value = float(match.group(1))
            unit = match.group(2) or ''
            
            # Get context (words around the number)
            context = self._get_context(query, match.start(), 20)
            
            numbers.append({
                'value': value,
                'unit': unit,
                'context': context
            })
        
        return numbers
    
    def extract_comparisons(self, query: str) -> List[str]:
        """
        Extract comparison operators and targets
        
        Args:
            query: User's natural language query
            
        Returns:
            List of comparison statements
        """
        comparisons = []
        
        comparison_patterns = [
            r'(more|less|higher|lower|greater|smaller).*than',
            r'(increase|decrease|grow|decline).*(?:by|to)\s*(\d+)',
            r'(compared|vs|versus|against).*'
        ]
        
        for pattern in comparison_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                comparisons.append(match.group(0))
        
        return comparisons
    
    def _get_context(self, text: str, position: int, window: int = 20) -> str:
        """Get context around a position in text"""
        start = max(0, position - window)
        end = min(len(text), position + window)
        return text[start:end].strip()
    
    def extract_dimensions(self, query: str) -> Dict[str, List[str]]:
        """
        Extract dimensions for grouping/breakdown
        
        Args:
            query: User's natural language query
            
        Returns:
            Dictionary of dimensions
        """
        dimensions = {
            'time': [],
            'geography': [],
            'product': [],
            'component': [],
            'severity': []
        }
        
        # Time dimensions
        time_dims = ['hourly', 'daily', 'weekly', 'monthly', 'yearly', 'by hour', 'by day']
        for td in time_dims:
            if td in query.lower():
                dimensions['time'].append(td)
        
        # Geography
        geo_patterns = ['region', 'country', 'zone', 'location', 'data center', 'dc']
        for gp in geo_patterns:
            if gp in query.lower():
                dimensions['geography'].append(gp)
        
        return {k: v for k, v in dimensions.items() if v}
