import os
import sys
import time
import random
from web3 import Web3
from eth_account import Account
from concurrent.futures import ThreadPoolExecutor, as_completed

# BOLD COLORS
class Colors:
    BOLD = '\033[1m'
    RED = '\033[1;91m'
    GREEN = '\033[1;92m'
    YELLOW = '\033[1;93m'
    BLUE = '\033[1;94m'
    MAGENTA = '\033[1;95m'
    CYAN = '\033[1;96m'
    WHITE = '\033[1;97m'
    RESET = '\033[0m'

# CONTRACT ADDRESSES
EUROZ_TOKEN = "0xED1B7De57918f6B7c8a7a7767557f09A80eC2a35"
CEUROZ_CONTRACT = "0xCD25e0e4972e075C371948c7137Bcd498C1F4e89"

# Multiple RPC endpoints for better reliability
RPC_URLS = [
    "https://sepolia.drpc.org/",
    "https://ethereum-sepolia-rpc.publicnode.com",
    "https://1rpc.io/sepolia",
    "https://0xrpc.io/sep",
    "https://gateway.tenderly.co/public/sepolia"
]

CHAIN_ID = 11155111
EXPLORER_URL = "https://sepolia.etherscan.io/tx/"
DEAD_ADDRESS = "0x000000000000000000000000000000000000dEaD"

