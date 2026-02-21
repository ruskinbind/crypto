import os
import sys
import random
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
# COLORS
# ═══════════════════════════════════════════════════════════════════════════════

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
WHITE = "\033[37m"

BOLD_GREEN = "\033[1;32m"
BOLD_YELLOW = "\033[1;33m"
BOLD_RED = "\033[1;31m"
BOLD_CYAN = "\033[1;36m"
BOLD_MAGENTA = "\033[1;35m"
BOLD_WHITE = "\033[1;37m"

# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def log_green(message: str) -> None:
    print(f"{BOLD_GREEN}[SUCCESS] {message}{RESET}")

def log_red(message: str) -> None:
    print(f"{BOLD_RED}[ERROR] {message}{RESET}")

def log_yellow(message: str) -> None:
    print(f"{BOLD_YELLOW}[INFO] {message}{RESET}")

def log_cyan(message: str) -> None:
    print(f"{BOLD_CYAN}[PROCESS] {message}{RESET}")

def log_magenta(message: str) -> None:
    print(f"{BOLD_MAGENTA}[TASK] {message}{RESET}")

def log_like(username: str, text: str) -> None:
    print(f"{BOLD_GREEN}[♥ LIKED] {BOLD_WHITE}@{username}{RESET} - {text[:50]}...")

def log_recast(username: str, text: str) -> None:
    print(f"{BOLD_YELLOW}[↻ RECASTED] {BOLD_WHITE}@{username}{RESET} - {text[:50]}...")

def log_follow(username: str, fid: int) -> None:
    print(f"{BOLD_CYAN}[+ FOLLOWED] {BOLD_WHITE}@{username} (FID: {fid}){RESET}")

def log_comment(username: str, reply: str) -> None:
    print(f"{BOLD_MAGENTA}[💬 COMMENTED] {BOLD_WHITE}@{username}{RESET} - '{reply[:40]}...'")

def log_post(message: str) -> None:
    print(f"{BOLD_CYAN}[✎ POSTED] {BOLD_WHITE}{message[:50]}...{RESET}")

def clear_screen() -> None:
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

def set_title() -> None:
    try:
        sys.stdout.write("\x1b]2;Farcaster Bot - By KAZUHA VIP ONLY\x1b\\")
        sys.stdout.flush()
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# BANNER
# ═══════════════════════════════════════════════════════════════════════════════

def banner() -> None:
    clear_screen()
    print(f"{BOLD_CYAN}======================================================================{RESET}")
    print(f"{BOLD_GREEN}       FARCASTER AUTO BOT{RESET}")
    print(f"{BOLD_MAGENTA}       Created by KAZUHA VIP ONLY{RESET}")
    print(f"{BOLD_CYAN}======================================================================{RESET}")

# ═══════════════════════════════════════════════════════════════════════════════
# GEMINI AI
# ═══════════════════════════════════════════════════════════════════════════════

