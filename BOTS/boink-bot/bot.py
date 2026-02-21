import os
import sys
import time
import random
import requests
import threading
from datetime import datetime
from web3 import Web3
from eth_account import Account
from concurrent.futures import ThreadPoolExecutor, as_completed
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
# NETWORK CONFIG
RPC_URL = "https://rpc-gel-sepolia.inkonchain.com"
CHAIN_ID = 763373
# CONTRACT ADDRESSES
CONTRACT_PREDICTION = "0x380b3e6472e64219B45E4DcCbD08e9d5ce61aaA0"
TOKEN_USDC = "0xFabab97dCE620294D2B0b0e46C68964e326300Ac"
# API HEADERS
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "origin": "https://prediction.boinknfts.club",
    "referer": "https://prediction.boinknfts.club/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/144.0.0.0 Safari/537.36",
    "content-type": "application/json"
}
# ABIS
ABI_PREDICTION = [
    {
        "constant": False,
        "inputs": [
            {"name": "marketId", "type": "uint256"},
            {"name": "position", "type": "bool"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "placeBet",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    }
]
ABI_ERC20 = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
]
# Thread lock
print_lock = threading.Lock()
success_count = 0
failed_count = 0
def clear_screen():
    os.system('cls' if os.name == 'posix' else 'clear')
def print_banner():
    clear_screen()
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{MAGENTA}              BOINK PREDICTION BOT{RESET}")
    print(f"{BOLD}{YELLOW}              CREATED BY KAZUHA{RESET}")
    print(f"{BOLD}{RED}              VIP ONLY{RESET}")
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"{YELLOW}  Network: Ink Sepolia | Chain ID: 763373{RESET}")
    print(f"{CYAN}{'='*60}{RESET}")
    print()
def print_menu():
    print(f"{GREEN}{'-'*60}{RESET}")
    print(f"{BOLD}{WHITE}  [1] CLAIM DAILY CHECKIN{RESET}")
    print(f"{BOLD}{WHITE}  [2] BET IN MARKET{RESET}")
    print(f"{BOLD}{WHITE}  [3] AUTO REFF{RESET}")
    print(f"{BOLD}{WHITE}  [4] EXIT{RESET}")
    print(f"{GREEN}{'-'*60}{RESET}")
    print()
def log_message(message, level="INFO"):
    time_str = datetime.now().strftime('%H:%M:%S')
    symbols = {
        "INFO": (CYAN, "ℹ"),
        "SUCCESS": (GREEN, "✓"),
        "ERROR": (RED, "✗"),
        "WARNING": (YELLOW, "⚠"),
        "WALLET": (MAGENTA, "◉"),
        "REFERRAL": (YELLOW, "★"),
        "CLAIM": (GREEN, "◆"),
        "BET": (BLUE, "●"),
        "DEBUG": (WHITE, "⚙"),
        "CYCLE": (MAGENTA, "⟳")
    }
    color, symbol = symbols.get(level, (WHITE, "○"))
    with print_lock:
        print(f"{WHITE}[{time_str}] {color}{symbol} {message}{RESET}")
def load_private_keys():
    try:
        with open("pv.txt", "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []
def save_private_key(private_key):
    with open("pv.txt", "a") as f:
        f.write(private_key + "\n")
def load_proxies():
    try:
        with open("proxy.txt", "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []
def get_web3():
    return Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 60}))
def generate_wallet():
    account = Account.create()
    return {
        'address': account.address,
        'private_key': account.key.hex(),
        'account': account
    }
# --- API FUNCTIONS ---
def register_user(session, address):
    try:
        res = session.get(f"https://inkpredict.vercel.app/api/user/{address}/stats", headers=HEADERS, timeout=15)
        return res.status_code == 200
    except:
        return False
def redeem_referral(session, address, code):
    try:
        res = session.get(f"https://inkpredict.vercel.app/api/referrals/status/{address}", headers=HEADERS, timeout=15)
        if res.status_code == 200 and res.json().get("redeemed"):
            return False
        payload = {"refereeAddress": address, "code": code.upper()}
        res = session.post("https://inkpredict.vercel.app/api/referrals/redeem", json=payload, headers=HEADERS, timeout=15)
        return res.status_code == 200 and res.json().get("success")
    except:
        return False
