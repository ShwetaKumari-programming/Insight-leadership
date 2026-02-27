"""Question processor - handles analyzing and responding to user questions"""

import time
import re
from typing import Dict, Any

import pandas as pd

from analytics import analytics
from business import business_logic_router, insight_text_router
from nlp_layer import nlp_engine, QueryUnderstanding
from data_utils import load_transaction_data
from explainability_layer import ExplainabilityEngine


class QuestionProcessor:
    """Process user questions and generate intelligent responses"""
    
    def __init__(self):
        self.question_keywords = {
            'how': 'instructional',
            'what': 'definition',
            'why': 'explanation',
            'where': 'location',
            'when': 'temporal',
            'who': 'identity',
            'can': 'capability',
            'should': 'advice',
            'help': 'assistance',
            'problem': 'troubleshooting'
        }
        
        self.response_templates = {
            'instructional': "Here's how you can approach this: {}",
            'definition': "In simple terms: {}",
            'explanation': "The reason is: {}",
            'location': "You can find this at: {}",
            'temporal': "This happens at: {}",
            'identity': "This refers to: {}",
            'capability': "Yes, you can do this by: {}",
            'advice': "I would recommend: {}",
            'assistance': "I can help you with: {}",
            'troubleshooting': "Here's how to fix this: {}"
        }

        self.transaction_df = self._load_transaction_data()
        self.explainability_engine = ExplainabilityEngine()

    def _load_transaction_data(self):
        try:
            return load_transaction_data()
        except Exception:
            return None
    
    def process(self, question: str) -> Dict[str, Any]:
        """
        Process a user question and generate a response
        Returns dict with response, analysis, and processing info
        """
        start_time = time.time()
        
        # Validate input
        if not question or not isinstance(question, str):
            return {
                "response": "Please ask a valid question.",
                "success": False,
                "processing_time": 0,
                "question_type": "invalid",
                "nlp_result": None
            }
        
        # Clean question
        question = question.strip()
        
        # ===== NLP Layer Processing =====
        nlp_result = nlp_engine.process(question)
        nlp_explanation = QueryUnderstanding.get_nlp_explanation(nlp_result)
        
        # Analyze question (legacy)
        analysis = self._analyze_question(question)
        analysis['nlp_understanding'] = nlp_result.to_dict()
        
        # Generate response using NLP insights
        response = self._generate_response_with_nlp(question, analysis, nlp_result)

        business_result = None
        explanation_why = None
        if self.transaction_df is not None:
            business_result = business_logic_router(
                nlp_result.intent,
                nlp_result.entities or {},
                self.transaction_df,
            )
            analysis["business_result"] = business_result
            
            # ===== EXPLAINABILITY LAYER =====
            # Generate explanation for the business result
            if business_result and (not isinstance(business_result, dict) or 'error' not in business_result):
                try:
                    explanation_why = self._generate_explanation(
                        nlp_result.intent,
                        business_result,
                        nlp_result.entities or {}
                    )
                except Exception as e:
                    # If explanation generation fails, just continue without it
                    explanation_why = None
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log to analytics
        analytics.log_question(question, response, processing_time)
        
        return {
            "response": response,
            "success": True,
            "processing_time": round(processing_time * 1000, 2),  # milliseconds
            "question_type": analysis['type'],
            "analysis": analysis,
            "nlp_understanding": nlp_explanation,
            "business_result": business_result,
            "explanation_why": explanation_why,
            "timestamp": str(time.time())
        }
    
    def _analyze_question(self, question: str) -> Dict[str, Any]:
        """Analyze the question to understand its type and content"""
        question_lower = question.lower()
        
        # Determine question type
        question_type = 'general'
        for keyword, qtype in self.question_keywords.items():
            if question_lower.startswith(keyword):
                question_type = qtype
                break
        
        # Count words and characters
        word_count = len(question.split())
        char_count = len(question)
        
        # Check question mark
        has_question_mark = '?' in question
        
        # Extract key terms (words after keywords)
        key_terms = self._extract_key_terms(question)
        
        return {
            "type": question_type,
            "word_count": word_count,
            "character_count": char_count,
            "has_question_mark": has_question_mark,
            "key_terms": key_terms,
            "language_quality": self._assess_language_quality(question)
        }
    
    def _extract_key_terms(self, question: str) -> list:
        """Extract important terms from the question"""
        # Remove common words and get important nouns/verbs
        common_words = {'what', 'how', 'why', 'where', 'when', 'who', 'is', 'are', 'the', 'a', 'an', 'and', 'or'}
        words = [w.lower() for w in question.split() if w.lower() not in common_words and len(w) > 3]
        return words[:5]  # Return top 5 key terms
    
    def _assess_language_quality(self, question: str) -> str:
        """Assess the quality of the question language"""
        word_count = len(question.split())
        has_proper_punctuation = '?' in question or '.' in question
        
        if word_count < 2:
            return "too_short"
        elif word_count > 50:
            return "too_long"
        elif has_proper_punctuation:
            return "good"
        else:
            return "needs_punctuation"
    
    def _generate_response(self, question: str, analysis: Dict[str, Any]) -> str:
        """Generate an intelligent response based on question analysis"""
        question_type = analysis['type']
        key_terms = analysis['key_terms']
        
        # Select template based on question type
        template = self.response_templates.get(question_type, self.response_templates['general'])
        
        # Generate contextual response
        if key_terms:
            context = f"regarding {', '.join(key_terms)}"
            base_response = f"Great question about {context}! "
        else:
            base_response = "Good question! "
        
        # Add detailed response based on type
        detailed_response = self._create_detailed_response(question_type, analysis)
        
        return base_response + detailed_response
    
    def _generate_response_with_nlp(self, question: str, analysis: Dict[str, Any], nlp_result) -> str:
        """Generate response using NLP insights"""
        
        nlp_intent = nlp_result.intent
        nlp_metrics = nlp_result.metrics
        nlp_entities = nlp_result.entities
        time_ref = nlp_result.time_reference
        
        # Build response based on NLP understanding
        response_parts = []
        
        # Add understanding acknowledgment
        response_parts.append(f"I understand you're asking about {nlp_intent.replace('_', ' ')}.")
        
        # Add entity-based insights
        if nlp_metrics:
            metrics_str = ', '.join(nlp_metrics)
            response_parts.append(f"The key metrics involved are: {metrics_str}.")
        
        if nlp_entities and 'components' in nlp_entities:
            components_str = ', '.join(nlp_entities['components'])
            response_parts.append(f"This relates to: {components_str}.")
        
        if time_ref:
            response_parts.append(f"You're interested in the {time_ref}.")
        
        # Add detailed analysis
        detailed = self._create_detailed_response(analysis['type'], analysis)
        response_parts.append(detailed)
        
        # Add confidence indicator
        if nlp_result.confidence < 0.6:
            response_parts.append(f"\nNote: I'm {nlp_result.confidence * 100:.0f}% confident in this understanding. Please clarify if needed.")
        
        return " ".join(response_parts)
    
    def _create_detailed_response(self, question_type: str, analysis: Dict[str, Any]) -> str:
        """Create a detailed response based on question type"""
        responses = {
            'instructional': "Here's a step-by-step approach: First, understand the basics. Second, practice with examples. Third, refine your understanding through feedback. This method works well for most learning scenarios.",
            'definition': "This is a concept that involves multiple aspects. The core idea centers around understanding fundamentals, applying principles, and adapting to different contexts. It's important to grasp both the theoretical and practical dimensions.",
            'explanation': "The underlying reason is based on logical principles. When we analyze the factors involved, we see that cause and effect relationships form the basis. Understanding these connections helps clarify the 'why' behind things.",
            'location': "You can find information and resources in multiple places. Online platforms, documentation, community forums, and expert guides are all valuable resources. Choose based on your specific needs.",
            'temporal': "This typically occurs in a timeframe that depends on several factors. Preparation takes time, execution follows, and results manifest over a period. The exact timeline varies based on circumstances.",
            'identity': "This refers to something with distinct characteristics and properties. It has specific features that define it, set it apart from others, and make it recognizable. Understanding its nature helps in applying it correctly.",
            'capability': "Yes, absolutely! You can accomplish this through proper methods and tools. The process involves breaking it down into manageable steps. With practice and dedication, you'll master this skill.",
            'advice': "I would suggest a balanced approach. Consider your specific situation carefully. Plan ahead, take calculated steps, and be ready to adapt. Success comes from thoughtful action combined with flexibility.",
            'assistance': "I'm here to help you with this. The best approach is to break it into smaller parts. We can work through each section together. Feel free to ask follow-up questions.",
            'troubleshooting': "Here's how to approach this problem: Identify the root cause, document what you observe, check common solutions, and test systematically. This methodical approach usually reveals the answer quickly."
        }
        
        return responses.get(question_type, "That's an interesting question! Let me provide you with a comprehensive answer. The key is to understand the fundamentals while keeping practical applications in mind.")
    
    def _generate_explanation(self, intent: str, business_result: Dict[str, Any], entities: Dict[str, Any]) -> str:
        """Generate explanation for why the analysis result occurred"""
        try:
            # Map intent to appropriate explanation method
            if intent == "failure_analysis_weekend":
                # Use failure comparison explanation if result has the right structure
                if isinstance(business_result, dict) and 'failure_rate' in business_result:
                    explanation = self.explainability_engine.explain_failure_comparison(business_result)
                else:
                    explanation = insight_text_router(intent, business_result, entities)
            
            elif intent == "top_spending_age_group":
                # Use generic explanation for spending analysis
                explanation = self.explainability_engine.explain_failure_analysis(business_result)
            
            elif intent == "device_comparison":
                # Use generic explanation for device comparison
                explanation = self.explainability_engine.explain_performance(business_result)
            
            elif intent == "state_failure_rate":
                # Use system health explanation for state failures
                explanation = self.explainability_engine.explain_system_health(business_result)
            
            else:
                # For unknown intents, use the business insight router
                explanation = insight_text_router(intent, business_result, entities)
            
            return explanation if explanation else None
        
        except Exception as e:
            # If any error occurs during explanation generation, return None
            return None


# Global processor instance
processor = QuestionProcessor()