class GeminiAI:
    def __init__(self):
        self.api_key = None
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        self.load_api_key()
        
    def load_api_key(self) -> None:
        if Path("key.txt").exists():
            with open("key.txt", 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.api_key = line
                        log_green("Gemini API Key loaded from key.txt")
                        return
        log_yellow("No API key in key.txt - Using fallback replies")
    
    def generate_reply(self, post_text: str) -> str:
        if not self.api_key:
            return self.get_fallback_reply()
        
        try:
            prompt = f"""You are a friendly Farcaster user. Generate a short, relevant reply to this post.
Keep it natural, casual, under 150 characters. No hashtags.

Post: "{post_text}"

Reply:"""

            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.8,
                    "maxOutputTokens": 80
                }
            }
            
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                reply = data['candidates'][0]['content']['parts'][0]['text'].strip()
                reply = reply.replace('"', '').replace("'", "")[:200]
                return reply
            else:
                return self.get_fallback_reply()
                
        except Exception as e:
            return self.get_fallback_reply()
    
    def get_fallback_reply(self) -> str:
        replies = [
            "This is really interesting! Thanks for sharing.",
            "Great post! I totally agree with this.",
            "Love this perspective! Keep posting.",
            "Couldn't agree more! Well said.",
            "This is so true! Thanks for the insight.",
            "Amazing content as always!",
            "Really appreciate you sharing this!",
            "This made my day! Great stuff.",
            "So well put! I needed to hear this.",
            "Brilliant take on this topic!",
            "Facts! This resonates with me.",
            "Awesome stuff, keep it coming!",
            "This is gold! Thanks for posting.",
            "Perfectly said! Couldn't agree more.",
            "Love this energy! Great post."
        ]
        return random.choice(replies)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN BOT CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class FarcasterBot:
    def __init__(self):
        self.config = {}
        self.accounts = []
        self.messages = []
        self.ai = GeminiAI()
        self.current_account = ""
        
        self.stats = {
            'likes': 0,
            'recasts': 0,
            'follows': 0,
            'posts': 0,
            'comments': 0
        }
        
        self.default_config = {
            'api_url': 'https://farcaster.xyz/~api/v2',
            'feed_key': 'home',
            'feed_type': 'default',
            'rate_limit_delay': {
                'min': 3,
                'max': 8,
                'follow_min': 8,
                'follow_max': 15
            },
            'timeout': 30,
            'max_retries': 3,
            'token_file': 'data.txt',
            'message_file': 'messages.txt',
            'like_count': 5,
            'recast_count': 5,
            'follow_count': 5,
            'comment_count': 3,
            'post_count': 1
        }
    
    def log_account(self, level: str, message: str) -> None:
        colors = {
            "info": BOLD_CYAN,
            "success": BOLD_GREEN,
            "error": BOLD_RED,
            "warn": BOLD_YELLOW,
            "task": BOLD_MAGENTA
        }
        color = colors.get(level, BOLD_WHITE)
        if self.current_account:
            print(f"{BOLD_YELLOW}[{self.current_account}] {color}{message}{RESET}")
        else:
            print(f"{color}{message}{RESET}")
    
    def load_config(self) -> bool:
        print(f"\n{BOLD_CYAN}[1/4] Loading Configuration...{RESET}")
        
        if Path("config.json").exists():
            try:
                with open("config.json", 'r') as f:
                    self.config = json.load(f)
                
                for key, value in self.default_config.items():
                    if key not in self.config:
                        self.config[key] = value
                
                log_green("Config loaded from config.json")
                return True
            except Exception as e:
                log_red(f"Config load error: {e}")
                self.config = self.default_config.copy()
                self.save_config()
                return True
        else:
            self.config = self.default_config.copy()
            self.save_config()
            log_yellow("Created default config.json")
            return True
    
    def save_config(self) -> None:
        with open("config.json", 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def load_accounts(self) -> bool:
        print(f"\n{BOLD_CYAN}[2/4] Loading Accounts...{RESET}")
        
        token_file = self.config.get('token_file', 'data.txt')
        
        if not Path(token_file).exists():
            with open(token_file, 'w') as f:
                f.write("# Paste Bearer tokens here (one per line)\n")
                f.write("# Get token from browser DevTools > Network > Authorization header\n")
            log_yellow(f"Created {token_file} - Add your tokens")
            return False
        
        try:
            with open(token_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if line.startswith('Bearer '):
                            line = line.replace('Bearer ', '')
                        self.accounts.append(line)
            
            if not self.accounts:
                log_red(f"No tokens found in {token_file}")
                return False
            
            log_green(f"Loaded {len(self.accounts)} account(s)")
            return True
            
        except Exception as e:
            log_red(f"Account load error: {e}")
            return False
    
    def load_messages(self) -> bool:
        print(f"\n{BOLD_CYAN}[3/4] Loading Messages...{RESET}")
        
        message_file = self.config.get('message_file', 'messages.txt')
        
        if not Path(message_file).exists():
            with open(message_file, 'w') as f:
                f.write("# Custom messages (one per line)\n")
                f.write("# Leave empty to use random generation\n")
            log_yellow(f"Created {message_file}")
            return False
        
        try:
            with open(message_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.messages.append(line)
            
            if self.messages:
                log_green(f"Loaded {len(self.messages)} custom message(s)")
                return True
            else:
                log_yellow("No custom messages - Using random generation")
                return False
                
        except Exception as e:
            log_yellow(f"Message load error: {e}")
            return False
    
    def load_api_key(self) -> bool:
        print(f"\n{BOLD_CYAN}[4/4] Loading API Key...{RESET}")
        
        if not Path("key.txt").exists():
            with open("key.txt", 'w') as f:
                f.write("# Paste your Gemini API key here\n")
                f.write("# Get it from: https://makersuite.google.com/app/apikey\n")
            log_yellow("Created key.txt - Add your Gemini API key")
            return False
        
        if self.ai.api_key:
            return True
        return False
    
    def get_random_user_agent(self) -> str:
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 Safari/605.1.15',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148',
            'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36'
        ]
        return random.choice(user_agents)
    
    def generate_random_message(self) -> str:
        greetings = ["gm", "Hello everyone", "Hey fam", "Good vibes", "Whats up", "Hi there"]
        middles = [
            "building cool stuff today", 
            "exploring web3", 
            "loving this community", 
            "great day for crypto",
            "excited about whats coming",
            "learning something new"
        ]
        endings = ["Lets go!", "Stay awesome", "WAGMI", "Keep building", "LFG", "Have a great day"]
        hashtags = ["farcaster", "web3", "gm", "wagmi", "crypto", "buidl"]
        
        random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=4))
        
        msg = f"{random.choice(greetings)}! {random.choice(middles)}. {random.choice(endings)} #{random.choice(hashtags)}{random_suffix}"
        return msg
    
    def make_request(self, method: str, endpoint: str, bearer_token: str, 
                    payload: Optional[Dict] = None) -> Optional[requests.Response]:
        url = f"{self.config['api_url']}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "User-Agent": self.get_random_user_agent()
        }
        
        for attempt in range(self.config.get('max_retries', 3)):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=payload,
                    timeout=self.config.get('timeout', 30)
                )
                
                if response.status_code == 429:
                    wait = int(response.headers.get('Retry-After', 60))
                    self.log_account("warn", f"Rate limited! Waiting {wait}s...")
                    time.sleep(wait)
                    continue
                
                return response
                
            except requests.exceptions.RequestException as e:
                self.log_account("error", f"Request failed (attempt {attempt+1}): {e}")
                if attempt < self.config.get('max_retries', 3) - 1:
                    time.sleep(2 ** attempt)
        return None
    
    def verify_token(self, bearer_token: str) -> Tuple[bool, Optional[Dict]]:
        response = self.make_request("GET", "me", bearer_token)
        if response and response.status_code == 200:
            data = response.json()
            if 'result' in data and 'user' in data['result']:
                user = data['result']['user']
                return True, {
                    'fid': user.get('fid'),
                    'username': user.get('username'),
                    'displayName': user.get('displayName')
                }
        return False, None
    
    def get_feed(self, bearer_token: str, limit: int = 100) -> Tuple[bool, List[Dict]]:
        payload = {
            "feedKey": self.config.get('feed_key', 'home'),
            "feedType": self.config.get('feed_type', 'default'),
            "castViewEvents": [],
            "updateState": True
        }
        
        response = self.make_request("POST", "feed-items", bearer_token, payload)
        
        if response and response.status_code == 200:
            data = response.json()
            cast_data = []
            if 'result' in data and 'items' in data['result']:
                for item in data['result']['items'][:limit]:
                    if 'cast' in item:
                        cast = item['cast']
                        author = cast.get('author', {})
                        cast_data.append({
                            'hash': cast.get('hash'),
                            'fid': author.get('fid'),
                            'username': author.get('username', 'unknown'),
                            'text': cast.get('text', '')
                        })
            return True, cast_data
        return False, []
    
    def like_cast(self, bearer_token: str, cast_hash: str) -> bool:
        payload = {"castHash": cast_hash}
        response = self.make_request("PUT", "cast-likes", bearer_token, payload)
        return response.status_code == 200 if response else False
    
    def recast(self, bearer_token: str, cast_hash: str) -> bool:
        payload = {"castHash": cast_hash}
        response = self.make_request("PUT", "recasts", bearer_token, payload)
        return response.status_code == 200 if response else False
    
    def follow_user(self, bearer_token: str, target_fid: int) -> bool:
        payload = {"targetFid": target_fid}
        response = self.make_request("PUT", "follows", bearer_token, payload)
        return response.status_code == 200 if response else False
    
    def post_cast(self, bearer_token: str, text: str) -> bool:
        payload = {"text": text, "embeds": []}
        response = self.make_request("POST", "casts", bearer_token, payload)
        return response.status_code == 201 if response else False
    
    def reply_to_cast(self, bearer_token: str, cast_hash: str, text: str) -> bool:
        payload = {
            "text": text,
            "embeds": [],
            "parent": {"hash": cast_hash}
        }
        response = self.make_request("POST", "casts", bearer_token, payload)
        return response.status_code == 201 if response else False
    
    def mask_token(self, token: str) -> str:
        if len(token) > 12:
            return f"{token[:8]}...{token[-4:]}"
        return "***"
    
    def process_account(self, bearer_token: str, acc_idx: int, actions: List[str]) -> Dict:
        token_masked = self.mask_token(bearer_token)
        
        results = {
            "token": token_masked,
            "login": False,
            "username": "unknown",
            "likes": 0,
            "recasts": 0,
            "follows": 0,
            "comments": 0,
            "posts": 0
        }
        
        print(f"\n{BOLD_MAGENTA}----------------------------------------------------------------------{RESET}")
        print(f"{BOLD_MAGENTA}Account: {BOLD_WHITE}{acc_idx}/{len(self.accounts)}{RESET}")
        print(f"{BOLD_CYAN}Token: {BOLD_WHITE}{token_masked}{RESET}")
        print(f"{BOLD_MAGENTA}----------------------------------------------------------------------{RESET}")
        
        self.log_account("info", "Verifying token...")
        valid, user_info = self.verify_token(bearer_token)
        
        if valid and user_info:
            self.current_account = user_info.get('username', 'unknown')
            results["username"] = self.current_account
            results["login"] = True
            self.log_account("success", f"Logged in as @{self.current_account} (FID: {user_info.get('fid')})")
        else:
            self.log_account("warn", "Token verification failed, continuing...")
            self.current_account = f"Account{acc_idx}"
        
        time.sleep(1)
        
        self.log_account("info", "Fetching feed...")
        success, feed = self.get_feed(bearer_token, 100)
        
        if not success or not feed:
            self.log_account("error", "Failed to get feed")
            return results
        
        self.log_account("success", f"Got {len(feed)} posts from feed")
        random.shuffle(feed)
        
        followed_fids = set()
        
        for action in actions:
            if action == 'post':
                continue
            
            target = self.config.get(f'{action}_count', 5)
            count = 0
            
            print(f"\n{BOLD_YELLOW}[{action.upper()}] Target: {target}{RESET}")
            print(f"{BOLD_CYAN}----------------------------------------------------------------------{RESET}")
            
            for cast in feed:
                if count >= target:
                    break
                
                cast_hash = cast['hash']
                username = cast['username']
                fid = cast['fid']
                text = cast['text'] if cast['text'] else 'No text'
                
                op_success = False
                
                if action == 'like':
                    op_success = self.like_cast(bearer_token, cast_hash)
                    if op_success:
                        log_like(username, text)
                        results['likes'] += 1
                        self.stats['likes'] += 1
                        count += 1
                
                elif action == 'recast':
                    op_success = self.recast(bearer_token, cast_hash)
                    if op_success:
                        log_recast(username, text)
                        results['recasts'] += 1
                        self.stats['recasts'] += 1
                        count += 1
                
                elif action == 'follow':
                    if fid and fid not in followed_fids:
                        op_success = self.follow_user(bearer_token, fid)
                        if op_success:
                            log_follow(username, fid)
                            followed_fids.add(fid)
                            results['follows'] += 1
                            self.stats['follows'] += 1
                            count += 1
                    else:
                        continue
                
                elif action == 'comment':
                    if cast['text']:
                        reply = self.ai.generate_reply(cast['text'])
                        op_success = self.reply_to_cast(bearer_token, cast_hash, reply)
                        if op_success:
                            log_comment(username, reply)
                            results['comments'] += 1
                            self.stats['comments'] += 1
                            count += 1
                
                delay = self.config['rate_limit_delay']
                if action == 'follow':
                    wait = random.uniform(delay['follow_min'], delay['follow_max'])
                else:
                    wait = random.uniform(delay['min'], delay['max'])
                time.sleep(wait)
            
            self.log_account("success", f"{action.upper()}: {count}/{target} completed")
        
        if 'post' in actions:
            post_count = self.config.get('post_count', 1)
            
            print(f"\n{BOLD_YELLOW}[POST] Target: {post_count}{RESET}")
            print(f"{BOLD_CYAN}----------------------------------------------------------------------{RESET}")
            
            for i in range(post_count):
                if self.messages:
                    message = random.choice(self.messages)
                else:
                    message = self.generate_random_message()
                
                if self.post_cast(bearer_token, message):
                    log_post(message)
                    results['posts'] += 1
                    self.stats['posts'] += 1
                else:
                    self.log_account("error", "Failed to post")
                
                if i < post_count - 1:
                    time.sleep(random.uniform(5, 10))
            
            self.log_account("success", f"POST: {results['posts']}/{post_count} completed")
        
        return results
    
    def run_automation(self, actions: List[str]) -> None:
        print(f"\n{BOLD_CYAN}======================================================================{RESET}")
        print(f"{BOLD_GREEN}       STARTING AUTOMATION{RESET}")
        print(f"{BOLD_CYAN}======================================================================{RESET}")
        
        print(f"\n{BOLD_WHITE}Actions: {', '.join([a.upper() for a in actions])}{RESET}")
        print(f"{BOLD_WHITE}Accounts: {len(self.accounts)}{RESET}")
        
        for action in actions:
            if action != 'post':
                print(f"{BOLD_CYAN}  {action.upper()}: {self.config.get(f'{action}_count', 5)}{RESET}")
            else:
                print(f"{BOLD_CYAN}  POST: {self.config.get('post_count', 1)}{RESET}")
        
        all_results = []
        
        for idx, bearer_token in enumerate(self.accounts, 1):
            results = self.process_account(bearer_token, idx, actions)
            all_results.append(results)
            
            if idx < len(self.accounts):
                delay = random.randint(15, 30)
                print(f"\n{BOLD_CYAN}Waiting {delay} seconds before next account...{RESET}")
                time.sleep(delay)
        
        self.print_summary(all_results)
    
    def print_summary(self, all_results: List[Dict]) -> None:
        print(f"\n{BOLD_GREEN}======================================================================{RESET}")
        print(f"{BOLD_GREEN}              SUMMARY{RESET}")
        print(f"{BOLD_GREEN}======================================================================{RESET}")
        
        for result in all_results:
            if result["login"]:
                status = f"{BOLD_GREEN}OK{RESET}"
            else:
                status = f"{BOLD_YELLOW}??{RESET}"
            
            print(f"  {status} {BOLD_WHITE}@{result['username']:<15}{RESET} "
                  f"♥{result['likes']} ↻{result['recasts']} +{result['follows']} "
                  f"💬{result['comments']} ✎{result['posts']}")
        
        print(f"\n{BOLD_CYAN}----------------------------------------------------------------------{RESET}")
        print(f"{BOLD_WHITE}TOTAL STATS:{RESET}")
        print(f"  {BOLD_GREEN}♥ Likes: {self.stats['likes']}{RESET}")
        print(f"  {BOLD_YELLOW}↻ Recasts: {self.stats['recasts']}{RESET}")
        print(f"  {BOLD_CYAN}+ Follows: {self.stats['follows']}{RESET}")
        print(f"  {BOLD_MAGENTA}💬 Comments: {self.stats['comments']}{RESET}")
        print(f"  {BOLD_WHITE}✎ Posts: {self.stats['posts']}{RESET}")
        print(f"{BOLD_GREEN}======================================================================{RESET}\n")
    
    def reset_stats(self) -> None:
        self.stats = {
            'likes': 0,
            'recasts': 0,
            'follows': 0,
            'posts': 0,
            'comments': 0
        }

