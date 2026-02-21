"""
╔══════════════════════════════════════════════════════════════╗
║              🤖 KAZUHA VIP DISCORD AUTO BOT                  ║
║                  Created by Kazuha VIP Only                  ║
╚══════════════════════════════════════════════════════════════╝
Identity and Discord Client Management
"""

import discord
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from config.config_manager import ConfigManager


class BotIdentity:
    """Represents a single bot identity/account"""
    
    def __init__(self, config: Dict[str, Any]):
        self.display_name = config.get('displayName', 'Unknown')
        self.token = config.get('discordToken', '')
        self.persona = config.get('persona', self._default_persona())
        self.servers = config.get('servers', {})
        
        self.client: Optional[discord.Client] = None
        self.connected = False
        self.user: Optional[discord.User] = None
        
    def _default_persona(self) -> Dict[str, Any]:
        return {
            'tone': 'casual',
            'maxWords': 25,
            'emojiRate': 0.2,
            'avoidTopics': [],
            'messageLengthRange': [10, 50]
        }
    
    async def connect(self) -> bool:
        """Connect to Discord"""
        if self.connected:
            return True
        
        self.client = discord.Client()
        
        @self.client.event
        async def on_ready():
            self.connected = True
            self.user = self.client.user
        
        try:
            # Start client in background
            asyncio.create_task(self.client.start(self.token))
            
            # Wait for connection
            for _ in range(30):
                if self.connected:
                    return True
                await asyncio.sleep(1)
            
            return False
            
        except Exception as e:
            print(f"Connection error for {self.display_name}: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Discord"""
        if self.client:
            await self.client.close()
        self.connected = False
    
    def get_enabled_servers(self) -> List[Dict[str, Any]]:
        """Get list of enabled server configurations"""
        enabled = []
        for server_id, config in self.servers.items():
            if config.get('enabled', False):
                enabled.append({
                    'id': server_id,
                    **config
                })
        return enabled
    
    def get_server_config(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for specific server"""
        return self.servers.get(server_id)


class IdentityManager:
    """Manages multiple bot identities"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.identities: Dict[str, BotIdentity] = {}
        
    async def load_identities(self) -> int:
        """Load all identities from config"""
        for identity_config in self.config.identities:
            name = identity_config.get('displayName', '')
            if name:
                self.identities[name] = BotIdentity(identity_config)
        
        return len(self.identities)
    
    async def connect_all(self) -> Dict[str, bool]:
        """Connect all identities"""
        results = {}
        for name, identity in self.identities.items():
            results[name] = await identity.connect()
        return results
    
    async def disconnect_all(self):
        """Disconnect all identities"""
        for identity in self.identities.values():
            await identity.disconnect()
    
    def get_identity(self, name: str) -> Optional[BotIdentity]:
        """Get identity by name"""
        return self.identities.get(name)
    
    def get_all_identities(self) -> List[BotIdentity]:
        """Get all loaded identities"""
        return list(self.identities.values())
    
    def get_identity_names(self) -> List[str]:
        """Get list of identity names"""
        return list(self.identities.keys())
    
    async def add_identity(self, name: str, token: str, 
                           persona: Dict[str, Any] = None) -> bool:
        """Add new identity"""
        identity_config = {
            'displayName': name,
            'discordToken': token,
            'persona': persona or {},
            'servers': {}
        }
        
        self.config.add_identity(identity_config)
        await self.config.save()
        
        self.identities[name] = BotIdentity(identity_config)
        return True
    
    def update_server_config(self, identity_name: str, 
                             server_id: str, config: Dict[str, Any]) -> bool:
        """Update server configuration for identity"""
        identity = self.identities.get(identity_name)
        if not identity:
            return False
        
        identity.servers[server_id] = config
        
        # Update in config manager
        self.config.update_identity(identity_name, {'servers': identity.servers})
        return True