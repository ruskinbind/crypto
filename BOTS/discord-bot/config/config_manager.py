"""
╔══════════════════════════════════════════════════════════════╗
║              🤖 KAZUHA VIP DISCORD AUTO BOT                  ║
║                  Created by Kazuha VIP Only                  ║
╚══════════════════════════════════════════════════════════════╝
Configuration Manager Module
"""

import json
import aiofiles
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .settings import Settings


class ConfigManager:
    """Manages bot configuration with async file operations"""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.api_keys: List[str] = []
        self.blocked_keys: Dict[str, datetime] = {}
        self._loaded = False
        
    async def load(self) -> bool:
        """Load configuration from files"""
        Settings.ensure_directories()
        
        # Load main config
        if Settings.CONFIG_FILE.exists():
            async with aiofiles.open(Settings.CONFIG_FILE, 'r') as f:
                content = await f.read()
                self.config = json.loads(content)
        else:
            self.config = self._get_default_config()
            await self.save()
            
        # Load API keys
        if Settings.API_KEYS_FILE.exists():
            async with aiofiles.open(Settings.API_KEYS_FILE, 'r') as f:
                content = await f.read()
                self.api_keys = [
                    key.strip() for key in content.splitlines() 
                    if key.strip() and not key.startswith('#')
                ]
        
        self._loaded = True
        return True
    
    async def save(self) -> bool:
        """Save configuration to file"""
        async with aiofiles.open(Settings.CONFIG_FILE, 'w') as f:
            await f.write(json.dumps(self.config, indent=4))
        return True
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration structure"""
        return {
            "global": {
                "maxServersActive": 10,
                "maxChannelsPerServer": 3,
                "dailyMessageCap": 25,
                "hourlyReplyCap": 5,
                "randomIntervalJitter": 5,
                "contextHistoryDepth": 10,
                "typingDelayRange": [1, 3],
                "activeHours": list(range(9, 23)),
                "ignoreProbability": 0.3,
                "maxRepliesPerUser": 3,
                "userReplyCooldownMinutes": 30
            },
            "identities": []
        }
    
    @property
    def global_settings(self) -> Dict[str, Any]:
        """Get global settings"""
        return self.config.get("global", {})
    
    @property
    def identities(self) -> List[Dict[str, Any]]:
        """Get all configured identities"""
        return self.config.get("identities", [])
    
    def get_identity(self, display_name: str) -> Optional[Dict[str, Any]]:
        """Get identity by display name"""
        for identity in self.identities:
            if identity.get("displayName") == display_name:
                return identity
        return None
    
    def add_identity(self, identity: Dict[str, Any]) -> bool:
        """Add new identity configuration"""
        if "identities" not in self.config:
            self.config["identities"] = []
        self.config["identities"].append(identity)
        return True
    
    def update_identity(self, display_name: str, updates: Dict[str, Any]) -> bool:
        """Update existing identity"""
        for i, identity in enumerate(self.identities):
            if identity.get("displayName") == display_name:
                self.config["identities"][i].update(updates)
                return True
        return False
    
    def get_active_api_key(self) -> Optional[str]:
        """Get an available API key (not blocked)"""
        now = datetime.now()
        
        # Clean expired blocks
        expired = [
            key for key, blocked_time in self.blocked_keys.items()
            if (now - blocked_time).total_seconds() > Settings.API_KEY_COOLDOWN_MINUTES * 60
        ]
        for key in expired:
            del self.blocked_keys[key]
        
        # Find available key
        for key in self.api_keys:
            if key not in self.blocked_keys:
                return key
        return None
    
    def block_api_key(self, key: str):
        """Block an API key temporarily"""
        self.blocked_keys[key] = datetime.now()
    
    def remove_api_key(self, key: str):
        """Remove invalid API key permanently"""
        if key in self.api_keys:
            self.api_keys.remove(key)
    
    def get_api_key_status(self) -> Dict[str, int]:
        """Get API key statistics"""
        return {
            "total": len(self.api_keys),
            "active": len(self.api_keys) - len(self.blocked_keys),
            "blocked": len(self.blocked_keys)
        }