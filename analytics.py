"""Analytics module for tracking questions and responses"""

import json
import os
from datetime import datetime
from typing import Dict, Any
from config import ANALYTICS_FILE, LOG_QUERIES


class Analytics:
    """Track and store analytics for user questions and responses"""
    
    def __init__(self):
        self.data = {
            "total_questions": 0,
            "total_responses": 0,
            "questions_log": [],
            "stats": {
                "total_characters_processed": 0,
                "average_question_length": 0,
                "most_common_words": {},
            }
        }
        self.load_analytics()
    
    def load_analytics(self):
        """Load analytics from file if it exists"""
        if os.path.exists(ANALYTICS_FILE):
            try:
                with open(ANALYTICS_FILE, 'r') as f:
                    self.data = json.load(f)
            except Exception as e:
                print(f"Error loading analytics: {e}")
    
    def save_analytics(self):
        """Save analytics to file"""
        try:
            with open(ANALYTICS_FILE, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving analytics: {e}")
    
    def log_question(self, question: str, response: str, processing_time: float) -> None:
        """Log a question and its response"""
        if not LOG_QUERIES:
            return
        
        self.data["total_questions"] += 1
        self.data["total_responses"] += 1
        
        # Update character processing stats
        self.data["stats"]["total_characters_processed"] += len(question)
        
        # Calculate average question length
        if self.data["total_questions"] > 0:
            self.data["stats"]["average_question_length"] = (
                self.data["stats"]["total_characters_processed"] / 
                self.data["total_questions"]
            )
        
        # Track most common words
        self._track_words(question)
        
        # Log the question and response
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "response": response,
            "processing_time_ms": round(processing_time * 1000, 2),
            "question_length": len(question),
            "response_length": len(response)
        }
        
        self.data["questions_log"].append(log_entry)
        
        # Keep only last 100 logs to avoid large files
        if len(self.data["questions_log"]) > 100:
            self.data["questions_log"] = self.data["questions_log"][-100:]
        
        self.save_analytics()
    
    def _track_words(self, text: str) -> None:
        """Track word frequency"""
        # Simple word tracking (lowercased, excluding common words)
        common_words = {'the', 'a', 'an', 'and', 'or', 'is', 'in', 'to', 'for', 'of'}
        words = text.lower().split()
        
        for word in words:
            # Clean word of punctuation
            word = ''.join(c for c in word if c.isalnum())
            
            if word and word not in common_words and len(word) > 2:
                self.data["stats"]["most_common_words"][word] = (
                    self.data["stats"]["most_common_words"].get(word, 0) + 1
                )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current analytics statistics"""
        return {
            "total_questions_processed": self.data["total_questions"],
            "total_responses_sent": self.data["total_responses"],
            "average_question_length": round(self.data["stats"]["average_question_length"], 2),
            "total_characters_processed": self.data["stats"]["total_characters_processed"],
            "top_words": dict(sorted(
                self.data["stats"]["most_common_words"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10])
        }
    
    def get_recent_questions(self, limit: int = 10) -> list:
        """Get recent questions"""
        return self.data["questions_log"][-limit:]


# Global analytics instance
analytics = Analytics()
