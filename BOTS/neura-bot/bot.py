#!/usr/bin/env python3
"""
NEURA PROTOCOL AUTO BOT - FULL FIXED VERSION
CREATED BY KAZUHA VIP ONLY
"""

import os
import sys
import json
import time
from datetime import datetime, date
from decimal import Decimal
from web3 import Web3
from eth_account import Account
from eth_abi.abi import encode as abi_encode
from dotenv import load_dotenv
import requests

load_dotenv()

class Colors:
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'

RPC_URL = "https://testnet.rpc.neuraprotocol.io/"
API_BASE = "https://neuraverse-testnet.infra.neuraprotocol.io/api"
SUBGRAPH_URL = "https://api.goldsky.com/api/public/project_cmc8t6vh6mqlg01w19r2g15a7/subgraphs/analytics/1.0.1/gn"
CHAIN_ID = 267

SWAP_ROUTER = Web3.to_checksum_address("0x5AeFBA317BAba46EAF98Fd6f381d07673bcA6467")
WANKR_ADDRESS = Web3.to_checksum_address("0xbd833b6ecc30caeabf81db18bb0f1e00c6997e7a")

CLAIM_TRACKER_FILE = "pulse_claims.json"

ERC20_ABI = json.loads('''
[
    {"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}
]
''')

MAX_UINT256 = 2**256 - 1
PULSE_IDS = ["pulse:1", "pulse:2", "pulse:3", "pulse:4", "pulse:5", "pulse:6", "pulse:7"]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    clear_screen()
    print(f"{Colors.CYAN}========================================{Colors.RESET}")
    print(f"{Colors.MAGENTA}       NEURA PROTOCOL AUTO BOT     {Colors.RESET}")
    print(f"{Colors.YELLOW}      CREATED BY KAZUHA VIP ONLY       {Colors.RESET}")
    print(f"{Colors.CYAN}========================================{Colors.RESET}")
    print()

def log_info(msg):
    print(f"{Colors.WHITE}[INFO] {msg}{Colors.RESET}")

def log_success(msg):
    print(f"{Colors.GREEN}[SUCCESS] {msg}{Colors.RESET}")

def log_error(msg):
    print(f"{Colors.RED}[ERROR] {msg}{Colors.RESET}")

def log_warning(msg):
    print(f"{Colors.YELLOW}[WARNING] {msg}{Colors.RESET}")

def log_step(msg):
    print(f"\n{Colors.CYAN}[STEP] {msg}{Colors.RESET}")

def print_menu():
    print(f"{Colors.GREEN}[1]{Colors.RESET} Daily Checkin")
    print(f"{Colors.GREEN}[2]{Colors.RESET} Swaps (ANKR to Other Tokens)")
    print(f"{Colors.GREEN}[3]{Colors.RESET} Claim Pulse")
    print(f"{Colors.GREEN}[4]{Colors.RESET} Auto Loop (24h)")
    print(f"{Colors.GREEN}[5]{Colors.RESET} Check Balance")
    print(f"{Colors.RED}[0]{Colors.RESET} Exit")
    print()

