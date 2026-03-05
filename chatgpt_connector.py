"""
ChatGPT Connector - Integrates OpenAI's GPT API for chat responses
"""
import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ChatGPTConnector:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
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
                print("ChatGPT connector initialized successfully with API key")
            except ImportError as e:
                self.available = False
                print(f"OpenAI package not installed: {e}")
            except Exception as e:
                self.available = False
                print(f"ChatGPT initialization error: {str(e)}")
        else:
            print("OPENAI_API_KEY environment variable not found")
    
    def ask(self, question: str, context: Optional[str] = None, history: Optional[List[Dict[str, Any]]] = None) -> dict:
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
            system_prompt = (
                "You are a helpful, conversational AI assistant. "
                "Answer based on the user's exact question and previous messages. "
                "If the question is about UPI/system analytics, provide clear actionable insights. "
                "If it is general, answer normally like ChatGPT."
            )
            
            if context:
                system_prompt += f"\n\nContext: {context}"
            
            messages = [{"role": "system", "content": system_prompt}]

            # Include recent conversation turns for true chat behavior.
            if history:
                for item in history[-12:]:
                    role = item.get("role")
                    content = str(item.get("content", "")).strip()
                    if role in {"user", "assistant"} and content:
                        messages.append({"role": role, "content": content})

            messages.append({"role": "user", "content": question})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
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
            print(f"ChatGPT API error: {str(e)}")
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


def ask_chatgpt(question: str, context: Optional[str] = None, history: Optional[List[Dict[str, Any]]] = None) -> dict:
    """Ask ChatGPT a question"""
    return chatgpt_connector.ask(question, context, history)
