"""
NLP Layer - Natural Language Processing for understanding user queries
Supports both rule-based and LLM-based approaches
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import re

from intent_classifier import IntentClassifier
from entity_extractor import EntityExtractor


@dataclass
class NLPResult:
    """Structure for NLP processing results"""
    raw_query: str
    intent: str
    confidence: float
    entities: Dict[str, Any]
    time_reference: Optional[str]
    metrics: List[str]
    context: Dict[str, Any]
    processing_method: str  # 'rule-based' or 'llm'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "raw_query": self.raw_query,
            "intent": self.intent,
            "confidence": self.confidence,
            "entities": self.entities,
            "time_reference": self.time_reference,
            "metrics": self.metrics,
            "context": self.context,
            "processing_method": self.processing_method
        }


class NLPEngine:
    """Main NLP Engine for natural language understanding"""
    
    def __init__(self, use_llm: bool = False, llm_provider: str = "openai"):
        """
        Initialize NLP Engine
        
        Args:
            use_llm: Whether to use LLM-based processing
            llm_provider: LLM provider ('openai', 'gemini', 'llama')
        """
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        
        self.use_llm = use_llm
        self.llm_provider = llm_provider
        
        if use_llm:
            try:
                from llm_connector import LLMConnector
                self.llm = LLMConnector(provider=llm_provider)
            except Exception as e:
                print(f"Warning: Could not initialize LLM ({e}). Falling back to rule-based.")
                self.use_llm = False
    
    def process(self, query: str) -> NLPResult:
        """
        Process a natural language query and extract understanding
        
        Args:
            query: User's natural language query
            
        Returns:
            NLPResult with intent, entities, and context
        """
        if self.use_llm:
            return self._process_with_llm(query)
        else:
            return self._process_rule_based(query)
    
    def _process_rule_based(self, query: str) -> NLPResult:
        """Process using rule-based NLP (no API calls)"""
        
        # Classify intent
        intent, confidence = self.intent_classifier.classify(query)
        
        # Extract entities
        entities = self.entity_extractor.extract(query)
        
        # Extract time references
        time_ref = self.entity_extractor.extract_time_reference(query)
        
        # Extract metrics
        metrics = self.entity_extractor.extract_metrics(query)
        
        # Build context
        context = self._build_context(intent, entities, metrics)
        
        return NLPResult(
            raw_query=query,
            intent=intent,
            confidence=confidence,
            entities=entities,
            time_reference=time_ref,
            metrics=metrics,
            context=context,
            processing_method="rule-based"
        )
    
    def _process_with_llm(self, query: str) -> NLPResult:
        """Process using LLM-based NLP (requires API key)"""
        try:
            result = self.llm.extract_understanding(query)
            
            return NLPResult(
                raw_query=query,
                intent=result.get("intent", "unknown"),
                confidence=result.get("confidence", 0.8),
                entities=result.get("entities", {}),
                time_reference=result.get("time_reference"),
                metrics=result.get("metrics", []),
                context=result.get("context", {}),
                processing_method="llm"
            )
        except Exception as e:
            print(f"LLM processing failed: {e}. Falling back to rule-based.")
            return self._process_rule_based(query)
    
    def _build_context(self, intent: str, entities: Dict, metrics: List) -> Dict[str, Any]:
        """Build contextual information for the query"""
        context = {
            "intent_category": self._categorize_intent(intent),
            "complexity": self._assess_complexity(intent, entities, metrics),
            "requires_data_fetch": len(metrics) > 0,
            "entities_count": len(entities),
            "metrics_count": len(metrics),
            "suggested_actions": self._suggest_actions(intent, metrics)
        }
        return context
    
    def _categorize_intent(self, intent: str) -> str:
        """Categorize intent into broader categories"""
        categories = {
            'trend': ['increase', 'decrease', 'growth', 'decline', 'trend'],
            'comparison': ['compare', 'versus', 'vs', 'difference', 'similar'],
            'analysis': ['analyze', 'breakdown', 'detail', 'explain', 'why'],
            'summary': ['summary', 'overview', 'total', 'aggregate'],
            'forecast': ['predict', 'forecast', 'expected', 'will', 'next']
        }
        
        intent_lower = intent.lower()
        for category, keywords in categories.items():
            if any(kw in intent_lower for kw in keywords):
                return category
        
        return "general"
    
    def _assess_complexity(self, intent: str, entities: Dict, metrics: List) -> str:
        """Assess query complexity"""
        score = len(entities) + len(metrics)
        
        if score == 0:
            return "simple"
        elif score <= 2:
            return "moderate"
        else:
            return "complex"
    
    def _suggest_actions(self, intent: str, metrics: List) -> List[str]:
        """Suggest actions based on intent"""
        actions = []
        
        if 'trend' in intent.lower():
            actions.append("Generate trend visualization")
        if 'compare' in intent.lower():
            actions.append("Create comparison report")
        if 'analyze' in intent.lower():
            actions.append("Provide detailed analysis")
        if metrics:
            actions.append(f"Fetch {', '.join(metrics)} data")
        
        if not actions:
            actions.append("Retrieve relevant information")
        
        return actions


class QueryUnderstanding:
    """Helper class for detailed query understanding"""
    
    @staticmethod
    def get_nlp_explanation(result: NLPResult) -> str:
        """Generate human-readable explanation of what was understood"""
        
        explanation = f"I understood you're asking about: {result.intent}.\n"
        
        if result.entities:
            entities_str = ", ".join([f"{k}: {v}" for k, v in result.entities.items()])
            explanation += f"Key entities: {entities_str}.\n"
        
        if result.time_reference:
            explanation += f"Time period: {result.time_reference}.\n"
        
        if result.metrics:
            explanation += f"Metrics of interest: {', '.join(result.metrics)}.\n"
        
        explanation += f"Confidence: {result.confidence * 100:.1f}%"
        
        return explanation


# Global NLP engine instance
nlp_engine = NLPEngine(use_llm=False)  # Set to True if you have LLM API key