def load_claim_tracker():
    """Load pulse claim tracking data"""
    try:
        if os.path.exists(CLAIM_TRACKER_FILE):
            with open(CLAIM_TRACKER_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        log_warning(f"Could not load claim tracker: {e}")
    return {}

def save_claim_tracker(data):
    """Save pulse claim tracking data"""
    try:
        with open(CLAIM_TRACKER_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log_error(f"Could not save claim tracker: {e}")

def get_today_date():
    """Get today's date as string"""
    return date.today().isoformat()

def is_pulse_claimed_today(address, pulse_id, tracker):
    """Check if pulse was already claimed today for this address"""
    today = get_today_date()
    address_lower = address.lower()
    
    if address_lower not in tracker:
        return False
    
    if today not in tracker[address_lower]:
        return False
    
    return pulse_id in tracker[address_lower][today]

def mark_pulse_claimed(address, pulse_id, tracker):
    """Mark a pulse as claimed for today"""
    today = get_today_date()
    address_lower = address.lower()
    
    if address_lower not in tracker:
        tracker[address_lower] = {}
    
    if today not in tracker[address_lower]:
        tracker[address_lower][today] = []
    
    if pulse_id not in tracker[address_lower][today]:
        tracker[address_lower][today].append(pulse_id)
    
    save_claim_tracker(tracker)

def cleanup_old_claims(tracker):
    """Remove claims older than 2 days to keep file small"""
    today = get_today_date()
    today_date = date.today()
    
    for address in list(tracker.keys()):
        for claim_date in list(tracker[address].keys()):
            try:
                claim_date_obj = date.fromisoformat(claim_date)
                days_diff = (today_date - claim_date_obj).days
                if days_diff > 2:
                    del tracker[address][claim_date]
            except:
                pass
        
        if not tracker[address]:
            del tracker[address]
    
    save_claim_tracker(tracker)
    return tracker

def load_config():
    private_keys = []
    privy_tokens = []
    
    for i in range(1, 100):
        key_name = f"PRIVATE_KEY_{i}"
        pk = os.getenv(key_name)
        if pk:
            if not pk.startswith("0x"):
                pk = "0x" + pk
            private_keys.append(pk)
        elif i == 1:
            pk = os.getenv("PRIVATE_KEY")
            if pk:
                if not pk.startswith("0x"):
                    pk = "0x" + pk
                private_keys.append(pk)
            break
        else:
            break
    
    for i in range(1, 100):
        token_name = f"PRIVY_TOKEN_{i}"
        pt = os.getenv(token_name)
        if pt:
            privy_tokens.append(pt)
        elif i == 1:
            pt = os.getenv("PRIVY_TOKEN")
            if pt:
                privy_tokens.append(pt)
            break
        else:
            break
    
    return private_keys, privy_tokens

def get_address_from_key(private_key):
    account = Account.from_key(private_key)
    return account.address

def fetch_available_tokens():
    log_info("Fetching available swap tokens...")
    
    try:
        query = "query AllTokens { tokens { id symbol name decimals } }"
        body = {"operationName": "AllTokens", "variables": {}, "query": query}
        
        response = requests.post(SUBGRAPH_URL, json=body, timeout=30)
        response.raise_for_status()
        
        tokens_data = response.json().get('data', {}).get('tokens', [])
        
        unique_tokens = {}
        for token in tokens_data:
            if not token.get('symbol') or ' ' in token['symbol']:
                continue
            symbol = token['symbol'].upper()
            if symbol not in unique_tokens:
                unique_tokens[symbol] = {
                    'address': Web3.to_checksum_address(token['id']),
                    'symbol': symbol,
                    'name': token.get('name', symbol),
                    'decimals': int(token['decimals'])
                }
        
        if 'WANKR' in unique_tokens:
            unique_tokens['ANKR'] = {
                'address': WANKR_ADDRESS,
                'symbol': 'ANKR',
                'name': 'Native ANKR',
                'decimals': 18
            }
        
        sorted_tokens = sorted(unique_tokens.values(), key=lambda t: t['symbol'])
        log_success(f"Found {len(sorted_tokens)} unique swappable tokens")
        
        return sorted_tokens
        
    except Exception as e:
        log_error(f"Failed to fetch tokens: {e}")
        return []

def get_auth_session(address, privy_token):
    session = requests.Session()
    
    session.headers.update({
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": f"Bearer {privy_token}",
        "content-type": "application/json",
        "origin": "https://neuraverse.neuraprotocol.io",
        "referer": "https://neuraverse.neuraprotocol.io/",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36",
    })
    
    session.cookies.set("privy-id-token", privy_token, domain="neuraverse-testnet.infra.neuraprotocol.io")
    session.cookies.set("privy-token", privy_token, domain="neuraverse-testnet.infra.neuraprotocol.io")
    
    return session

def claim_daily_checkin(session, address):
    log_step(f"Processing Daily Checkin for {address[:10]}...")
    
    try:
        response = session.get(f"{API_BASE}/tasks")
        
        if response.status_code == 200:
            tasks = response.json().get("tasks", [])
            
            for task in tasks:
                if task["id"] == "daily_login":
                    status = task.get("status", "")
                    
                    if status == "claimable":
                        claim_response = session.post(f"{API_BASE}/tasks/daily_login/claim")
                        
                        if claim_response.status_code == 200:
                            log_success(f"Daily Checkin Claimed! Points: +{task.get('points', 10)}")
                            return True
                        else:
                            log_error(f"Claim Failed: {claim_response.text}")
                            
                    elif status == "claimed":
                        log_warning("Daily Checkin Already Claimed Today")
                        return True
                        
                    elif status == "notCompleted":
                        log_warning("Daily Checkin Not Yet Available")
                        event_payload = {
                            "type": "daily:login",
                            "payload": {"address": address.lower()}
                        }
                        session.post(f"{API_BASE}/events", json=event_payload)
                    else:
                        log_warning(f"Status: {status}")
                    break
        else:
            log_error(f"Failed to get tasks: {response.status_code}")
            
    except Exception as e:
        log_error(f"Error: {str(e)}")
    
    return False

def claim_pulse(session, address):
    log_step(f"Claiming Pulses for {address[:10]}...")
    
    tracker = load_claim_tracker()
    tracker = cleanup_old_claims(tracker)
    
    claimed = 0
    already_claimed = 0
    failed = 0
    
    for pulse_id in PULSE_IDS:
        if is_pulse_claimed_today(address, pulse_id, tracker):
            log_warning(f"{pulse_id}: Already claimed today (skipping)")
            already_claimed += 1
            continue
        
        try:
            payload = {
                "type": "pulse:collectPulse",
                "payload": {"id": pulse_id}
            }
            
            response = session.post(f"{API_BASE}/events", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("address") or result.get("success"):
                    log_success(f"{pulse_id} Claimed!")
                    mark_pulse_claimed(address, pulse_id, tracker)
                    claimed += 1
                elif "already" in str(result).lower() or "collected" in str(result).lower():
                    log_warning(f"{pulse_id}: Already claimed on server")
                    mark_pulse_claimed(address, pulse_id, tracker)
                    already_claimed += 1
                else:
                    error_msg = result.get("error", result.get("message", "Unknown"))
                    if "already" in str(error_msg).lower():
                        log_warning(f"{pulse_id}: Already claimed")
                        mark_pulse_claimed(address, pulse_id, tracker)
                        already_claimed += 1
                    else:
                        log_error(f"{pulse_id}: {error_msg}")
                        failed += 1
            else:
                response_text = response.text.lower()
                if "already" in response_text or "claimed" in response_text:
                    log_warning(f"{pulse_id}: Already claimed")
                    mark_pulse_claimed(address, pulse_id, tracker)
                    already_claimed += 1
                else:
                    log_error(f"{pulse_id}: Error {response.status_code}")
                    failed += 1
            
            time.sleep(1.5)
            
        except Exception as e:
            log_error(f"{pulse_id}: {str(e)}")
            failed += 1
    
    log_info(f"Summary: Claimed={claimed}, Already Claimed={already_claimed}, Failed={failed}")
    return claimed


class SwapBot:
    
    def __init__(self, w3, private_key):
        self.w3 = w3
        self.account = Account.from_key(private_key)
        self.address = self.account.address
        self.private_key = private_key
    
    def _encode_inner_swap(self, token_in, token_out, deadline_ms, amount_in_wei):
        types = ['address', 'address', 'uint256', 'address', 'uint256', 'uint256', 'uint256', 'uint256']
        values = [
            Web3.to_checksum_address(token_in),
            Web3.to_checksum_address(token_out),
            0,
            self.address,
            deadline_ms,
            amount_in_wei,
            1,
            0
        ]
        encoded_params = abi_encode(types, values)
        return '0x1679c792' + encoded_params.hex()
    
    def _encode_router_multicall(self, calls):
        function_selector = '0xac9650d8'
        encoded_params = abi_encode(['bytes[]'], [calls])
        return function_selector + encoded_params.hex()
    
    def check_and_approve(self, token_address, amount_wei):
        try:
            token_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=ERC20_ABI
            )
            
            allowance = token_contract.functions.allowance(
                self.address,
                SWAP_ROUTER
            ).call()
            
            if allowance < amount_wei:
                log_info(f"Approving token for router...")
                
                nonce = self.w3.eth.get_transaction_count(self.address)
                gas_price = self.w3.eth.gas_price
                
                approve_tx = token_contract.functions.approve(
                    SWAP_ROUTER,
                    MAX_UINT256
                ).build_transaction({
                    'from': self.address,
                    'nonce': nonce,
                    'gasPrice': gas_price,
                    'gas': 100000,
                    'chainId': CHAIN_ID
                })
                
                signed_tx = self.w3.eth.account.sign_transaction(approve_tx, self.private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                
                log_info(f"Approval TX: {tx_hash.hex()}")
                
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                
                if receipt['status'] == 1:
                    log_success("Approval successful!")
                    return True
                else:
                    log_error("Approval failed!")
                    return False
            else:
                log_info("Allowance already sufficient")
                return True
                
        except Exception as e:
            log_error(f"Approval error: {e}")
            return False
    
    def get_token_balance(self, token_address):
        try:
            token_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=ERC20_ABI
            )
            balance = token_contract.functions.balanceOf(self.address).call()
            decimals = token_contract.functions.decimals().call()
            return balance, decimals
        except Exception as e:
            log_error(f"Balance check error: {e}")
            return 0, 18
    
    def perform_swap(self, token_in, token_out, amount_in_str):
        try:
            amount_in_decimal = Decimal(amount_in_str)
            if amount_in_decimal <= 0:
                raise ValueError("Amount must be positive")
        except Exception:
            raise ValueError(f'Invalid amount: "{amount_in_str}"')
        
        log_step(f"Swapping {amount_in_str} {token_in['symbol']} to {token_out['symbol']}...")
        
        try:
            amount_in_wei = int(amount_in_decimal * (10 ** token_in['decimals']))
            is_native_swap = token_in['symbol'] in ['ANKR', 'WANKR']
            
            if is_native_swap:
                balance = self.w3.eth.get_balance(self.address)
                if balance < amount_in_wei + Web3.to_wei(0.001, 'ether'):
                    raise ValueError(f"Insufficient ANKR balance")
            else:
                balance, _ = self.get_token_balance(token_in['address'])
                if balance < amount_in_wei:
                    raise ValueError(f"Insufficient {token_in['symbol']} balance")
            
            if not is_native_swap:
                if not self.check_and_approve(token_in['address'], amount_in_wei):
                    raise ValueError("Approval failed")
            
            nonce = self.w3.eth.get_transaction_count(self.address)
            gas_price = self.w3.eth.gas_price
            
            min_gas_price = Web3.to_wei(1, 'gwei')
            if gas_price < min_gas_price:
                gas_price = min_gas_price
            
            deadline_ms = (int(time.time() * 1000)) + (20 * 60 * 1000)
            
            token_in_for_router = WANKR_ADDRESS if is_native_swap else token_in['address']
            
            inner_call = self._encode_inner_swap(
                token_in=token_in_for_router,
                token_out=token_out['address'],
                deadline_ms=deadline_ms,
                amount_in_wei=amount_in_wei
            )
            
            inner_bytes = Web3.to_bytes(hexstr=inner_call)
            calldata = self._encode_router_multicall([inner_bytes])
            
            tx_value = amount_in_wei if is_native_swap else 0
            
            log_info("Sending swap transaction...")
            
            tx = {
                'from': self.address,
                'to': SWAP_ROUTER,
                'value': tx_value,
                'data': calldata,
                'nonce': nonce,
                'gas': 500000,
                'gasPrice': gas_price,
                'chainId': CHAIN_ID
            }
            
            try:
                estimated_gas = self.w3.eth.estimate_gas(tx)
                tx['gas'] = int(estimated_gas * 1.3)
                log_info(f"Estimated gas: {estimated_gas}")
            except Exception as e:
                log_warning(f"Gas estimation failed, using 500000")
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            log_info(f"TX Hash: {tx_hash.hex()}")
            log_info("Waiting for confirmation...")
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt['status'] == 1:
                log_success(f"Swap successful!")
                log_success(f"Explorer: https://testnet.neuraprotocol.io/tx/{tx_hash.hex()}")
                return True
            else:
                log_error("Swap transaction failed!")
                return False
                
        except Exception as e:
            log_error(f"Swap error: {str(e)}")
            return False
    
    def perform_swap_with_retries(self, token_in, token_out, amount_in_str, max_retries=3):
        for i in range(max_retries):
            try:
                result = self.perform_swap(token_in, token_out, amount_in_str)
                if result:
                    return True
            except ValueError as e:
                log_error(f"Swap cancelled: {e}")
                return False
            except Exception as e:
                log_warning(f"Attempt {i+1}/{max_retries} failed: {e}")
                
                if i < max_retries - 1:
                    log_info("Retrying in 10 seconds...")
                    time.sleep(10)
        
        log_error(f"Swap failed after {max_retries} attempts")
        return False


def check_balances(w3, address, tokens):
    log_step(f"Checking balances for {address[:10]}...")
    
    native_balance = w3.eth.get_balance(address)
    native_ankr = Web3.from_wei(native_balance, 'ether')
    log_info(f"ANKR (Native): {native_ankr:.6f}")
    
    for token in tokens[:15]:
        try:
            if token['symbol'] in ['ANKR', 'WANKR']:
                continue
            contract = w3.eth.contract(
                address=token['address'],
                abi=ERC20_ABI
            )
            balance = contract.functions.balanceOf(address).call()
            if balance > 0:
                balance_formatted = Decimal(balance) / (10 ** token['decimals'])
                log_info(f"{token['symbol']}: {balance_formatted:.6f}")
        except:
            pass


def select_token_for_swap(tokens):
    print(f"\n{Colors.CYAN}Available Tokens (ANKR will swap to selected token):{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")
    
    other_tokens = [t for t in tokens if t['symbol'] not in ['ANKR', 'WANKR']]
    
    for i, token in enumerate(other_tokens):
        print(f"{Colors.GREEN}[{i+1}]{Colors.RESET} {token['symbol']} - {token['name'][:30]}")
    
    print()
    
    try:
        token_idx = int(input(f"{Colors.YELLOW}Select Token number (ANKR will swap to this): {Colors.RESET}")) - 1
        if token_idx < 0 or token_idx >= len(other_tokens):
            raise ValueError("Invalid selection")
        token_out = other_tokens[token_idx]
        
        amount = input(f"{Colors.YELLOW}Enter ANKR amount to swap (e.g., 0.01): {Colors.RESET}")
        
        repeats_str = input(f"{Colors.YELLOW}How many times to repeat? (default: 1): {Colors.RESET}")
        repeats = int(repeats_str) if repeats_str.isdigit() and int(repeats_str) > 0 else 1
        
        token_ankr = {
            'address': WANKR_ADDRESS,
            'symbol': 'ANKR',
            'name': 'Native ANKR',
            'decimals': 18
        }
        
        return token_ankr, token_out, amount, repeats
        
    except (ValueError, KeyboardInterrupt) as e:
        log_error(f"Invalid input: {e}")
        return None, None, None, 0


def execute_swaps(w3, private_keys, tokens):
    token_ankr, token_out, amount, repeats = select_token_for_swap(tokens)
    
    if not token_ankr or not token_out:
        return
    
    log_info(f"Swap configured: {amount} ANKR to {token_out['symbol']}")
    log_info(f"Repeats: {repeats}")
    
    for pk in private_keys:
        bot = SwapBot(w3, pk)
        log_step(f"Processing Wallet {bot.address[:10]}...")
        
        balance = w3.eth.get_balance(bot.address)
        balance_ankr = Web3.from_wei(balance, 'ether')
        log_info(f"ANKR Balance: {balance_ankr:.6f}")
        
        if balance < Web3.to_wei(0.001, 'ether'):
            log_error("Insufficient balance for gas, skipping...")
            continue
        
        for j in range(repeats):
            log_step(f"Swap Cycle {j+1}/{repeats}")
            
            success = bot.perform_swap_with_retries(token_ankr, token_out, amount)
            
            if success and j < repeats - 1:
                log_info("Waiting 10 seconds before next swap...")
                time.sleep(10)
        
        log_success(f"All cycles completed for wallet {bot.address[:10]}")
        time.sleep(3)
    
    log_success("All wallets processed!")


def auto_loop_24h(w3, private_keys, privy_tokens, tokens):
    log_step("Starting 24-hour auto loop...")
    
    if not tokens:
        tokens = fetch_available_tokens()
    
    if not tokens:
        log_error("Failed to fetch tokens")
        return
    
    token_ankr = {
        'address': WANKR_ADDRESS,
        'symbol': 'ANKR',
        'name': 'Native ANKR',
        'decimals': 18
    }
    
    other_tokens = [t for t in tokens if t['symbol'] not in ['ANKR', 'WANKR']]
    
    if not other_tokens:
        log_error("No other tokens found")
        return
    
    while True:
        try:
            log_step("Starting new cycle...")
            
            for i, pk in enumerate(private_keys):
                bot = SwapBot(w3, pk)
                privy_token = privy_tokens[i] if i < len(privy_tokens) else None
                
                log_step(f"Processing Wallet {bot.address[:10]}...")
                
                if privy_token:
                    session = get_auth_session(bot.address, privy_token)
                    claim_daily_checkin(session, bot.address)
                    claim_pulse(session, bot.address)
                
                balance = w3.eth.get_balance(bot.address)
                if balance > Web3.to_wei(0.05, 'ether'):
                    for j in range(5):
                        token_out = other_tokens[j % len(other_tokens)]
                        log_step(f"Swap {j+1}/5: ANKR to {token_out['symbol']}")
                        
                        bot.perform_swap_with_retries(token_ankr, token_out, "0.005")
                        time.sleep(10)
                
                time.sleep(5)
            
            log_success("Cycle completed! Waiting 24 hours...")
            time.sleep(24 * 60 * 60)
            
        except KeyboardInterrupt:
            log_warning("Loop stopped by user")
            break
        except Exception as e:
            log_error(f"Error in loop: {e}")
            log_info("Retrying in 1 hour...")
            time.sleep(60 * 60)


def create_env_template():
    if not os.path.exists(".env"):
        template = """# NEURA PROTOCOL BOT CONFIG
# CREATED BY KAZUHA VIP ONLY

# Private Key (with or without 0x prefix)
PRIVATE_KEY_1=your_private_key_here

# Privy Token (from browser - F12 -> Application -> Cookies)
PRIVY_TOKEN_1=your_privy_token_here

# For multiple wallets:
# PRIVATE_KEY_2=second_private_key
# PRIVY_TOKEN_2=second_privy_token
"""
        with open(".env", "w") as f:
            f.write(template)
        log_warning("Created .env template file")
        return False
    return True


def main():
    print_banner()
    
    if not create_env_template():
        log_error("Please configure .env file and restart")
        return
    
    private_keys, privy_tokens = load_config()
    
    if not private_keys:
        log_error("No private keys found in .env")
        log_warning("Add PRIVATE_KEY_1=your_key to .env file")
        return
    
    log_success(f"Loaded {len(private_keys)} Wallet(s)")
    log_success(f"Loaded {len(privy_tokens)} Privy Token(s)")
    
    for i, key in enumerate(private_keys):
        addr = get_address_from_key(key)
        has_token = "Yes" if i < len(privy_tokens) else "No"
        log_info(f"[{i+1}] {addr} | Privy Token: {has_token}")
    
    print()
    
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    if not w3.is_connected():
        log_error("Failed to connect to Neura Testnet")
        return
    
    log_success(f"Connected to Neura Testnet (Chain ID: {CHAIN_ID})")
    log_info(f"Router: {SWAP_ROUTER}")
    log_info(f"WANKR: {WANKR_ADDRESS}")
    print()
    
    tokens = fetch_available_tokens()
    
    while True:
        print_menu()
        
        try:
            choice = input(f"{Colors.CYAN}Enter choice: {Colors.RESET}")
            print()
            
            if choice == "1":
                log_step("=== DAILY CHECKIN ===")
                for i, pk in enumerate(private_keys):
                    address = get_address_from_key(pk)
                    privy_token = privy_tokens[i] if i < len(privy_tokens) else None
                    
                    if privy_token:
                        session = get_auth_session(address, privy_token)
                        claim_daily_checkin(session, address)
                    else:
                        log_error(f"No privy token for wallet {i+1}")
                
            elif choice == "2":
                log_step("=== SWAPS (ANKR TO OTHER) ===")
                if not tokens:
                    tokens = fetch_available_tokens()
                execute_swaps(w3, private_keys, tokens)
                
            elif choice == "3":
                log_step("=== CLAIM PULSE ===")
                for i, pk in enumerate(private_keys):
                    address = get_address_from_key(pk)
                    privy_token = privy_tokens[i] if i < len(privy_tokens) else None
                    
                    if privy_token:
                        session = get_auth_session(address, privy_token)
                        claim_pulse(session, address)
                    else:
                        log_error(f"No privy token for wallet {i+1}")
                
            elif choice == "4":
                log_step("=== AUTO LOOP 24H ===")
                auto_loop_24h(w3, private_keys, privy_tokens, tokens)
                
            elif choice == "5":
                log_step("=== CHECK BALANCES ===")
                if not tokens:
                    tokens = fetch_available_tokens()
                for pk in private_keys:
                    address = get_address_from_key(pk)
                    check_balances(w3, address, tokens)
                
            elif choice == "0":
                log_warning("Exiting... Goodbye!")
                break
                
            else:
                log_error("Invalid choice!")
            
            print()
            input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
            print_banner()
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Interrupted! Goodbye!{Colors.RESET}")
            break
        except Exception as e:
            log_error(f"Error: {str(e)}")
            input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
            print_banner()


if __name__ == "__main__":
    main()