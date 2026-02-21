"""
╔══════════════════════════════════════════════════════════════╗
║              🤖 KAZUHA VIP DISCORD AUTO BOT                  ║
║                  Created by Kazuha VIP Only                  ║
╚══════════════════════════════════════════════════════════════╝
AI Engine Module - Groq Integration
"""

import random
from typing import Optional, List, Dict, Any
from groq import AsyncGroq

from config.settings import Settings
from config.config_manager import ConfigManager


class AIEngine:
    """AI-powered response generation using Groq API"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.client: Optional[AsyncGroq] = None
        self.current_key: Optional[str] = None
        
    async def initialize(self) -> bool:
        """Initialize AI engine with available API key"""
        self.current_key = self.config.get_active_api_key()
        if not self.current_key:
            return False
        
        self.client = AsyncGroq(api_key=self.current_key)
        return True
    
    async def _rotate_key(self) -> bool:
        """Rotate to next available API key"""
        if self.current_key:
            self.config.block_api_key(self.current_key)
        
        self.current_key = self.config.get_active_api_key()
        if not self.current_key:
            return False
        
        self.client = AsyncGroq(api_key=self.current_key)
        return True
    
    def _build_system_prompt(self, persona: Dict[str, Any]) -> str:
        """Build system prompt based on persona"""
        tone = persona.get('tone', 'casual')
        max_words = persona.get('maxWords', 25)
        avoid_topics = persona.get('avoidTopics', [])
        
        prompt = f"""You are a friendly Discord user participating in a chat conversation.

PERSONALITY:
- Tone: {tone}
- Keep responses under {max_words} words
- Be natural and conversational
- Don't use excessive punctuation or emojis
- Never mention you're an AI or bot
- Respond as a genuine community member

RULES:
- Match the energy of the conversation
- Be helpful but concise
- Use casual language appropriate for Discord
- Occasionally use 1-2 emojis if natural
"""
        
        if avoid_topics:
            prompt += f"\n- Avoid these topics: {', '.join(avoid_topics)}"
        
        return prompt
    
    def _build_context_messages(self, 
                                 context: List[Dict[str, str]], 
                                 target_message: str,
                                 our_username: str) -> List[Dict[str, str]]:
        """Build message context for AI"""
        messages = []
        
        # Add context messages
        for msg in context:
            role = "assistant" if msg.get('is_self') else "user"
            content = msg.get('content', '')
            author = msg.get('author', 'Unknown')
            
            if role == "user":
                messages.append({
                    "role": "user",
                    "content": f"[{author}]: {content}"
                })
            else:
                messages.append({
                    "role": "assistant", 
                    "content": content
                })
        
        # Add target message to reply to
        messages.append({
            "role": "user",
            "content": f"Reply naturally to this message: {target_message}"
        })
        
        return messages
    
    async def generate_reply(self,
                            message_content: str,
                            context: List[Dict[str, str]],
                            persona: Dict[str, Any],
                            our_username: str) -> Optional[str]:
        """Generate AI reply for a message"""
        if not self.client:
            if not await self.initialize():
                return None
        
        system_prompt = self._build_system_prompt(persona)
        messages = self._build_context_messages(context, message_content, our_username)
        
        try:
            response = await self.client.chat.completions.create(
                model=Settings.AI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *messages
                ],
                max_tokens=Settings.AI_MAX_TOKENS,
                temperature=Settings.AI_TEMPERATURE
            )
            
            reply = response.choices[0].message.content.strip()
            
            # Apply persona constraints
            max_words = persona.get('maxWords', 25)
            words = reply.split()
            if len(words) > max_words:
                reply = ' '.join(words[:max_words])
            
            # Random emoji addition based on rate
            emoji_rate = persona.get('emojiRate', 0.2)
            if random.random() < emoji_rate and not any(c in reply for c in ['😊', '👍', '🔥', '💯']):
                emojis = ['😊', '👍', '🔥', '💯', '✨', '🙌', '😄', '👀']
                reply += f" {random.choice(emojis)}"
            
            return reply
            
        except Exception as e:
            error_str = str(e).lower()
            
            if 'rate_limit' in error_str or '429' in str(e):
                # Rate limited - rotate key
                if await self._rotate_key():
                    return await self.generate_reply(
                        message_content, context, persona, our_username
                    )
                return None
            
            elif 'invalid_api_key' in error_str or '401' in str(e):
                # Invalid key - remove and rotate
                if self.current_key:
                    self.config.remove_api_key(self.current_key)
                if await self._rotate_key():
                    return await self.generate_reply(
                        message_content, context, persona, our_username
                    )
                return None
            
            else:
                raise e
    
    async def generate_gm_message(self, variations: bool = True) -> str:
        """Generate a good morning message"""
        if not variations:
            return "Good morning! ☀️"
        
        gm_messages = [
            "Good morning everyone! ☀️",
            "GM! Hope everyone has a great day 🌅",
            "Morning! ☕",
            "GM fam! 🌞",
            "Good morning! Ready for a new day 💪",
            "Morning everyone! 🌄",
            "GM! ☀️",
            "Gooood morning! 🌅",
            "Rise and shine! GM ✨",
            "Morning! Have an awesome day 🔥"
        ]
        
        return random.choice(gm_messages)