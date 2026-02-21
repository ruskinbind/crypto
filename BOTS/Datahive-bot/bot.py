import requests
import json
from datetime import datetime
import pytz
import time
import uuid
import platform
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Back, Style, init

# Initialize colorama
init(autoreset=True)

class DataHiveBot:
    def __init__(self):
        self.base_url = "https://api.datahive.ai/api"
        self.wib = pytz.timezone('Asia/Jakarta')
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.lock = threading.Lock()
        
    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def get_device_info(self):
        return {
            "device_id": str(uuid.uuid4()),
            "os": f"{platform.system()} {platform.release()}",
            "cpu_model": "Intel Core i5",
            "cpu_arch": platform.machine(),
            "cpu_count": "4"
        }

    def get_headers(self, token, device_info):
        return {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "authorization": f"Bearer {token}",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "pragma": "no-cache",
            "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "none",
            "sec-fetch-storage-access": "active",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "x-app-version": "0.2.4",
            "x-cpu-architecture": device_info["cpu_arch"],
            "x-cpu-model": device_info["cpu_model"],
            "x-cpu-processor-count": device_info["cpu_count"],
            "x-device-id": device_info["device_id"],
            "x-device-os": device_info["os"],
            "x-device-type": "extension",
            "x-s": "f",
            "x-user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "x-user-language": "en-US"
        }

    def get_time(self):
        return datetime.now(self.wib).strftime('%H:%M:%S')

    def log(self, message):
        print(f"{Fore.CYAN + Style.BRIGHT}[{self.get_time()}]{Style.RESET_ALL} {message}")

    def print_banner(self):
        self.clear_terminal()
        print(f"{Fore.CYAN + Style.BRIGHT}{'='*60}")
        print(f"{Fore.GREEN + Style.BRIGHT}     ____        _        _   _ _           ")
        print(f"{Fore.GREEN + Style.BRIGHT}    |  _ \\  __ _| |_ __ _| | | (_)_   _____ ")
        print(f"{Fore.GREEN + Style.BRIGHT}    | | | |/ _` | __/ _` | |_| | \\ \\ / / _ \\")
        print(f"{Fore.GREEN + Style.BRIGHT}    | |_| | (_| | || (_| |  _  | |\\ V /  __/")
        print(f"{Fore.GREEN + Style.BRIGHT}    |____/ \\__,_|\\__\\__,_|_| |_|_| \\_/ \\___|")
        print(f"{Fore.YELLOW + Style.BRIGHT}\n                 AUTO FARMING BOT")
        print(f"{Fore.MAGENTA + Style.BRIGHT}              Created By: {Fore.WHITE + Style.BRIGHT}KAZUHA")
        print(f"{Fore.RED + Style.BRIGHT}               Access: {Fore.WHITE + Style.BRIGHT}VIP ONLY")
        print(f"{Fore.CYAN + Style.BRIGHT}{'='*60}\n{Style.RESET_ALL}")

    def mask_email(self, email):
        if "@" in email:
            local, domain = email.split('@', 1)
            if len(local) <= 6:
                hide_local = local[:2] + '***' + local[-1:]
            else:
                hide_local = local[:3] + '***' + local[-3:]
            return f"{hide_local}@{domain}"
        return email

    def load_tokens(self, filename="token.txt"):
        try:
            with open(filename, 'r') as f:
                tokens = [line.strip() for line in f if line.strip()]
            self.log(f"{Fore.GREEN + Style.BRIGHT}Loaded {len(tokens)} accounts successfully{Style.RESET_ALL}")
            return tokens
        except FileNotFoundError:
            self.log(f"{Fore.RED + Style.BRIGHT}ERROR: {filename} not found{Style.RESET_ALL}")
            return []

    def load_proxies(self, filename="proxy.txt"):
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.YELLOW + Style.BRIGHT}WARNING: {filename} not found{Style.RESET_ALL}")
                return []
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if self.proxies:
                self.log(f"{Fore.GREEN + Style.BRIGHT}Loaded {len(self.proxies)} proxies{Style.RESET_ALL}")
            else:
                self.log(f"{Fore.YELLOW + Style.BRIGHT}No proxies found in file{Style.RESET_ALL}")
            return self.proxies
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Error loading proxies: {e}{Style.RESET_ALL}")
            return []

    def format_proxy(self, proxy):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxy.startswith(scheme) for scheme in schemes):
            return proxy
        return f"http://{proxy}"

    def get_proxy_for_account(self, account_index):
        if not self.proxies:
            return None
        with self.lock:
            proxy_index = account_index % len(self.proxies)
            return self.format_proxy(self.proxies[proxy_index])

    def rotate_proxy(self, account_index):
        if not self.proxies:
            return None
        with self.lock:
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
            return self.format_proxy(self.proxies[self.proxy_index])

    def get_worker_info(self, token, device_info, proxy=None):
        try:
            url = f"{self.base_url}/worker"
            headers = self.get_headers(token, device_info)
            proxies = {"http": proxy, "https": proxy} if proxy else None
            
            response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            return None

    def ping_uptime(self, token, device_info, proxy=None):
        try:
            url = f"{self.base_url}/ping/uptime"
            headers = self.get_headers(token, device_info)
            proxies = {"http": proxy, "https": proxy} if proxy else None
            
            response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
            return response.status_code == 200
        except Exception as e:
            return False

    def check_worker_ip(self, token, device_info, proxy=None):
        try:
            url = f"{self.base_url}/network/worker-ip"
            headers = self.get_headers(token, device_info)
            proxies = {"http": proxy, "https": proxy} if proxy else None
            
            response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('ip', 'Unknown')
            return None
        except Exception as e:
            return None

    def process_worker(self, worker, rotate_proxy, use_proxy):
        account_num = worker['num']
        token = worker['token']
        device_info = worker['device_info']
        email = worker['email']
        proxy = worker['proxy']
        
        result = {
            'num': account_num,
            'email': email,
            'proxy': proxy,
            'ping_ok': False,
            'ip': None,
            'points_24h': 0,
            'total_points': 0
        }
        
        ping_ok = self.ping_uptime(token, device_info, proxy)
        
        if not ping_ok and rotate_proxy and use_proxy:
            proxy = self.rotate_proxy(account_num)
            worker['proxy'] = proxy
            result['proxy'] = proxy
            ping_ok = self.ping_uptime(token, device_info, proxy)
        
        result['ping_ok'] = ping_ok
        
        if ping_ok:
            ip = self.check_worker_ip(token, device_info, proxy)
            result['ip'] = ip
            
            worker_info = self.get_worker_info(token, device_info, proxy)
            if worker_info:
                result['points_24h'] = worker_info.get('points24h', 0)
                if 'user' in worker_info:
                    result['total_points'] = worker_info['user'].get('points', 0)
        
        return result

    def print_worker_result(self, result):
        num = result['num']
        email = self.mask_email(result['email'])
        ping_ok = result['ping_ok']
        
        if ping_ok:
            points_24h = result['points_24h']
            total_points = result['total_points']
            ip = result['ip'] if result['ip'] else "N/A"
            
            print(f"{Fore.WHITE + Style.BRIGHT}[{Fore.CYAN + Style.BRIGHT}{num:02d}{Fore.WHITE + Style.BRIGHT}] {Fore.GREEN + Style.BRIGHT}✓{Style.RESET_ALL} {Fore.YELLOW + Style.BRIGHT}{email:25s}{Style.RESET_ALL} │ {Fore.MAGENTA + Style.BRIGHT}24h:{Fore.GREEN + Style.BRIGHT}{points_24h:8.2f}{Style.RESET_ALL} │ {Fore.MAGENTA + Style.BRIGHT}Total:{Fore.GREEN + Style.BRIGHT}{total_points:10.2f}{Style.RESET_ALL} │ {Fore.BLUE + Style.BRIGHT}IP:{Fore.WHITE}{ip}{Style.RESET_ALL}")
        else:
            print(f"{Fore.WHITE + Style.BRIGHT}[{Fore.CYAN + Style.BRIGHT}{num:02d}{Fore.WHITE + Style.BRIGHT}] {Fore.RED + Style.BRIGHT}✗{Style.RESET_ALL} {Fore.YELLOW + Style.BRIGHT}{email:25s}{Style.RESET_ALL} │ {Fore.RED + Style.BRIGHT}Connection Failed{Style.RESET_ALL}")

    def run(self):
        self.print_banner()
        
        tokens = self.load_tokens()
        if not tokens:
            self.log(f"{Fore.RED + Style.BRIGHT}No tokens found! Add tokens to token.txt{Style.RESET_ALL}")
            return
        
        print(f"{Fore.CYAN + Style.BRIGHT}{'─'*60}")
        print(f"{Fore.YELLOW + Style.BRIGHT}PROXY CONFIGURATION{Style.RESET_ALL}")
        print(f"{Fore.CYAN + Style.BRIGHT}{'─'*60}")
        print(f"{Fore.WHITE + Style.BRIGHT}[1]{Style.RESET_ALL} {Fore.GREEN + Style.BRIGHT}With Proxy{Style.RESET_ALL}")
        print(f"{Fore.WHITE + Style.BRIGHT}[2]{Style.RESET_ALL} {Fore.YELLOW + Style.BRIGHT}Without Proxy{Style.RESET_ALL}")
        print(f"{Fore.CYAN + Style.BRIGHT}{'─'*60}{Style.RESET_ALL}")
        
        while True:
            try:
                choice = input(f"{Fore.CYAN + Style.BRIGHT}Select option [1-2]: {Style.RESET_ALL}").strip()
                if choice in ['1', '2']:
                    choice = int(choice)
                    break
                print(f"{Fore.RED + Style.BRIGHT}Invalid choice!{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Enter a valid number!{Style.RESET_ALL}")
        
        use_proxy = (choice == 1)
        rotate_proxy = False
        num_workers = 1
        
        if use_proxy:
            self.load_proxies()
            if not self.proxies:
                self.log(f"{Fore.YELLOW + Style.BRIGHT}No proxies! Running without proxy{Style.RESET_ALL}")
                use_proxy = False
            else:
                num_workers = len(self.proxies)
                while True:
                    rotate_input = input(f"{Fore.CYAN + Style.BRIGHT}Enable proxy rotation? [y/n]: {Style.RESET_ALL}").strip().lower()
                    if rotate_input in ['y', 'n']:
                        rotate_proxy = (rotate_input == 'y')
                        status = "Enabled" if rotate_proxy else "Disabled"
                        self.log(f"{Fore.GREEN + Style.BRIGHT}Proxy rotation: {status}{Style.RESET_ALL}")
                        break
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input!{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN + Style.BRIGHT}{'─'*60}")
        print(f"{Fore.YELLOW + Style.BRIGHT}INITIALIZING ACCOUNTS{Style.RESET_ALL}")
        print(f"{Fore.CYAN + Style.BRIGHT}{'─'*60}{Style.RESET_ALL}")
        
        active_workers = []
        
        for i, token in enumerate(tokens, 1):
            device_info = self.get_device_info()
            proxy = self.get_proxy_for_account(i - 1) if use_proxy else None
            
            worker_info = self.get_worker_info(token, device_info, proxy)
            
            if worker_info:
                email = worker_info.get('user', {}).get('email', f'account_{i}@unknown.com')
                points_24h = worker_info.get('points24h', 0)
                total_points = worker_info.get('user', {}).get('points', 0)
                
                print(f"{Fore.WHITE + Style.BRIGHT}[{Fore.CYAN + Style.BRIGHT}{i:02d}{Fore.WHITE}]{Style.RESET_ALL} {Fore.GREEN + Style.BRIGHT}✓ Connected{Style.RESET_ALL} │ {Fore.YELLOW + Style.BRIGHT}{self.mask_email(email)}{Style.RESET_ALL} │ {Fore.MAGENTA + Style.BRIGHT}Points: {Fore.GREEN + Style.BRIGHT}{total_points:.2f}{Style.RESET_ALL}")
                
                active_workers.append({
                    'num': i,
                    'token': token,
                    'device_info': device_info,
                    'email': email,
                    'proxy': proxy
                })
            else:
                print(f"{Fore.WHITE + Style.BRIGHT}[{Fore.CYAN + Style.BRIGHT}{i:02d}{Fore.WHITE}]{Style.RESET_ALL} {Fore.RED + Style.BRIGHT}✗ Failed{Style.RESET_ALL}")
                if rotate_proxy and use_proxy:
                    proxy = self.rotate_proxy(i - 1)
        
        print(f"{Fore.CYAN + Style.BRIGHT}{'─'*60}{Style.RESET_ALL}")
        self.log(f"{Fore.GREEN + Style.BRIGHT}Active: {len(active_workers)}/{len(tokens)} accounts{Style.RESET_ALL}")
        
        if not active_workers:
            self.log(f"{Fore.RED + Style.BRIGHT}No active workers!{Style.RESET_ALL}")
            return
        
        if use_proxy and num_workers > 0:
            max_workers = min(num_workers, len(active_workers))
        else:
            max_workers = len(active_workers)
        
        self.log(f"{Fore.GREEN + Style.BRIGHT}Workers: {max_workers} threads{Style.RESET_ALL}")
        
        ping_count = 0
        
        try:
            while True:
                ping_count += 1
                
                print(f"\n{Fore.CYAN + Style.BRIGHT}{'─'*60}")
                print(f"{Fore.YELLOW + Style.BRIGHT}FARMING CYCLE #{ping_count}{Style.RESET_ALL}")
                print(f"{Fore.CYAN + Style.BRIGHT}{'─'*60}{Style.RESET_ALL}")
                
                total_points = 0
                total_24h = 0
                success_count = 0
                failed_count = 0
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = {
                        executor.submit(self.process_worker, worker, rotate_proxy, use_proxy): worker 
                        for worker in active_workers
                    }
                    
                    for future in as_completed(futures):
                        try:
                            result = future.result()
                            self.print_worker_result(result)
                            
                            if result['ping_ok']:
                                success_count += 1
                                total_points += result['total_points']
                                total_24h += result['points_24h']
                            else:
                                failed_count += 1
                        except Exception as e:
                            self.log(f"{Fore.RED + Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
                            failed_count += 1
                
                print(f"{Fore.CYAN + Style.BRIGHT}{'─'*60}{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}Success: {Fore.GREEN + Style.BRIGHT}{success_count}/{len(active_workers)}{Style.RESET_ALL} │ {Fore.WHITE + Style.BRIGHT}Failed: {Fore.RED + Style.BRIGHT}{failed_count}{Style.RESET_ALL} │ {Fore.WHITE + Style.BRIGHT}24h: {Fore.GREEN + Style.BRIGHT}{total_24h:.2f}{Style.RESET_ALL} │ {Fore.WHITE + Style.BRIGHT}Total: {Fore.GREEN + Style.BRIGHT}{total_points:.2f}{Style.RESET_ALL}")
                
                for remaining in range(60, 0, -1):
                    print(f"\r{Fore.CYAN + Style.BRIGHT}[{self.get_time()}]{Style.RESET_ALL} {Fore.YELLOW + Style.BRIGHT}Next cycle in {Fore.WHITE + Style.BRIGHT}{remaining:02d}s{Style.RESET_ALL}  ", end="", flush=True)
                    time.sleep(1)
                print()
                
        except KeyboardInterrupt:
            print(f"\n\n{Fore.CYAN + Style.BRIGHT}{'─'*60}")
            print(f"{Fore.YELLOW + Style.BRIGHT}SESSION ENDED{Style.RESET_ALL}")
            print(f"{Fore.CYAN + Style.BRIGHT}{'─'*60}{Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}Total Cycles: {Fore.GREEN + Style.BRIGHT}{ping_count}{Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}Total Accounts: {Fore.GREEN + Style.BRIGHT}{len(active_workers)}{Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}Total Pings: {Fore.GREEN + Style.BRIGHT}{ping_count * len(active_workers)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN + Style.BRIGHT}{'─'*60}{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA + Style.BRIGHT}Created By: {Fore.WHITE + Style.BRIGHT}KAZUHA{Style.RESET_ALL}")
            print(f"{Fore.RED + Style.BRIGHT}Access: {Fore.WHITE + Style.BRIGHT}VIP ONLY{Style.RESET_ALL}")
            print(f"{Fore.CYAN + Style.BRIGHT}{'─'*60}{Style.RESET_ALL}")


if __name__ == "__main__":
    try:
        bot = DataHiveBot()
        bot.run()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED + Style.BRIGHT}Exiting...{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED + Style.BRIGHT}Fatal Error: {e}{Style.RESET_ALL}")