"""
Explainability Layer - Rules + AI
Transforms raw analytics into human-readable explanations
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import re


class ExplainabilityEngine:
    """Main engine for generating explanations from analytics results"""
    
    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm
        self.rule_based_explainer = RuleBasedExplainer()
        if use_llm:
            try:
                from llm_connector import LLMConnector
                self.llm_explainer = LLMConnector()
            except:
                self.llm_explainer = None
                self.use_llm = False
    
    def explain_failure_comparison(self, comparison: Dict[str, Any]) -> str:
        """
        Explain failure rate comparison results
        
        Args:
            comparison: Result from WeekendAnalyzer.compare_failure_rates()
            
        Returns:
            Human-readable explanation
        """
        return self.rule_based_explainer.explain_failure_comparison(comparison)
    
    def explain_root_causes(self, causes: Dict[str, Any]) -> str:
        """
        Explain root cause analysis results
        
        Args:
            causes: Result from WeekendAnalyzer.analyze_weekend_vs_weekday_causes()
            
        Returns:
            Human-readable explanation
        """
        return self.rule_based_explainer.explain_root_causes(causes)
    
    def explain_weekend_analysis(self, report: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate comprehensive explanation for weekend analysis
        
        Args:
            report: Complete weekend analysis report
            
        Returns:
            Dictionary with explanations for each section
        """
        return self.rule_based_explainer.explain_weekend_analysis(report)
    
    def explain_with_llm(self, data: Dict[str, Any], question: str) -> str:
        """
        Generate explanation using LLM
        
        Args:
            data: Analytics data
            question: User's original question
            
        Returns:
            LLM-generated explanation
        """
        if not self.use_llm or not self.llm_explainer:
            return self.rule_based_explainer.explain_generic(data)
        
        prompt = self._build_llm_prompt(data, question)
        return self.llm_explainer.generate_explanation(prompt)
    
    def explain_failure_analysis(self, data: Dict[str, Any]) -> str:
        """
        Explain failure analysis results
        
        Args:
            data: Dictionary with failure_rate, error_distribution, total_transactions
            
        Returns:
            Human-readable explanation
        """
        return self.rule_based_explainer.explain_failure_analysis(data)
    
    def explain_performance(self, data: Dict[str, Any]) -> str:
        """
        Explain performance analysis results
        
        Args:
            data: Dictionary with latency metrics
            
        Returns:
            Human-readable explanation
        """
        return self.rule_based_explainer.explain_performance(data)
    
    def explain_trends(self, data: Dict[str, Any]) -> str:
        """
        Explain trend analysis results
        
        Args:
            data: Dictionary with trend data
            
        Returns:
            Human-readable explanation
        """
        return self.rule_based_explainer.explain_trends(data)
    
    def explain_system_health(self, data: Dict[str, Any]) -> str:
        """
        Explain overall system health
        
        Args:
            data: Dictionary with system metrics
            
        Returns:
            Human-readable explanation
        """
        return self.rule_based_explainer.explain_system_health(data)
    
    def _build_llm_prompt(self, data: Dict[str, Any], question: str) -> str:
        """Build prompt for LLM explanation"""
        return f"""
Given the following analytics data, provide a clear explanation that answers the question.

Question: {question}

Data:
{data}

Provide a concise explanation focusing on:
1. What happened
2. Why it happened (root causes)
3. When it happened (time patterns)
4. What to do about it (recommendations)

Explanation:"""


