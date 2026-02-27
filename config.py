"""Configuration settings for the chat backend"""

import os
from datetime import datetime

# Server configuration
HOST = "127.0.0.1"
PORT = 8001
DEBUG = True

# Analytics configuration
ANALYTICS_FILE = "analytics.json"
LOG_QUERIES = True

# Response configuration
DEFAULT_RESPONSE_DELAY = 1.0  # seconds
SHOW_PROCESSING_TIME = True
