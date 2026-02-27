"""
Intent Classification - Identify what the user is asking for
"""

from typing import Tuple, Dict
import re


class IntentClassifier:
    """Classify user intent from natural language"""
    
    def __init__(self):
        """Initialize intent patterns and keywords"""
        self.intent_patterns = {
            # Trend Analysis
            'trend_analysis': {
                'keywords': ['trend', 'increasing', 'decreasing', 'growth', 'decline', 'rising', 'falling', 'spike', 'dip'],
                'patterns': [
                    r'(trend|trending|direction).*(last|past|previous)',
                    r'(increase|decrease|grow|decline).*(rate|speed|pace)',
                    r'(up|down|spike|dip).*weekend'
                ]
            },
            
            # Comparison Analysis
            'comparison': {
                'keywords': ['compare', 'versus', 'vs', 'difference', 'similar', 'different', 'same', 'both'],
                'patterns': [
                    r'compare.*with',
                    r'difference.*(between|from)',
                    r'versus|vs'
                ]
            },
            
            # Failure/Error Analysis
            'failure_analysis': {
                'keywords': ['failure', 'failed', 'error', 'bug', 'crash', 'broken', 'issue', 'problem'],
                'patterns': [
                    r'(failure|error|bug|crash).*(rate|count|increase)',
                    r'why.*fail',
                    r'(issue|problem).*increase'
                ]
            },
            
            # Performance Analysis
            'performance_analysis': {
                'keywords': ['performance', 'latency', 'speed', 'slow', 'fast', 'throughput', 'response time'],
                'patterns': [
                    r'(slow|fast|speed|latency|performance)',
                    r'response.*time',
                    r'throughput.*change'
                ]
            },
            
            # Root Cause Analysis
            'root_cause_analysis': {
                'keywords': ['why', 'cause', 'reason', 'caused', 'because', 'root cause'],
                'patterns': [
                    r'^why',
                    r'(why|cause|reason).*fail',
                    r'what.*caused',
                    r'root.*cause'
                ]
            },
            
            # Forecasting
            'forecasting': {
                'keywords': ['predict', 'forecast', 'expect', 'will', 'next', 'tomorrow', 'future', 'upcoming'],
                'patterns': [
                    r'(predict|forecast|expect).*(next|tomorrow|future)',
                    r'will.*(be|happen)',
                    r'upcoming.*(week|month)'
                ]
            },
            
            # Summary/Overview
            'summary': {
                'keywords': ['summary', 'overview', 'total', 'aggregate', 'overall', 'general'],
                'patterns': [
                    r'(summary|overview|total|aggregate)',
                    r'give.*summary',
                    r'overall.*status'
                ]
            },
            
            # Anomaly Detection
            'anomaly_detection': {
                'keywords': ['unusual', 'abnormal', 'unexpected', 'anomaly', 'outlier', 'odd'],
                'patterns': [
                    r'(unusual|abnormal|unexpected|anomaly)',
                    r'anything.*odd',
                    r'strange.*pattern'
                ]
            },
            
            # Distribution Analysis
            'distribution_analysis': {
                'keywords': ['distribution', 'spread', 'range', 'variance', 'histogram', 'breakdown'],
                'patterns': [
                    r'(distribution|spread|range|breakdown)',
                    r'how.*distributed',
                    r'breakdown.*by'
                ]
            },
            
            # Correlation Analysis
            'correlation_analysis': {
                'keywords': ['correlation', 'related', 'relationship', 'impact', 'affect', 'effect'],
                'patterns': [
                    r'(correlation|relationship|impact).*between',
                    r'does.*affect',
                    r'effect.*on'
                ]
            }
        }
    
    def classify(self, query: str) -> Tuple[str, float]:
        """
        Classify the intent of a query
        
        Args:
            query: User's natural language query
            
        Returns:
            Tuple of (intent, confidence)
        """
        query_lower = query.lower()
        best_intent = 'general_inquiry'
        best_confidence = 0.0
        
        # Check each intent pattern
        for intent, patterns_dict in self.intent_patterns.items():
            confidence = 0.0
            
            # Check keywords (weight: 0.3)
            keywords = patterns_dict['keywords']
            keyword_matches = sum(1 for kw in keywords if kw in query_lower)
            if keyword_matches > 0:
                confidence += min(keyword_matches * 0.15, 0.3)
            
            # Check regex patterns (weight: 0.7)
            patterns = patterns_dict['patterns']
            pattern_matches = sum(1 for pattern in patterns if re.search(pattern, query_lower, re.IGNORECASE))
            if pattern_matches > 0:
                confidence += min(pattern_matches * 0.35, 0.7)
            
            # Update best match
            if confidence > best_confidence:
                best_confidence = confidence
                best_intent = intent
        
        # Ensure confidence is between 0 and 1
        best_confidence = min(max(best_confidence, 0.0), 1.0)
        
        # Default low confidence for unknown queries
        if best_confidence < 0.2:
            best_intent = 'general_inquiry'
            best_confidence = 0.5
        
        return best_intent, best_confidence
    
    def get_intent_description(self, intent: str) -> str:
        """Get human-readable description of intent"""
        descriptions = {
            'trend_analysis': 'Analyzing trends and directional changes',
            'comparison': 'Comparing two or more items',
            'failure_analysis': 'Investigating failures and errors',
            'performance_analysis': 'Analyzing system performance metrics',
            'root_cause_analysis': 'Finding the root cause of an issue',
            'forecasting': 'Predicting future values',
            'summary': 'Getting an overview or summary',
            'anomaly_detection': 'Finding unusual or unexpected patterns',
            'distribution_analysis': 'Understanding data distribution',
            'correlation_analysis': 'Finding relationships between variables',
            'general_inquiry': 'General information request'
        }
        return descriptions.get(intent, 'Unknown intent')
    
    def get_followup_questions(self, intent: str) -> list:
        """Suggest follow-up questions based on intent"""
        followups = {
            'trend_analysis': [
                'What time period are you interested in?',
                'Which metric would you like to analyze?',
                'Do you want to compare with previous periods?'
            ],
            'comparison': [
                'What specifically would you like to compare?',
                'What metrics matter most?',
                'What time period are you looking at?'
            ],
            'failure_analysis': [
                'What type of failures?',
                'Which system or component?',
                'What time period saw the increase?'
            ],
            'performance_analysis': [
                'Which performance metric?',
                'What is your baseline?',
                'When did this occur?'
            ],
            'root_cause_analysis': [
                'What specific issue occurred?',
                'When did it happen?',
                'Any recent changes in the system?'
            ],
            'forecasting': [
                'What time horizon?',
                'What confidence level do you need?',
                'Based on what historical period?'
            ],
            'general_inquiry': [
                'Could you be more specific?',
                'What aspect interests you most?',
                'What time period or metric?'
            ]
        }
        return followups.get(intent, [])