# ═══════════════════════════════════════════════════════════════════════════════
# MENU
# ═══════════════════════════════════════════════════════════════════════════════

def display_menu() -> None:
    print(f"\n{BOLD_CYAN}----------------------------------------------------------------------{RESET}")
    print(f"{BOLD_WHITE}           MAIN MENU{RESET}")
    print(f"{BOLD_CYAN}----------------------------------------------------------------------{RESET}")
    print(f"  {BOLD_GREEN}[1]{RESET} {BOLD_WHITE}Like Only{RESET}")
    print(f"  {BOLD_GREEN}[2]{RESET} {BOLD_WHITE}Recast Only{RESET}")
    print(f"  {BOLD_GREEN}[3]{RESET} {BOLD_WHITE}Follow Only{RESET}")
    print(f"  {BOLD_GREEN}[4]{RESET} {BOLD_WHITE}Comment Only (AI){RESET}")
    print(f"  {BOLD_GREEN}[5]{RESET} {BOLD_WHITE}Post Only{RESET}")
    print(f"  {BOLD_YELLOW}[6]{RESET} {BOLD_WHITE}Like + Recast{RESET}")
    print(f"  {BOLD_YELLOW}[7]{RESET} {BOLD_WHITE}Like + Follow{RESET}")
    print(f"  {BOLD_YELLOW}[8]{RESET} {BOLD_WHITE}Like + Recast + Follow{RESET}")
    print(f"  {BOLD_MAGENTA}[9]{RESET} {BOLD_WHITE}Full Auto (All Actions){RESET}")
    print(f"  {BOLD_CYAN}[10]{RESET} {BOLD_WHITE}Edit Config{RESET}")
    print(f"  {BOLD_RED}[0]{RESET} {BOLD_WHITE}Exit{RESET}")
    print(f"{BOLD_CYAN}----------------------------------------------------------------------{RESET}")

