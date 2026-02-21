"""
╔══════════════════════════════════════════════════════════════╗
║              🤖 KAZUHA VIP DISCORD AUTO BOT                  ║
║                  Created by Kazuha VIP Only                  ║
╚══════════════════════════════════════════════════════════════╝
Channel Message Processing
"""

import discord
import asyncio
import random
from typing import Dict, List, Optional, Any
from datetime import datetime

from .identity_manager import BotIdentity
from .ai_engine import AIEngine
from .memory_manager import MemoryManager
from .eligibility_tracker import EligibilityTracker
from utils.filters import MessageFilter
from utils.helpers import Helpers
from utils.logger import Logger

try:
    from nltk.sentiment import SentimentIntensityAnalyzer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


class ChannelProcessor:
    """Processes messages in Discord channels"""
    
    def __init__(self, identity: BotIdentity, ai_engine: AIEngine,
                 memory: MemoryManager, eligibility: EligibilityTracker,
                 global_settings: Dict[str, Any], logger: Logger):
        self.identity = identity
        self.ai = ai_engine
        self.memory = memory
        self.eligibility = eligibility
        self.settings = global_settings
        self.logger = logger
        
        self.sentiment_analyzer = None
        if NLTK_AVAILABLE:
            try:
                self.sentiment_analyzer = SentimentIntensityAnalyzer()
            except:
                pass
    
    def _get_sentiment(self, text: str) -> float:
        """Get sentiment score (-1 to 1)"""
        if not self.sentiment_analyzer:
            return 0.0
        try:
            return self.sentiment_analyzer.polarity_scores(text)['compound']
        except:
            return 0.0
    
    async def _get_context(self, channel: discord.TextChannel, 
                           limit: int = 10) -> List[Dict[str, str]]:
        """Get recent message context"""
        context = []
        
        try:
            async for msg in channel.history(limit=limit):
                if msg.author.bot and msg.author.id != self.identity.user.id:
                    continue
                
                context.append({
                    'author': msg.author.display_name,
                    'content': MessageFilter.extract_clean_text(msg.content),
                    'is_self': msg.author.id == self.identity.user.id,
                    'timestamp': msg.created_at.isoformat()
                })
        except Exception as e:
            self.logger.warning(f"Failed to get context: {e}")
        
        return list(reversed(context))
    
    async def _should_reply(self, message: discord.Message, 
                            server_id: str) -> tuple[bool, str]:
        """Determine if bot should reply to message"""
        # Skip own messages
        if message.author.id == self.identity.user.id:
            return False, "Own message"
        
        # Skip bot messages
        if message.author.bot:
            return False, "Bot message"
        
        # Random ignore for human-likeness
        ignore_prob = self.settings.get('ignoreProbability', 0.3)
        if Helpers.should_ignore(ignore_prob):
            return False, "Random ignore (human-likeness)"
        
        # Check message validity
        valid, reason = MessageFilter.is_valid_for_reply(
            message.content,
            bool(message.attachments),
            bool(message.embeds),
            bool(message.stickers)
        )
        if not valid:
            return False, reason
        
        # Check sentiment (skip negative/toxic)
        sentiment = self._get_sentiment(message.content)
        if sentiment < -0.3:
            return False, f"Negative sentiment ({sentiment:.2f})"
        
        # Check user reply limits
        max_replies = self.settings.get('maxRepliesPerUser', 3)
        cooldown = self.settings.get('userReplyCooldownMinutes', 30)
        
        can_reply, reply_reason = self.memory.can_reply_to_user(
            server_id, str(message.author.id), max_replies, cooldown
        )
        if not can_reply:
            return False, reply_reason
        
        # Check action limits
        can_act, act_reason = self.eligibility.can_perform_action(
            server_id,
            self.settings.get('dailyMessageCap', 25),
            self.settings.get('hourlyReplyCap', 5),
            3  # Per-server daily cap
        )
        if not can_act:
            return False, act_reason
        
        return True, "Valid for reply"
    
    async def process_ai_channel(self, channel_id: str, 
                                  server_config: Dict[str, Any]) -> bool:
        """Process an AI-enabled channel"""
        if not self.identity.client or not self.identity.connected:
            return False
        
        channel = self.identity.client.get_channel(int(channel_id))
        if not channel:
            return False
        
        server_id = str(channel.guild.id)
        
        # Get recent messages
        try:
            messages = [msg async for msg in channel.history(limit=5)]
        except Exception as e:
            self.logger.error(f"Failed to fetch messages: {e}")
            return False
        
        # Find a message to reply to
        for message in messages:
            should_reply, reason = await self._should_reply(message, server_id)
            
            if not should_reply:
                continue
            
            # Log the attempt
            action_lines = [
                f"💬 @{message.author.display_name} said: \"{Helpers.truncate_text(message.content)}\"",
                f"📊 Reply check: {reason}"
            ]
            
            # Get context
            context = await self._get_context(channel, self.settings.get('contextHistoryDepth', 10))
            action_lines.append("🧠 Reading message context...")
            
            # Generate AI reply
            action_lines.append("🤖 Generating AI reply...")
            
            reply = await self.ai.generate_reply(
                message.content,
                context,
                self.identity.persona,
                self.identity.user.display_name
            )
            
            if not reply:
                action_lines.append("❌ Failed to generate reply")
                self.logger.action(
                    self.identity.display_name,
                    channel.guild.name,
                    channel.name,
                    action_lines
                )
                return False
            
            # Add human-like typo occasionally
            reply = Helpers.add_human_typo(reply)
            
            # Typing indicator
            action_lines.append("⌨️ Typing...")
            delay = Helpers.get_typing_delay(self.settings.get('typingDelayRange', [1, 3]))
            
            try:
                async with channel.typing():
                    await asyncio.sleep(delay)
                
                # Send reply
                await message.reply(reply, mention_author=False)
                
                action_lines.append(f"✓ Replied: \"{Helpers.truncate_text(reply)}\"")
                
                # Update tracking
                self.memory.increment_reply_count(server_id, str(message.author.id))
                self.memory.update_user_info(
                    server_id, 
                    str(message.author.id),
                    f"Last topic: {Helpers.truncate_text(message.content, 30)}",
                    "positive" if self._get_sentiment(message.content) > 0.3 else "neutral"
                )
                self.eligibility.record_action(server_id)
                await self.memory.save()
                
                self.logger.action(
                    self.identity.display_name,
                    channel.guild.name,
                    channel.name,
                    action_lines
                )
                
                return True
                
            except Exception as e:
                action_lines.append(f"❌ Send failed: {e}")
                self.logger.action(
                    self.identity.display_name,
                    channel.guild.name,
                    channel.name,
                    action_lines
                )
                return False
        
        return False
    
    async def process_gm_channel(self, channel_id: str, 
                                  message: str,
                                  server_config: Dict[str, Any]) -> bool:
        """Process a GM (fixed message) channel"""
        if not self.identity.client or not self.identity.connected:
            return False
        
        channel = self.identity.client.get_channel(int(channel_id))
        if not channel:
            return False
        
        server_id = str(channel.guild.id)
        
        # Check action limits
        can_act, reason = self.eligibility.can_perform_action(server_id)
        if not can_act:
            self.logger.warning(f"[{self.identity.display_name}] GM skipped: {reason}")
            return False
        
        action_lines = [
            "📤 Sending scheduled message...",
            "⌨️ Typing..."
        ]
        
        try:
            # Typing delay
            delay = Helpers.get_typing_delay(self.settings.get('typingDelayRange', [1, 3]))
            async with channel.typing():
                await asyncio.sleep(delay)
            
            # Send message
            await channel.send(message)
            
            action_lines.append(f"✓ Sent: \"{message}\"")
            
            # Track action
            self.eligibility.record_action(server_id)
            
            self.logger.action(
                self.identity.display_name,
                channel.guild.name,
                channel.name,
                action_lines
            )
            
            return True
            
        except Exception as e:
            action_lines.append(f"❌ Failed: {e}")
            self.logger.action(
                self.identity.display_name,
                channel.guild.name,
                channel.name,
                action_lines
            )
            return False