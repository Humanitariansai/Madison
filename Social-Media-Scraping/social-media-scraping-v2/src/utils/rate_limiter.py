#!/usr/bin/env python3
"""
Rate limiting utility for API calls
"""
import time
from datetime import datetime, timedelta
from typing import Dict

class RateLimiter:
    def __init__(self):
        self.last_calls: Dict[str, datetime] = {}
        self.min_intervals = {
            'twitter': 1.0,  # 1 second between Twitter calls
            'reddit': 0.5,   # 0.5 seconds between Reddit calls
            'linkedin': 2.0, # 2 seconds between LinkedIn calls (more conservative)
        }
    
    def wait_if_needed(self, api_name: str):
        """Wait if needed to respect rate limits"""
        if api_name not in self.min_intervals:
            return
        
        min_interval = self.min_intervals[api_name]
        
        if api_name in self.last_calls:
            elapsed = (datetime.now() - self.last_calls[api_name]).total_seconds()
            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                print(f"⏳ Rate limiting: waiting {sleep_time:.1f}s for {api_name}")
                time.sleep(sleep_time)
        
        self.last_calls[api_name] = datetime.now()

# Global rate limiter instance
rate_limiter = RateLimiter()