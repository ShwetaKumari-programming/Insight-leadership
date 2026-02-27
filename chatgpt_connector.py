"""
ChatGPT Connector - Integrates OpenAI's GPT API for chat responses
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ChatGPTConnector:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = 'gpt-3.5-turbo'
        self.available = False
        self.client = None
        
        if self.api_key:
            try:
                from openai import OpenAI
                # Initialize client with just the API key and timeout
                self.client = OpenAI(
                    api_key=self.api_key,
                    timeout=30.0,
                )
                self.available = True
                print("✅ ChatGPT connector initialized successfully with API key")
            except ImportError as e:
                self.available = False
                print(f"⚠️ OpenAI package not installed: {e}")
            except Exception as e:
                self.available = False
                print(f"⚠️ ChatGPT initialization error: {str(e)}")
                print(f"   API Key starts with: {self.api_key[:20]}..." if self.api_key else "   No API key found")
        else:
            print("⚠️ OPENAI_API_KEY environment variable not found")
    
    def ask(self, question: str, context: Optional[str] = None) -> dict:
        """
        Ask ChatGPT a question with optional context about transaction data
        
        Args:
            question: User's question
            context: Optional transaction data context
            
        Returns:
            dict with response, success status, model info
        """
        if not self.available or not self.client:
            return {
                "success": False,
                "response": "ChatGPT not configured. Set OPENAI_API_KEY environment variable.",
                "model": "none"
            }
        
        try:
            system_prompt = "You are an analytics assistant helping analyze transaction data and system performance. Provide clear, actionable insights."
            
            if context:
                system_prompt += f"\n\nContext: {context}"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            
            return {
                "success": True,
                "response": answer,
                "model": self.model,
                "tokens_used": response.usage.total_tokens
            }
        
        except Exception as e:
            print(f"❌ ChatGPT API Error: {str(e)}")
            return {
                "success": False,
                "response": f"ChatGPT error: {str(e)}",
                "model": self.model,
                "error": str(e)
            }


# Global connector instance
chatgpt_connector = ChatGPTConnector()


def is_chatgpt_available() -> bool:
    """Check if ChatGPT is available"""
    return chatgpt_connector.available


def ask_chatgpt(question: str, context: Optional[str] = None) -> dict:
    """Ask ChatGPT a question"""
    return chatgpt_connector.ask(question, context)
