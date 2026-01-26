#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     ██╗  ██╗ █████╗ ███████╗██╗   ██╗██╗  ██╗ █████╗     ██╗   ██╗██╗██████╗ ║
║     ██║ ██╔╝██╔══██╗╚══███╔╝██║   ██║██║  ██║██╔══██╗    ██║   ██║██║██╔══██╗║
║     █████╔╝ ███████║  ███╔╝ ██║   ██║███████║███████║    ██║   ██║██║██████╔╝║
║     ██╔═██╗ ██╔══██║ ███╔╝  ██║   ██║██╔══██║██╔══██║    ╚██╗ ██╔╝██║██╔═══╝ ║
║     ██║  ██╗██║  ██║███████╗╚██████╔╝██║  ██║██║  ██║     ╚████╔╝ ██║██║     ║
║     ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝      ╚═══╝  ╚═╝╚═╝     ║
║                                                                              ║
║                    🤖 DISCORD AUTO BOT - VIP EDITION 🤖                      ║
║                         Created by Kazuha VIP Only                           ║
║                              Version 3.0.0                                   ║
║                                                                              ║
║  Features:                                                                   ║
║  ✅ Daily Check-in     ✅ Role Claim      ✅ Anti-Spam                       ║
║  ✅ Smart Delays       ✅ Multi-Server    ✅ Contribution Focus              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import sys
import json
import random
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from pathlib import Path

try:
    import questionary
    from questionary import Style
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
    import aiofiles
    import aiohttp
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: pip install questionary rich aiofiles aiohttp discord.py-self groq")
    sys.exit(1)

try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("Warning: groq not installed. AI features disabled.")

try:
    import discord
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    print("Error: discord.py-self not installed!")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
# SETTINGS - ANTI-SPAM + ROLE FOCUS
# ═══════════════════════════════════════════════════════════════════════════════

