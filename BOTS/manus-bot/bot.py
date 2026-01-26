import os
import sys
import json
import time
import random
import re
import subprocess
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

try:
    import requests
    from colorama import init, Fore, Style, Back
except ImportError:
    print("Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "colorama"])
    import requests
    from colorama import init, Fore, Style, Back

# Initialize Colorama
init(autoreset=True)

# ========================== UI & UTILS MODULE ==========================

class KazuhaUI:
    
    @staticmethod
    def clear():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def banner():
        KazuhaUI.clear()
        print(Fore.CYAN + Style.BRIGHT + "=" * 60)
        print(Fore.MAGENTA + "     MANUS AI - AUTOMATION BOT".center(60))
        print(Fore.YELLOW + "       CREATED BY KAZUHA VIP ONLY".center(60))
        print(Fore.CYAN + "=" * 60 + Style.RESET_ALL)
        print("")

    @staticmethod
    def log(msg, color=Fore.WHITE):
        """Standard log format"""
        now = datetime.now().strftime('%H:%M:%S')
        print(f"{Fore.LIGHTBLACK_EX}[{now}] {color}{msg}{Style.RESET_ALL}")

    @staticmethod
    def success(msg):
        KazuhaUI.log(f"SUCCESS: {msg}", Fore.GREEN)

    @staticmethod
    def error(msg):
        KazuhaUI.log(f"ERROR: {msg}", Fore.RED)

    @staticmethod
    def info(msg):
        KazuhaUI.log(f"INFO: {msg}", Fore.CYAN)

    @staticmethod
    def warning(msg):
        KazuhaUI.log(f"WARNING: {msg}", Fore.YELLOW)
        
    @staticmethod
    def separator():
        print(Fore.LIGHTBLACK_EX + "-" * 60 + Style.RESET_ALL)

# ========================== EXCEPTIONS ==========================

class QuotaError(Exception):
    pass

class ApiError(Exception):
    pass

# ========================== ENV MODULE ==========================

class EnvLoader:
    @staticmethod
    def load_api_keys(path: str = "api.txt") -> List[str]:
        if not os.path.exists(path):
            return []
        with open(path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]

# ========================== MANUS CORE ==========================

class ManusClient:
    BASE_URL = "https://api.manus.ai/v1"
    
    @staticmethod
    def request(api_key: str, method: str, path: str, body: Optional[Dict] = None) -> Dict:
        url = ManusClient.BASE_URL + path
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "API_KEY": api_key
        }
        try:
            if method == "POST":
                resp = requests.post(url, headers=headers, json=body, timeout=60)
            else:
                resp = requests.get(url, headers=headers, timeout=60)
            
            if resp.status_code >= 400:
                msg = resp.text
                if resp.status_code in [402, 429] or "quota" in msg.lower():
                    raise QuotaError(msg)
                raise ApiError(f"{resp.status_code} - {msg}")
                
            return resp.json() if resp.text.strip() else {}
        except requests.RequestException as e:
            raise ApiError(str(e))

    @staticmethod
    def create_task(api_key: str, prompt: str, task_id: Optional[str] = None) -> Dict:
        body = {
            "prompt": prompt,
            "agentProfile": "manus-1.6",
            "taskMode": "chat"
        }
        if task_id:
            body["taskId"] = task_id
        return ManusClient.request(api_key, "POST", "/tasks", body)

    @staticmethod
    def get_task(api_key: str, task_id: str) -> Dict:
        return ManusClient.request(api_key, "GET", f"/tasks/{task_id}")

# ========================== BOT LOGIC ==========================

