import os
import sys
import random
import requests
import pyfiglet
import json
import time
from datetime import datetime
from typing import Optional, List, Dict

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

def clear_screen() -> None:
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

def banner() -> None:
    clear_screen()
    print(f"{BOLD_CYAN}======================================================================{RESET}")
    print(f"{BOLD_GREEN}       RICHECOIN TESTNET AUTO BOT{RESET}")
    print(f"{BOLD_MAGENTA}       Created by KAZUHA VIP ONLY{RESET}")
    print(f"{BOLD_CYAN}======================================================================{RESET}")

def set_title() -> None:
    try:
        sys.stdout.write("\x1b]2;Richecoin Testnet Bot - By KAZUHA\x1b\\")
        sys.stdout.flush()
    except Exception:
        pass

BASE_URL = "https://richecoin.org/rewards/api"
API_LOGIN = f"{BASE_URL}/login.php"
API_DAILY_CLAIM = f"{BASE_URL}/claim_daily.php"
API_CLAIM_TASK = f"{BASE_URL}/claim_task.php"
API_USER_DATA = f"{BASE_URL}/get_user_data.php"

DEFAULT_REF_ADDRESS = "0xab3f670120987d2592e98476c8a3b304c65956bc"

HEX_CHARS = "0123456789abcdef"

