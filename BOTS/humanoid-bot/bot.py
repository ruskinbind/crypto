from curl_cffi import requests
from curl_cffi.requests import Session
from fake_useragent import FakeUserAgent
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import to_hex
import random
import string
import json
import os
import time

# COLORS
RED = "\033[1;91m"
GREEN = "\033[1;92m"
YELLOW = "\033[1;93m"
BLUE = "\033[1;94m"
MAGENTA = "\033[1;95m"
CYAN = "\033[1;96m"
WHITE = "\033[1;97m"
RESET = "\033[0m"
BOLD = "\033[1m"


class Humanoid:
    def __init__(self):
        self.BASE_API = "https://app.humanoidnetwork.org/api"
        self.HF_API = "https://huggingface.co"
        self.REF_CODE = ""
        self.HEADERS = {}
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.access_tokens = {}
        self.ref_file = "reff.json"
        self.use_proxy = False

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(message, flush=True)

    def print_banner(self):
        self.clear_terminal()
        print(f"{CYAN}{'='*60}{RESET}")
        print(f"{BOLD}{MAGENTA}              HUMANOID AUTO BOT{RESET}")
        print(f"{BOLD}{YELLOW}              CREATED BY KAZUHA VIP ONLY{RESET}")
        print(f"{CYAN}{'='*60}{RESET}")
        print()

    def print_menu(self):
        print(f"{GREEN}{'-'*60}{RESET}")
        print(f"{BOLD}{WHITE}  [1] CLAIM DAILY CHECK (Social Tasks Only){RESET}")
        print(f"{BOLD}{WHITE}  [2] TRAINING (Models & Datasets){RESET}")
        print(f"{BOLD}{WHITE}  [3] AUTO REFF{RESET}")
        print(f"{BOLD}{WHITE}  [4] RUN REFF ACCOUNTS{RESET}")
        print(f"{BOLD}{WHITE}  [5] EXIT{RESET}")
        print(f"{GREEN}{'-'*60}{RESET}")
        print()

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    def load_ref_code(self):
        filename = "code.txt"
        try:
            if not os.path.exists(filename):
                self.log(f"{RED}[ERROR] code.txt not found!{RESET}")
                self.log(f"{YELLOW}[INFO] Create code.txt and add your referral code{RESET}")
                return False
            with open(filename, 'r') as f:
                code = f.read().strip()
            if not code:
                self.log(f"{RED}[ERROR] No referral code found in code.txt{RESET}")
                return False
            self.REF_CODE = code
            self.log(f"{GREEN}[INFO] Referral Code Loaded: {WHITE}{self.REF_CODE}{RESET}")
            return True
        except Exception as e:
            self.log(f"{RED}[ERROR] Failed to load referral code: {e}{RESET}")
            return False

    def load_reff_accounts(self):
        if os.path.exists(self.ref_file):
            try:
                with open(self.ref_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_reff_account(self, private_key, address):
        accounts = self.load_reff_accounts()
        for acc in accounts:
            if acc.get("address") == address:
                return
        accounts.append({"private_key": private_key, "address": address})
        with open(self.ref_file, 'w') as f:
            json.dump(accounts, f, indent=2)

    def load_proxies(self):
        filename = "proxy.txt"
        try:
            if not os.path.exists(filename):
                self.log(f"{YELLOW}[INFO] proxy.txt not found, using direct connection{RESET}")
                self.proxies = []
                self.use_proxy = False
                return False
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            if not self.proxies:
                self.log(f"{YELLOW}[INFO] No proxies found, using direct connection{RESET}")
                self.use_proxy = False
                return False
            self.log(f"{GREEN}[INFO] Proxies Loaded: {WHITE}{len(self.proxies)}{RESET}")
            self.use_proxy = True
            return True
        except Exception as e:
            self.log(f"{RED}[ERROR] Failed to load proxies: {e}{RESET}")
            self.proxies = []
            self.use_proxy = False
            return False

    def load_accounts(self):
        filename = "pv.txt"
        try:
            if not os.path.exists(filename):
                self.log(f"{RED}[ERROR] pv.txt not found!{RESET}")
                self.log(f"{YELLOW}[INFO] Create pv.txt and add private keys{RESET}")
                return []
            with open(filename, 'r') as f:
                accounts = [line.strip() for line in f.read().splitlines() if line.strip()]
            if not accounts:
                self.log(f"{RED}[ERROR] No accounts found in pv.txt{RESET}")
                return []
            return accounts
        except Exception as e:
            self.log(f"{RED}[ERROR] Failed to load accounts: {e}{RESET}")
            return []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, account):
        if not self.use_proxy or not self.proxies:
            return None
        if account not in self.account_proxies:
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        if not self.use_proxy or not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy

    def get_proxy_dict(self, proxy_url):
        if not proxy_url:
            return None
        return {"http": proxy_url, "https": proxy_url}

    def generate_address(self, account: str):
        try:
            if not account.startswith('0x'):
                account = '0x' + account
            acc = Account.from_key(account)
            return acc.address
        except Exception as e:
            self.log(f"{RED}[ERROR] Invalid key: {e}{RESET}")
            return None

    def generate_payload(self, account: str, address: str, message: str):
        if not account.startswith('0x'):
            account = '0x' + account
        encoded_message = encode_defunct(text=message)
        signed_message = Account.sign_message(encoded_message, private_key=account)
        signature = to_hex(signed_message.signature)
        return {"walletAddress": address, "signature": signature, "message": message}

    def generate_random_x_handle(self, min_len=5, max_len=12):
        chars = string.ascii_lowercase + string.digits
        length = random.randint(min_len, max_len)
        return ''.join(random.choice(chars) for _ in range(length))

    def generate_tweet_id(self, x_handle):
        if x_handle is None:
            x_handle = self.generate_random_x_handle()
        tweet_id = str(random.randint(10**17, 10**18 - 1))
        return {"tweetId": f"https://x.com/{x_handle}/status/{tweet_id}"}

    def mask_account(self, account):
        try:
            return account[:6] + '*' * 6 + account[-6:]
        except:
            return None

    def setup_headers(self, address):
        self.HEADERS[address] = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://app.humanoidnetwork.org",
            "referer": "https://app.humanoidnetwork.org/",
            "user-agent": FakeUserAgent().random
        }

    def auth_nonce(self, address: str, proxy_url=None, retries=3):
        url = f"{self.BASE_API}/auth/nonce"
        data = {"walletAddress": address}
        headers = self.HEADERS[address]
        proxy_dict = self.get_proxy_dict(proxy_url)
        
        for attempt in range(retries):
            try:
                session = requests.Session(impersonate="chrome124")
                response = session.post(url, json=data, headers=headers, proxies=proxy_dict, timeout=30)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.log(f"{YELLOW}[WARN] Nonce status: {response.status_code}{RESET}")
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(2)
        return None

    def auth_authenticate(self, account: str, address: str, message: str, proxy_url=None, retries=3, include_ref=False, ref_code=None):
        url = f"{self.BASE_API}/auth/authenticate"
        payload = self.generate_payload(account, address, message)
        
        # Only include referral code if specified
        if include_ref and ref_code:
            payload["referralCode"] = ref_code
        
        headers = self.HEADERS[address]
        proxy_dict = self.get_proxy_dict(proxy_url)
        
        for attempt in range(retries):
            try:
                session = requests.Session(impersonate="chrome124")
                response = session.post(url, json=payload, headers=headers, proxies=proxy_dict, timeout=30)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(2)
        return None

    def user_data(self, address: str, proxy_url=None, retries=3):
        url = f"{self.BASE_API}/user"
        headers = {**self.HEADERS[address], "authorization": f"Bearer {self.access_tokens[address]}"}
        proxy_dict = self.get_proxy_dict(proxy_url)
        
        for attempt in range(retries):
            try:
                session = requests.Session(impersonate="chrome124")
                response = session.get(url, headers=headers, proxies=proxy_dict, timeout=30)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(2)
        return None

    def apply_ref(self, address: str, ref_code: str, proxy_url=None, retries=3):
        url = f"{self.BASE_API}/referral/apply"
        data = {"referralCode": ref_code}
        headers = {**self.HEADERS[address], "authorization": f"Bearer {self.access_tokens[address]}"}
        proxy_dict = self.get_proxy_dict(proxy_url)
        
        for attempt in range(retries):
            try:
                session = requests.Session(impersonate="chrome124")
                response = session.post(url, json=data, headers=headers, proxies=proxy_dict, timeout=30)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 400:
                    return None
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(2)
        return None

    def training_progress(self, address: str, proxy_url=None, retries=3):
        url = f"{self.BASE_API}/training/progress"
        headers = {**self.HEADERS[address], "authorization": f"Bearer {self.access_tokens[address]}"}
        proxy_dict = self.get_proxy_dict(proxy_url)
        
        for attempt in range(retries):
            try:
                session = requests.Session(impersonate="chrome124")
                response = session.get(url, headers=headers, proxies=proxy_dict, timeout=30)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(2)
        return None

    def scrape_huggingface(self, endpoint: str, limit: int, proxy_url=None, retries=3):
        url = f"{self.HF_API}/api/{endpoint}"
        params = {"limit": limit + 100, "sort": "lastModified", "direction": -1}
        proxy_dict = self.get_proxy_dict(proxy_url)
        
        for attempt in range(retries):
            try:
                session = requests.Session(impersonate="chrome124")
                response = session.get(url, params=params, proxies=proxy_dict, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    random.shuffle(data)
                    return data[:limit + 50]
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(2)
        return None

    def submit_training(self, address: str, training_data: dict, proxy_url=None, retries=3):
        url = f"{self.BASE_API}/training"
        headers = {**self.HEADERS[address], "authorization": f"Bearer {self.access_tokens[address]}"}
        headers["referer"] = "https://app.humanoidnetwork.org/training"
        proxy_dict = self.get_proxy_dict(proxy_url)
        
        for attempt in range(retries):
            try:
                session = requests.Session(impersonate="chrome124")
                response = session.post(url, json=training_data, headers=headers, proxies=proxy_dict, timeout=30)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 400:
                    return None
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(2)
        return None

    def task_lists(self, address: str, proxy_url=None, retries=3):
        url = f"{self.BASE_API}/tasks"
        headers = {**self.HEADERS[address], "authorization": f"Bearer {self.access_tokens[address]}"}
        proxy_dict = self.get_proxy_dict(proxy_url)
        
        for attempt in range(retries):
            try:
                session = requests.Session(impersonate="chrome124")
                response = session.get(url, headers=headers, proxies=proxy_dict, timeout=30)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(2)
        return None

    def complete_task(self, address: str, task_id: str, requirements: dict, proxy_url=None, retries=3):
        url = f"{self.BASE_API}/tasks"
        data = {"taskId": task_id, "data": requirements}
        headers = {**self.HEADERS[address], "authorization": f"Bearer {self.access_tokens[address]}"}
        proxy_dict = self.get_proxy_dict(proxy_url)
        
        for attempt in range(retries):
            try:
                session = requests.Session(impersonate="chrome124")
                response = session.post(url, json=data, headers=headers, proxies=proxy_dict, timeout=30)
                if response.status_code == 400:
                    return "already_done"
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(2)
        return None

    def complete_social_tasks(self, address: str, proxy_url=None):
        self.log(f"{WHITE}[INFO] Completing Social Tasks...{RESET}")
        
        tasks_list = [
            {"id": "1", "name": "Follow HAN on X", "data": {"url": "https://x.com/HumanoidNetwork"}},
            {"id": "2", "name": "Join Telegram", "data": {"url": "https://t.me/TheHumanoidNetwork"}},
            {"id": "3", "name": "Share on Social Media", "data": {}},
            {"id": "5", "name": "Join Discord", "data": {"url": "https://discord.gg/f5C32A89q8"}},
            {"id": "6", "name": "Follow Instagram", "data": {"url": "https://www.instagram.com/humanoidnetwork"}},
            {"id": "7", "name": "Subscribe YouTube", "data": {"url": "https://www.youtube.com/@HumanoidNetwork"}},
            {"id": "8", "name": "Follow TikTok", "data": {"url": "https://www.tiktok.com/@humanoidnetwork"}},
            {"id": "9", "name": "Join Reddit", "data": {"url": "https://www.reddit.com/user/humanoidNetwork/"}}
        ]

        completed_count = 0
        already_done_count = 0
        
        for task in tasks_list:
            result = self.complete_task(address, task["id"], task["data"], proxy_url)
            if result == "already_done":
                already_done_count += 1
            elif result:
                completed_count += 1
                self.log(f"{GREEN}[SUCCESS] Task: {WHITE}{task['name']}{RESET}")
            time.sleep(1)
        
        if completed_count > 0:
            self.log(f"{GREEN}[SUCCESS] New Tasks Completed: {completed_count}{RESET}")
        if already_done_count > 0:
            self.log(f"{YELLOW}[INFO] Already Done: {already_done_count} Tasks{RESET}")
        
        return completed_count

    def process_login(self, account: str, address: str):
        proxy = self.get_next_proxy_for_account(address)
        
        nonce = self.auth_nonce(address, proxy)
        if not nonce:
            return False
        
        message = nonce.get("message")
        if not message:
            return False
        
        # Normal login without referral code
        authenticate = self.auth_authenticate(account, address, message, proxy, include_ref=False)
        if not authenticate:
            return False
        
        token = authenticate.get("token")
        if not token:
            return False
        
        self.access_tokens[address] = token
        return True

    # ==================== DAILY CHECK - ONLY SOCIAL TASKS ====================
    def daily_check(self, accounts):
        print(f"{CYAN}{'='*60}{RESET}")
        print(f"{BOLD}{MAGENTA}              CLAIM DAILY CHECK{RESET}")
        print(f"{BOLD}{YELLOW}         (Social Tasks Only - No Training){RESET}")
        print(f"{CYAN}{'='*60}{RESET}")
        print()
        
        self.log(f"{WHITE}[INFO] Total Accounts: {GREEN}{len(accounts)}{RESET}")
        conn_type = "Proxy" if self.use_proxy else "Direct"
        self.log(f"{WHITE}[INFO] Connection: {GREEN}{conn_type}{RESET}")
        print()
        
        for idx, account in enumerate(accounts, start=1):
            address = self.generate_address(account)
            if not address:
                self.log(f"{RED}[ERROR] Invalid Private Key{RESET}")
                continue
            
            print(f"{CYAN}{'='*60}{RESET}")
            print(f"{BOLD}{WHITE}  [Account {idx}] {self.mask_account(address)}{RESET}")
            print(f"{CYAN}{'='*60}{RESET}")
            
            self.setup_headers(address)
            logined = self.process_login(account, address)
            
            if not logined:
                self.log(f"{RED}[ERROR] Login Failed{RESET}")
                continue
            
            self.log(f"{GREEN}[SUCCESS] Login OK{RESET}")
            proxy = self.get_next_proxy_for_account(address)
            
            # Get user data
            user = self.user_data(address, proxy)
            initial_points = 0
            if user:
                refer_by = user.get("user", {}).get("referredBy", None)
                initial_points = user.get("totalPoints", 0)
                
                if refer_by is None and self.REF_CODE:
                    ref_result = self.apply_ref(address, self.REF_CODE, proxy)
                    if ref_result:
                        self.log(f"{GREEN}[SUCCESS] Referral Applied{RESET}")
                
                self.log(f"{WHITE}[INFO] Current Points: {GREEN}{initial_points}{RESET}")

            # Complete social tasks ONLY
            self.complete_social_tasks(address, proxy)
            
            # Get final points
            final_user = self.user_data(address, proxy)
            if final_user:
                final_points = final_user.get("totalPoints", 0)
                earned = final_points - initial_points
                self.log(f"{WHITE}[INFO] Final Points: {GREEN}{final_points}{WHITE} | Earned: {GREEN}+{earned}{RESET}")
            
            print()
        
        print(f"{GREEN}{'='*60}{RESET}")
        print(f"{BOLD}{GREEN}      DAILY CHECK COMPLETED{RESET}")
        print(f"{GREEN}{'='*60}{RESET}")

    # ==================== TRAINING - MODELS & DATASETS ====================
    def training(self, accounts):
        print(f"{CYAN}{'='*60}{RESET}")
        print(f"{BOLD}{MAGENTA}              TRAINING{RESET}")
        print(f"{BOLD}{YELLOW}         (Models & Datasets Submission){RESET}")
        print(f"{CYAN}{'='*60}{RESET}")
        print()
        
        self.log(f"{WHITE}[INFO] Total Accounts: {GREEN}{len(accounts)}{RESET}")
        conn_type = "Proxy" if self.use_proxy else "Direct"
        self.log(f"{WHITE}[INFO] Connection: {GREEN}{conn_type}{RESET}")
        print()
        
        for idx, account in enumerate(accounts, start=1):
            address = self.generate_address(account)
            if not address:
                self.log(f"{RED}[ERROR] Invalid Private Key{RESET}")
                continue
            
            print(f"{CYAN}{'='*60}{RESET}")
            print(f"{BOLD}{WHITE}  [Account {idx}] {self.mask_account(address)}{RESET}")
            print(f"{CYAN}{'='*60}{RESET}")
            
            self.setup_headers(address)
            logined = self.process_login(account, address)
            
            if not logined:
                self.log(f"{RED}[ERROR] Login Failed{RESET}")
                continue
            
            self.log(f"{GREEN}[SUCCESS] Login OK{RESET}")
            proxy = self.get_next_proxy_for_account(address)
            
            # Get initial points
            user = self.user_data(address, proxy)
            initial_points = 0
            if user:
                initial_points = user.get("totalPoints", 0)
                self.log(f"{WHITE}[INFO] Current Points: {GREEN}{initial_points}{RESET}")
            
            # Get training progress
            progress = self.training_progress(address, proxy)
            if not progress:
                self.log(f"{RED}[ERROR] Failed to get training progress{RESET}")
                continue
            
            models_remaining = progress.get("daily", {}).get("models", {}).get("remaining", 0)
            models_completed = progress.get("daily", {}).get("models", {}).get("completed", 0)
            models_limit = progress.get("daily", {}).get("models", {}).get("limit", 0)
            
            datasets_remaining = progress.get("daily", {}).get("datasets", {}).get("remaining", 0)
            datasets_completed = progress.get("daily", {}).get("datasets", {}).get("completed", 0)
            datasets_limit = progress.get("daily", {}).get("datasets", {}).get("limit", 0)
            
            self.log(f"{WHITE}[INFO] Models: {GREEN}{models_completed}/{models_limit}{WHITE} | Remaining: {YELLOW}{models_remaining}{RESET}")
            self.log(f"{WHITE}[INFO] Datasets: {GREEN}{datasets_completed}/{datasets_limit}{WHITE} | Remaining: {YELLOW}{datasets_remaining}{RESET}")
            
            # Submit Models
            if models_remaining > 0:
                self.log(f"{WHITE}[INFO] Submitting {models_remaining} Models...{RESET}")
                models = self.scrape_huggingface("models", models_remaining, proxy)
                if models:
                    success_count = 0
                    for model in models:
                        if success_count >= models_remaining:
                            break
                        model_name = model.get("id", model.get("modelId", ""))
                        if not model_name:
                            continue
                        model_url = f"{self.HF_API}/{model_name}"
                        training_data = {
                            "fileName": model_name,
                            "fileUrl": model_url,
                            "fileType": "model",
                            "recaptchaToken": ""
                        }
                        submit = self.submit_training(address, training_data, proxy)
                        if submit:
                            success_count += 1
                            short_name = model_name[:40] + "..." if len(model_name) > 40 else model_name
                            self.log(f"{GREEN}[SUCCESS] Model: {WHITE}{short_name}{RESET}")
                        time.sleep(1)
                    self.log(f"{GREEN}[INFO] Models Submitted: {success_count}/{models_remaining}{RESET}")
                else:
                    self.log(f"{RED}[ERROR] Failed to scrape models from HuggingFace{RESET}")
            else:
                self.log(f"{GREEN}[SUCCESS] Daily Models Already Completed!{RESET}")
            
            # Submit Datasets
            if datasets_remaining > 0:
                self.log(f"{WHITE}[INFO] Submitting {datasets_remaining} Datasets...{RESET}")
                datasets = self.scrape_huggingface("datasets", datasets_remaining, proxy)
                if datasets:
                    success_count = 0
                    for dataset in datasets:
                        if success_count >= datasets_remaining:
                            break
                        dataset_name = dataset.get("id", dataset.get("datasetId", ""))
                        if not dataset_name:
                            continue
                        dataset_url = f"{self.HF_API}/datasets/{dataset_name}"
                        training_data = {
                            "fileName": dataset_name,
                            "fileUrl": dataset_url,
                            "fileType": "dataset",
                            "recaptchaToken": ""
                        }
                        submit = self.submit_training(address, training_data, proxy)
                        if submit:
                            success_count += 1
                            short_name = dataset_name[:40] + "..." if len(dataset_name) > 40 else dataset_name
                            self.log(f"{GREEN}[SUCCESS] Dataset: {WHITE}{short_name}{RESET}")
                        time.sleep(1)
                    self.log(f"{GREEN}[INFO] Datasets Submitted: {success_count}/{datasets_remaining}{RESET}")
                else:
                    self.log(f"{RED}[ERROR] Failed to scrape datasets from HuggingFace{RESET}")
            else:
                self.log(f"{GREEN}[SUCCESS] Daily Datasets Already Completed!{RESET}")
            
            # Get final points
            final_user = self.user_data(address, proxy)
            if final_user:
                final_points = final_user.get("totalPoints", 0)
                earned = final_points - initial_points
                self.log(f"{WHITE}[INFO] Final Points: {GREEN}{final_points}{WHITE} | Earned: {GREEN}+{earned}{RESET}")
            
            print()
        
        print(f"{GREEN}{'='*60}{RESET}")
        print(f"{BOLD}{GREEN}      TRAINING COMPLETED{RESET}")
        print(f"{GREEN}{'='*60}{RESET}")

    # ==================== AUTO REFF - FIXED ====================
    def auto_reff_worker(self, worker_id):
        # Create new wallet
        new_account = Account.create()
        private_key = new_account.key.hex()
        address = new_account.address
        
        self.log(f"{WHITE}[{worker_id}] New Wallet: {CYAN}{self.mask_account(address)}{RESET}")
        
        self.setup_headers(address)
        proxy = self.get_next_proxy_for_account(address)
        
        # Step 1: Get nonce
        nonce = self.auth_nonce(address, proxy)
        if not nonce:
            self.log(f"{RED}[{worker_id}] Failed to get nonce{RESET}")
            return False
        
        message = nonce.get("message")
        if not message:
            self.log(f"{RED}[{worker_id}] No message in nonce{RESET}")
            return False
        
        # Step 2: Authenticate WITH referral code included
        authenticate = self.auth_authenticate(
            private_key, 
            address, 
            message, 
            proxy, 
            include_ref=True, 
            ref_code=self.REF_CODE
        )
        
        if not authenticate:
            self.log(f"{RED}[{worker_id}] Authentication failed{RESET}")
            return False
        
        token = authenticate.get("token")
        if not token:
            self.log(f"{RED}[{worker_id}] No token received{RESET}")
            return False
        
        self.access_tokens[address] = token
        
        # Step 3: Check if referral was applied by checking user data
        user = self.user_data(address, proxy)
        if user:
            referred_by = user.get("user", {}).get("referredBy", None)
            if referred_by:
                self.log(f"{GREEN}[{worker_id}] Referral Applied Successfully!{RESET}")
                self.save_reff_account(private_key, address)
                return True
            else:
                # Try applying referral separately
                self.log(f"{YELLOW}[{worker_id}] Trying to apply referral...{RESET}")
                apply_result = self.apply_ref(address, self.REF_CODE, proxy)
                if apply_result:
                    self.log(f"{GREEN}[{worker_id}] Referral Applied Successfully!{RESET}")
                    self.save_reff_account(private_key, address)
                    return True
                else:
                    self.log(f"{RED}[{worker_id}] Failed to apply referral{RESET}")
                    return False
        else:
            self.log(f"{RED}[{worker_id}] Failed to get user data{RESET}")
            return False

    def auto_reff(self, count):
        print(f"{CYAN}{'='*60}{RESET}")
        print(f"{BOLD}{MAGENTA}              AUTO REFF{RESET}")
        print(f"{CYAN}{'='*60}{RESET}")
        print()
        
        if not self.REF_CODE:
            self.log(f"{RED}[ERROR] No referral code loaded{RESET}")
            return
        
        conn_type = "Proxy" if self.use_proxy else "Direct"
        self.log(f"{WHITE}[INFO] Referral Code: {GREEN}{self.REF_CODE}{RESET}")
        self.log(f"{WHITE}[INFO] Connection: {GREEN}{conn_type}{RESET}")
        self.log(f"{WHITE}[INFO] Target Count: {GREEN}{count}{RESET}")
        print()
        
        success = 0
        failed = 0
        
        for i in range(count):
            self.log(f"{CYAN}{'─'*40}{RESET}")
            result = self.auto_reff_worker(i + 1)
            if result:
                success += 1
            else:
                failed += 1
            
            # Delay between each referral
            if i < count - 1:
                time.sleep(2)
        
        print()
        print(f"{GREEN}{'='*60}{RESET}")
        print(f"{BOLD}{GREEN}      AUTO REFF COMPLETED{RESET}")
        print(f"{BOLD}{GREEN}      Success: {success}/{count}{RESET}")
        print(f"{BOLD}{RED}      Failed: {failed}/{count}{RESET}")
        print(f"{GREEN}{'='*60}{RESET}")

    # ==================== RUN REFF ACCOUNTS ====================
    def run_reff_accounts(self):
        print(f"{CYAN}{'='*60}{RESET}")
        print(f"{BOLD}{MAGENTA}              RUN REFF ACCOUNTS{RESET}")
        print(f"{CYAN}{'='*60}{RESET}")
        print()
        
        reff_accounts = self.load_reff_accounts()
        if not reff_accounts:
            self.log(f"{RED}[ERROR] No Reff Accounts in reff.json{RESET}")
            return
        
        conn_type = "Proxy" if self.use_proxy else "Direct"
        self.log(f"{WHITE}[INFO] Connection: {GREEN}{conn_type}{RESET}")
        self.log(f"{WHITE}[INFO] Reff Accounts: {GREEN}{len(reff_accounts)}{RESET}")
        print()
        
        for idx, acc in enumerate(reff_accounts):
            private_key = acc.get("private_key")
            address = acc.get("address")
            if not private_key or not address:
                continue
            
            print(f"{CYAN}{'='*60}{RESET}")
            print(f"{BOLD}{WHITE}  [Reff {idx + 1}] {self.mask_account(address)}{RESET}")
            print(f"{CYAN}{'='*60}{RESET}")
            
            self.setup_headers(address)
            logined = self.process_login(private_key, address)
            
            if not logined:
                self.log(f"{RED}[ERROR] Login Failed{RESET}")
                continue
            
            self.log(f"{GREEN}[SUCCESS] Login OK{RESET}")
            proxy = self.get_next_proxy_for_account(address)
            
            # Get user data
            user = self.user_data(address, proxy)
            initial_points = 0
            if user:
                initial_points = user.get("totalPoints", 0)
                self.log(f"{WHITE}[INFO] Current Points: {GREEN}{initial_points}{RESET}")
            
            # Complete social tasks
            self.complete_social_tasks(address, proxy)
            
            # Training
            progress = self.training_progress(address, proxy)
            if progress:
                models_remaining = progress.get("daily", {}).get("models", {}).get("remaining", 0)
                datasets_remaining = progress.get("daily", {}).get("datasets", {}).get("remaining", 0)
                
                if models_remaining > 0:
                    models = self.scrape_huggingface("models", models_remaining, proxy)
                    if models:
                        success_count = 0
                        for model in models:
                            if success_count >= models_remaining:
                                break
                            model_name = model.get("id", "")
                            if not model_name:
                                continue
                            training_data = {
                                "fileName": model_name,
                                "fileUrl": f"{self.HF_API}/{model_name}",
                                "fileType": "model",
                                "recaptchaToken": ""
                            }
                            if self.submit_training(address, training_data, proxy):
                                success_count += 1
                            time.sleep(1)
                        self.log(f"{GREEN}[SUCCESS] Models: {success_count} Submitted{RESET}")
                
                if datasets_remaining > 0:
                    datasets = self.scrape_huggingface("datasets", datasets_remaining, proxy)
                    if datasets:
                        success_count = 0
                        for dataset in datasets:
                            if success_count >= datasets_remaining:
                                break
                            dataset_name = dataset.get("id", "")
                            if not dataset_name:
                                continue
                            training_data = {
                                "fileName": dataset_name,
                                "fileUrl": f"{self.HF_API}/datasets/{dataset_name}",
                                "fileType": "dataset",
                                "recaptchaToken": ""
                            }
                            if self.submit_training(address, training_data, proxy):
                                success_count += 1
                            time.sleep(1)
                        self.log(f"{GREEN}[SUCCESS] Datasets: {success_count} Submitted{RESET}")
            
            # Get final points
            final_user = self.user_data(address, proxy)
            if final_user:
                final_points = final_user.get("totalPoints", 0)
                earned = final_points - initial_points
                self.log(f"{WHITE}[INFO] Final Points: {GREEN}{final_points}{WHITE} | Earned: {GREEN}+{earned}{RESET}")
            
            print()
        
        print(f"{GREEN}{'='*60}{RESET}")
        print(f"{BOLD}{GREEN}      REFF ACCOUNTS RUN COMPLETED{RESET}")
        print(f"{GREEN}{'='*60}{RESET}")

    # ==================== MAIN MENU ====================
    def main(self):
        accounts = self.load_accounts()
        self.load_proxies()
        self.load_ref_code()
        
        while True:
            self.print_banner()
            conn_type = "Proxy" if self.use_proxy else "Direct"
            self.log(f"{WHITE}[INFO] Connection Mode: {GREEN}{conn_type}{RESET}")
            
            if self.use_proxy:
                self.log(f"{WHITE}[INFO] Proxies Loaded: {GREEN}{len(self.proxies)}{RESET}")
            
            self.log(f"{WHITE}[INFO] Accounts Loaded: {GREEN}{len(accounts)}{RESET}")
            self.log(f"{WHITE}[INFO] Referral Code: {GREEN}{self.REF_CODE if self.REF_CODE else 'Not Set'}{RESET}")
            
            reff_accounts = self.load_reff_accounts()
            self.log(f"{WHITE}[INFO] Reff Accounts: {GREEN}{len(reff_accounts)}{RESET}")
            
            print()
            self.print_menu()
            
            try:
                choice = input(f"{BOLD}{WHITE}Select option: {RESET}").strip()
            except:
                continue
            
            if choice == "1":
                if not accounts:
                    self.log(f"{RED}[ERROR] No accounts in pv.txt{RESET}")
                    input(f"{YELLOW}Press Enter to continue...{RESET}")
                    continue
                self.daily_check(accounts)
                input(f"{YELLOW}Press Enter to continue...{RESET}")
            
            elif choice == "2":
                if not accounts:
                    self.log(f"{RED}[ERROR] No accounts in pv.txt{RESET}")
                    input(f"{YELLOW}Press Enter to continue...{RESET}")
                    continue
                self.training(accounts)
                input(f"{YELLOW}Press Enter to continue...{RESET}")
            
            elif choice == "3":
                if not self.REF_CODE:
                    self.log(f"{RED}[ERROR] No referral code in code.txt{RESET}")
                    input(f"{YELLOW}Press Enter to continue...{RESET}")
                    continue
                try:
                    count = int(input(f"{BOLD}{WHITE}Enter Reff Count: {RESET}").strip())
                    if count <= 0:
                        count = 1
                except:
                    count = 1
                self.auto_reff(count)
                input(f"{YELLOW}Press Enter to continue...{RESET}")
            
            elif choice == "4":
                self.run_reff_accounts()
                input(f"{YELLOW}Press Enter to continue...{RESET}")
            
            elif choice == "5":
                print(f"{CYAN}{'='*60}{RESET}")
                print(f"{BOLD}{MAGENTA}      Goodbye! Thanks for using Humanoid Bot{RESET}")
                print(f"{BOLD}{YELLOW}      CREATED BY KAZUHA - VIP ONLY{RESET}")
                print(f"{CYAN}{'='*60}{RESET}")
                break
            
            else:
                print(f"{RED}[ERROR] Invalid option!{RESET}")
                input(f"{YELLOW}Press Enter to continue...{RESET}")


if __name__ == "__main__":
    try:
        bot = Humanoid()
        bot.main()
    except KeyboardInterrupt:
        print(f"{CYAN}{'='*60}{RESET}")
        print(f"{BOLD}{RED}      EXIT - Humanoid Bot{RESET}")
        print(f"{CYAN}{'='*60}{RESET}")