# ABI DEFINITIONS
EUROZ_ABI = [
    {"inputs":[{"name":"account","type":"address"}],"name":"mint","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"spender","type":"address"},{"name":"value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"to","type":"address"},{"name":"value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]

CEUROZ_ABI = [
    {"inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"wrap","outputs":[],"stateMutability":"nonpayable","type":"function"}
]

class EurozBot:
    def __init__(self, private_key, wallet_num=1):
        # Rotate RPC for each wallet to distribute load
        rpc_index = (wallet_num - 1) % len(RPC_URLS)
        self.rpc_url = RPC_URLS[rpc_index]
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={'timeout': 60}))
        self.private_key = private_key
        self.wallet_num = wallet_num
        if not self.private_key.startswith("0x"):
            self.private_key = "0x" + self.private_key
        self.account = Account.from_key(self.private_key)
        self.address = self.account.address
        print(f"{Colors.BLUE}[W{self.wallet_num}] Using RPC: {self.rpc_url}{Colors.RESET}")

    def get_balance(self):
        try:
            balance = self.w3.eth.get_balance(self.address)
            return float(self.w3.from_wei(balance, 'ether'))
        except Exception as e:
            print(f"{Colors.RED}[W{self.wallet_num}] Balance check error: {e}{Colors.RESET}")
            return 0

    def get_euroz_balance(self):
        try:
            contract = self.w3.eth.contract(address=Web3.to_checksum_address(EUROZ_TOKEN), abi=EUROZ_ABI)
            balance = contract.functions.balanceOf(self.address).call()
            return float(balance / 1000000)
        except Exception as e:
            print(f"{Colors.RED}[W{self.wallet_num}] EUROZ balance check error: {e}{Colors.RESET}")
            return 0

    def get_nonce(self):
        pending = self.w3.eth.get_transaction_count(self.address, 'pending')
        latest = self.w3.eth.get_transaction_count(self.address, 'latest')
        return max(pending, latest)

    def get_gas_params(self):
        max_priority_fee = self.w3.to_wei(1.5, 'gwei')
        max_fee = self.w3.to_wei(1.500000019, 'gwei')
        return max_fee, max_priority_fee

    def send_tx(self, tx):
        # Random delay 1-3 seconds for organic look
        delay = random.uniform(1, 3)
        time.sleep(delay)
        
        for attempt in range(5):  # Increased to 5 attempts
            try:
                signed = self.w3.eth.account.sign_transaction(tx, self.private_key)
                # Support both old and new eth-account versions
                raw_tx = getattr(signed, 'rawTransaction', None) or getattr(signed, 'raw_transaction', None)
                if raw_tx is None:
                    raise AttributeError("Could not find raw transaction attribute")
                
                tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
                tx_hash_hex = "0x" + tx_hash.hex() if not tx_hash.hex().startswith("0x") else tx_hash.hex()
                print(f"{Colors.CYAN}[W{self.wallet_num}] TX: {tx_hash_hex}{Colors.RESET}")
                print(f"{Colors.YELLOW}[W{self.wallet_num}] WAITING...{Colors.RESET}")
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
                if receipt['status'] == 1:
                    print(f"{Colors.GREEN}[W{self.wallet_num}] SUCCESS - BLOCK: {receipt['blockNumber']}{Colors.RESET}")
                    print(f"{Colors.GREEN}[W{self.wallet_num}] {EXPLORER_URL}{tx_hash_hex}{Colors.RESET}")
                    return True
                else:
                    print(f"{Colors.RED}[W{self.wallet_num}] FAILED{Colors.RESET}")
                    return False
            except Exception as e:
                err = str(e)
                if "429" in err or "Too Many Requests" in err:
                    wait_time = (attempt + 1) * 5
                    print(f"{Colors.YELLOW}[W{self.wallet_num}] RATE LIMIT, WAITING {wait_time}s...{Colors.RESET}")
                    time.sleep(wait_time)
                    continue
                elif "already known" in err:
                    print(f"{Colors.YELLOW}[W{self.wallet_num}] ALREADY SENT, WAITING...{Colors.RESET}")
                    time.sleep(15)
                    return True
                elif "nonce too low" in err:
                    print(f"{Colors.YELLOW}[W{self.wallet_num}] NONCE ERROR, RETRY...{Colors.RESET}")
                    time.sleep(3)
                    tx['nonce'] = self.get_nonce()
                    continue
                elif "replacement transaction underpriced" in err:
                    print(f"{Colors.YELLOW}[W{self.wallet_num}] GAS ERROR, RETRY...{Colors.RESET}")
                    time.sleep(3)
                    tx['nonce'] = self.get_nonce()
                    tx['maxFeePerGas'] = int(tx['maxFeePerGas'] * 1.2)
                    continue
                else:
                    print(f"{Colors.RED}[W{self.wallet_num}] ERROR: {e}{Colors.RESET}")
                    return False
        return False

    def mint_euroz(self):
        print(f"{Colors.MAGENTA}[W{self.wallet_num}] MINTING 10 EUROZ...{Colors.RESET}")
        try:
            contract = self.w3.eth.contract(address=Web3.to_checksum_address(EUROZ_TOKEN), abi=EUROZ_ABI)
            max_fee, max_priority = self.get_gas_params()
            nonce = self.get_nonce()
            tx = contract.functions.mint(self.address).build_transaction({
                'chainId': CHAIN_ID,
                'gas': 80000,
                'maxFeePerGas': max_fee,
                'maxPriorityFeePerGas': max_priority,
                'nonce': nonce,
                'type': 2
            })
            return self.send_tx(tx)
        except Exception as e:
            print(f"{Colors.RED}[W{self.wallet_num}] MINT ERROR: {e}{Colors.RESET}")
            return False

    def approve_euroz(self, amount):
        print(f"{Colors.MAGENTA}[W{self.wallet_num}] APPROVING {amount} EUROZ...{Colors.RESET}")
        try:
            contract = self.w3.eth.contract(address=Web3.to_checksum_address(EUROZ_TOKEN), abi=EUROZ_ABI)
            amount_wei = int(amount * 1000000)
            max_fee, max_priority = self.get_gas_params()
            nonce = self.get_nonce()
            tx = contract.functions.approve(Web3.to_checksum_address(CEUROZ_CONTRACT), amount_wei).build_transaction({
                'chainId': CHAIN_ID,
                'gas': 70000,
                'maxFeePerGas': max_fee,
                'maxPriorityFeePerGas': max_priority,
                'nonce': nonce,
                'type': 2
            })
            return self.send_tx(tx)
        except Exception as e:
            print(f"{Colors.RED}[W{self.wallet_num}] APPROVE ERROR: {e}{Colors.RESET}")
            return False

    def shield_euroz(self, amount):
        print(f"{Colors.MAGENTA}[W{self.wallet_num}] SHIELDING {amount} EUROZ...{Colors.RESET}")
        if not self.approve_euroz(amount):
            return False
        time.sleep(5)
        try:
            contract = self.w3.eth.contract(address=Web3.to_checksum_address(CEUROZ_CONTRACT), abi=CEUROZ_ABI)
            amount_wei = int(amount * 1000000)
            max_fee, max_priority = self.get_gas_params()
            nonce = self.get_nonce()
            tx = contract.functions.wrap(self.address, amount_wei).build_transaction({
                'chainId': CHAIN_ID,
                'gas': 550000,
                'maxFeePerGas': max_fee,
                'maxPriorityFeePerGas': max_priority,
                'nonce': nonce,
                'type': 2
            })
            return self.send_tx(tx)
        except Exception as e:
            print(f"{Colors.RED}[W{self.wallet_num}] SHIELD ERROR: {e}{Colors.RESET}")
            return False

    def transfer_euroz(self, to_address, amount):
        print(f"{Colors.MAGENTA}[W{self.wallet_num}] TRANSFERRING {amount} EUROZ TO {to_address[:10]}...{Colors.RESET}")
        try:
            to_address = Web3.to_checksum_address(to_address)
            contract = self.w3.eth.contract(address=Web3.to_checksum_address(EUROZ_TOKEN), abi=EUROZ_ABI)
            amount_wei = int(amount * 1000000)
            max_fee, max_priority = self.get_gas_params()
            nonce = self.get_nonce()
            tx = contract.functions.transfer(to_address, amount_wei).build_transaction({
                'chainId': CHAIN_ID,
                'gas': 65000,
                'maxFeePerGas': max_fee,
                'maxPriorityFeePerGas': max_priority,
                'nonce': nonce,
                'type': 2
            })
            return self.send_tx(tx)
        except Exception as e:
            print(f"{Colors.RED}[W{self.wallet_num}] TRANSFER ERROR: {e}{Colors.RESET}")
            return False

    def transfer_euroz_random(self):
        # Random amount between 0.01 and 1
        amount = round(random.uniform(0.01, 1.0), 6)
        
        # 50% chance self, 50% chance dead address
        if random.random() < 0.5:
            to_address = self.address
            recipient_type = "SELF"
        else:
            to_address = DEAD_ADDRESS
            recipient_type = "DEAD"
        
        print(f"{Colors.BLUE}[W{self.wallet_num}] RANDOM: {amount} EUROZ -> {recipient_type}{Colors.RESET}")
        return self.transfer_euroz(to_address, amount)

def load_private_keys():
    if not os.path.exists("pv.txt"):
        print(f"{Colors.RED}ERROR: pv.txt NOT FOUND{Colors.RESET}")
        return []
    with open("pv.txt", "r") as f:
        keys = [line.strip() for line in f if line.strip()]
    return keys

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def wait_for_enter():
    input(f"{Colors.YELLOW}PRESS ENTER TO CONTINUE...{Colors.RESET}")
    clear_screen()

def print_banner():
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.MAGENTA}        ZAMA CONFIDENTIAL TOKEN BOT (MULTI-WALLET){Colors.RESET}")
    print(f"{Colors.YELLOW}            CREATED BY KAZUHA VIP ONLY{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")