class Settings:
    """Global settings - Created by Kazuha VIP Only"""
    
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    MEMORY_DIR = DATA_DIR / "memory"
    CONFIG_FILE = DATA_DIR / "bot_config.json"
    API_KEYS_FILE = DATA_DIR / "groq_api_keys.txt"
    
    BOT_NAME = "Kazuha VIP Bot"
    BOT_VERSION = "3.0.0"
    CREATED_BY = "Kazuha VIP Only"
    
    # AI Model - Fast & Free
    AI_MODEL = "llama-3.1-8b-instant"
    AI_MAX_TOKENS = 80
    AI_TEMPERATURE = 0.85
    
    API_KEY_COOLDOWN_MINUTES = 30
    
    # ╔════════════════════════════════════════════════════════════╗
    # ║  🛡️ ANTI-SPAM SETTINGS                                    ║
    # ╚════════════════════════════════════════════════════════════╝
    MIN_DELAY_BETWEEN_REPLIES = 8      # Minimum 8 seconds between replies
    MAX_DELAY_BETWEEN_REPLIES = 20     # Maximum 20 seconds between replies
    MAX_REPLIES_PER_CYCLE = 2          # Max 2 replies per check cycle
    CYCLE_INTERVAL_SECONDS = 60        # Check every 60 seconds
    MAX_REPLIES_PER_HOUR = 15          # Max 15 replies per hour
    MAX_REPLIES_PER_SERVER_HOUR = 8    # Max 8 replies per server per hour
    
    # Role Keywords to look for in announcements
    ROLE_KEYWORDS = [
        "claim", "role", "react", "click", "verify", "check-in",
        "checkin", "daily", "claim role", "get role", "new role",
        "airdrop", "eligible", "whitelist", "wl", "og", "early",
        "✅", "🎉", "🔔", "📢", "🎁", "💎"
    ]
    
    # Reaction emojis for role claim
    ROLE_REACTIONS = ["✅", "🎉", "👍", "💎", "🔥", "✨", "🙋", "🙋‍♂️", "🙋‍♀️"]
    
    # Skip these low value messages
    LOW_VALUE_PATTERNS = [
        r'^\.+$',           # Just dots
        r'^!+$',            # Just exclamations
        r'^\?+$',           # Just question marks
        r'^(ok|k|yes|no|ye|na|hm+|ah+|oh+)$',
        r'^(lol|lmao|haha|hehe|xd|rofl)$',
        r'^(gm|gn|hi|hey|hello|bye)$',  # Will handle GM separately
        r'^(ty|thx|thanks|thank you|np|yw)$',
        r'^<@!?\d+>$',      # Just a mention
        r'^<#\d+>$',        # Just a channel mention
    ]
    
    BLACKLIST_KEYWORDS = ["nsfw", "porn", "xxx", "nude", "scam", "hack", "crack"]
    
    @classmethod
    def ensure_directories(cls):
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.MEMORY_DIR.mkdir(exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# LOGGER - DETAILED OUTPUT
# ═══════════════════════════════════════════════════════════════════════════════

class Logger:
    """Rich console logging with detailed output"""
    
    def __init__(self):
        self.console = Console()
    
    def banner(self):
        banner_text = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     ██╗  ██╗ █████╗ ███████╗██╗   ██╗██╗  ██╗ █████╗     ██╗   ██╗██╗██████╗ ║
║     ██║ ██╔╝██╔══██╗╚══███╔╝██║   ██║██║  ██║██╔══██╗    ██║   ██║██║██╔══██╗║
║     █████╔╝ ███████║  ███╔╝ ██║   ██║███████║███████║    ██║   ██║██║██████╔╝║
║     ██╔═██╗ ██╔══██║ ███╔╝  ██║   ██║██╔══██║██╔══██║    ╚██╗ ██╔╝██║██╔═══╝ ║
║     ██║  ██╗██║  ██║███████╗╚██████╔╝██║  ██║██║  ██║     ╚████╔╝ ██║██║     ║
║     ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝      ╚═══╝  ╚═╝╚═╝     ║
║                                                                              ║
║                    🤖 DISCORD AUTO BOT - VIP EDITION 🤖                     ║
║                         Created by Kazuha VIP Only                           ║
║                              Version 1.0 (beta)                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        self.console.print(Text(banner_text, style="bold cyan"))
    
    def status_panel(self, accounts: int, api_keys: dict, features: list):
        table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("📦 Accounts", str(accounts))
        table.add_row("🔑 API Keys", f"{api_keys['total']} total ({api_keys['active']} active)")
        table.add_row("🤖 AI Model", Settings.AI_MODEL)
        table.add_row("⏱️ Delay", f"{Settings.MIN_DELAY_BETWEEN_REPLIES}-{Settings.MAX_DELAY_BETWEEN_REPLIES}s")
        table.add_row("🛡️ Max/Hour", f"{Settings.MAX_REPLIES_PER_HOUR} replies")
        table.add_row("✨ Features", " | ".join(features))
        
        panel = Panel(table, title="[bold white]✓ System Status[/bold white]", 
                     border_style="green", box=box.ROUNDED)
        self.console.print(panel)
    
    def info(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[dim]{timestamp}[/dim] [blue]ℹ️[/blue] [white]{message}[/white]")
    
    def success(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[dim]{timestamp}[/dim] [bold green]✅[/bold green] [green]{message}[/green]")
    
    def warning(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[dim]{timestamp}[/dim] [bold yellow]⚠️[/bold yellow] [yellow]{message}[/yellow]")
    
    def error(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[dim]{timestamp}[/dim] [bold red]❌[/bold red] [red]{message}[/red]")
    
    def debug(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[dim]{timestamp}[/dim] [magenta]🔍[/magenta] [dim]{message}[/dim]")
    
    def chat(self, server: str, channel: str, author: str, content: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        content_short = content[:40] + "..." if len(content) > 40 else content
        self.console.print(
            f"[dim]{timestamp}[/dim] [cyan]💬[/cyan] "
            f"[yellow]{server}[/yellow] → [magenta]#{channel}[/magenta] "
            f"[white]@{author}:[/white] [dim]{content_short}[/dim]"
        )
    
    def reply_sent(self, server: str, channel: str, reply: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        reply_short = reply[:40] + "..." if len(reply) > 40 else reply
        self.console.print(
            f"[dim]{timestamp}[/dim] [green]✅ REPLIED[/green] "
            f"[yellow]{server}[/yellow] → [magenta]#{channel}[/magenta]: "
            f"[white]{reply_short}[/white]"
        )
    
    def role_claim(self, server: str, channel: str, action: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(
            f"[dim]{timestamp}[/dim] [bold cyan]🎯 ROLE[/bold cyan] "
            f"[yellow]{server}[/yellow] → [magenta]#{channel}[/magenta]: "
            f"[green]{action}[/green]"
        )
    
    def daily_checkin(self, server: str, channel: str, status: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(
            f"[dim]{timestamp}[/dim] [bold yellow]📅 CHECK-IN[/bold yellow] "
            f"[yellow]{server}[/yellow] → [magenta]#{channel}[/magenta]: "
            f"[green]{status}[/green]"
        )
    
    def skip(self, reason: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[dim]{timestamp}[/dim] [yellow]⏭️[/yellow] [dim]{reason}[/dim]")
    
    def delay(self, seconds: int, reason: str = "Anti-spam"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(
            f"[dim]{timestamp}[/dim] [blue]⏳ DELAY[/blue] "
            f"[dim]Waiting {seconds}s ({reason})[/dim]"
        )
    
    def cycle_start(self, server: str, channels: int):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(
            f"\n[dim]{timestamp}[/dim] [bold cyan]🔄 CYCLE START[/bold cyan] "
            f"[yellow]{server}[/yellow] ({channels} channels)"
        )
    
    def cycle_end(self, replies: int, next_cycle: int):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(
            f"[dim]{timestamp}[/dim] [bold cyan]🔄 CYCLE END[/bold cyan] "
            f"[green]{replies} replies sent[/green] | "
            f"[dim]Next cycle in {next_cycle}s[/dim]\n"
        )
    
    def separator(self):
        self.console.print("[dim]" + "─" * 70 + "[/dim]")


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class ConfigManager:
    """Manages bot configuration"""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.api_keys: List[str] = []
        self.blocked_keys: Dict[str, datetime] = {}
    
    async def load(self) -> bool:
        Settings.ensure_directories()
        
        if Settings.CONFIG_FILE.exists():
            async with aiofiles.open(Settings.CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.config = json.loads(await f.read())
        else:
            self.config = self._default_config()
            await self.save()
        
        if Settings.API_KEYS_FILE.exists():
            async with aiofiles.open(Settings.API_KEYS_FILE, 'r', encoding='utf-8') as f:
                self.api_keys = [k.strip() for k in (await f.read()).splitlines() 
                               if k.strip() and not k.startswith('#')]
        return True
    
    async def save(self) -> bool:
        async with aiofiles.open(Settings.CONFIG_FILE, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(self.config, indent=4, ensure_ascii=False))
        return True
    
    def _default_config(self) -> Dict:
        return {
            "global": {
                "cycleIntervalSeconds": 60,
                "maxRepliesPerCycle": 2,
                "maxRepliesPerHour": 15,
                "delayBetweenReplies": [8, 20],
                "activeHours": list(range(0, 24)),
                "enableRoleClaim": True,
                "enableDailyCheckin": True,
                "enableAIChat": True
            },
            "identities": []
        }
    
    @property
    def global_settings(self) -> Dict: 
        return self.config.get("global", {})
    
    @property
    def identities(self) -> List[Dict]: 
        return self.config.get("identities", [])
    
    def get_identity(self, name: str) -> Optional[Dict]:
        return next((i for i in self.identities if i.get("displayName") == name), None)
    
    def add_identity(self, identity: Dict):
        if "identities" not in self.config:
            self.config["identities"] = []
        self.config["identities"].append(identity)
    
    def update_identity(self, name: str, updates: Dict):
        for i, identity in enumerate(self.identities):
            if identity.get("displayName") == name:
                self.config["identities"][i].update(updates)
                return True
        return False
    
    def get_active_api_key(self) -> Optional[str]:
        now = datetime.now()
        # Clean expired blocks
        self.blocked_keys = {k: v for k, v in self.blocked_keys.items() 
                           if (now - v).seconds < Settings.API_KEY_COOLDOWN_MINUTES * 60}
        return next((k for k in self.api_keys if k not in self.blocked_keys), None)
    
    def block_api_key(self, key: str):
        self.blocked_keys[key] = datetime.now()
    
    def get_api_key_status(self) -> Dict:
        return {
            "total": len(self.api_keys),
            "active": len(self.api_keys) - len(self.blocked_keys),
            "blocked": len(self.blocked_keys)
        }


# ═══════════════════════════════════════════════════════════════════════════════
# RATE LIMITER - ANTI-SPAM
# ═══════════════════════════════════════════════════════════════════════════════

class RateLimiter:
    """Tracks and limits reply rates to prevent spam"""
    
    def __init__(self):
        self.hourly_replies: Dict[str, List[datetime]] = {}  # server_id -> timestamps
        self.global_replies: List[datetime] = []
        self.last_reply_time: Optional[datetime] = None
    
    def can_reply(self, server_id: str) -> tuple:
        """Check if we can reply (returns bool, reason)"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        # Clean old entries
        self.global_replies = [t for t in self.global_replies if t > hour_ago]
        if server_id in self.hourly_replies:
            self.hourly_replies[server_id] = [t for t in self.hourly_replies[server_id] if t > hour_ago]
        
        # Check global limit
        if len(self.global_replies) >= Settings.MAX_REPLIES_PER_HOUR:
            return False, f"Global limit ({Settings.MAX_REPLIES_PER_HOUR}/hr)"
        
        # Check server limit
        server_count = len(self.hourly_replies.get(server_id, []))
        if server_count >= Settings.MAX_REPLIES_PER_SERVER_HOUR:
            return False, f"Server limit ({Settings.MAX_REPLIES_PER_SERVER_HOUR}/hr)"
        
        return True, "OK"
    
    def record_reply(self, server_id: str):
        """Record a reply was sent"""
        now = datetime.now()
        self.global_replies.append(now)
        if server_id not in self.hourly_replies:
            self.hourly_replies[server_id] = []
        self.hourly_replies[server_id].append(now)
        self.last_reply_time = now
    
    def get_delay(self) -> int:
        """Get random delay between replies"""
        return random.randint(Settings.MIN_DELAY_BETWEEN_REPLIES, Settings.MAX_DELAY_BETWEEN_REPLIES)
    
    def get_stats(self) -> Dict:
        """Get current rate limit stats"""
        hour_ago = datetime.now() - timedelta(hours=1)
        self.global_replies = [t for t in self.global_replies if t > hour_ago]
        return {
            "global": len(self.global_replies),
            "max_global": Settings.MAX_REPLIES_PER_HOUR,
            "servers": {k: len([t for t in v if t > hour_ago]) 
                       for k, v in self.hourly_replies.items()}
        }


# ═══════════════════════════════════════════════════════════════════════════════
# MESSAGE FILTER - SMART FILTERING
# ═══════════════════════════════════════════════════════════════════════════════

class MessageFilter:
    """Smart message filtering - quality over quantity"""
    
    @classmethod
    def is_worth_replying(cls, content: str, author_bot: bool = False) -> tuple:
        """Check if message is worth a reply (returns bool, reason)"""
        
        if not content or not content.strip():
            return False, "Empty"
        
        content = content.strip()
        content_lower = content.lower()
        
        # Skip very short messages
        if len(content) < 3:
            return False, "Too short"
        
        # Skip bot messages (unless it's a question to us)
        if author_bot:
            return False, "Bot message"
        
        # Check blacklist
        for word in Settings.BLACKLIST_KEYWORDS:
            if word in content_lower:
                return False, f"Blacklisted: {word}"
        
        # Check low value patterns
        for pattern in Settings.LOW_VALUE_PATTERNS:
            if re.match(pattern, content_lower):
                return False, "Low value"
        
        # Skip if just emojis
        emoji_pattern = re.compile(r'^[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\s]+$')
        if emoji_pattern.match(content):
            return False, "Emoji only"
        
        # Skip if just mentions
        if re.match(r'^(<@!?\d+>\s*)+$', content):
            return False, "Mention only"
        
        # Good message - worth replying
        return True, "Worth replying"
    
    @classmethod
    def is_role_announcement(cls, content: str) -> bool:
        """Check if message is about roles/claims"""
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in Settings.ROLE_KEYWORDS)
    
    @classmethod
    def is_checkin_channel(cls, channel_name: str) -> bool:
        """Check if channel is for daily check-in"""
        name_lower = channel_name.lower()
        checkin_keywords = ["check", "daily", "gm", "attendance", "verify", "checkin"]
        return any(kw in name_lower for kw in checkin_keywords)
    
    @classmethod
    def clean_text(cls, content: str) -> str:
        """Clean message for context"""
        content = re.sub(r'<@!?\d+>', '[user]', content)
        content = re.sub(r'<#\d+>', '[channel]', content)
        content = re.sub(r'<a?:\w+:\d+>', '', content)
        content = re.sub(r'https?://\S+', '[link]', content)
        return content.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# MEMORY MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class MemoryManager:
    """Tracks replied messages and daily activities"""
    
    def __init__(self, identity_name: str):
        self.identity_name = identity_name
        self.memory_file = Settings.MEMORY_DIR / f"{identity_name}_memory.json"
        self.replied_messages: Set[int] = set()
        self.daily_checkins: Dict[str, str] = {}  # server_id -> date
        self.claimed_roles: Set[int] = set()  # message IDs we reacted to
    
    async def load(self):
        Settings.ensure_directories()
        if self.memory_file.exists():
            try:
                async with aiofiles.open(self.memory_file, 'r') as f:
                    data = json.loads(await f.read())
                    self.replied_messages = set(data.get('replied', [])[-500:])
                    self.daily_checkins = data.get('checkins', {})
                    self.claimed_roles = set(data.get('claimed', [])[-200:])
            except:
                pass
    
    async def save(self):
        data = {
            'replied': list(self.replied_messages)[-500:],
            'checkins': self.daily_checkins,
            'claimed': list(self.claimed_roles)[-200:]
        }
        async with aiofiles.open(self.memory_file, 'w') as f:
            await f.write(json.dumps(data))
    
    def has_replied(self, msg_id: int) -> bool:
        return msg_id in self.replied_messages
    
    def mark_replied(self, msg_id: int):
        self.replied_messages.add(msg_id)
    
    def has_checked_in_today(self, server_id: str) -> bool:
        today = datetime.now().strftime('%Y-%m-%d')
        return self.daily_checkins.get(server_id) == today
    
    def mark_checked_in(self, server_id: str):
        self.daily_checkins[server_id] = datetime.now().strftime('%Y-%m-%d')
    
    def has_claimed_role(self, msg_id: int) -> bool:
        return msg_id in self.claimed_roles
    
    def mark_role_claimed(self, msg_id: int):
        self.claimed_roles.add(msg_id)


# ═══════════════════════════════════════════════════════════════════════════════
# AI ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class AIEngine:
    """AI response generation with contribution focus"""
    
    def __init__(self, config: ConfigManager, logger: Logger):
        self.config = config
        self.logger = logger
        self.client = None
        self.current_key: Optional[str] = None
    
    async def initialize(self) -> bool:
        if not GROQ_AVAILABLE:
            return False
        self.current_key = self.config.get_active_api_key()
        if not self.current_key:
            return False
        self.client = AsyncGroq(api_key=self.current_key)
        return True
    
    async def _rotate_key(self) -> bool:
        if self.current_key:
            self.config.block_api_key(self.current_key)
        self.current_key = self.config.get_active_api_key()
        if not self.current_key:
            return False
        self.client = AsyncGroq(api_key=self.current_key)
        return True
    
    async def generate_reply(self, message: str, context: List[Dict], 
                            persona: Dict, channel_name: str) -> Optional[str]:
        if not self.client and not await self.initialize():
            return None
        
        tone = persona.get('tone', 'casual')
        max_words = persona.get('maxWords', 15)
        
        system_prompt = f"""You are a friendly Discord community member. Your style is {tone}.

IMPORTANT RULES:
- Keep replies VERY SHORT: {max_words} words MAX
- Be helpful and add value to conversation
- Sound natural, like a real person
- Use 1 emoji occasionally (not always)
- NEVER say you're AI/bot
- Match the conversation vibe
- Don't spam or repeat yourself
- Add something meaningful

Channel: #{channel_name}
Be genuine and contribute positively!"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add context (last 3 messages)
        for msg in context[-3:]:
            if msg.get('content'):
                messages.append({
                    "role": "assistant" if msg.get('is_self') else "user",
                    "content": f"{msg.get('author', 'User')}: {msg.get('content', '')}"
                })
        
        messages.append({"role": "user", "content": f"Reply naturally to: {message}"})
        
        try:
            response = await self.client.chat.completions.create(
                model=Settings.AI_MODEL,
                messages=messages,
                max_tokens=Settings.AI_MAX_TOKENS,
                temperature=Settings.AI_TEMPERATURE
            )
            
            reply = response.choices[0].message.content.strip()
            
            # Clean up
            reply = reply.replace('"', '').strip()
            
            # Remove "Username:" prefix if AI added it
            if ':' in reply[:20]:
                parts = reply.split(':', 1)
                if len(parts[0].split()) <= 2:  # Likely a name
                    reply = parts[1].strip()
            
            # Enforce word limit
            words = reply.split()
            if len(words) > max_words:
                reply = ' '.join(words[:max_words])
            
            # Maybe add emoji
            if random.random() < 0.3:
                emojis = ['😊', '👍', '🔥', '💯', '✨', '😄', '🙌']
                if not any(e in reply for e in emojis):
                    reply += f" {random.choice(emojis)}"
            
            return reply
            
        except Exception as e:
            error_str = str(e).lower()
            if 'rate_limit' in error_str or '429' in str(e):
                if await self._rotate_key():
                    return await self.generate_reply(message, context, persona, channel_name)
            elif 'invalid_api_key' in error_str or '401' in str(e):
                if self.current_key:
                    self.config.api_keys.remove(self.current_key)
                if await self._rotate_key():
                    return await self.generate_reply(message, context, persona, channel_name)
            self.logger.error(f"AI Error: {e}")
            return None
    
    async def generate_gm(self) -> str:
        """Generate a GM message"""
        gm_messages = [
            "gm everyone! ☀️", "GM! 🌅", "good morning! 👋",
            "gm gm! ✨", "morning fam! 🌞", "GM! Hope everyone's doing great 💪",
            "gm! ready for a new day 🔥", "good morning all! 🙌"
        ]
        return random.choice(gm_messages)


# ═══════════════════════════════════════════════════════════════════════════════
# BOT IDENTITY
# ═══════════════════════════════════════════════════════════════════════════════

class BotIdentity:
    """Single bot identity"""
    
    def __init__(self, config: Dict):
        self.display_name = config.get('displayName', 'Unknown')
        self.token = config.get('discordToken', '')
        self.persona = config.get('persona', {
            'tone': 'casual', 'maxWords': 15, 'emojiRate': 0.3
        })
        self.servers = config.get('servers', {})
        self.client: Optional[discord.Client] = None
        self.connected = False
        self.user = None
    
    async def connect(self) -> bool:
        if self.connected:
            return True
        if not self.token:
            return False
        
        self.client = discord.Client()
        event = asyncio.Event()
        
        @self.client.event
        async def on_ready():
            self.connected = True
            self.user = self.client.user
            event.set()
        
        try:
            asyncio.create_task(self.client.start(self.token))
            await asyncio.wait_for(event.wait(), timeout=30)
            return True
        except:
            return False
    
    async def disconnect(self):
        if self.client and not self.client.is_closed():
            await self.client.close()
        self.connected = False


class IdentityManager:
    """Manages bot identities"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.identities: Dict[str, BotIdentity] = {}
    
    async def load_identities(self) -> int:
        for cfg in self.config.identities:
            name = cfg.get('displayName', '')
            if name:
                self.identities[name] = BotIdentity(cfg)
        return len(self.identities)
    
    async def connect_all(self) -> Dict[str, bool]:
        return {name: await identity.connect() for name, identity in self.identities.items()}
    
    async def disconnect_all(self):
        for identity in self.identities.values():
            await identity.disconnect()
    
    def get_identity(self, name: str) -> Optional[BotIdentity]:
        return self.identities.get(name)
    
    def get_all(self) -> List[BotIdentity]:
        return list(self.identities.values())
    
    def get_names(self) -> List[str]:
        return list(self.identities.keys())
    
    async def add_identity(self, name: str, token: str, persona: Dict = None):
        cfg = {
            'displayName': name,
            'discordToken': token,
            'persona': persona or {'tone': 'casual', 'maxWords': 15, 'emojiRate': 0.3},
            'servers': {}
        }
        self.config.add_identity(cfg)
        await self.config.save()
        self.identities[name] = BotIdentity(cfg)
    
    def update_server_config(self, identity_name: str, server_id: str, cfg: Dict):
        identity = self.identities.get(identity_name)
        if identity:
            identity.servers[server_id] = cfg
            self.config.update_identity(identity_name, {'servers': identity.servers})


# ═══════════════════════════════════════════════════════════════════════════════
# CHANNEL PROCESSOR - SMART PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════

class ChannelProcessor:
    """Processes channels with anti-spam and role claiming"""
    
    def __init__(self, identity: BotIdentity, ai: AIEngine, memory: MemoryManager,
                 rate_limiter: RateLimiter, logger: Logger):
        self.identity = identity
        self.ai = ai
        self.memory = memory
        self.rate_limiter = rate_limiter
        self.logger = logger
    
    async def process_server(self, server_config: Dict) -> int:
        """Process all channels in a server, returns number of replies sent"""
        if not self.identity.connected:
            return 0
        
        replies_sent = 0
        max_replies = Settings.MAX_REPLIES_PER_CYCLE
        
        channels = server_config.get('preferredChannels', {})
        server_name = server_config.get('serverName', 'Unknown')
        
        # Process announcement channels first for roles
        for channel_name, channel_cfg in channels.items():
            if channel_cfg.get('type') == 'announcement':
                await self._check_announcements(channel_cfg, server_name)
        
        # Process chat channels
        for channel_name, channel_cfg in channels.items():
            if replies_sent >= max_replies:
                break
            
            channel_type = channel_cfg.get('type', 'chat')
            
            if channel_type == 'gm':
                sent = await self._process_gm_channel(channel_cfg, server_name, channel_name)
            elif channel_type == 'chat':
                sent = await self._process_chat_channel(channel_cfg, server_name, channel_name)
                if sent:
                    replies_sent += 1
                    # Delay between replies
                    delay = self.rate_limiter.get_delay()
                    self.logger.delay(delay, "Anti-spam")
                    await asyncio.sleep(delay)
        
        return replies_sent
    
    async def _check_announcements(self, channel_cfg: Dict, server_name: str):
        """Check announcement channel for role claims"""
        channel_id = channel_cfg.get('id')
        if not channel_id:
            return
        
        try:
            channel = self.identity.client.get_channel(int(channel_id))
            if not channel:
                return
            
            # Check last 10 messages for role announcements
            async for msg in channel.history(limit=10):
                # Skip if already claimed
                if self.memory.has_claimed_role(msg.id):
                    continue
                
                # Check if it's a role announcement
                if MessageFilter.is_role_announcement(msg.content):
                    # Try to react
                    for reaction in msg.reactions:
                        emoji = str(reaction.emoji)
                        if emoji in Settings.ROLE_REACTIONS:
                            try:
                                await msg.add_reaction(emoji)
                                self.memory.mark_role_claimed(msg.id)
                                self.logger.role_claim(server_name, channel.name, 
                                                      f"Reacted with {emoji}")
                                await asyncio.sleep(2)
                                break
                            except:
                                pass
                    
                    # If no reactions yet but has role keywords, try common reactions
                    if not msg.reactions:
                        for emoji in ["✅", "🎉", "👍"]:
                            try:
                                await msg.add_reaction(emoji)
                                self.memory.mark_role_claimed(msg.id)
                                self.logger.role_claim(server_name, channel.name,
                                                      f"Reacted with {emoji}")
                                await asyncio.sleep(2)
                                break
                            except:
                                pass
        except Exception as e:
            self.logger.debug(f"Announcement check error: {e}")
    
    async def _process_gm_channel(self, channel_cfg: Dict, server_name: str, 
                                   channel_name: str) -> bool:
        """Process GM/check-in channel"""
        channel_id = channel_cfg.get('id')
        if not channel_id:
            return False
        
        try:
            channel = self.identity.client.get_channel(int(channel_id))
            if not channel:
                return False
            
            server_id = str(channel.guild.id)
            
            # Check if already checked in today
            if self.memory.has_checked_in_today(server_id):
                return False
            
            # Send GM
            gm_msg = await self.ai.generate_gm()
            
            try:
                await channel.send(gm_msg)
                self.memory.mark_checked_in(server_id)
                self.logger.daily_checkin(server_name, channel.name, f"Sent: {gm_msg}")
                await self.memory.save()
                return True
            except Exception as e:
                self.logger.debug(f"GM send error: {e}")
                return False
                
        except Exception as e:
            self.logger.debug(f"GM channel error: {e}")
            return False
    
    async def _process_chat_channel(self, channel_cfg: Dict, server_name: str,
                                     channel_name: str) -> bool:
        """Process chat channel with AI replies"""
        channel_id = channel_cfg.get('id')
        if not channel_id:
            return False
        
        try:
            channel = self.identity.client.get_channel(int(channel_id))
            if not channel:
                return False
            
            server_id = str(channel.guild.id)
            
            # Check rate limit
            can_reply, reason = self.rate_limiter.can_reply(server_id)
            if not can_reply:
                self.logger.skip(f"Rate limited: {reason}")
                return False
            
            # Get recent messages
            messages = []
            async for msg in channel.history(limit=15):
                messages.append(msg)
            
            # Find a message worth replying to
            for msg in messages:
                # Skip own messages
                if msg.author.id == self.identity.user.id:
                    continue
                
                # Skip already replied
                if self.memory.has_replied(msg.id):
                    continue
                
                # Skip old messages (> 5 min)
                age = (datetime.utcnow() - msg.created_at.replace(tzinfo=None)).seconds
                if age > 300:
                    continue
                
                # Check if worth replying
                worth, reason = MessageFilter.is_worth_replying(msg.content, msg.author.bot)
                if not worth:
                    continue
                
                # Log the message
                self.logger.chat(server_name, channel.name, 
                               msg.author.display_name, msg.content)
                
                # Get context
                context = []
                async for ctx_msg in channel.history(limit=5):
                    context.append({
                        'author': ctx_msg.author.display_name,
                        'content': MessageFilter.clean_text(ctx_msg.content),
                        'is_self': ctx_msg.author.id == self.identity.user.id
                    })
                context.reverse()
                
                # Generate reply
                reply = await self.ai.generate_reply(
                    msg.content, context, self.identity.persona, channel.name
                )
                
                if not reply:
                    continue
                
                # Type and send
                try:
                    delay = random.uniform(1, 2.5)
                    async with channel.typing():
                        await asyncio.sleep(delay)
                    
                    await msg.reply(reply, mention_author=False)
                    
                    # Record
                    self.memory.mark_replied(msg.id)
                    self.rate_limiter.record_reply(server_id)
                    await self.memory.save()
                    
                    self.logger.reply_sent(server_name, channel.name, reply)
                    return True
                    
                except Exception as e:
                    self.logger.debug(f"Send error: {e}")
                    continue
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Chat channel error: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN BOT APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

custom_style = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'fg:white bold'),
    ('answer', 'fg:green bold'),
    ('pointer', 'fg:cyan bold'),
    ('highlighted', 'fg:cyan bold'),
    ('selected', 'fg:green'),
])


class KazuhaVIPBot:
    """Main bot - Created by Kazuha VIP Only"""
    
    def __init__(self):
        self.console = Console()
        self.logger = Logger()
        self.config: Optional[ConfigManager] = None
        self.identity_manager: Optional[IdentityManager] = None
        self.ai_engine: Optional[AIEngine] = None
        self.rate_limiter = RateLimiter()
        self.running = False
    
    async def initialize(self) -> bool:
        self.logger.banner()
        
        self.config = ConfigManager()
        await self.config.load()
        
        self.identity_manager = IdentityManager(self.config)
        await self.identity_manager.load_identities()
        
        self.ai_engine = AIEngine(self.config, self.logger)
        
        self._display_status()
        return True
    
    def _display_status(self):
        features = ["Daily Check-in", "Role Claim", "Anti-Spam", "AI Chat"]
        self.logger.status_panel(
            len(self.identity_manager.get_names()),
            self.config.get_api_key_status(),
            features
        )
    
    async def _menu_fetch_channel_id(self):
        self.logger.console.print("\n[bold cyan]═══ Fetch Channel ID ═══[/bold cyan]\n")
        
        names = self.identity_manager.get_names()
        if not names:
            self.logger.warning("No accounts configured.")
            return
        
        account = await questionary.select("Select account:", 
                                          choices=names + ["← Back"],
                                          style=custom_style).ask_async()
        if account == "← Back" or not account:
            return
        
        identity = self.identity_manager.get_identity(account)
        
        if not identity.connected:
            self.logger.info(f"Connecting {account}...")
            if not await identity.connect():
                self.logger.error("Failed to connect.")
                return
            await asyncio.sleep(3)
        
        guilds = identity.client.guilds
        if not guilds:
            self.logger.warning("No servers found.")
            return
        
        server = await questionary.select("Select server:",
                                         choices=[f"{g.name} ({g.id})" for g in guilds] + ["← Back"],
                                         style=custom_style).ask_async()
        if server == "← Back" or not server:
            return
        
        server_id = server.split("(")[-1].rstrip(")")
        guild = next((g for g in guilds if str(g.id) == server_id), None)
        
        if guild:
            table = Table(title=f"Channels in {guild.name}", box=box.ROUNDED)
            table.add_column("#", style="dim")
            table.add_column("Channel", style="cyan")
            table.add_column("ID", style="green")
            table.add_column("Type Suggestion", style="yellow")
            
            for i, ch in enumerate(guild.text_channels, 1):
                ch_type = "gm" if any(x in ch.name.lower() for x in ['gm', 'check', 'daily']) else \
                         "announcement" if any(x in ch.name.lower() for x in ['announce', 'news', 'update']) else "chat"
                table.add_row(str(i), f"#{ch.name}", str(ch.id), ch_type)
            
            self.console.print(table)
        
        input("\nPress Enter to continue...")
    
    async def _menu_setup_accounts(self):
        self.logger.console.print("\n[bold cyan]═══ Setup Accounts ═══[/bold cyan]\n")
        
        while True:
            action = await questionary.select("What to do?", choices=[
                "➕ Add New Account",
                "🖥️ Configure Server/Channels",
                "📋 View Configuration",
                "← Back"
            ], style=custom_style).ask_async()
            
            if action == "← Back" or not action:
                break
            elif action == "➕ Add New Account":
                await self._add_account()
            elif action == "🖥️ Configure Server/Channels":
                await self._configure_server()
            elif action == "📋 View Configuration":
                await self._view_config()
    
    async def _add_account(self):
        name = await questionary.text("Display name:", style=custom_style).ask_async()
        if not name:
            return
        
        token = await questionary.text("Discord token:", style=custom_style).ask_async()
        if not token:
            return
        
        await self.identity_manager.add_identity(name, token)
        self.logger.success(f"Account '{name}' added!")
    
    async def _configure_server(self):
        names = self.identity_manager.get_names()
        if not names:
            self.logger.warning("No accounts.")
            return
        
        account = await questionary.select("Select account:", 
                                          choices=names + ["← Back"],
                                          style=custom_style).ask_async()
        if account == "← Back" or not account:
            return
        
        identity = self.identity_manager.get_identity(account)
        
        if not identity.connected:
            self.logger.info(f"Connecting {account}...")
            if not await identity.connect():
                self.logger.error("Failed to connect.")
                return
            await asyncio.sleep(3)
        
        guilds = identity.client.guilds
        server = await questionary.select("Select server:",
                                         choices=[f"{g.name} ({g.id})" for g in guilds] + ["← Back"],
                                         style=custom_style).ask_async()
        if server == "← Back" or not server:
            return
        
        server_id = server.split("(")[1].split(")")[0]
        guild = next((g for g in guilds if str(g.id) == server_id), None)
        if not guild:
            return
        
        server_config = identity.servers.get(server_id, {
            'enabled': True,
            'serverName': guild.name,
            'preferredChannels': {}
        })
        
        while True:
            action = await questionary.select(f"Configure {guild.name}:", choices=[
                "➕ Add Channel",
                "📋 View Channels",
                "✅ Enable/Disable Server",
                "💾 Save & Back"
            ], style=custom_style).ask_async()
            
            if action == "💾 Save & Back" or not action:
                self.identity_manager.update_server_config(account, server_id, server_config)
                await self.config.save()
                self.logger.success("Saved!")
                break
            
            elif action == "➕ Add Channel":
                self.console.print("\n[cyan]Available channels:[/cyan]")
                for i, ch in enumerate(guild.text_channels[:25], 1):
                    self.console.print(f"  {i}. #{ch.name} - {ch.id}")
                
                channel_id = await questionary.text("Channel ID:", style=custom_style).ask_async()
                if not channel_id:
                    continue
                
                channel_name = await questionary.text("Name (e.g., 'general'):", 
                                                     style=custom_style).ask_async()
                if not channel_name:
                    continue
                
                channel_type = await questionary.select("Channel type:", choices=[
                    "chat - AI replies to messages",
                    "gm - Daily check-in/GM",
                    "announcement - Role claims"
                ], style=custom_style).ask_async()
                
                ch_type = channel_type.split(" - ")[0]
                
                server_config['preferredChannels'][channel_name] = {
                    'id': channel_id,
                    'type': ch_type
                }
                self.logger.success(f"Channel '{channel_name}' added as {ch_type}!")
            
            elif action == "📋 View Channels":
                channels = server_config.get('preferredChannels', {})
                if not channels:
                    self.logger.warning("No channels configured.")
                else:
                    table = Table(box=box.ROUNDED)
                    table.add_column("Name", style="cyan")
                    table.add_column("ID", style="green")
                    table.add_column("Type", style="yellow")
                    for name, cfg in channels.items():
                        table.add_row(name, cfg.get('id', '?'), cfg.get('type', 'chat'))
                    self.console.print(table)
                input("\nPress Enter...")
            
            elif action == "✅ Enable/Disable Server":
                server_config['enabled'] = not server_config.get('enabled', True)
                status = "ENABLED ✅" if server_config['enabled'] else "DISABLED ❌"
                self.logger.success(f"Server {status}")
    
    async def _view_config(self):
        self.console.print("\n[bold cyan]═══ Current Configuration ═══[/bold cyan]\n")
        
        for identity in self.identity_manager.get_all():
            content = [f"[yellow]Persona:[/yellow] {identity.persona.get('tone', 'casual')}"]
            content.append(f"[yellow]Servers:[/yellow] {len(identity.servers)}")
            
            for sid, scfg in identity.servers.items():
                status = "✅" if scfg.get('enabled') else "❌"
                channels = len(scfg.get('preferredChannels', {}))
                content.append(f"  {status} {scfg.get('serverName', sid)} ({channels} channels)")
                
                for cname, ccfg in scfg.get('preferredChannels', {}).items():
                    content.append(f"      • #{cname} [{ccfg.get('type', 'chat')}]")
            
            panel = Panel("\n".join(content), title=f"[bold]{identity.display_name}[/bold]",
                         border_style="cyan")
            self.console.print(panel)
        
        input("\nPress Enter...")
    
    async def _menu_run_program(self):
        self.logger.console.print("\n[bold cyan]═══ Running Bot ═══[/bold cyan]\n")
        
        identities = self.identity_manager.get_all()
        if not identities:
            self.logger.error("No accounts configured.")
            return
        
        if not self.config.api_keys:
            self.logger.error("No API keys in data/groq_api_keys.txt")
            return
        
        # Count enabled servers
        enabled = sum(1 for i in identities 
                     for s in i.servers.values() if s.get('enabled'))
        if not enabled:
            self.logger.warning("No enabled servers.")
            return
        
        confirm = await questionary.confirm(
            f"Start with {len(identities)} account(s), {enabled} server(s)?",
            default=True, style=custom_style
        ).ask_async()
        
        if not confirm:
            return
        
        self.running = True
        
        # Initialize AI
        if not await self.ai_engine.initialize():
            self.logger.error("AI engine failed!")
            return
        self.logger.success("AI Engine ready!")
        
        # Connect accounts
        self.logger.info("Connecting accounts...")
        for name, success in (await self.identity_manager.connect_all()).items():
            if success:
                self.logger.success(f"  ✅ {name} connected")
            else:
                self.logger.error(f"  ❌ {name} failed")
        
        await asyncio.sleep(3)
        
        # Setup processors
        processors = []
        for identity in identities:
            if not identity.connected:
                continue
            
            memory = MemoryManager(identity.display_name)
            await memory.load()
            
            processor = ChannelProcessor(
                identity=identity,
                ai=self.ai_engine,
                memory=memory,
                rate_limiter=self.rate_limiter,
                logger=self.logger
            )
            
            for server_id, server_cfg in identity.servers.items():
                if server_cfg.get('enabled'):
                    processors.append({
                        'processor': processor,
                        'server_config': server_cfg,
                        'identity_name': identity.display_name
                    })
        
        if not processors:
            self.logger.warning("No processors configured!")
            return
        
        # Show running panel
        self.console.print(Panel(
            f"[bold green]🤖 Bot is running![/bold green]\n\n"
            f"[white]Model: [cyan]{Settings.AI_MODEL}[/cyan]\n"
            f"Servers: [cyan]{len(processors)}[/cyan]\n"
            f"Cycle: [cyan]{Settings.CYCLE_INTERVAL_SECONDS}s[/cyan]\n"
            f"Max replies/cycle: [cyan]{Settings.MAX_REPLIES_PER_CYCLE}[/cyan]\n"
            f"Max replies/hour: [cyan]{Settings.MAX_REPLIES_PER_HOUR}[/cyan]\n\n"
            f"Press [bold cyan]Ctrl+C[/bold cyan] to stop.[/white]",
            title="[bold]Kazuha VIP Bot - Active[/bold]",
            border_style="green"
        ))
        
        self.console.print("\n[bold cyan]═══════════════════ LIVE LOGS ═══════════════════[/bold cyan]\n")
        
        try:
            while self.running:
                total_replies = 0
                
                for proc_info in processors:
                    if not self.running:
                        break
                    
                    server_name = proc_info['server_config'].get('serverName', 'Unknown')
                    channels = len(proc_info['server_config'].get('preferredChannels', {}))
                    
                    self.logger.cycle_start(server_name, channels)
                    
                    try:
                        replies = await proc_info['processor'].process_server(
                            proc_info['server_config']
                        )
                        total_replies += replies
                    except Exception as e:
                        self.logger.error(f"Server error: {e}")
                    
                    # Delay between servers
                    await asyncio.sleep(5)
                
                # Show stats
                stats = self.rate_limiter.get_stats()
                self.logger.cycle_end(
                    total_replies, 
                    Settings.CYCLE_INTERVAL_SECONDS
                )
                self.logger.info(
                    f"Stats: {stats['global']}/{stats['max_global']} replies this hour"
                )
                
                self.logger.separator()
                
                # Wait for next cycle
                await asyncio.sleep(Settings.CYCLE_INTERVAL_SECONDS)
                
        except KeyboardInterrupt:
            self.logger.warning("\n⏹️ Stopping...")
        
        finally:
            self.running = False
            await self.identity_manager.disconnect_all()
            self.logger.success("Bot stopped!")
    
    async def main_menu(self):
        while True:
            self.console.print("\n")
            
            choice = await questionary.select("🎮 Main Menu:", choices=[
                "1️⃣  Fetch Channel ID",
                "2️⃣  Setup Accounts",
                "3️⃣  Run Program",
                "4️⃣  View Status",
                "5️⃣  Exit"
            ], style=custom_style).ask_async()
            
            if not choice:
                continue
            
            if "Fetch" in choice:
                await self._menu_fetch_channel_id()
            elif "Setup" in choice:
                await self._menu_setup_accounts()
            elif "Run" in choice:
                await self._menu_run_program()
            elif "View" in choice:
                await self._view_config()
            elif "Exit" in choice:
                if await questionary.confirm("Exit?", default=False, 
                                            style=custom_style).ask_async():
                    self.console.print("\n[bold cyan]👋 Goodbye![/bold cyan]")
                    self.console.print("[dim]Created by Kazuha VIP Only[/dim]\n")
                    break
    
    async def run(self):
        try:
            await self.initialize()
            await self.main_menu()
        except Exception as e:
            self.logger.error(f"Fatal: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.identity_manager:
                await self.identity_manager.disconnect_all()


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    bot = KazuhaVIPBot()
    await bot.run()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())