def claim_daily_api(session, addr):
    try:
        res = session.get(f"https://inkpredict.vercel.app/api/user/{addr}/daily-reward", headers=HEADERS, timeout=15)
        if res.status_code == 200 and res.json().get("canClaim"):
            claim_res = session.post(f"https://inkpredict.vercel.app/api/user/{addr}/claim-daily", headers=HEADERS, json={"userAddress": addr}, timeout=15)
            if claim_res.status_code == 200 and claim_res.json().get("success"):
                data = claim_res.json()
                return True, data.get("xpEarned", 10), data.get("currentStreak", 1)
        return False, 0, 0
    except:
        return False, 0, 0
def get_user_stats(session, addr):
    try:
        res = session.get(f"https://inkpredict.vercel.app/api/user/{addr}/stats", headers=HEADERS, timeout=15)
        if res.status_code == 200:
            return res.json().get("stats", {})
    except:
        pass
    return {}
def get_user_rank(session, addr):
    try:
        res = session.get("https://inkpredict.vercel.app/api/leaderboard?timeframe=all", headers=HEADERS, timeout=15)
        if res.status_code == 200:
            leaderboard = res.json().get("leaderboard", [])
            for i, user in enumerate(leaderboard):
                if user['user_address'].lower() == addr.lower():
                    log_message(f"Current Rank: #{i + 1}", "SUCCESS")
                    return i + 1
            log_message("Current Rank: Not in Top List", "INFO")
    except:
        pass
    return None
def notify_api(session, addr, mid, amt, pos, thash):
    try:
        session.post(
            "https://inkpredict.vercel.app/api/user/bet",
            json={
                "userAddress": addr,
                "marketId": str(mid),
                "amount": str(amt),
                "position": pos,
                "transactionHash": thash
            },
            headers=HEADERS,
            timeout=15
        )
        log_message("API Sync Success", "SUCCESS")
    except:
        pass
# --- FEATURE 1: AUTO REFERRAL ---
def process_single_referral(wallet_num, total, referral_code, proxies):
    global success_count, failed_count
    try:
        wallet = generate_wallet()
        session = requests.Session()
        if proxies:
            proxy = proxies[wallet_num % len(proxies)]
            session.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        
        log_message(f"[{wallet_num}/{total}] Created: {wallet['address'][:20]}...", "WALLET")
        time.sleep(0.5)
        register_user(session, wallet['address'])
        time.sleep(1)
        
        if redeem_referral(session, wallet['address'], referral_code):
            log_message(f"[{wallet_num}/{total}] Referral Success!", "SUCCESS")
            # save_private_key(wallet['private_key'])  <-- Disabled per user request
            time.sleep(1)
            claimed, xp, streak = claim_daily_api(session, wallet['address'])
            if claimed:
                log_message(f"[{wallet_num}/{total}] Daily Claimed +{xp} XP", "CLAIM")
            success_count += 1
            return wallet
        else:
            log_message(f"[{wallet_num}/{total}] Referral Failed!", "ERROR")
            failed_count += 1
            return None
    except Exception as e:
        log_message(f"[{wallet_num}/{total}] Error: {str(e)[:30]}", "ERROR")
        failed_count += 1
        return None
