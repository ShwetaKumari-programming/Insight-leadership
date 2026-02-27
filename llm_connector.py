"""
LLM Connector - Connect to LLM APIs (OpenAI, Gemini, LLaMA)
Optional module for advanced NLP processing
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """LLM Configuration"""
    provider: str
    api_key: Optional[str] = None
    model: str = ""
    temperature: float = 0.3
    max_tokens: int = 500


class LLMConnector:
    """Connect to Language Models for natural language understanding"""
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        """
        Initialize LLM Connector
        
        Args:
            provider: LLM provider ('openai', 'gemini', 'llama')
            api_key: API key (defaults to environment variable)
        """
        self.provider = provider.lower()
        
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv(f'{provider.upper()}_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                f"API key not found. Set {provider.upper()}_API_KEY environment variable "
                f"or pass api_key parameter."
            )
        
        # Initialize provider-specific client
        if self.provider == "openai":
            self._init_openai()
        elif self.provider == "gemini":
            self._init_gemini()
        elif self.provider == "llama":
            self._init_llama()
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            import openai
            openai.api_key = self.api_key
            self.client = openai
            self.model = "gpt-3.5-turbo"
        except ImportError:
            raise ImportError("OpenAI library not installed. Install with: pip install openai")
    
    def _init_gemini(self):
        """Initialize Google Gemini client"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai
            self.model = "gemini-pro"
        except ImportError:
            raise ImportError("Google generativeai library not installed. Install with: pip install google-generativeai")
    
    def _init_llama(self):
        """Initialize LLaMA client (Ollama or LM Studio)"""
        # For local LLaMA, using Ollama or LM Studio
        self.client = None
        self.model = "llama2"
    
    def extract_understanding(self, query: str) -> Dict[str, Any]:
        """
        Extract understanding from query using LLM
        
        Args:
            query: User's natural language query
            
        Returns:
            Dictionary with intent, entities, metrics, etc.
        """
        if self.provider == "openai":
            return self._extract_openai(query)
        elif self.provider == "gemini":
            return self._extract_gemini(query)
        elif self.provider == "llama":
            return self._extract_llama(query)
    
    def _extract_openai(self, query: str) -> Dict[str, Any]:
        """Extract using OpenAI"""
        prompt = self._build_extraction_prompt(query)
        
        try:
            response = self.client.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at understanding user queries and extracting structured information. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse response
            import json
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            return result
        
        except Exception as e:
            print(f"OpenAI extraction failed: {e}")
            raise
    
    def _extract_gemini(self, query: str) -> Dict[str, Any]:
        """Extract using Google Gemini"""
        prompt = self._build_extraction_prompt(query)
        
        try:
            model = self.client.GenerativeModel(self.model)
            response = model.generate_content(prompt)
            
            # Parse response
            import json
            result = json.loads(response.text)
            return result
        
        except Exception as e:
            print(f"Gemini extraction failed: {e}")
            raise
    
    def _extract_llama(self, query: str) -> Dict[str, Any]:
        """Extract using LLaMA (local)"""
        import requests
        
        prompt = self._build_extraction_prompt(query)
        
        try:
            # Assuming Ollama running on localhost:11434
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": self.model, "prompt": prompt}
            )
            
            # Parse response
            import json
            result = json.loads(response.text)
            return result
        
        except Exception as e:
            print(f"LLaMA extraction failed: {e}")
            raise
    
    def _build_extraction_prompt(self, query: str) -> str:
        """Build extraction prompt for LLM"""
        prompt = f"""
Analyze this user query and extract structured information:

Query: "{query}"

Please respond with ONLY a JSON object (no markdown, no explanation) with these fields:
{{
    "intent": "main intent of the query (e.g., 'trend_analysis', 'comparison', 'failure_analysis')",
    "confidence": 0.0-1.0 confidence score,
    "entities": {{
        "metrics": ["metric1", "metric2"],
        "components": ["component1", "component2"],
        "values": [{"value": 123, "unit": "%"}]
    }},
    "time_reference": "time period mentioned (e.g., 'last weekend', 'past week')",
    "metrics": ["list", "of", "metrics"],
    "context": {{
        "query_length": word count,
        "has_comparison": true/false,
        "has_time_reference": true/false
    }}
}}

Make sure the response is valid JSON that can be parsed.
"""
        return prompt
    
    @staticmethod
    def is_available(provider: str = "openai") -> bool:
        """Check if LLM provider is available"""
        try:
            api_key = os.getenv(f'{provider.upper()}_API_KEY')
            return bool(api_key)
        except:
            return False


# Helper function to test LLM connection
def test_llm_connection(provider: str = "openai") -> bool:
    """Test if LLM connection works"""
    try:
        connector = LLMConnector(provider=provider)
        result = connector.extract_understanding("Why did failures increase last weekend?")
        return bool(result)
    except Exception as e:
        print(f"LLM connection test failed: {e}")
        return False
