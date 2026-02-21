"""
╔══════════════════════════════════════════════════════════════╗
║              🤖 KAZUHA VIP DISCORD AUTO BOT                  ║
║                  Created by Kazuha VIP Only                  ║
╚══════════════════════════════════════════════════════════════╝
Global Settings Module
"""

import os
from pathlib import Path

class Settings:
    """Global application settings"""
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    MEMORY_DIR = DATA_DIR / "memory"
    CONFIG_FILE = DATA_DIR / "bot_config.json"
    API_KEYS_FILE = DATA_DIR / "groq_api_keys.txt"
    
    # Bot Settings
    BOT_NAME = "Kazuha VIP Bot"
    BOT_VERSION = "1.0.0"
    CREATED_BY = "Kazuha VIP Only"
    
    # AI Settings
    AI_MODEL = "llama-3.1-70b-versatile"
    AI_MAX_TOKENS = 150
    AI_TEMPERATURE = 0.8
    
    # Rate Limits
    API_KEY_COOLDOWN_MINUTES = 30
    MIN_INTERVAL_MINUTES = 15
    
    # Message Filters
    LOW_VALUE_WORDS = [
        "ok", "okay", "k", "lol", "lmao", "haha", "yes", "no", 
        "yeah", "yep", "nope", "thanks", "thx", "ty", "np",
        "idk", "idc", "bruh", "bro", "hmm", "mhm", "ah", "oh"
    ]
    
    BLACKLIST_KEYWORDS = [
        "nsfw", "porn", "xxx", "nude", "naked", "sex",
        "scam", "hack", "crack", "cheat", "exploit"
    ]
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.MEMORY_DIR.mkdir(exist_ok=True)