def auto_referral():
    global success_count, failed_count
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{MAGENTA}              AUTO REFERRAL MODE{RESET}")
    print(f"{CYAN}{'='*60}{RESET}")
    print()
    
    while True:
        try:
            num_wallets = int(input(f"{YELLOW}How many wallets to create? : {WHITE}"))
            if num_wallets > 0: break
        except: pass
        print(f"{RED}[ERROR] Enter valid number!{RESET}")
    
    while True:
        try:
            num_threads = int(input(f"{YELLOW}How many threads to use? : {WHITE}"))
            if num_threads > 0: break
        except: pass
        print(f"{RED}[ERROR] Enter valid number!{RESET}")
    
    referral_code = input(f"{YELLOW}Enter your referral code: {WHITE}").strip().upper()
    if not referral_code:
        print(f"{RED}[ERROR] No referral code provided!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    
    proxies = load_proxies()
    print()
    print(f"{CYAN}{'-'*60}{RESET}")
    log_message(f"Starting {num_wallets} wallets with {num_threads} threads", "INFO")
    log_message(f"Referral Code: {referral_code}", "INFO")
    if proxies: log_message(f"Using {len(proxies)} keys", "INFO")
    print(f"{CYAN}{'-'*60}{RESET}")
    print()
    
    success_count = 0
    failed_count = 0
    created_wallets = []
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for i in range(1, num_wallets + 1):
            future = executor.submit(process_single_referral, i, num_wallets, referral_code, proxies)
            futures.append(future)
            time.sleep(0.3)
        for future in as_completed(futures):
            result = future.result()
            if result: created_wallets.append(result)
    
    print()
    print(f"{GREEN}{'='*60}{RESET}")
    print(f"{BOLD}{GREEN}              SUMMARY{RESET}")
    print(f"{GREEN}{'='*60}{RESET}")
    print(f"{WHITE}  Total Attempted : {CYAN}{num_wallets}{RESET}")
    print(f"{WHITE}  Successful      : {GREEN}{success_count}{RESET}")
    print(f"{WHITE}  Failed          : {RED}{failed_count}{RESET}")

    print(f"{GREEN}{'='*60}{RESET}")
    input(f"{YELLOW}Press Enter to continue...{RESET}")
# --- FEATURE 2: DAILY CHECKIN ---
def daily_checkin_flow():
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{MAGENTA}              DAILY CHECK-IN / CLAIM{RESET}")
    print(f"{CYAN}{'='*60}{RESET}")
    print()
    
    pks = load_private_keys()
    if not pks:
        print(f"{RED}[ERROR] No accounts found in pv.txt!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    
    proxies = load_proxies()
    log_message(f"Loaded {len(pks)} accounts", "INFO")
    if proxies: log_message(f"Loaded {len(proxies)} proxies", "INFO")
    print(f"{CYAN}{'-'*60}{RESET}")
    print()
    
    print(f"{YELLOW}Run 24h auto loop? (y/n){RESET}")
    choice = input(f"{WHITE}> {RESET}").strip().lower()
    
    loop = choice == 'y'
    
    cycle = 1
    while True:
        if loop:
            print()
            print(f"{CYAN}{'='*60}{RESET}")
            log_message(f"Daily Cycle #{cycle}", "CYCLE")
            print(f"{CYAN}{'-'*60}{RESET}")
            
        claimed_count = 0
        for i, pk in enumerate(pks, 1):
            if not pk.startswith("0x"): pk = "0x" + pk
            try:
                account = Account.from_key(pk)
                address = account.address
                session = requests.Session()
                if proxies:
                    proxy = proxies[i % len(proxies)]
                    session.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
                
                log_message(f"[{i}/{len(pks)}] {address[:12]}...{address[-6:]}", "INFO")
                claimed, xp, streak = claim_daily_api(session, address)
                if claimed:
                    log_message(f"[{i}/{len(pks)}] Claimed +{xp} XP | Streak: {streak}", "SUCCESS")
                    claimed_count += 1
                else:
                    log_message(f"[{i}/{len(pks)}] Already claimed or error", "WARNING")
                
                stats = get_user_stats(session, address)
                if stats:
                    log_message(f"[{i}/{len(pks)}] XP: {stats.get('xp', 0)} | Bets: {stats.get('total_bets', 0)}", "INFO")
                if i < len(pks): time.sleep(random.randint(2, 4))
            except Exception as e:
                log_message(f"[{i}/{len(pks)}] Error: {str(e)[:30]}", "ERROR")
        
        print(f"{GREEN}{'-'*60}{RESET}")
        log_message(f"Cycle #{cycle} Complete. Claimed: {claimed_count}/{len(pks)}", "SUCCESS")
        
        if not loop:
            input(f"{YELLOW}Press Enter to continue...{RESET}")
            break
            
        cycle += 1
        countdown(86400)
# --- FEATURE 3: MARKET BETTING ---
def get_active_markets(session):
    try:
        res = session.get("https://inkpredict.vercel.app/api/markets", headers=HEADERS, timeout=15)
        # Using the simple logic from Script 1
        return [m["id"] for m in res.json()["markets"] if not m["resolved"]]
    except: return []
def find_best_signal(session, active_ids):
    candidates = []
    min_confidence = 1.5
    
    log_message(f"Scanning {len(active_ids)} active markets...", "INFO")
    
    for mid in active_ids:
        try:
            res = session.get(f"https://inkpredict.vercel.app/api/market/{mid}/bets", headers=HEADERS, timeout=5)
            if res.status_code == 200:
                bets = res.json().get("bets", [])
                vol_yes = sum(float(b.get("amount", 0)) for b in bets if b.get("position") is True)
                vol_no = sum(float(b.get("amount", 0)) for b in bets if b.get("position") is False)
                
                if vol_yes < 2 or vol_no < 2: continue
                
                ratio = vol_yes / vol_no if vol_yes > vol_no else vol_no / vol_yes
                current_pos = True if vol_yes > vol_no else False
                
                log_message(f"Market {mid}: YES={vol_yes:.1f} NO={vol_no:.1f} Ratio={ratio:.1f}x", "DEBUG")
                
                if ratio >= min_confidence:
                    candidates.append((mid, current_pos, ratio))
        except: continue
    
    if candidates:
        # Pick a random market from the candidates
        import random
        selected_market, selected_pos, selected_ratio = random.choice(candidates)
        pos_str = "YES" if selected_pos else "NO"
        log_message(f"Signal Found: Market {selected_market} -> {pos_str} (Ratio {selected_ratio:.1f}x)", "SUCCESS")
        return selected_market, selected_pos
    
    log_message("No strong signal found. Skipping bet.", "WARNING")
    return None, None
def check_approve(w3, account, contract_usdc, amount_wei):
    try:
        allowance = contract_usdc.functions.allowance(account.address, CONTRACT_PREDICTION).call()
        if allowance < amount_wei:
            log_message("Approving USDC...", "WARNING")
            tx = contract_usdc.functions.approve(CONTRACT_PREDICTION, 2**256 - 1).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 100000,
                'gasPrice': w3.eth.gas_price,
                'chainId': CHAIN_ID
            })
            signed = w3.eth.account.sign_transaction(tx, account.key)
            w3.eth.send_raw_transaction(signed.raw_transaction)
            log_message("Approve Sent, waiting...", "INFO")
            time.sleep(5)
        return True
    except Exception as e:
        log_message(f"Approve Error: {str(e)[:40]}", "ERROR")
        return False