def print_wallets_info(bots):
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.WHITE}LOADED {len(bots)} WALLETS:{Colors.RESET}")
    for i, bot in enumerate(bots, 1):
        print(f"{Colors.GREEN}[W{i}] {bot.address[:10]}...{bot.address[-8:]}{Colors.RESET}")
        print(f"     ETH: {bot.get_balance():.6f} | EUROZ: {bot.get_euroz_balance():.6f}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")

def print_menu():
    print(f"{Colors.WHITE}[1] MINT EUROZ (ALL WALLETS){Colors.RESET}")
    print(f"{Colors.WHITE}[2] SHIELD EUROZ TO cEUROZ (ALL WALLETS){Colors.RESET}")
    print(f"{Colors.WHITE}[3] TRANSFER EUROZ (CUSTOM ADDRESS){Colors.RESET}")
    print(f"{Colors.WHITE}[4] TRANSFER EUROZ (RANDOM AMOUNT + RANDOM RECIPIENT){Colors.RESET}")
    print(f"{Colors.WHITE}[5] AUTO MODE (CUSTOM){Colors.RESET}")
    print(f"{Colors.WHITE}[6] AUTO MODE (RANDOM){Colors.RESET}")
    print(f"{Colors.WHITE}[7] REFRESH BALANCES{Colors.RESET}")
    print(f"{Colors.WHITE}[0] EXIT{Colors.RESET}")

def execute_parallel(bots, func, *args):
    # Limit concurrent threads to avoid rate limits
    max_workers = min(10, len(bots))  # Max 10 concurrent
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(func, bot, *args): bot for bot in bots}
        results = []
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                bot = futures[future]
                print(f"{Colors.RED}[W{bot.wallet_num}] EXCEPTION: {e}{Colors.RESET}")
                results.append(False)
        return results

def mint_all(bot):
    return bot.mint_euroz()

def shield_all(bot, amount):
    return bot.shield_euroz(amount)

def transfer_all(bot, to_addr, amount):
    return bot.transfer_euroz(to_addr, amount)

def transfer_random_all(bot):
    return bot.transfer_euroz_random()

def auto_mode_custom(bot, to_addr, amount):
    print(f"{Colors.CYAN}[W{bot.wallet_num}] STARTING AUTO MODE (CUSTOM){Colors.RESET}")
    if not bot.mint_euroz():
        return False
    time.sleep(5)
    if not bot.shield_euroz(amount):
        return False
    time.sleep(5)
    if not bot.transfer_euroz(to_addr, amount):
        return False
    print(f"{Colors.GREEN}[W{bot.wallet_num}] AUTO MODE COMPLETE{Colors.RESET}")
    return True