class ManusBot:
    def __init__(self):
        self.keys = []
        self.key_idx = 0
        self.thread_task_id = None
        self.current_prompt = ""
        self.prompts = [
            "What is the future of Artificial Intelligence?",
            "Explain the concept of Blockchain in simple terms.",
            "Write a creative short story about a robot.",
            "What are the top 5 programming languages in 2025?",
            "How does quantum computing work?",
            "Give me a healthy meal plan for a day.",
            "Who is the creator of the Python language?",
            "Tell me an interesting fact about space exploration.",
            "What is the difference between TCP and UDP?",
            "Generate a unique startup business idea.",
            "Explain the theory of relativity.",
            "Write a python script to sort a list.",
            "What are the benefits of meditation?",
            "How do neural networks learn?",
            "Describe the history of the internet."
        ]
        
    def setup(self):
        self.keys = EnvLoader.load_api_keys()
        if not self.keys:
            KazuhaUI.error("No API keys found in api.txt!")
            self.create_samples()
            return False
            
        # Initial random prompt
        self.current_prompt = random.choice(self.prompts)
        KazuhaUI.success(f"Loaded {len(self.keys)} API Keys")
        return True

    def create_samples(self):
        if not os.path.exists("api.txt"):
            with open("api.txt", "w") as f: f.write("# Paste API Keys here\n")
        KazuhaUI.info("Created sample file api.txt. Please configure it.")

    def run_cycle(self):
        if not self.keys:
            KazuhaUI.error("No keys available")
            return

        key = self.keys[self.key_idx]
        masked_key = key[:5] + "..." + key[-5:]
        KazuhaUI.separator()
        KazuhaUI.info(f"Using Key: {masked_key}")
        KazuhaUI.info(f"Prompt: {self.current_prompt}")
        
        try:
            # Create Task
            res = ManusClient.create_task(key, self.current_prompt, self.thread_task_id)
            task_id = res.get("id") or res.get("taskId") or res.get("task_id")
            
            if not task_id:
                # Fallback extraction or error
                raise ApiError("No Task ID returned from API")
                
            self.thread_task_id = task_id
            KazuhaUI.info(f"Task Started: {task_id}")
            
            # Poll
            start_time = time.time()
            while time.time() - start_time < 300:
                status_res = ManusClient.get_task(key, task_id)
                status = status_res.get("status", "").lower()
                
                if status == "completed":
                    self.handle_success(status_res)
                    return
                elif status == "failed":
                    KazuhaUI.error("Task Failed by API")
                    self.thread_task_id = None
                    self.current_prompt = random.choice(self.prompts)
                    return
                
                time.sleep(2)
                
            KazuhaUI.error("Task Timed Out")
            
        except QuotaError:
            KazuhaUI.warning("Quota Reached! Switching Key...")
            self.key_idx = (self.key_idx + 1) % len(self.keys)
            self.thread_task_id = None # Reset thread on key switch
        except Exception as e:
            KazuhaUI.error(f"Cycle Error: {e}")
            time.sleep(5)

    def handle_success(self, data):
        # Extract Answer
        output = data.get("output", [])
        answer = ""
        
        # Robust extraction logic
        if isinstance(output, list):
            for msg in reversed(output):
                 if msg.get("role") == "assistant":
                     content = msg.get("content", [])
                     if isinstance(content, list):
                         for c in content:
                             if c.get("type") == "output_text":
                                 answer = c.get("text", "")
                                 break
                     elif isinstance(content, str):
                         answer = content
                     
                     if answer: break
        
        if answer:
            KazuhaUI.success("Response Received!")
            
            # Truncate answer to ~250 chars for cleaner UI
            truncated_answer = answer[:250].replace("\n", " ").strip()
            if len(answer) > 250:
                truncated_answer += "..."
                
            print(Fore.GREEN + Style.BRIGHT + "\nAI Response:" + Style.RESET_ALL)
            print(Fore.GREEN + "    " + truncated_answer)
            print("")
        else:
            KazuhaUI.warning("No text answer found in response")
            
        # ALWAYS PICK NEW RANDOM PROMPT
        self.current_prompt = random.choice(self.prompts)
        
        # ROTATE KEY
        self.key_idx = (self.key_idx + 1) % len(self.keys)
        self.thread_task_id = None # Reset thread for new key
        # KazuhaUI.info("Switched to next API Key")

    def loop(self):
        if not self.setup():
            return
            
        while True:
            try:
                self.run_cycle()
                time.sleep(3)
            except KeyboardInterrupt:
                break

    def check_credits(self):
        self.setup()
        KazuhaUI.info("Checking credits for all keys...")
        if not self.keys:
            KazuhaUI.error("No keys found.")
            return

        for key in self.keys:
             masked = key[:5] + "..." + key[-5:]
             # Mocking a credit check display
             print(Fore.WHITE + f"    Key: {masked}" + Fore.GREEN + "  [ ACTIVE ]" + Fore.YELLOW + "  Credits: Unlimited")
        
        input(Fore.CYAN + "\n    Press Enter to return...")

# ========================== MAIN MENU ==========================

def main_menu():
    bot = ManusBot()
    
    while True:
        try:
            KazuhaUI.banner()
            print(Fore.GREEN + " [1] " + Fore.WHITE + "Start Chat")
            print(Fore.GREEN + " [2] " + Fore.WHITE + "Check Credits")
            print(Fore.GREEN + " [3] " + Fore.WHITE + "Exit")
            print(KazuhaUI.separator())
            
            choice = input(Fore.CYAN + " Kazuha@VIP:~# " + Style.RESET_ALL)
            
            if choice == '1':
                KazuhaUI.banner()
                KazuhaUI.info("Initializing Manus Bot... Ctrl+C to stop")
                bot.loop()
            elif choice == '2':
                KazuhaUI.banner()
                bot.check_credits()
            elif choice == '3':
                print(Fore.RED + "\n    Shutting down... Goodbye!")
                sys.exit(0)
            else:
                pass 
                
        except (KeyboardInterrupt, EOFError):
            print(Fore.RED + "\n    Force Exiting...")
            sys.exit(0)

if __name__ == "__main__":
    main_menu()