def edit_config(bot: FarcasterBot) -> None:
    print(f"\n{BOLD_CYAN}======================================================================{RESET}")
    print(f"{BOLD_GREEN}       EDIT CONFIG{RESET}")
    print(f"{BOLD_CYAN}======================================================================{RESET}")
    
    print(f"\n{BOLD_WHITE}Current Settings:{RESET}")
    print(f"  {BOLD_CYAN}Like Count:{RESET} {bot.config.get('like_count', 5)}")
    print(f"  {BOLD_CYAN}Recast Count:{RESET} {bot.config.get('recast_count', 5)}")
    print(f"  {BOLD_CYAN}Follow Count:{RESET} {bot.config.get('follow_count', 5)}")
    print(f"  {BOLD_CYAN}Comment Count:{RESET} {bot.config.get('comment_count', 3)}")
    print(f"  {BOLD_CYAN}Post Count:{RESET} {bot.config.get('post_count', 1)}")
    
    print(f"\n{BOLD_YELLOW}Enter new values (press Enter to keep current):{RESET}")
    
    try:
        like = input(f"  {BOLD_WHITE}Like Count [{bot.config.get('like_count', 5)}]: {RESET}").strip()
        if like:
            bot.config['like_count'] = int(like)
        
        recast = input(f"  {BOLD_WHITE}Recast Count [{bot.config.get('recast_count', 5)}]: {RESET}").strip()
        if recast:
            bot.config['recast_count'] = int(recast)
        
        follow = input(f"  {BOLD_WHITE}Follow Count [{bot.config.get('follow_count', 5)}]: {RESET}").strip()
        if follow:
            bot.config['follow_count'] = int(follow)
        
        comment = input(f"  {BOLD_WHITE}Comment Count [{bot.config.get('comment_count', 3)}]: {RESET}").strip()
        if comment:
            bot.config['comment_count'] = int(comment)
        
        post = input(f"  {BOLD_WHITE}Post Count [{bot.config.get('post_count', 1)}]: {RESET}").strip()
        if post:
            bot.config['post_count'] = int(post)
        
        bot.save_config()
        log_green("Config saved successfully!")
        
    except ValueError:
        log_red("Invalid input! Config not changed.")
    
    input(f"\n{BOLD_YELLOW}Press Enter to continue...{RESET}")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    set_title()
    
    bot = FarcasterBot()
    
    banner()
    
    if not bot.load_config():
        input(f"\n{BOLD_YELLOW}Press Enter to continue...{RESET}")
        return
    
    if not bot.load_accounts():
        print(f"\n{BOLD_YELLOW}Add your Bearer tokens to data.txt{RESET}")
        print(f"{BOLD_WHITE}Format: One token per line{RESET}")
        input(f"\n{BOLD_YELLOW}Press Enter to exit...{RESET}")
        return
    
    bot.load_messages()
    bot.load_api_key()
    
    print(f"\n{BOLD_GREEN}All systems ready!{RESET}")
    time.sleep(1)
    
    action_map = {
        '1': ['like'],
        '2': ['recast'],
        '3': ['follow'],
        '4': ['comment'],
        '5': ['post'],
        '6': ['like', 'recast'],
        '7': ['like', 'follow'],
        '8': ['like', 'recast', 'follow'],
        '9': ['like', 'recast', 'follow', 'comment', 'post']
    }
    
    while True:
        banner()
        display_menu()
        
        choice = input(f"\n{BOLD_YELLOW}Select option: {RESET}").strip()
        
        if choice == '0':
            print(f"\n{BOLD_GREEN}======================================================================{RESET}")
            print(f"{BOLD_RED}     Thank you for using Farcaster Bot{RESET}")
            print(f"{BOLD_MAGENTA}     Created by KAZUHA VIP ONLY{RESET}")
            print(f"{BOLD_GREEN}======================================================================{RESET}\n")
            sys.exit(0)
        
        elif choice == '10':
            edit_config(bot)
        
        elif choice in action_map:
            actions = action_map[choice]
            bot.reset_stats()
            bot.run_automation(actions)
            input(f"\n{BOLD_YELLOW}Press Enter to continue...{RESET}")
        
        else:
            log_red("Invalid option! Please select a valid option.")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{BOLD_YELLOW}Interrupted by user{RESET}")
        print(f"{BOLD_GREEN}======================================================================{RESET}")
        print(f"{BOLD_RED}[ EXIT ] Farcaster Bot{RESET}")
        print(f"{BOLD_MAGENTA}Created by KAZUHA VIP ONLY{RESET}")
        print(f"{BOLD_GREEN}======================================================================{RESET}\n")
        sys.exit(0)