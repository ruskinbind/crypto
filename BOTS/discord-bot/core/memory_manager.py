"""
╔══════════════════════════════════════════════════════════════╗
║              🤖 KAZUHA VIP DISCORD AUTO BOT                  ║
║                  Created by Kazuha VIP Only                  ║
╚══════════════════════════════════════════════════════════════╝
Conversation Memory Management
"""

import json
import aiofiles
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from collections import defaultdict

from config.settings import Settings


class MemoryManager:
    """Manages conversation memory and user interaction tracking"""
    
    def __init__(self, identity_name: str):
        self.identity_name = identity_name
        self.memory_file = Settings.MEMORY_DIR / f"{identity_name}_memory.json"
        self.user_memory: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.reply_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.last_reply_time: Dict[str, Dict[str, datetime]] = defaultdict(dict)
        self._loaded = False
        
    async def load(self) -> bool:
        """Load memory from file"""
        Settings.ensure_directories()
        
        if self.memory_file.exists():
            try:
                async with aiofiles.open(self.memory_file, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    
                    # Restore user memory
                    self.user_memory = defaultdict(dict, data.get('user_memory', {}))
                    
                    # Restore reply counts (reset daily)
                    stored_date = data.get('date', '')
                    today = datetime.now().strftime('%Y-%m-%d')
                    
                    if stored_date == today:
                        self.reply_counts = defaultdict(
                            lambda: defaultdict(int),
                            {k: defaultdict(int, v) for k, v in data.get('reply_counts', {}).items()}
                        )
                    
            except (json.JSONDecodeError, KeyError):
                pass
        
        self._loaded = True
        return True
    
    async def save(self) -> bool:
        """Save memory to file"""
        data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'user_memory': dict(self.user_memory),
            'reply_counts': {k: dict(v) for k, v in self.reply_counts.items()}
        }
        
        async with aiofiles.open(self.memory_file, 'w') as f:
            await f.write(json.dumps(data, indent=2, default=str))
        
        return True
    
    def get_user_info(self, server_id: str, user_id: str) -> Dict[str, Any]:
        """Get stored info about a user"""
        key = f"{server_id}_{user_id}"
        return self.user_memory.get(key, {})
    
    def update_user_info(self, server_id: str, user_id: str, 
                        summary: str, sentiment: str = "neutral"):
        """Update user interaction summary"""
        key = f"{server_id}_{user_id}"
        
        if key not in self.user_memory:
            self.user_memory[key] = {
                'first_seen': datetime.now().isoformat(),
                'interaction_count': 0
            }
        
        self.user_memory[key].update({
            'summary': summary,
            'sentiment': sentiment,
            'last_interaction': datetime.now().isoformat(),
            'interaction_count': self.user_memory[key].get('interaction_count', 0) + 1
        })
    
    def get_reply_count(self, server_id: str, user_id: str) -> int:
        """Get number of times we've replied to user today"""
        return self.reply_counts[server_id].get(user_id, 0)
    
    def increment_reply_count(self, server_id: str, user_id: str):
        """Increment reply count for user"""
        self.reply_counts[server_id][user_id] += 1
        self.last_reply_time[server_id][user_id] = datetime.now()
    
    def can_reply_to_user(self, server_id: str, user_id: str, 
                          max_replies: int = 3, 
                          cooldown_minutes: int = 30) -> tuple[bool, str]:
        """Check if we can reply to this user"""
        reply_count = self.get_reply_count(server_id, user_id)
        
        if reply_count >= max_replies:
            return False, f"Max replies ({max_replies}) reached for this user today"
        
        # Check cooldown
        last_time = self.last_reply_time.get(server_id, {}).get(user_id)
        if last_time:
            elapsed = (datetime.now() - last_time).total_seconds()
            if elapsed < cooldown_minutes * 60:
                remaining = int((cooldown_minutes * 60 - elapsed) / 60)
                return False, f"Cooldown active ({remaining}m remaining)"
        
        return True, f"Can reply ({reply_count + 1}/{max_replies})"
    
    def cleanup_old_entries(self, days: int = 7):
        """Remove entries older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        keys_to_remove = []
        for key, info in self.user_memory.items():
            last_interaction = info.get('last_interaction', '')
            if last_interaction and last_interaction < cutoff_str:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.user_memory[key]