def auto_mode_random(bot):
    print(f"{Colors.CYAN}[W{bot.wallet_num}] STARTING AUTO MODE (RANDOM){Colors.RESET}")
    if not bot.mint_euroz():
        return False
    time.sleep(5)
    
    # Random amount for shield
    amount = round(random.uniform(0.01, 1.0), 6)
    if not bot.shield_euroz(amount):
        return False
    time.sleep(5)
    
    # Random transfer
    if not bot.transfer_euroz_random():
        return False
    print(f"{Colors.GREEN}[W{bot.wallet_num}] AUTO MODE COMPLETE{Colors.RESET}")
    return True

def main():
    clear_screen()
    print_banner()
    
    keys = load_private_keys()
    if not keys:
        print(f"{Colors.RED}NO PRIVATE KEYS FOUND{Colors.RESET}")
        sys.exit(1)
    
    bots = []
    for i, key in enumerate(keys, 1):
        try:
            bot = EurozBot(key, i)
            bots.append(bot)
        except Exception as e:
            print(f"{Colors.RED}WALLET {i} INVALID: {e}{Colors.RESET}")
    
    if not bots:
        print(f"{Colors.RED}NO VALID WALLETS{Colors.RESET}")
        sys.exit(1)
    
    print_wallets_info(bots)
    
    while True:
        print_menu()
        choice = input(f"{Colors.YELLOW}SELECT OPTION: {Colors.RESET}").strip()
        
        if choice == "1":
            print(f"{Colors.CYAN}MINTING ON ALL WALLETS...{Colors.RESET}")
            execute_parallel(bots, mint_all)
            wait_for_enter()
            print_banner()
            print_wallets_info(bots)
            
        elif choice == "2":
            amount = input(f"{Colors.YELLOW}AMOUNT TO SHIELD: {Colors.RESET}").strip()
            try:
                amt = float(amount)
                print(f"{Colors.CYAN}SHIELDING ON ALL WALLETS...{Colors.RESET}")
                execute_parallel(bots, shield_all, amt)
            except:
                print(f"{Colors.RED}INVALID AMOUNT{Colors.RESET}")
            wait_for_enter()
            print_banner()
            print_wallets_info(bots)
            
        elif choice == "3":
            to_addr = input(f"{Colors.YELLOW}RECIPIENT ADDRESS: {Colors.RESET}").strip()
            amount = input(f"{Colors.YELLOW}AMOUNT: {Colors.RESET}").strip()
            try:
                amt = float(amount)
                print(f"{Colors.CYAN}TRANSFERRING FROM ALL WALLETS...{Colors.RESET}")
                execute_parallel(bots, transfer_all, to_addr, amt)
            except:
                print(f"{Colors.RED}INVALID INPUT{Colors.RESET}")
            wait_for_enter()
            print_banner()
            print_wallets_info(bots)
        
        elif choice == "4":
            print(f"{Colors.CYAN}RANDOM TRANSFERS FROM ALL WALLETS...{Colors.RESET}")
            print(f"{Colors.YELLOW}Amount: 0.01-1.0 EUROZ | Recipient: 50% SELF / 50% DEAD{Colors.RESET}")
            execute_parallel(bots, transfer_random_all)
            wait_for_enter()
            print_banner()
            print_wallets_info(bots)
            
        elif choice == "5":
            to_addr = input(f"{Colors.YELLOW}RECIPIENT ADDRESS: {Colors.RESET}").strip()
            amount = input(f"{Colors.YELLOW}AMOUNT: {Colors.RESET}").strip()
            try:
                amt = float(amount)
                print(f"{Colors.CYAN}AUTO MODE (CUSTOM) ON ALL WALLETS...{Colors.RESET}")
                execute_parallel(bots, auto_mode_custom, to_addr, amt)
                print(f"{Colors.GREEN}ALL WALLETS COMPLETED{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.RED}AUTO MODE ERROR: {e}{Colors.RESET}")
            wait_for_enter()
            print_banner()
            print_wallets_info(bots)
        
        elif choice == "6":
            print(f"{Colors.CYAN}AUTO MODE (RANDOM) ON ALL WALLETS...{Colors.RESET}")
            print(f"{Colors.YELLOW}Amount: 0.01-1.0 EUROZ | Recipient: 50% SELF / 50% DEAD{Colors.RESET}")
            execute_parallel(bots, auto_mode_random)
            print(f"{Colors.GREEN}ALL WALLETS COMPLETED{Colors.RESET}")
            wait_for_enter()
            print_banner()
            print_wallets_info(bots)
            
        elif choice == "7":
            print(f"{Colors.CYAN}REFRESHING BALANCES...{Colors.RESET}")
            clear_screen()
            print_banner()
            print_wallets_info(bots)
            
        elif choice == "0":
            print(f"{Colors.MAGENTA}GOODBYE{Colors.RESET}")
            break
            
        else:
            print(f"{Colors.RED}INVALID OPTION{Colors.RESET}")
            time.sleep(1)
            clear_screen()
            print_banner()
            print_wallets_info(bots)

if __name__ == "__main__":
    main()
