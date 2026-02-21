"""
╔══════════════════════════════════════════════════════════════╗
║              🤖 KAZUHA VIP DISCORD AUTO BOT                  ║
║                  Created by Kazuha VIP Only                  ║
╚══════════════════════════════════════════════════════════════╝
Message Filtering Module
"""

import re
from typing import Optional
from config.settings import Settings


class MessageFilter:
    """Intelligent message filtering for natural participation"""
    
    # Regex patterns
    EMOJI_PATTERN = re.compile(
        r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF'
        r'\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF'
        r'\U00002702-\U000027B0\U000024C2-\U0001F251]+'
    )
    MENTION_PATTERN = re.compile(r'<@!?\d+>|<#\d+>|<@&\d+>')
    URL_PATTERN = re.compile(r'https?://\S+')
    DISCORD_EMOJI_PATTERN = re.compile(r'<a?:\w+:\d+>')
    
    @classmethod
    def is_valid_for_reply(cls, content: str, 
                           has_attachments: bool = False,
                           has_embeds: bool = False,
                           has_stickers: bool = False) -> tuple[bool, str]:
        """
        Check if message is valid for AI reply
        Returns: (is_valid, reason)
        """
        # Skip media-only messages
        if has_attachments or has_embeds or has_stickers:
            return False, "Contains media/embeds/stickers"
        
        if not content or not content.strip():
            return False, "Empty message"
        
        cleaned = content.strip()
        
        # Remove emojis and check if anything remains
        without_emojis = cls.EMOJI_PATTERN.sub('', cleaned)
        without_discord_emojis = cls.DISCORD_EMOJI_PATTERN.sub('', without_emojis)
        without_mentions = cls.MENTION_PATTERN.sub('', without_discord_emojis)
        text_only = without_mentions.strip()
        
        if not text_only:
            return False, "Emoji/mention only message"
        
        # Check minimum length
        if len(text_only) < 3:
            return False, "Message too short"
        
        # Check for low-value messages
        lower_text = text_only.lower()
        if lower_text in Settings.LOW_VALUE_WORDS:
            return False, f"Low-value word: {lower_text}"
        
        # Check for blacklisted content
        for keyword in Settings.BLACKLIST_KEYWORDS:
            if keyword.lower() in lower_text:
                return False, f"Blacklisted keyword: {keyword}"
        
        # Check if it's just URLs
        without_urls = cls.URL_PATTERN.sub('', text_only).strip()
        if not without_urls:
            return False, "URL only message"
        
        return True, "Valid message"
    
    @classmethod
    def is_question(cls, content: str) -> bool:
        """Check if message is a question"""
        indicators = ['?', 'how', 'what', 'when', 'where', 'why', 'who', 
                     'which', 'can', 'could', 'would', 'should', 'is', 'are',
                     'do', 'does', 'did', 'have', 'has', 'will']
        content_lower = content.lower().strip()
        
        if '?' in content:
            return True
        
        for indicator in indicators:
            if content_lower.startswith(indicator + ' '):
                return True
        
        return False
    
    @classmethod
    def extract_clean_text(cls, content: str) -> str:
        """Extract clean text from message"""
        # Remove Discord-specific formatting
        cleaned = cls.MENTION_PATTERN.sub('[user]', content)
        cleaned = cls.DISCORD_EMOJI_PATTERN.sub('', cleaned)
        cleaned = cls.URL_PATTERN.sub('[link]', cleaned)
        return cleaned.strip()