def execute_bet_tx(w3, account, contract_pred, contract_usdc, market_id, position, usdc_amount):
    try:
        dec = contract_usdc.functions.decimals().call()
        amount_wei = int(usdc_amount * (10 ** dec))
        
        # Check Balance (kept for safety, though Script 1 doesn't have it this explicit, it's good)
        balance = contract_usdc.functions.balanceOf(account.address).call()
        if balance < amount_wei:
            log_message("Insufficient USDC balance!", "ERROR")
            return None
        
        if not check_approve(w3, account, contract_usdc, amount_wei): return None
        
        pos_str = "YES" if position else "NO"
        log_message(f"Betting Market {market_id} -> {pos_str} ({usdc_amount} USDC)", "BET")
        
        tx = contract_pred.functions.placeBet(int(market_id), position, amount_wei).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 350000,
            'gasPrice': int(w3.eth.gas_price * 1.1),
            'chainId': CHAIN_ID
        })
        
        signed = w3.eth.account.sign_transaction(tx, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        tx_hash_hex = tx_hash.hex()
        
        log_message(f"Tx Hash: {tx_hash_hex}", "SUCCESS")
        
        # Wait for receipt but don't error out if status is 0 (matching Script 1 behavior)
        try:
            w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        except Exception as e:
            log_message(f"Wait Error (Transaction might still be valid): {str(e)}", "WARNING")
            
        return tx_hash_hex
        
    except Exception as e:
        log_message(f"Bet Error: {str(e)[:60]}", "ERROR")
        return None
def bet_market_flow():
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{MAGENTA}              BET MARKET MODE{RESET}")
    print(f"{CYAN}{'='*60}{RESET}")
    print()
    
    pks = load_private_keys()
    if not pks:
        print(f"{RED}[ERROR] No accounts found in pv.txt!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    
    proxies = load_proxies()
    
    try:
        bet_amount = float(input(f"{YELLOW}How many amount USDC for bet: {WHITE}"))
        bet_count = int(input(f"{YELLOW}How many times bets: {WHITE}"))
    except ValueError:
        bet_amount, bet_count = 1, 1
    
    log_message(f"Loaded {len(pks)} accounts", "INFO")
    if proxies: log_message(f"Loaded {len(proxies)} proxies", "INFO")
    print(f"\n{CYAN}{'='*60}{RESET}\n")
    
    w3 = get_web3()
    if not w3.is_connected():
        print(f"{RED}[ERROR] Cannot connect to RPC!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    
    contract_pred = w3.eth.contract(address=CONTRACT_PREDICTION, abi=ABI_PREDICTION)
    contract_usdc = w3.eth.contract(address=TOKEN_USDC, abi=ABI_ERC20)
    
    cycle = 1
    while True:
        log_message(f"Cycle #{cycle} Started", "CYCLE")
        print(f"{CYAN}{'-'*60}{RESET}")
        
        session = requests.Session()
        if proxies:
            proxy = random.choice(proxies)
            session.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        
        active_ids = get_active_markets(session)
        if not active_ids:
            log_message("No active markets!", "ERROR")
            cycle += 1
            countdown(3600)
            continue
        
        target_market_id, target_pos = find_best_signal(session, active_ids)
        if not target_market_id:
            log_message("No signal, waiting 1 hour...", "WARNING")
            cycle += 1
            countdown(3600)
            continue
        
        for idx, pk in enumerate(pks, 1):
            if pk.startswith("0x"): pk = pk[2:]
            try:
                account = Account.from_key(pk)
                address = account.address
                
                log_message(f"Account #{idx}/{len(pks)}: {address[:6]}...{address[-4:]}", "INFO")
                if proxies:
                    current_proxy = proxies[idx % len(proxies)]
                    session.proxies = {"http": f"http://{current_proxy}", "https": f"http://{current_proxy}"}
                
                # Claim daily first
                claim_daily_api(session, address)
                
                for b_idx in range(bet_count):
                    # No processing log in Script 1 betting loop? It has: log(f"Processing Bet...")
                    log_message(f"Processing Bet {b_idx+1}/{bet_count}", "INFO")
                    
                    tx_hash = execute_bet_tx(w3, account, contract_pred, contract_usdc, target_market_id, target_pos, bet_amount)
                    if tx_hash:
                        notify_api(session, address, target_market_id, bet_amount, target_pos, tx_hash)
                        # Script 1 also updates stats/rank after bet
                        stats = get_user_stats(session, address)
                        if stats:
                            log_message(f"XP: {stats.get('xp', 0)} | Bets: {stats.get('total_bets', 0)}", "SUCCESS")
                        get_user_rank(session, address)
                    
                    time.sleep(1)
                
                if idx < len(pks):
                    random_delay()
                    print(f"{WHITE}{'.'*60}{RESET}")
            except Exception as e:
                log_message(f"Error: {str(e)[:40]}", "ERROR")
        
        print(f"{CYAN}{'-'*60}{RESET}")
        log_message(f"Cycle #{cycle} Complete", "CYCLE")
        print(f"{CYAN}{'='*60}{RESET}\n")
        
        cycle += 1
        countdown(86400)
# --- UTILS ---
def random_delay():
    delay = random.randint(2, 5)
    log_message(f"Delay {delay} seconds...", "INFO")
    time.sleep(delay)
def countdown(seconds):
    for i in range(seconds, 0, -1):
        hours = i // 3600
        minutes = (i % 3600) // 60
        secs = i % 60
        print(f"\r{YELLOW}[COUNTDOWN] Next cycle in: {hours:02d}:{minutes:02d}:{secs:02d} {RESET}", end="", flush=True)
        time.sleep(1)
    print("\r" + " " * 60 + "\r", end="", flush=True)
def main():
    while True:
        print_banner()
        print_menu()
        choice = input(f"{BOLD}{WHITE}Select option: {RESET}").strip()
        
        if choice == "1":
            daily_checkin_flow()
        elif choice == "2":
            bet_market_flow()
        elif choice == "3":
            auto_referral()
        elif choice == "4":
            print(f"{CYAN}{'='*60}{RESET}")
            print(f"{BOLD}{MAGENTA}      Goodbye!{RESET}")
            print(f"{CYAN}{'='*60}{RESET}")
            sys.exit(0)
        else:
            print(f"{RED}[ERROR] Invalid option!{RESET}")
            time.sleep(1)
if __name__ == "__main__":
    main()