"""
╔══════════════════════════════════════════════════════════════╗
║              🤖 KAZUHA VIP DISCORD AUTO BOT                  ║
║                  Created by Kazuha VIP Only                  ║
╚══════════════════════════════════════════════════════════════╝
Utility Helper Functions
"""

import random
import asyncio
from datetime import datetime
from typing import List, Optional


class Helpers:
    """Collection of utility helper functions"""
    
    @staticmethod
    def is_active_hour(active_hours: List[int]) -> bool:
        """Check if current hour is in active hours"""
        current_hour = datetime.now().hour
        return current_hour in active_hours
    
    @staticmethod
    def get_random_interval(base_minutes: int, jitter: int = 5) -> float:
        """Get randomized interval in seconds"""
        total_minutes = base_minutes + random.uniform(0, jitter)
        return total_minutes * 60
    
    @staticmethod
    def get_typing_delay(delay_range: List[int]) -> float:
        """Get random typing delay"""
        min_delay, max_delay = delay_range
        return random.uniform(min_delay, max_delay)
    
    @staticmethod
    def should_ignore(probability: float) -> bool:
        """Determine if message should be ignored based on probability"""
        return random.random() < probability
    
    @staticmethod
    def add_human_typo(text: str, probability: float = 0.05) -> str:
        """Occasionally add a human-like typo"""
        if random.random() > probability or len(text) < 10:
            return text
        
        # Simple typo: swap two adjacent characters
        pos = random.randint(1, len(text) - 2)
        chars = list(text)
        chars[pos], chars[pos + 1] = chars[pos + 1], chars[pos]
        return ''.join(chars)
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 50) -> str:
        """Truncate text for display"""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
    
    @staticmethod
    async def random_delay(min_seconds: float = 1, max_seconds: float = 3):
        """Add random delay for human-like behavior"""
        await asyncio.sleep(random.uniform(min_seconds, max_seconds))
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format seconds into readable duration"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"