class AccountManager:
    def __init__(self):
        self.accounts: List[Dict] = []
        self.sessions: Dict[str, requests.Session] = {}
    
    def load_accounts_from_file(self, filename: str = "pv.txt") -> bool:
        try:
            if not os.path.exists(filename):
                log_red(f"File {filename} not found")
                return False
            
            self.accounts = []
            with open(filename, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line and ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            address_or_key = parts[0].strip()
                            name = parts[1].strip()
                            
                            if address_or_key.startswith('0x') and len(address_or_key) == 42:
                                address = address_or_key
                            else:
                                address = self.generate_address_from_key(address_or_key)
                                if not address:
                                    address = self.generate_random_address()
                            
                            self.accounts.append({
                                "address": address,
                                "name": name,
                                "session_id": None
                            })
            
            if self.accounts:
                log_green(f"Loaded {len(self.accounts)} accounts from {filename}")
                return True
            else:
                log_yellow(f"No valid accounts found in {filename}")
                return False
                
        except Exception as e:
            log_red(f"Failed to load accounts: {e}")
            return False
    
    def generate_address_from_key(self, private_key: str) -> Optional[str]:
        try:
            from eth_account import Account
            account = Account.from_key(private_key)
            return account.address
        except:
            return None
    
    def generate_random_address(self) -> str:
        return "0x" + "".join(random.choice(HEX_CHARS) for _ in range(40))
    
    def get_session(self, address: str) -> requests.Session:
        if address not in self.sessions:
            self.sessions[address] = requests.Session()
        return self.sessions[address]
    
    def mask_address(self, address: str) -> str:
        if len(address) > 12:
            return f"{address[:6]}...{address[-4:]}"
        return address

class RichecoinBot:
    def __init__(self):
        self.account_manager = AccountManager()
        self.current_name = ""
        
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Safari/605.1.15",
            "Origin": "https://richecoin.org",
            "Referer": "https://richecoin.org/rewards/dashboard",
        }
        
        self.tasks_info = {
            "1": {"title": "Follow Twitter", "points": 50},
            "2": {"title": "Join Discord", "points": 50},
            "3": {"title": "Use Faucet", "points": 100},
            "4": {"title": "Create Token", "points": 100},
            "5": {"title": "Join Channel", "points": 50},
            "6": {"title": "Join Group", "points": 50},
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
        print(f"{BOLD_YELLOW}[{self.current_name}] {color}{message}{RESET}")
    
    def generate_eth_address(self) -> str:
        return "0x" + "".join(random.choice(HEX_CHARS) for _ in range(40))
    
    def login_with_new_address(self, index: int, ref: Optional[str] = None) -> bool:
        address = self.generate_eth_address()
        log_yellow(f"Processing address number {index}")
        log_cyan(f"Generated: {address}")
        
        payload = {
            "address": address,
            "ref": ref if ref else DEFAULT_REF_ADDRESS,
        }
        
        try:
            response = requests.post(API_LOGIN, headers=self.headers, json=payload, timeout=15)
            
            if response.status_code == 200:
                log_green(f"Address number {index} registered successfully status 200")
                return True
            else:
                log_red(f"Address number {index} failed status {response.status_code}")
                return False
                
        except requests.RequestException as e:
            log_red(f"Request failed for address number {index}: {e}")
            return False
    
    def run_auto_referral(self) -> None:
        print(f"\n{BOLD_CYAN}======================================================================{RESET}")
        print(f"{BOLD_GREEN}         AUTO REFERRAL - Generate Addresses{RESET}")
        print(f"{BOLD_CYAN}======================================================================{RESET}\n")
        
        print(f"{BOLD_YELLOW}Enter your referral address or press Enter for default:{RESET}")
        print(f"{BOLD_CYAN}Default: {DEFAULT_REF_ADDRESS}{RESET}")
        ref_input = input(f"{BOLD_WHITE}>>> {RESET}").strip()
        
        ref_address = ref_input if ref_input.startswith("0x") and len(ref_input) == 42 else DEFAULT_REF_ADDRESS
        log_cyan(f"Using referral: {ref_address}")
        
        while True:
            try:
                count_str = input(f"\n{BOLD_YELLOW}Enter number of addresses to generate: {RESET}")
                count = int(count_str)
                if count <= 0:
                    log_red("Value must be greater than zero")
                    continue
                break
            except ValueError:
                log_red("Invalid input please enter a number")
                continue
        
        print(f"\n{BOLD_MAGENTA}Starting auto referral...{RESET}\n")
        
        successful = 0
        failed = 0
        
        for i in range(1, count + 1):
            print(f"{BOLD_CYAN}----------------------------------------------------------------------{RESET}")
            if self.login_with_new_address(i, ref_address):
                successful += 1
            else:
                failed += 1
            
            if i < count:
                delay = random.uniform(1, 3)
                time.sleep(delay)
        
        print(f"\n{BOLD_GREEN}======================================================================{RESET}")
        print(f"{BOLD_GREEN}         AUTO REFERRAL COMPLETED{RESET}")
        print(f"{BOLD_GREEN}======================================================================{RESET}")
        print(f"{BOLD_WHITE}Total Addresses: {count}{RESET}")
        print(f"{BOLD_GREEN}Successful: {successful}{RESET}")
        print(f"{BOLD_RED}Failed: {failed}{RESET}")
        print(f"{BOLD_GREEN}======================================================================{RESET}\n")
        
        input(f"{BOLD_YELLOW}Press Enter to continue...{RESET}")
    
    def login_account(self, address: str, session: requests.Session) -> Optional[str]:
        payload = {
            "address": address,
            "ref": DEFAULT_REF_ADDRESS,
        }
        
        try:
            response = session.post(API_LOGIN, headers=self.headers, json=payload, timeout=15)
            
            if response.status_code == 200:
                session_id = session.cookies.get('PHPSESSID')
                self.log_account("success", f"Login successful")
                return session_id
            else:
                self.log_account("error", f"Login failed status {response.status_code}")
                return None
                
        except Exception as e:
            self.log_account("error", f"Login error: {e}")
            return None
    
    def get_user_data(self, session: requests.Session) -> Optional[Dict]:
        try:
            response = session.get(API_USER_DATA, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return data.get("data", {})
            return None
            
        except Exception as e:
            self.log_account("error", f"Failed to get user data: {e}")
            return None
    
    def claim_daily_reward(self, session: requests.Session) -> bool:
        try:
            response = session.post(API_DAILY_CLAIM, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    points = data.get("points_added", 0)
                    streak = data.get("new_streak", 0)
                    total = data.get("new_total", 0)
                    
                    self.log_account("success", f"Daily reward claimed +{points} points")
                    self.log_account("info", f"Streak: Day {streak} Total: {total} points")
                    return True
                else:
                    message = data.get("message", "Unknown error")
                    self.log_account("warn", f"Daily claim: {message}")
                    return False
            return False
            
        except Exception as e:
            self.log_account("error", f"Daily claim error: {e}")
            return False
    
    def claim_task(self, session: requests.Session, task_id: str) -> bool:
        payload = {"task_id": int(task_id)}
        
        try:
            response = session.post(
                API_CLAIM_TASK, 
                headers=self.headers, 
                json=payload, 
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    points = data.get("points_added", 0)
                    task_info = self.tasks_info.get(task_id, {})
                    task_title = task_info.get("title", f"Task {task_id}")
                    
                    self.log_account("success", f"Task {task_title} completed +{points} points")
                    return True
                else:
                    message = data.get("message", "Unknown error")
                    self.log_account("warn", f"Task {task_id}: {message}")
                    return False
            return False
            
        except Exception as e:
            self.log_account("error", f"Task claim error: {e}")
            return False
    
    def process_account(self, account: Dict) -> Dict:
        address = account["address"]
        name = account["name"]
        self.current_name = name
        
        results = {
            "name": name,
            "address": address,
            "login": False,
            "daily_claimed": False,
            "tasks_completed": 0,
            "total_points": 0
        }
        
        print(f"\n{BOLD_MAGENTA}----------------------------------------------------------------------{RESET}")
        print(f"{BOLD_MAGENTA}Account: {BOLD_WHITE}{name}{RESET}")
        print(f"{BOLD_CYAN}Address: {BOLD_WHITE}{self.account_manager.mask_address(address)}{RESET}")
        print(f"{BOLD_MAGENTA}----------------------------------------------------------------------{RESET}")
        
        session = self.account_manager.get_session(address)
        
        self.log_account("info", "Logging in...")
        session_id = self.login_account(address, session)
        
        if not session_id:
            self.log_account("error", "Failed to login skipping account")
            return results
        
        results["login"] = True
        time.sleep(1)
        
        self.log_account("info", "Fetching user data...")
        user_data = self.get_user_data(session)
        
        if user_data:
            current_points = user_data.get("points", 0)
            rank = user_data.get("rank", "Unknown")
            referrals = user_data.get("referrals", {}).get("count", 0)
            
            self.log_account("info", f"Points: {current_points} Rank: {rank} Referrals: {referrals}")
        
        time.sleep(1)
        
        print(f"\n{BOLD_YELLOW}[DAILY CHECK-IN]{RESET}")
        
        if user_data:
            daily_login = user_data.get("daily_login", {})
            can_claim = daily_login.get("can_claim", False)
            
            if can_claim:
                self.log_account("info", "Claiming daily reward...")
                if self.claim_daily_reward(session):
                    results["daily_claimed"] = True
            else:
                streak = daily_login.get("streak", 0)
                self.log_account("warn", f"Daily already claimed Current streak: Day {streak}")
        else:
            self.log_account("info", "Attempting daily claim...")
            if self.claim_daily_reward(session):
                results["daily_claimed"] = True
        
        time.sleep(1)
        
        print(f"\n{BOLD_YELLOW}[TASKS]{RESET}")
        
        if user_data:
            tasks = user_data.get("tasks", [])
            
            for task in tasks:
                task_id = task.get("id", "")
                title = task.get("title", "Unknown")
                points = task.get("points", 0)
                completed = task.get("completed", False)
                
                if completed:
                    self.log_account("info", f"Task {title} already completed")
                else:
                    self.log_account("task", f"Claiming task: {title} +{points} pts")
                    if self.claim_task(session, task_id):
                        results["tasks_completed"] += 1
                    time.sleep(random.uniform(1, 2))
        else:
            for task_id, task_info in self.tasks_info.items():
                self.log_account("task", f"Claiming task: {task_info['title']}")
                if self.claim_task(session, task_id):
                    results["tasks_completed"] += 1
                time.sleep(random.uniform(1, 2))
        
        time.sleep(1)
        final_data = self.get_user_data(session)
        if final_data:
            results["total_points"] = final_data.get("points", 0)
            self.log_account("success", f"Final points: {results['total_points']}")
        
        return results
    
    def run_daily_checkin_tasks(self) -> None:
        print(f"\n{BOLD_CYAN}======================================================================{RESET}")
        print(f"{BOLD_GREEN}       DAILY CHECK-IN AND TASKS{RESET}")
        print(f"{BOLD_CYAN}======================================================================{RESET}\n")
        
        if not self.account_manager.load_accounts_from_file("pv.txt"):
            print(f"{BOLD_YELLOW}No accounts found in pv.txt{RESET}")
            print(f"{BOLD_YELLOW}Enter address:name or press Enter to go back:{RESET}")
            
            manual_input = input(f"{BOLD_WHITE}>>> {RESET}").strip()
            
            if not manual_input:
                return
            
            if ':' in manual_input:
                parts = manual_input.split(':', 1)
                address = parts[0].strip()
                name = parts[1].strip()
                
                if not address.startswith('0x'):
                    address = self.account_manager.generate_random_address()
                
                self.account_manager.accounts = [{
                    "address": address,
                    "name": name,
                    "session_id": None
                }]
            else:
                log_red("Invalid format Use address:name")
                input(f"{BOLD_YELLOW}Press Enter to continue...{RESET}")
                return
        
        print(f"\n{BOLD_GREEN}Found {len(self.account_manager.accounts)} accounts{RESET}\n")
        
        all_results = []
        
        for idx, account in enumerate(self.account_manager.accounts, 1):
            print(f"\n{BOLD_CYAN}Processing Account {idx}/{len(self.account_manager.accounts)}{RESET}")
            
            results = self.process_account(account)
            all_results.append(results)
            
            if idx < len(self.account_manager.accounts):
                delay = random.randint(3, 6)
                print(f"\n{BOLD_CYAN}Waiting {delay} seconds before next account...{RESET}")
                time.sleep(delay)
        
        print(f"\n{BOLD_GREEN}======================================================================{RESET}")
        print(f"{BOLD_GREEN}              SUMMARY{RESET}")
        print(f"{BOLD_GREEN}======================================================================{RESET}")
        
        total_daily = sum(1 for r in all_results if r["daily_claimed"])
        total_tasks = sum(r["tasks_completed"] for r in all_results)
        
        for result in all_results:
            if result["login"]:
                status = f"{BOLD_GREEN}OK{RESET}"
            else:
                status = f"{BOLD_RED}FAIL{RESET}"
            
            if result["daily_claimed"]:
                daily = f"{BOLD_GREEN}YES{RESET}"
            else:
                daily = f"{BOLD_YELLOW}NO{RESET}"
            
            print(f"  {status} {BOLD_WHITE}{result['name']:<15}{RESET} Daily: {daily} Tasks: {result['tasks_completed']} Points: {result['total_points']}")
        
        print(f"\n{BOLD_CYAN}Total Daily Claims: {total_daily}/{len(all_results)}{RESET}")
        print(f"{BOLD_CYAN}Total Tasks Completed: {total_tasks}{RESET}")
        print(f"{BOLD_GREEN}======================================================================{RESET}\n")
        
        input(f"{BOLD_YELLOW}Press Enter to continue...{RESET}")

def display_menu() -> None:
    print(f"\n{BOLD_CYAN}----------------------------------------------------------------------{RESET}")
    print(f"{BOLD_WHITE}           MAIN MENU{RESET}")
    print(f"{BOLD_CYAN}----------------------------------------------------------------------{RESET}")
    print(f"  {BOLD_GREEN}[1]{RESET} {BOLD_WHITE}Auto Referral{RESET}")
    print(f"  {BOLD_YELLOW}[2]{RESET} {BOLD_WHITE}Daily Check-in and Tasks{RESET}")
    print(f"  {BOLD_RED}[3]{RESET} {BOLD_WHITE}Exit{RESET}")
    print(f"{BOLD_CYAN}----------------------------------------------------------------------{RESET}")

def main() -> None:
    set_title()
    bot = RichecoinBot()
    
    while True:
        banner()
        display_menu()
        
        choice = input(f"\n{BOLD_YELLOW}Select option [1-3]: {RESET}").strip()
        
        if choice == "1":
            bot.run_auto_referral()
        
        elif choice == "2":
            bot.run_daily_checkin_tasks()
        
        elif choice == "3":
            print(f"\n{BOLD_GREEN}======================================================================{RESET}")
            print(f"{BOLD_RED}     Thank you for using Richecoin Bot{RESET}")
            print(f"{BOLD_MAGENTA}     Created by KAZUHA VIP ONLY{RESET}")
            print(f"{BOLD_GREEN}======================================================================{RESET}\n")
            sys.exit(0)
        
        else:
            log_red("Invalid option Please select 1 2 or 3")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{BOLD_YELLOW}Interrupted by user{RESET}")
        print(f"{BOLD_GREEN}======================================================================{RESET}")
        print(f"{BOLD_RED}[ EXIT ] Richecoin Bot{RESET}")
        print(f"{BOLD_GREEN}======================================================================{RESET}\n")
        sys.exit(0)