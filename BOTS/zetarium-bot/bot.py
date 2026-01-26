import os
import time
import random
from datetime import datetime
from dotenv import load_dotenv
import pytz
import requests
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
import warnings
import sys

warnings.filterwarnings('ignore')
if not sys.warnoptions:
    os.environ["PYTHONWARNINGS"] = "ignore"

load_dotenv()

# =============================================================================
# COLORS
# =============================================================================

class C:
    RED = '\033[1;91m'
    GREEN = '\033[1;92m'
    YELLOW = '\033[1;93m'
    BLUE = '\033[1;94m'
    MAGENTA = '\033[1;95m'
    CYAN = '\033[1;96m'
    WHITE = '\033[1;97m'
    RESET = '\033[0m'

# =============================================================================
# CONFIGURATION
# =============================================================================

RPC_URL = "https://data-seed-prebsc-1-s1.binance.org:8545"
TOKEN_ADDRESS = "0x2186fc0e8404eCF9F63cCBf1C75d5fAF6B843786"
MARKET_CONTRACT_ADDRESS = "0x852a5C778034e0776181955536528347Aa901d24"
FAUCET_CONTRACT_ADDRESS = "0xc9e16209Ed6B2A4f41b751788FE74F5c0B7F8E1c"

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_timestamp():
    wib = pytz.timezone('Asia/Jakarta')
    return datetime.now(wib).strftime("%H:%M:%S")

def log_success(msg):
    print(f"{C.GREEN}[{get_timestamp()}] [SUCCESS]{C.RESET} {msg}")

def log_error(msg):
    print(f"{C.RED}[{get_timestamp()}] [ERROR]{C.RESET} {msg}")

def log_info(msg):
    print(f"{C.CYAN}[{get_timestamp()}] [INFO]{C.RESET} {msg}")

def log_warn(msg):
    print(f"{C.YELLOW}[{get_timestamp()}] [WARN]{C.RESET} {msg}")

def show_banner():
    clear_screen()
    print()
    print(f"{C.CYAN}==========================================================={C.RESET}")
    print(f"{C.CYAN}{C.RESET}           {C.GREEN}ZETARIUM AUTO BOT{C.RESET}                          {C.CYAN}{C.RESET}")
    print(f"{C.CYAN}{C.RESET}           {C.YELLOW}Created by Kazuha VIP Only{C.RESET}                 {C.CYAN}{C.RESET}")
    print(f"{C.CYAN}==========================================================={C.RESET}")

def show_menu():
    print()
    print(f"{C.WHITE}  [1] Claim Daily Check In{C.RESET}")
    print(f"{C.WHITE}  [2] Claim Faucet{C.RESET}")
    print(f"{C.WHITE}  [3] Make Prediction{C.RESET}")
    print(f"{C.WHITE}  [4] Exit{C.RESET}")
    print()
    print(f"{C.CYAN}==========================================================={C.RESET}")

def show_tx_details(tx_hash, receipt, action):
    print()
    print(f"{C.CYAN}-----------------------------------------------------------{C.RESET}")
    print(f"{C.GREEN}[TX SUCCESS]{C.RESET} {action}")
    print(f"{C.CYAN}-----------------------------------------------------------{C.RESET}")
    print(f"{C.WHITE}  Transaction Hash  : {C.YELLOW}{tx_hash}{C.RESET}")
    print(f"{C.WHITE}  Block Number      : {C.YELLOW}{receipt['blockNumber']}{C.RESET}")
    print(f"{C.WHITE}  Gas Used          : {C.YELLOW}{receipt['gasUsed']}{C.RESET}")
    if receipt['status'] == 1:
        print(f"{C.WHITE}  Status            : {C.GREEN}Success{C.RESET}")
    else:
        print(f"{C.WHITE}  Status            : {C.RED}Failed{C.RESET}")
    print(f"{C.CYAN}-----------------------------------------------------------{C.RESET}")
    print(f"{C.WHITE}  Explorer          : {C.CYAN}https://testnet.bscscan.com/tx/{tx_hash}{C.RESET}")
    print(f"{C.CYAN}-----------------------------------------------------------{C.RESET}")
    print()

