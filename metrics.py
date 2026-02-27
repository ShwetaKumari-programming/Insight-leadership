import time
from collections import deque

# Store last N requests
REQUEST_LOG = deque(maxlen=500)


def log_request(start_time, success=True):
    latency = (time.time() - start_time) * 1000  # ms
    REQUEST_LOG.append({
        "latency": latency,
        "success": success,
        "timestamp": time.time()
    })