class RuleBasedExplainer:
    """Rule-based explanation generator using templates"""
    
    def explain_failure_comparison(self, comparison: Dict[str, Any]) -> str:
        """Generate explanation for failure rate comparison"""
        weekend = comparison['weekend']
        weekday = comparison['weekday']
        comp = comparison['comparison']
        
        weekend_rate = weekend['failure_rate_percent']
        weekday_rate = weekday['failure_rate_percent']
        ratio = comp['weekend_vs_weekday_ratio']
        diff = comp['absolute_difference_percent']
        
        # Build explanation
        explanation = []
        
        # Main finding
        if ratio > 3:
            severity = "significantly higher"
            concern = "This is a CRITICAL issue"
        elif ratio > 2:
            severity = "substantially higher"
            concern = "This requires immediate attention"
        elif ratio > 1.5:
            severity = "notably higher"
            concern = "This should be investigated"
        else:
            severity = "slightly higher"
            concern = "This is within acceptable variance"
        
        explanation.append(
            f"Transaction failures are {severity} on weekends compared to weekdays. "
            f"The weekend failure rate is {weekend_rate:.1f}%, which is {ratio:.2f}x "
            f"higher than the weekday rate of {weekday_rate:.1f}%. "
            f"{concern}."
        )
        
        # Context with numbers
        explanation.append(
            f"\n\nOut of {weekend['total_transactions']:,} weekend transactions, "
            f"{weekend['failed_count']:,} failed, while only {weekday['failed_count']:,} "
            f"out of {weekday['total_transactions']:,} weekday transactions failed. "
            f"This represents an absolute increase of {diff:.1f} percentage points."
        )
        
        # Likely causes
        explanation.append(
            "\n\nCommon causes for weekend-specific failures include:"
        )
        
        if ratio > 2.5:
            explanation.append(
                "\n• Service capacity limitations during weekend traffic spikes"
                "\n• Reduced operational support or monitoring coverage"
                "\n• Scheduled maintenance or batch jobs interfering with services"
                "\n• Different user behavior patterns overwhelming specific components"
            )
        else:
            explanation.append(
                "\n• Moderate traffic variations between weekdays and weekends"
                "\n• Minor configuration differences in weekend operations"
                "\n• Possible scheduled tasks affecting performance"
            )
        
        return ''.join(explanation)
    
    def explain_root_causes(self, causes: Dict[str, Any]) -> str:
        """Generate explanation for root cause analysis"""
        weekend = causes['weekend']
        weekday = causes['weekday']
        differences = causes['differences']
        
        explanation = []
        
        # Top causes
        weekend_top = weekend['top_cause']
        weekday_top = weekday['top_cause']
        
        explanation.append(
            f"Root cause analysis reveals distinct error patterns between weekends and weekdays. "
        )
        
        if weekend_top == weekday_top:
            explanation.append(
                f"Error {weekend_top} is the leading cause in both periods, but with different frequencies."
            )
        else:
            explanation.append(
                f"The top error shifts from {weekday_top} on weekdays to {weekend_top} on weekends, "
                f"indicating a change in failure patterns."
            )
        
        # Weekend breakdown
        explanation.append(
            f"\n\n**Weekend Failure Breakdown** ({weekend['total_failures']:,} total failures):"
        )
        
        sorted_weekend = sorted(
            weekend['root_causes_percent'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        for error_code, percent in sorted_weekend:
            count = weekend['root_causes'][error_code]
            error_meaning = self._get_error_meaning(error_code)
            explanation.append(
                f"\n• Error {error_code} ({error_meaning}): {percent:.1f}% ({count:,} occurrences)"
            )
        
        # Weekday breakdown
        explanation.append(
            f"\n\n**Weekday Failure Breakdown** ({weekday['total_failures']:,} total failures):"
        )
        
        sorted_weekday = sorted(
            weekday['root_causes_percent'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        for error_code, percent in sorted_weekday:
            count = weekday['root_causes'][error_code]
            error_meaning = self._get_error_meaning(error_code)
            explanation.append(
                f"\n• Error {error_code} ({error_meaning}): {percent:.1f}% ({count:,} occurrences)"
            )
        
        # Key differences
        if differences['errors_unique_to_weekend']:
            explanation.append(
                f"\n\n**Weekend-Specific Errors:** {', '.join(differences['errors_unique_to_weekend'])}"
            )
        
        if differences['errors_unique_to_weekday']:
            explanation.append(
                f"\n**Weekday-Specific Errors:** {', '.join(differences['errors_unique_to_weekday'])}"
            )
        
        # Recommendations based on top error
        explanation.append(
            f"\n\n**Recommended Actions:**"
        )
        recommendations = self._get_error_recommendations(weekend_top)
        for rec in recommendations:
            explanation.append(f"\n• {rec}")
        
        return ''.join(explanation)
    
    def explain_weekend_analysis(self, report: Dict[str, Any]) -> Dict[str, str]:
        """Generate comprehensive explanation for full weekend analysis"""
        explanations = {}
        
        # Summary explanation
        if 'summary' in report:
            summary = report['summary']
            ratio = float(summary.get('increase_ratio', '0x').replace('x', ''))
            
            explanations['summary'] = (
                f"Weekend failures increased by {ratio:.2f}x compared to weekdays. "
                f"Out of {summary['total_weekend_transactions']:,} weekend transactions, "
                f"{summary['weekend_failure_rate']:.1f}% failed, compared to "
                f"{summary['weekday_failure_rate']:.1f}% on weekdays - "
                f"an increase of {summary['increase_percent']:.1f} percentage points."
            )
        
        # Root causes explanation
        if 'root_causes' in report:
            causes = report['root_causes']
            top_weekend = causes['weekend']['top_cause']
            top_weekday = causes['weekday']['top_cause']
            
            explanations['root_causes'] = (
                f"The primary failure cause shifts from Error {top_weekday} on weekdays "
                f"to Error {top_weekday} on weekends. "
                f"{self._get_error_meaning(top_weekend)} errors dominate weekend failures."
            )
        
        # Component analysis explanation
        if 'component_analysis' in report and report['component_analysis']:
            comp_analysis = report['component_analysis']
            if 'top_failing_component' in comp_analysis:
                top_comp = comp_analysis['top_failing_component']
                explanations['components'] = (
                    f"The {top_comp['component']} component has the highest failure rate "
                    f"at {top_comp['failure_rate']:.1f}% on weekends."
                )
        
        # Timeline explanation
        if 'timeline_analysis' in report:
            timeline = report['timeline_analysis']
            if 'peak_failure_hour' in timeline:
                peak = timeline['peak_failure_hour']
                explanations['timeline'] = (
                    f"Weekend failures peak at {peak['hour']}:00 with "
                    f"{peak['failure_rate']:.1f}% failure rate, suggesting "
                    f"traffic or load patterns at this time."
                )
        
        return explanations
    
    def explain_generic(self, data: Dict[str, Any]) -> str:
        """Generic explanation for any analytics data"""
        explanation = ["Analysis Results:\n"]
        
        for key, value in data.items():
            if isinstance(value, dict):
                explanation.append(f"\n{key.replace('_', ' ').title()}:")
                for k, v in value.items():
                    explanation.append(f"\n• {k.replace('_', ' ').title()}: {v}")
            else:
                explanation.append(f"\n{key.replace('_', ' ').title()}: {value}")
        
        return ''.join(explanation)
    
    def _get_error_meaning(self, error_code: str) -> str:
        """Get human-readable meaning for error codes"""
        error_meanings = {
            '500': 'Internal Server Error',
            '502': 'Bad Gateway',
            '503': 'Service Unavailable',
            '504': 'Gateway Timeout',
            '400': 'Bad Request',
            '401': 'Unauthorized',
            '403': 'Forbidden',
            '404': 'Not Found',
            '429': 'Too Many Requests',
            '408': 'Request Timeout'
        }
        return error_meanings.get(str(error_code), 'Unknown Error')
    
    def _get_error_recommendations(self, error_code: str) -> List[str]:
        """Get recommendations based on error type"""
        recommendations = {
            '503': [
                "Increase service capacity or add more instances",
                "Implement auto-scaling for weekend traffic patterns",
                "Review connection pool sizes and limits",
                "Check for resource exhaustion (CPU, memory, connections)"
            ],
            '504': [
                "Optimize slow backend queries or operations",
                "Increase timeout thresholds if appropriate",
                "Review network latency between services",
                "Implement caching for frequently accessed data"
            ],
            '500': [
                "Review application logs for exceptions",
                "Check for unhandled errors in code",
                "Verify database connections and queries",
                "Monitor memory leaks or resource issues"
            ],
            '502': [
                "Verify backend service health and availability",
                "Check load balancer configuration",
                "Review network connectivity between services",
                "Ensure backend services are not overloaded"
            ]
        }
        
        return recommendations.get(
            str(error_code),
            ["Review error logs and metrics", "Investigate specific failure patterns"]
        )
    
    def explain_failure_analysis(self, data: Dict[str, Any]) -> str:
        """Explain failure analysis results"""
        failure_rate = data.get('failure_rate', 0)
        error_dist = data.get('error_distribution', {})
        total = data.get('total_transactions', 0)
        
        explanation = [
            "## 📊 Failure Analysis Report\n",
            f"📈 **Overall Failure Rate**: {failure_rate:.2f}%\n",
            f"📊 **Total Transactions**: {total:,}\n"
        ]
        
        if failure_rate > 20:
            explanation.append("⚠️ **Severity**: CRITICAL - High failure rate detected\n")
        elif failure_rate > 10:
            explanation.append("⚠️ **Severity**: HIGH - Elevated failure rate\n")
        elif failure_rate > 5:
            explanation.append("⚠️ **Severity**: MEDIUM - Notable failures\n")
        else:
            explanation.append("✅ **Severity**: LOW - Acceptable failure rate\n")
        
        if error_dist:
            explanation.append("\n### Top Errors:\n")
            for error, count in sorted(error_dist.items(), key=lambda x: x[1], reverse=True)[:5]:
                pct = (count / total * 100) if total > 0 else 0
                explanation.append(f"• **{self._get_error_meaning(error)}** ({error}): {pct:.1f}%\n")
        
        return ''.join(explanation)
    
    def explain_performance(self, data: Dict[str, Any]) -> str:
        """Explain performance analysis results"""
        avg_latency = data.get('metrics', {}).get('avg_latency', 0)
        p95_latency = data.get('metrics', {}).get('p95_latency', 0)
        
        explanation = [
            "## ⚡ Performance Analysis\n",
            f"📊 **Average Latency**: {avg_latency:.0f}ms\n",
            f"📈 **P95 Latency**: {p95_latency:.0f}ms\n"
        ]
        
        if avg_latency > 1000:
            explanation.append("⚠️ **Status**: SLOW - High average latency\n")
        elif avg_latency > 500:
            explanation.append("⚠️ **Status**: MODERATE - Acceptable latency\n")
        else:
            explanation.append("✅ **Status**: FAST - Good performance\n")
        
        explanation.append("\n### Recommendations:\n")
        if avg_latency > 500:
            explanation.append("• Optimize database queries\n")
            explanation.append("• Implement caching strategies\n")
            explanation.append("• Review external API calls\n")
        else:
            explanation.append("• Continue monitoring\n")
            explanation.append("• System is performing well\n")
        
        return ''.join(explanation)
    
    def explain_trends(self, data: Dict[str, Any]) -> str:
        """Explain trend analysis results"""
        explanation = [
            "## 📈 Trend Analysis\n",
            "Based on historical data patterns:\n"
        ]
        
        if data.get('trend_direction') == 'increasing':
            explanation.append("⬆️ **Trend**: INCREASING - Failures are rising\n")
            explanation.append("⚠️ **Action Required**: Investigate root causes and implement mitigation\n")
        elif data.get('trend_direction') == 'decreasing':
            explanation.append("⬇️ **Trend**: DECREASING - Failures are improving\n")
            explanation.append("✅ **Status**: Positive trajectory\n")
        else:
            explanation.append("➡️ **Trend**: STABLE - Pattern is consistent\n")
            explanation.append("ℹ️ **Status**: Maintaining current state\n")
        
        explanation.append("\n### Forecast:\n")
        explanation.append(f"• Next 7 days: {data.get('forecast', 'Normal operations expected')}\n")
        
        return ''.join(explanation)
    
    def explain_system_health(self, data: Dict[str, Any]) -> str:
        """Explain overall system health"""
        total_txn = data.get('total_transactions', 0)
        metrics = data.get('metrics', {})
        
        failure_rate = metrics.get('failure_rate', 0)
        avg_latency = metrics.get('avg_latency', 0)
        
        explanation = [
            "## 🏥 System Health Summary\n",
            f"📊 **Transactions Analyzed**: {total_txn:,}\n"
        ]
        
        # Overall health status
        if failure_rate > 15 or avg_latency > 1000:
            explanation.append("🔴 **Overall Status**: CRITICAL\n")
        elif failure_rate > 10 or avg_latency > 500:
            explanation.append("🟡 **Overall Status**: WARNING\n")
        else:
            explanation.append("🟢 **Overall Status**: HEALTHY\n")
        
        explanation.append("\n### Key Metrics:\n")
        explanation.append(f"• Failure Rate: {failure_rate:.2f}%\n")
        explanation.append(f"• Average Latency: {avg_latency:.0f}ms\n")
        explanation.append(f"• Uptime: {100 - failure_rate:.2f}%\n")
        
        explanation.append("\n### Recommendations:\n")
        if failure_rate > 10:
            explanation.append("• Increase monitoring and alerting\n")
            explanation.append("• Review error logs and patterns\n")
        if avg_latency > 500:
            explanation.append("• Optimize slow operations\n")
        if (failure_rate <= 5 and avg_latency <= 300):
            explanation.append("• System is performing well\n")
            explanation.append("• Continue regular monitoring\n")
        
        return ''.join(explanation)


class ExplanationFormatter:
    """Format explanations for different output types"""
    
    @staticmethod
    def format_for_chat(explanation: str) -> str:
        """Format explanation for chat interface"""
        return explanation
    
    @staticmethod
    def format_for_api(explanation: str) -> Dict[str, Any]:
        """Format explanation for API response"""
        return {
            "explanation": explanation,
            "timestamp": datetime.now().isoformat(),
            "format": "natural_language"
        }
    
    @staticmethod
    def format_markdown(explanation: str) -> str:
        """Format explanation as Markdown"""
        # Already has markdown formatting from rule-based explainer
        return explanation
    
    @staticmethod
    def extract_key_points(explanation: str) -> List[str]:
        """Extract bullet points from explanation"""
        lines = explanation.split('\n')
        bullet_points = [
            line.strip('• ').strip()
            for line in lines
            if line.strip().startswith('•')
        ]
        return bullet_points


# Singleton instance
explainability_engine = ExplainabilityEngine(use_llm=False)


if __name__ == "__main__":
    # Test the explainability layer
    print("Testing Explainability Layer...\n")
    
    # Sample comparison data
    sample_comparison = {
        'weekend': {
            'failure_rate_percent': 15.18,
            'total_transactions': 26372,
            'failed_count': 4004,
        },
        'weekday': {
            'failure_rate_percent': 4.84,
            'total_transactions': 63968,
            'failed_count': 3098,
        },
        'comparison': {
            'absolute_difference_percent': 10.34,
            'weekend_vs_weekday_ratio': 3.13
        }
    }
    
    engine = ExplainabilityEngine()
    explanation = engine.explain_failure_comparison(sample_comparison)
    
    print("=" * 70)
    print("EXPLANATION: Failure Rate Comparison")
    print("=" * 70)
    print(explanation)
    print("\n" + "=" * 70)