# =============================================================================
# ZETARIUM BOT CLASS
# =============================================================================

class ZetariumBot:
    def __init__(self):
        self.base_url = "https://airdrop-data.zetarium.world"
        self.api_url = "https://api.zetarium.world"
        self.prediction_url = "https://prediction-market-api.zetarium.world"
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        
        self.private_key = os.getenv('PRIVATE_KEY')
        self.bearer_token = os.getenv('BEARER_TOKEN')
        
        self.token_abi = [
            {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "payable": False, "stateMutability": "nonpayable", "type": "function"},
            {"constant": True, "inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
            {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"}
        ]
        
        self.market_abi = [
            {"constant": False, "inputs": [{"name": "marketId", "type": "uint256"}, {"name": "outcome", "type": "uint8"}, {"name": "amount", "type": "uint256"}], "name": "makePrediction", "outputs": [], "payable": False, "stateMutability": "nonpayable", "type": "function"}
        ]
        
        self.faucet_abi = [
            {"constant": False, "inputs": [], "name": "claim", "outputs": [], "payable": False, "stateMutability": "nonpayable", "type": "function"}
        ]

    def get_wallet(self):
        try:
            account = Account.from_key(self.private_key)
            return account.address
        except:
            return None

    def check_balance(self):
        try:
            wallet = self.get_wallet()
            token_contract = self.w3.eth.contract(address=Web3.to_checksum_address(TOKEN_ADDRESS), abi=self.token_abi)
            balance = token_contract.functions.balanceOf(wallet).call()
            return float(self.w3.from_wei(balance, 'ether'))
        except Exception as e:
            log_error(f"Balance check failed: {e}")
            return 0

    def sign_message(self, message):
        try:
            account = Account.from_key(self.private_key)
            message_hash = encode_defunct(text=message)
            signed = account.sign_message(message_hash)
            return "0x" + signed.signature.hex()
        except:
            return None

    def get_user_info(self):
        headers = {"authorization": f"Bearer {self.bearer_token}", "user-agent": "Mozilla/5.0"}
        try:
            res = requests.get(f"{self.base_url}/auth/me", headers=headers, timeout=30)
            return res.json() if res.status_code == 200 else None
        except:
            return None

    def show_account_info(self):
        print()
        print(f"{C.CYAN}-----------------------------------------------------------{C.RESET}")
        print(f"{C.WHITE}  ACCOUNT INFO{C.RESET}")
        print(f"{C.CYAN}-----------------------------------------------------------{C.RESET}")
        
        wallet = self.get_wallet()
        if wallet:
            print(f"{C.WHITE}  Wallet   : {C.GREEN}{wallet[:12]}...{wallet[-8:]}{C.RESET}")
            balance = self.check_balance()
            print(f"{C.WHITE}  Balance  : {C.YELLOW}{balance:.2f} USDC{C.RESET}")
        
        user = self.get_user_info()
        if user and 'user' in user:
            username = user['user'].get('username', 'N/A')
            points = user['user'].get('points', 0)
            print(f"{C.WHITE}  Username : {C.MAGENTA}{username}{C.RESET}")
            print(f"{C.WHITE}  Points   : {C.CYAN}{points}{C.RESET}")
        
        print(f"{C.CYAN}-----------------------------------------------------------{C.RESET}")

    def claim_daily_checkin(self):
        print()
        print(f"{C.CYAN}-----------------------------------------------------------{C.RESET}")
        print(f"{C.WHITE}  CLAIM DAILY CHECK IN{C.RESET}")
        print(f"{C.CYAN}-----------------------------------------------------------{C.RESET}")
        
        log_info("Processing Daily Check-In...")
        
        wallet = self.get_wallet()
        if not wallet:
            log_error("Invalid private key")
            return False
        
        headers = {"authorization": f"Bearer {self.bearer_token}", "content-type": "application/json", "user-agent": "Mozilla/5.0"}
        
        try:
            msg = f"GM! Claim daily points - {wallet.lower()}"
            sig = self.sign_message(msg)
            if not sig:
                log_error("Signature failed")
                return False
            
            res = requests.post(f"{self.api_url}/api/profile/{wallet}/gm", json={"message": msg, "signature": sig}, headers=headers, timeout=30)
            
            if res.status_code == 200:
                log_success("Daily Check-In Claimed Successfully!")
                return True
            elif res.status_code == 400:
                log_warn("Daily Check-In Already Claimed Today")
                return True
            else:
                log_error(f"Check-In Failed: {res.text}")
                return False
        except Exception as e:
            log_error(f"Check-In Error: {e}")
            return False

    def claim_faucet(self):
        print()
        print(f"{C.CYAN}-----------------------------------------------------------{C.RESET}")
        print(f"{C.WHITE}  CLAIM FAUCET{C.RESET}")
        print(f"{C.CYAN}-----------------------------------------------------------{C.RESET}")
        
        log_info("Processing Faucet Claim...")
        
        try:
            wallet = self.get_wallet()
            log_info(f"Wallet: {wallet[:12]}...{wallet[-8:]}")
            
            contract = self.w3.eth.contract(address=Web3.to_checksum_address(FAUCET_CONTRACT_ADDRESS), abi=self.faucet_abi)
            contract_func = contract.functions.claim()
            
            try:
                gas_estimate = contract_func.estimate_gas({'from': wallet})
                gas_limit = int(gas_estimate * 1.2)
            except:
                log_warn("Faucet Already Claimed")
                return False
            
            tx = contract_func.build_transaction({
                'from': wallet,
                'nonce': self.w3.eth.get_transaction_count(wallet),
                'gas': gas_limit,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            log_info("Waiting for confirmation...")
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            
            if receipt['status'] == 1:
                show_tx_details(tx_hash_hex, receipt, "Faucet Claimed")
                new_balance = self.check_balance()
                log_info(f"New Balance: {new_balance:.2f} USDC")
                return True
            else:
                log_error("Faucet Transaction Failed")
                return False
        except Exception as e:
            log_error(f"Faucet Error: {e}")
            return False

    def check_and_approve(self, amount_wei):
        try:
            wallet = self.get_wallet()
            token_contract = self.w3.eth.contract(address=Web3.to_checksum_address(TOKEN_ADDRESS), abi=self.token_abi)
            spender = Web3.to_checksum_address(MARKET_CONTRACT_ADDRESS)
            
            allowance = token_contract.functions.allowance(wallet, spender).call()
            
            if allowance < amount_wei:
                log_info("Approving USDC...")
                max_amount = 115792089237316195423570985008687907853269984665640564039457584007913129639935
                tx = token_contract.functions.approve(spender, max_amount).build_transaction({
                    'from': wallet,
                    'nonce': self.w3.eth.get_transaction_count(wallet),
                    'gas': 100000,
                    'gasPrice': self.w3.eth.gas_price
                })
                signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt['status'] == 1:
                    log_success(f"USDC Approved!")
                time.sleep(3)
            return True
        except Exception as e:
            log_error(f"Approve Failed: {e}")
            return False

    def get_markets(self):
        headers = {"accept": "*/*", "user-agent": "Mozilla/5.0", "origin": "https://prediction.zetarium.world"}
        try:
            res = requests.get(f"{self.prediction_url}/markets?limit=200", headers=headers, timeout=30)
            return res.json() if res.status_code == 200 else None
        except:
            return None

    def make_prediction(self):
        print()
        print(f"{C.CYAN}-----------------------------------------------------------{C.RESET}")
        print(f"{C.WHITE}  MAKE PREDICTION{C.RESET}")
        print(f"{C.CYAN}-----------------------------------------------------------{C.RESET}")
        
        log_info("Processing Prediction...")
        
        wallet = self.get_wallet()
        if not wallet:
            log_error("Invalid private key")
            return False
        
        log_info(f"Wallet: {wallet[:12]}...{wallet[-8:]}")
        
        balance = self.check_balance()
        log_info(f"Current Balance: {balance:.2f} USDC")
        
        if balance < 10:
            log_error("Insufficient balance for prediction")
            return False
        
        log_info("Fetching active markets...")
        markets = self.get_markets()
        if not markets or "markets" not in markets:
            log_error("Failed to fetch markets")
            return False
        
        active_markets = [m for m in markets['markets'] if m.get('status') == 0]
        
        if not active_markets:
            log_warn("No active markets found")
            return False
        
        log_success(f"Found {len(active_markets)} active markets")
        
        print()
        while True:
            try:
                num_predictions = int(input(f"{C.GREEN}[?]{C.RESET} How many predictions to make: {C.WHITE}"))
                if num_predictions <= 0:
                    log_error("Enter positive number!")
                    continue
                if num_predictions > len(active_markets):
                    log_warn(f"Only {len(active_markets)} markets available")
                    num_predictions = len(active_markets)
                break
            except ValueError:
                log_error("Invalid number!")
        
        print()
        log_info(f"Starting {num_predictions} predictions...")
        
        random.shuffle(active_markets)
        
        successful = 0
        failed = 0
        
        for i in range(num_predictions):
            print()
            print(f"{C.YELLOW}=============== Prediction [{i+1}/{num_predictions}] ==============={C.RESET}")
            
            balance = self.check_balance()
            if balance < 10:
                log_error("Insufficient balance, stopping...")
                break
            
            target = active_markets[i]
            
            m_id = target['id']
            question = target['question']
            yes_pool = int(target.get('yesPool', 0))
            no_pool = int(target.get('noPool', 0))
            
            if yes_pool > no_pool:
                outcome = 1
                pick = "YES"
            elif no_pool > yes_pool:
                outcome = 2
                pick = "NO"
            else:
                outcome = random.choice([1, 2])
                pick = "YES" if outcome == 1 else "NO"
            
            bet_amount = random.randint(5, min(10, int(balance * 0.9)))
            amount_wei = self.w3.to_wei(bet_amount, 'ether')
            
            print()
            print(f"{C.CYAN}-----------------------------------------------------------{C.RESET}")
            print(f"{C.WHITE}  MARKET DETAILS{C.RESET}")
            print(f"{C.CYAN}-----------------------------------------------------------{C.RESET}")
            print(f"{C.WHITE}  Market   : {C.MAGENTA}{question[:45]}...{C.RESET}")
            print(f"{C.WHITE}  Pick     : {C.GREEN}{pick}{C.RESET}")
            print(f"{C.WHITE}  Amount   : {C.YELLOW}{bet_amount} USDC{C.RESET}")
            print(f"{C.CYAN}-----------------------------------------------------------{C.RESET}")
            
            if not self.check_and_approve(amount_wei):
                failed += 1
                continue
            
            try:
                market_contract = self.w3.eth.contract(address=Web3.to_checksum_address(MARKET_CONTRACT_ADDRESS), abi=self.market_abi)
                contract_func = market_contract.functions.makePrediction(int(m_id), int(outcome), amount_wei)
                
                try:
                    gas_estimate = contract_func.estimate_gas({'from': wallet})
                    gas_limit = int(gas_estimate * 1.2)
                except:
                    log_warn("Market rejected, skipping...")
                    failed += 1
                    time.sleep(2)
                    continue
                
                nonce = self.w3.eth.get_transaction_count(wallet, 'pending')
                tx = contract_func.build_transaction({
                    'from': wallet,
                    'nonce': nonce,
                    'gas': gas_limit,
                    'gasPrice': self.w3.eth.gas_price
                })
                
                signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                tx_hash_hex = tx_hash.hex()
                
                log_info("Waiting for confirmation...")
                
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                
                if receipt['status'] == 1:
                    print()
                    print(f"{C.CYAN}-----------------------------------------------------------{C.RESET}")
                    print(f"{C.GREEN}  [TX SUCCESS]{C.RESET} {C.WHITE}Prediction {i+1} Placed{C.RESET}")
                    print(f"{C.CYAN}-----------------------------------------------------------{C.RESET}")
                    print(f"{C.WHITE}  Hash     : {C.YELLOW}{tx_hash_hex}{C.RESET}")
                    print(f"{C.WHITE}  Block    : {C.YELLOW}{receipt['blockNumber']}{C.RESET}")
                    print(f"{C.WHITE}  Gas Used : {C.YELLOW}{receipt['gasUsed']}{C.RESET}")
                    print(f"{C.WHITE}  Status   : {C.GREEN}Success{C.RESET}")
                    print(f"{C.CYAN}-----------------------------------------------------------{C.RESET}")
                    print(f"{C.WHITE}  Explorer : {C.CYAN}https://testnet.bscscan.com/tx/{tx_hash_hex}{C.RESET}")
                    print(f"{C.CYAN}-----------------------------------------------------------{C.RESET}")
                    successful += 1
                else:
                    log_error(f"Prediction {i+1} Failed on chain!")
                    failed += 1
                    
            except Exception as e:
                log_error(f"Error: {e}")
                failed += 1
            
            if i < num_predictions - 1:
                time.sleep(random.randint(3, 6))
        
        print()
        print(f"{C.CYAN}==========================================================={C.RESET}")
        print(f"{C.WHITE}  PREDICTION SUMMARY{C.RESET}")
        print(f"{C.CYAN}==========================================================={C.RESET}")
        print(f"{C.WHITE}  Total       : {C.YELLOW}{num_predictions}{C.RESET}")
        print(f"{C.WHITE}  Successful  : {C.GREEN}{successful}{C.RESET}")
        print(f"{C.WHITE}  Failed      : {C.RED}{failed}{C.RESET}")
        new_balance = self.check_balance()
        print(f"{C.WHITE}  Balance     : {C.YELLOW}{new_balance:.2f} USDC{C.RESET}")
        print(f"{C.CYAN}==========================================================={C.RESET}")
        
        return True
# =============================================================================
# MAIN
# =============================================================================

def main():
    bot = ZetariumBot()
    
    if not bot.private_key or not bot.bearer_token:
        clear_screen()
        print()
        print(f"{C.RED}ERROR: Missing PRIVATE_KEY or BEARER_TOKEN in .env file{C.RESET}")
        print()
        return
    
    while True:
        show_banner()
        bot.show_account_info()
        show_menu()
        
        choice = input(f"{C.GREEN}[?]{C.RESET} Select option: {C.WHITE}").strip()
        
        if choice == '1':
            bot.claim_daily_checkin()
            input(f"\n{C.CYAN}[*]{C.RESET} Press Enter to continue...")
        elif choice == '2':
            bot.claim_faucet()
            input(f"\n{C.CYAN}[*]{C.RESET} Press Enter to continue...")
        elif choice == '3':
            bot.make_prediction()
            input(f"\n{C.CYAN}[*]{C.RESET} Press Enter to continue...")
        elif choice == '4':
            print()
            log_info("Exiting... Goodbye!")
            print()
            break
        else:
            log_error("Invalid option! Select 1-4")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{C.RED}[!]{C.RESET} Cancelled by user!")
    except Exception as e:
        print(f"\n{C.RED}[!]{C.RESET} Error: {e}")