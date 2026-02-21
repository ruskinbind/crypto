#!/usr/bin/env python3
import os
import sys
import time
from web3 import Web3
from eth_account import Account

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
RPC_URL = "https://timothy.megaeth.com/rpc"
CHAIN_ID = 6343

# TOKEN CONTRACTS
USDC_CONTRACT = "0xd4db9b3dc633f7b1403f4ba2281aa1aca43296d8"
USDT_CONTRACT = "0x17b9dcd0c3aa34a8ef821af3a639a6c6ae174f15"
WBTC_CONTRACT = "0x7e4bdcf9a36cf3083de7acfbb5f2a540c543406a"

# LEND CONTRACTS
USDC_LEND_CONTRACT = "0xa6d9684ef3f231d08ffed5a47241928964a9f361"
USDT_LEND_CONTRACT = "0x8c8db01c13281cfdee8f4e521f0cbb5940c5051f"

# BORROW CONTRACT
BORROW_CONTRACT = "0x041b19fb41e96f7890a4b60c9196a453c734ad24"

# BTC PRICE
BTC_PRICE_USD = 100000

# ERC20 ABI
ERC20_ABI = [
    {"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"stateMutability":"view","type":"function"}
]

# LEND ABI
LEND_ABI = [
    {"inputs":[{"name":"assets","type":"uint256"},{"name":"receiver","type":"address"}],"name":"deposit","outputs":[{"name":"shares","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"assets","type":"uint256"},{"name":"receiver","type":"address"},{"name":"owner","type":"address"}],"name":"withdraw","outputs":[{"name":"shares","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"owner","type":"address"}],"name":"maxWithdraw","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    clear_screen()
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{MAGENTA}              AVON LEND AND BORROW BOT{RESET}")
    print(f"{BOLD}{YELLOW}              CREATED BY KAZUHA{RESET}")
    print(f"{BOLD}{RED}              VIP ONLY{RESET}")
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"{YELLOW}  Network: MegaETH Timothy | Chain ID: 6343{RESET}")
    print(f"{CYAN}{'='*60}{RESET}")
    print()

def print_menu():
    print(f"{GREEN}{'-'*60}{RESET}")
    print(f"{BOLD}{WHITE}  [1] USDC LEND DEPOSIT{RESET}")
    print(f"{BOLD}{WHITE}  [2] USDC LEND WITHDRAW{RESET}")
    print(f"{BOLD}{WHITE}  [3] USDT LEND DEPOSIT{RESET}")
    print(f"{BOLD}{WHITE}  [4] USDT LEND WITHDRAW{RESET}")
    print(f"{BOLD}{WHITE}  [5] BORROW USDC (BTC Collateral){RESET}")
    print(f"{BOLD}{WHITE}  [6] PORTFOLIO DEPOSIT USDT{RESET}")
    print(f"{BOLD}{WHITE}  [7] PORTFOLIO WITHDRAW USDT{RESET}")
    print(f"{BOLD}{WHITE}  [8] AUTO ALL (10% of balance){RESET}")
    print(f"{BOLD}{WHITE}  [9] EXIT{RESET}")
    print(f"{GREEN}{'-'*60}{RESET}")
    print()

def load_private_key():
    try:
        with open("pv.txt", "r") as f:
            pk = f.read().strip()
            if not pk.startswith("0x"):
                pk = "0x" + pk
            return pk
    except FileNotFoundError:
        print(f"{RED}[ERROR] pv.txt file not found!{RESET}")
        print(f"{YELLOW}Create pv.txt and add your private key{RESET}")
        sys.exit(1)

def get_web3():
    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 60}))
    return w3

def wait_for_receipt(w3, tx_hash, timeout=180):
    print(f"{YELLOW}[INFO] Waiting for confirmation...{RESET}")
    start = time.time()
    while time.time() - start < timeout:
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            if receipt is not None:
                return receipt
        except Exception:
            pass
        time.sleep(3)
    return None
# ... [previous code remains unchanged until the functions] ...

def approve_token(w3, account, token_contract, spender, amount, token_name):
    print(f"{YELLOW}[INFO] Approving {token_name}...{RESET}")
    try:
        token = w3.eth.contract(address=Web3.to_checksum_address(token_contract), abi=ERC20_ABI)
        nonce = w3.eth.get_transaction_count(account.address, 'pending')
        tx = token.functions.approve(
            Web3.to_checksum_address(spender),
            amount
        ).build_transaction({
            'chainId': CHAIN_ID,
            'gas': 1000000000,
            'gasPrice': 3500000,
            'nonce': nonce
        })
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)  # ✅ Fixed: raw_transaction
        tx_hash_hex = "0x" + tx_hash.hex() if not tx_hash.hex().startswith("0x") else tx_hash.hex()
        print(f"{CYAN}[INFO] Approve TX: {tx_hash_hex}{RESET}")
        receipt = wait_for_receipt(w3, tx_hash, timeout=180)
        if receipt is not None:
            block_num = receipt.blockNumber
            if receipt.status == 1:
                print(f"{GREEN}[SUCCESS] Approve successful!{RESET}")
                print(f"{WHITE}[INFO] Block: {CYAN}{block_num}{RESET}")
                return tx_hash_hex
            else:
                print(f"{RED}[FAILED] Approve reverted!{RESET}")
                return None
        else:
            return tx_hash_hex
    except Exception as e:
        print(f"{RED}[ERROR] Approve error: {e}{RESET}")
        return None

def deposit_lend(w3, account, lend_contract, amount, token_name):
    print(f"{YELLOW}[INFO] Depositing {token_name}...{RESET}")
    try:
        lend = w3.eth.contract(address=Web3.to_checksum_address(lend_contract), abi=LEND_ABI)
        nonce = w3.eth.get_transaction_count(account.address, 'pending')
        tx = lend.functions.deposit(
            amount,
            Web3.to_checksum_address(account.address)
        ).build_transaction({
            'chainId': CHAIN_ID,
            'gas': 1000000000,
            'gasPrice': 3500000,
            'nonce': nonce
        })
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)  # ✅ Fixed: raw_transaction
        tx_hash_hex = "0x" + tx_hash.hex() if not tx_hash.hex().startswith("0x") else tx_hash.hex()
        print(f"{CYAN}[INFO] Deposit TX: {tx_hash_hex}{RESET}")
        receipt = wait_for_receipt(w3, tx_hash, timeout=180)
        if receipt is not None:
            block_num = receipt.blockNumber
            if receipt.status == 1:
                print(f"{GREEN}[SUCCESS] Deposit successful!{RESET}")
                print(f"{WHITE}[INFO] Block: {CYAN}{block_num}{RESET}")
                return tx_hash_hex, block_num
            else:
                print(f"{RED}[FAILED] Deposit reverted!{RESET}")
                return None, None
        else:
            return tx_hash_hex, 0
    except Exception as e:
        print(f"{RED}[ERROR] Deposit error: {e}{RESET}")
        return None, None

def withdraw_lend(w3, account, lend_contract, amount, token_name):
    print(f"{YELLOW}[INFO] Withdrawing {token_name}...{RESET}")
    try:
        lend = w3.eth.contract(address=Web3.to_checksum_address(lend_contract), abi=LEND_ABI)
        nonce = w3.eth.get_transaction_count(account.address, 'pending')
        tx = lend.functions.withdraw(
            amount,
            Web3.to_checksum_address(account.address),
            Web3.to_checksum_address(account.address)
        ).build_transaction({
            'chainId': CHAIN_ID,
            'gas': 1000000000,
            'gasPrice': 3500000,
            'nonce': nonce
        })
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)  # ✅ Fixed: raw_transaction
        tx_hash_hex = "0x" + tx_hash.hex() if not tx_hash.hex().startswith("0x") else tx_hash.hex()
        print(f"{CYAN}[INFO] Withdraw TX: {tx_hash_hex}{RESET}")
        receipt = wait_for_receipt(w3, tx_hash, timeout=180)
        if receipt is not None:
            block_num = receipt.blockNumber
            if receipt.status == 1:
                print(f"{GREEN}[SUCCESS] Withdraw successful!{RESET}")
                print(f"{WHITE}[INFO] Block: {CYAN}{block_num}{RESET}")
                return tx_hash_hex, block_num
            else:
                print(f"{RED}[FAILED] Withdraw reverted!{RESET}")
                return None, None
        else:
            return tx_hash_hex, 0
    except Exception as e:
        print(f"{RED}[ERROR] Withdraw error: {e}{RESET}")
        return None, None

def do_borrow(w3, account, borrow_amount, collateral_amount):
    print(f"{YELLOW}[INFO] Borrowing USDC...{RESET}")
    try:
        nonce = w3.eth.get_transaction_count(account.address, 'pending')
        borrow_rate = 50000000000000000
        lend_rate = 930000000000000000
        timestamp = int(time.time() * 1000000000)
        function_selector = "0xb25b8e5c"
        data = function_selector
        data += format(borrow_amount, '064x')
        data += format(collateral_amount, '064x')
        data += format(borrow_rate, '064x')
        data += format(lend_rate, '064x')
        data += format(timestamp, '064x')
        tx = {
            'chainId': CHAIN_ID,
            'to': Web3.to_checksum_address(BORROW_CONTRACT),
            'gas': 1000000000,
            'gasPrice': 3500000,
            'nonce': nonce,
            'data': data,
            'value': 0
        }
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)  # ✅ Fixed: raw_transaction
        tx_hash_hex = "0x" + tx_hash.hex() if not tx_hash.hex().startswith("0x") else tx_hash.hex()
        print(f"{CYAN}[INFO] Borrow TX: {tx_hash_hex}{RESET}")
        receipt = wait_for_receipt(w3, tx_hash, timeout=180)
        if receipt is not None:
            block_num = receipt.blockNumber
            if receipt.status == 1:
                print(f"{GREEN}[SUCCESS] Borrow successful!{RESET}")
                print(f"{WHITE}[INFO] Block: {CYAN}{block_num}{RESET}")
                return tx_hash_hex, block_num
            else:
                print(f"{RED}[FAILED] Borrow reverted!{RESET}")
                return None, None
        else:
            return tx_hash_hex, 0
    except Exception as e:
        print(f"{RED}[ERROR] Borrow error: {e}{RESET}")
        return None, None

# ... [rest of the code remains unchanged] ...


            

def do_deposit(token_name, token_contract, lend_contract):
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{MAGENTA}              {token_name} LEND DEPOSIT{RESET}")
    print(f"{CYAN}{'='*60}{RESET}")
    print()
    private_key = load_private_key()
    account = Account.from_key(private_key)
    print(f"{WHITE}[INFO] Wallet: {CYAN}{account.address}{RESET}")
    w3 = get_web3()
    if not w3.is_connected():
        print(f"{RED}[ERROR] Cannot connect to RPC!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    print(f"{GREEN}[INFO] Connected to MegaETH{RESET}")
    token = w3.eth.contract(address=Web3.to_checksum_address(token_contract), abi=ERC20_ABI)
    token_balance = token.functions.balanceOf(account.address).call()
    print(f"{WHITE}[INFO] {token_name} Balance: {GREEN}{token_balance / 10**6:.6f} {token_name}{RESET}")
    print()
    if token_balance == 0:
        print(f"{RED}[ERROR] No {token_name} balance!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    print(f"{YELLOW}Enter amount to deposit ({token_name}):{RESET}")
    try:
        amount_input = input(f"{WHITE}> {RESET}").strip()
        amount = float(amount_input)
        amount_wei = int(amount * 10**6)
    except ValueError:
        print(f"{RED}[ERROR] Invalid amount!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    if amount_wei > token_balance:
        print(f"{RED}[ERROR] Insufficient balance!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    allowance = token.functions.allowance(account.address, Web3.to_checksum_address(lend_contract)).call()
    if allowance < amount_wei:
        approve_token(w3, account, token_contract, lend_contract, amount_wei, token_name)
        time.sleep(5)
    tx_hash, block_num = deposit_lend(w3, account, lend_contract, amount_wei, token_name)
    if tx_hash:
        print(f"{GREEN}{'='*60}{RESET}")
        print(f"{BOLD}{GREEN}      DEPOSIT COMPLETED{RESET}")
        print(f"{GREEN}{'='*60}{RESET}")
    input(f"{YELLOW}Press Enter to continue...{RESET}")

def do_withdraw(token_name, token_contract, lend_contract):
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{MAGENTA}              {token_name} LEND WITHDRAW{RESET}")
    print(f"{CYAN}{'='*60}{RESET}")
    print()
    private_key = load_private_key()
    account = Account.from_key(private_key)
    print(f"{WHITE}[INFO] Wallet: {CYAN}{account.address}{RESET}")
    w3 = get_web3()
    if not w3.is_connected():
        print(f"{RED}[ERROR] Cannot connect to RPC!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    print(f"{GREEN}[INFO] Connected to MegaETH{RESET}")
    lend = w3.eth.contract(address=Web3.to_checksum_address(lend_contract), abi=LEND_ABI)
    lend_balance = lend.functions.balanceOf(account.address).call()
    try:
        max_withdraw = lend.functions.maxWithdraw(account.address).call()
    except:
        max_withdraw = lend_balance
    print(f"{WHITE}[INFO] Lend Shares: {GREEN}{lend_balance / 10**6:.6f}{RESET}")
    print(f"{WHITE}[INFO] Max Withdraw: {GREEN}{max_withdraw / 10**6:.6f} {token_name}{RESET}")
    print()
    if lend_balance == 0:
        print(f"{RED}[ERROR] No balance to withdraw!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    print(f"{YELLOW}Enter amount to withdraw ({token_name}):{RESET}")
    try:
        amount_input = input(f"{WHITE}> {RESET}").strip()
        amount = float(amount_input)
        amount_wei = int(amount * 10**6)
    except ValueError:
        print(f"{RED}[ERROR] Invalid amount!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    if amount_wei > max_withdraw:
        print(f"{RED}[ERROR] Amount exceeds max!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    tx_hash, block_num = withdraw_lend(w3, account, lend_contract, amount_wei, token_name)
    if tx_hash:
        print(f"{GREEN}{'='*60}{RESET}")
        print(f"{BOLD}{GREEN}      WITHDRAW COMPLETED{RESET}")
        print(f"{GREEN}{'='*60}{RESET}")
    input(f"{YELLOW}Press Enter to continue...{RESET}")

def borrow_usdc():
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{MAGENTA}              BORROW USDC (BTC Collateral){RESET}")
    print(f"{CYAN}{'='*60}{RESET}")
    print()
    private_key = load_private_key()
    account = Account.from_key(private_key)
    print(f"{WHITE}[INFO] Wallet: {CYAN}{account.address}{RESET}")
    w3 = get_web3()
    if not w3.is_connected():
        print(f"{RED}[ERROR] Cannot connect to RPC!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    print(f"{GREEN}[INFO] Connected to MegaETH{RESET}")
    wbtc = w3.eth.contract(address=Web3.to_checksum_address(WBTC_CONTRACT), abi=ERC20_ABI)
    wbtc_balance = wbtc.functions.balanceOf(account.address).call()
    print(f"{WHITE}[INFO] BTC Balance: {GREEN}{wbtc_balance / 10**8:.8f} BTC{RESET}")
    print()
    if wbtc_balance == 0:
        print(f"{RED}[ERROR] No BTC for collateral!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    print(f"{YELLOW}Enter BTC collateral amount:{RESET}")
    try:
        collateral_input = input(f"{WHITE}> {RESET}").strip()
        collateral_amount = float(collateral_input)
        collateral_wei = int(collateral_amount * 10**8)
    except ValueError:
        print(f"{RED}[ERROR] Invalid amount!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    if collateral_wei > wbtc_balance:
        print(f"{RED}[ERROR] Insufficient BTC!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    btc_value_usd = collateral_amount * BTC_PRICE_USD
    borrow_amount = btc_value_usd * 0.70
    borrow_wei = int(borrow_amount * 10**6)
    print(f"{WHITE}[INFO] You will receive: {GREEN}{borrow_amount:.6f} USDC{RESET}")
    confirm = input(f"{YELLOW}Confirm? (y/n): {RESET}").strip().lower()
    if confirm != 'y':
        return
    allowance = wbtc.functions.allowance(account.address, Web3.to_checksum_address(BORROW_CONTRACT)).call()
    if allowance < collateral_wei:
        approve_token(w3, account, WBTC_CONTRACT, BORROW_CONTRACT, collateral_wei, "BTC")
        time.sleep(5)
    tx_hash, block_num = do_borrow(w3, account, borrow_wei, collateral_wei)
    if tx_hash:
        print(f"{GREEN}{'='*60}{RESET}")
        print(f"{BOLD}{GREEN}      BORROW COMPLETED{RESET}")
        print(f"{GREEN}{'='*60}{RESET}")
    input(f"{YELLOW}Press Enter to continue...{RESET}")

def portfolio_deposit_usdt():
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{MAGENTA}              PORTFOLIO DEPOSIT USDT{RESET}")
    print(f"{CYAN}{'='*60}{RESET}")
    print()
    private_key = load_private_key()
    account = Account.from_key(private_key)
    print(f"{WHITE}[INFO] Wallet: {CYAN}{account.address}{RESET}")
    w3 = get_web3()
    if not w3.is_connected():
        print(f"{RED}[ERROR] Cannot connect to RPC!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    print(f"{GREEN}[INFO] Connected to MegaETH{RESET}")
    usdt = w3.eth.contract(address=Web3.to_checksum_address(USDT_CONTRACT), abi=ERC20_ABI)
    usdt_balance = usdt.functions.balanceOf(account.address).call()
    print(f"{WHITE}[INFO] USDT Balance: {GREEN}{usdt_balance / 10**6:.6f} USDT{RESET}")
    print()
    if usdt_balance == 0:
        print(f"{RED}[ERROR] No USDT balance!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    print(f"{YELLOW}Enter amount to deposit (USDT):{RESET}")
    try:
        amount_input = input(f"{WHITE}> {RESET}").strip()
        amount = float(amount_input)
        amount_wei = int(amount * 10**6)
    except ValueError:
        print(f"{RED}[ERROR] Invalid amount!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    if amount_wei > usdt_balance:
        print(f"{RED}[ERROR] Insufficient balance!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    allowance = usdt.functions.allowance(account.address, Web3.to_checksum_address(USDT_LEND_CONTRACT)).call()
    if allowance < amount_wei:
        approve_token(w3, account, USDT_CONTRACT, USDT_LEND_CONTRACT, amount_wei, "USDT")
        time.sleep(5)
    tx_hash, block_num = deposit_lend(w3, account, USDT_LEND_CONTRACT, amount_wei, "USDT")
    if tx_hash:
        print(f"{GREEN}{'='*60}{RESET}")
        print(f"{BOLD}{GREEN}      PORTFOLIO DEPOSIT COMPLETED{RESET}")
        print(f"{GREEN}{'='*60}{RESET}")
    input(f"{YELLOW}Press Enter to continue...{RESET}")

def portfolio_withdraw_usdt():
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{MAGENTA}              PORTFOLIO WITHDRAW USDT{RESET}")
    print(f"{CYAN}{'='*60}{RESET}")
    print()
    private_key = load_private_key()
    account = Account.from_key(private_key)
    print(f"{WHITE}[INFO] Wallet: {CYAN}{account.address}{RESET}")
    w3 = get_web3()
    if not w3.is_connected():
        print(f"{RED}[ERROR] Cannot connect to RPC!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    print(f"{GREEN}[INFO] Connected to MegaETH{RESET}")
    lend = w3.eth.contract(address=Web3.to_checksum_address(USDT_LEND_CONTRACT), abi=LEND_ABI)
    lend_balance = lend.functions.balanceOf(account.address).call()
    try:
        max_withdraw = lend.functions.maxWithdraw(account.address).call()
    except:
        max_withdraw = lend_balance
    print(f"{WHITE}[INFO] Portfolio Shares: {GREEN}{lend_balance / 10**6:.6f}{RESET}")
    print(f"{WHITE}[INFO] Max Withdraw: {GREEN}{max_withdraw / 10**6:.6f} USDT{RESET}")
    print()
    if lend_balance == 0:
        print(f"{RED}[ERROR] No balance to withdraw!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    print(f"{YELLOW}Enter amount to withdraw (USDT):{RESET}")
    try:
        amount_input = input(f"{WHITE}> {RESET}").strip()
        amount = float(amount_input)
        amount_wei = int(amount * 10**6)
    except ValueError:
        print(f"{RED}[ERROR] Invalid amount!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    if amount_wei > max_withdraw:
        print(f"{RED}[ERROR] Amount exceeds max!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    tx_hash, block_num = withdraw_lend(w3, account, USDT_LEND_CONTRACT, amount_wei, "USDT")
    if tx_hash:
        print(f"{GREEN}{'='*60}{RESET}")
        print(f"{BOLD}{GREEN}      PORTFOLIO WITHDRAW COMPLETED{RESET}")
        print(f"{GREEN}{'='*60}{RESET}")
    input(f"{YELLOW}Press Enter to continue...{RESET}")

def auto_all():
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{MAGENTA}              AUTO ALL (10% of balance){RESET}")
    print(f"{CYAN}{'='*60}{RESET}")
    print()
    private_key = load_private_key()
    account = Account.from_key(private_key)
    print(f"{WHITE}[INFO] Wallet: {CYAN}{account.address}{RESET}")
    w3 = get_web3()
    if not w3.is_connected():
        print(f"{RED}[ERROR] Cannot connect to RPC!{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    print(f"{GREEN}[INFO] Connected to MegaETH{RESET}")
    print()
    
    # Get all balances
    usdc = w3.eth.contract(address=Web3.to_checksum_address(USDC_CONTRACT), abi=ERC20_ABI)
    usdt = w3.eth.contract(address=Web3.to_checksum_address(USDT_CONTRACT), abi=ERC20_ABI)
    wbtc = w3.eth.contract(address=Web3.to_checksum_address(WBTC_CONTRACT), abi=ERC20_ABI)
    usdc_lend = w3.eth.contract(address=Web3.to_checksum_address(USDC_LEND_CONTRACT), abi=LEND_ABI)
    usdt_lend = w3.eth.contract(address=Web3.to_checksum_address(USDT_LEND_CONTRACT), abi=LEND_ABI)
    
    usdc_balance = usdc.functions.balanceOf(account.address).call()
    usdt_balance = usdt.functions.balanceOf(account.address).call()
    wbtc_balance = wbtc.functions.balanceOf(account.address).call()
    usdc_lend_balance = usdc_lend.functions.balanceOf(account.address).call()
    usdt_lend_balance = usdt_lend.functions.balanceOf(account.address).call()
    
    try:
        usdc_max_withdraw = usdc_lend.functions.maxWithdraw(account.address).call()
    except:
        usdc_max_withdraw = usdc_lend_balance
    try:
        usdt_max_withdraw = usdt_lend.functions.maxWithdraw(account.address).call()
    except:
        usdt_max_withdraw = usdt_lend_balance
    
    print(f"{WHITE}[INFO] USDC Balance: {GREEN}{usdc_balance / 10**6:.6f} USDC{RESET}")
    print(f"{WHITE}[INFO] USDT Balance: {GREEN}{usdt_balance / 10**6:.6f} USDT{RESET}")
    print(f"{WHITE}[INFO] BTC Balance: {GREEN}{wbtc_balance / 10**8:.8f} BTC{RESET}")
    print(f"{WHITE}[INFO] USDC Lend: {GREEN}{usdc_lend_balance / 10**6:.6f}{RESET}")
    print(f"{WHITE}[INFO] USDT Lend: {GREEN}{usdt_lend_balance / 10**6:.6f}{RESET}")
    print()
    
    # Calculate 10% amounts
    usdc_10 = int(usdc_balance * 0.10)
    usdt_10 = int(usdt_balance * 0.10)
    wbtc_10 = int(wbtc_balance * 0.10)
    usdc_withdraw_10 = int(usdc_max_withdraw * 0.10)
    usdt_withdraw_10 = int(usdt_max_withdraw * 0.10)
    
    print(f"{YELLOW}[INFO] AUTO ALL TASKS:{RESET}")
    print(f"{WHITE}  1. USDC Deposit: {GREEN}{usdc_10 / 10**6:.6f} USDC{RESET}")
    print(f"{WHITE}  2. USDT Deposit: {GREEN}{usdt_10 / 10**6:.6f} USDT{RESET}")
    print(f"{WHITE}  3. USDC Withdraw: {GREEN}{usdc_withdraw_10 / 10**6:.6f} USDC{RESET}")
    print(f"{WHITE}  4. USDT Withdraw: {GREEN}{usdt_withdraw_10 / 10**6:.6f} USDT{RESET}")
    if wbtc_10 > 0:
        btc_value = (wbtc_10 / 10**8) * BTC_PRICE_USD
        borrow_usdc = btc_value * 0.70
        print(f"{WHITE}  5. Borrow USDC: {GREEN}{borrow_usdc:.6f} USDC{RESET}")
    print(f"{WHITE}  6. Portfolio Deposit USDT{RESET}")
    print(f"{WHITE}  7. Portfolio Withdraw USDT{RESET}")
    print()
    
    confirm = input(f"{YELLOW}Start AUTO ALL? (y/n): {RESET}").strip().lower()
    if confirm != 'y':
        print(f"{RED}[CANCELLED]{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    
    success_count = 0
    total_tasks = 0
    
    # STEP 1: USDC Deposit
    if usdc_10 > 0:
        total_tasks += 1
        print()
        print(f"{CYAN}{'='*60}{RESET}")
        print(f"{BOLD}{WHITE}[STEP 1] USDC LEND DEPOSIT{RESET}")
        print(f"{CYAN}{'='*60}{RESET}")
        allowance = usdc.functions.allowance(account.address, Web3.to_checksum_address(USDC_LEND_CONTRACT)).call()
        if allowance < usdc_10:
            approve_token(w3, account, USDC_CONTRACT, USDC_LEND_CONTRACT, usdc_10, "USDC")
            time.sleep(5)
        tx_hash, _ = deposit_lend(w3, account, USDC_LEND_CONTRACT, usdc_10, "USDC")
        if tx_hash:
            success_count += 1
        time.sleep(3)
    
    # STEP 2: USDT Deposit
    if usdt_10 > 0:
        total_tasks += 1
        print()
        print(f"{CYAN}{'='*60}{RESET}")
        print(f"{BOLD}{WHITE}[STEP 2] USDT LEND DEPOSIT{RESET}")
        print(f"{CYAN}{'='*60}{RESET}")
        allowance = usdt.functions.allowance(account.address, Web3.to_checksum_address(USDT_LEND_CONTRACT)).call()
        if allowance < usdt_10:
            approve_token(w3, account, USDT_CONTRACT, USDT_LEND_CONTRACT, usdt_10, "USDT")
            time.sleep(5)
        tx_hash, _ = deposit_lend(w3, account, USDT_LEND_CONTRACT, usdt_10, "USDT")
        if tx_hash:
            success_count += 1
        time.sleep(3)
    
    # STEP 3: USDC Withdraw
    if usdc_withdraw_10 > 0:
        total_tasks += 1
        print()
        print(f"{CYAN}{'='*60}{RESET}")
        print(f"{BOLD}{WHITE}[STEP 3] USDC LEND WITHDRAW{RESET}")
        print(f"{CYAN}{'='*60}{RESET}")
        tx_hash, _ = withdraw_lend(w3, account, USDC_LEND_CONTRACT, usdc_withdraw_10, "USDC")
        if tx_hash:
            success_count += 1
        time.sleep(3)
    
    # STEP 4: USDT Withdraw
    if usdt_withdraw_10 > 0:
        total_tasks += 1
        print()
        print(f"{CYAN}{'='*60}{RESET}")
        print(f"{BOLD}{WHITE}[STEP 4] USDT LEND WITHDRAW{RESET}")
        print(f"{CYAN}{'='*60}{RESET}")
        tx_hash, _ = withdraw_lend(w3, account, USDT_LEND_CONTRACT, usdt_withdraw_10, "USDT")
        if tx_hash:
            success_count += 1
        time.sleep(3)
    
    # STEP 5: Borrow USDC with BTC
    if wbtc_10 > 0:
        total_tasks += 1
        print()
        print(f"{CYAN}{'='*60}{RESET}")
        print(f"{BOLD}{WHITE}[STEP 5] BORROW USDC (BTC Collateral){RESET}")
        print(f"{CYAN}{'='*60}{RESET}")
        btc_value = (wbtc_10 / 10**8) * BTC_PRICE_USD
        borrow_wei = int(btc_value * 0.70 * 10**6)
        allowance = wbtc.functions.allowance(account.address, Web3.to_checksum_address(BORROW_CONTRACT)).call()
        if allowance < wbtc_10:
            approve_token(w3, account, WBTC_CONTRACT, BORROW_CONTRACT, wbtc_10, "BTC")
            time.sleep(5)
        tx_hash, _ = do_borrow(w3, account, borrow_wei, wbtc_10)
        if tx_hash:
            success_count += 1
        time.sleep(3)
    
    # STEP 6: Portfolio Deposit USDT
    usdt_balance_new = usdt.functions.balanceOf(account.address).call()
    usdt_portfolio_10 = int(usdt_balance_new * 0.10)
    if usdt_portfolio_10 > 0:
        total_tasks += 1
        print()
        print(f"{CYAN}{'='*60}{RESET}")
        print(f"{BOLD}{WHITE}[STEP 6] PORTFOLIO DEPOSIT USDT{RESET}")
        print(f"{CYAN}{'='*60}{RESET}")
        allowance = usdt.functions.allowance(account.address, Web3.to_checksum_address(USDT_LEND_CONTRACT)).call()
        if allowance < usdt_portfolio_10:
            approve_token(w3, account, USDT_CONTRACT, USDT_LEND_CONTRACT, usdt_portfolio_10, "USDT")
            time.sleep(5)
        tx_hash, _ = deposit_lend(w3, account, USDT_LEND_CONTRACT, usdt_portfolio_10, "USDT")
        if tx_hash:
            success_count += 1
        time.sleep(3)
    
    # STEP 7: Portfolio Withdraw USDT
    usdt_lend_balance_new = usdt_lend.functions.balanceOf(account.address).call()
    try:
        usdt_max_withdraw_new = usdt_lend.functions.maxWithdraw(account.address).call()
    except:
        usdt_max_withdraw_new = usdt_lend_balance_new
    usdt_portfolio_withdraw_10 = int(usdt_max_withdraw_new * 0.10)
    if usdt_portfolio_withdraw_10 > 0:
        total_tasks += 1
        print()
        print(f"{CYAN}{'='*60}{RESET}")
        print(f"{BOLD}{WHITE}[STEP 7] PORTFOLIO WITHDRAW USDT{RESET}")
        print(f"{CYAN}{'='*60}{RESET}")
        tx_hash, _ = withdraw_lend(w3, account, USDT_LEND_CONTRACT, usdt_portfolio_withdraw_10, "USDT")
        if tx_hash:
            success_count += 1
        time.sleep(3)
    
    print()
    print(f"{GREEN}{'='*60}{RESET}")
    print(f"{BOLD}{GREEN}      AUTO ALL COMPLETED{RESET}")
    print(f"{BOLD}{GREEN}      Success: {success_count}/{total_tasks} Tasks{RESET}")
    print(f"{GREEN}{'='*60}{RESET}")
    print()
    input(f"{YELLOW}Press Enter to continue...{RESET}")

def main():
    while True:
        print_banner()
        print_menu()
        choice = input(f"{BOLD}{WHITE}Select option: {RESET}").strip()
        if choice == "1":
            do_deposit("USDC", USDC_CONTRACT, USDC_LEND_CONTRACT)
        elif choice == "2":
            do_withdraw("USDC", USDC_CONTRACT, USDC_LEND_CONTRACT)
        elif choice == "3":
            do_deposit("USDT", USDT_CONTRACT, USDT_LEND_CONTRACT)
        elif choice == "4":
            do_withdraw("USDT", USDT_CONTRACT, USDT_LEND_CONTRACT)
        elif choice == "5":
            borrow_usdc()
        elif choice == "6":
            portfolio_deposit_usdt()
        elif choice == "7":
            portfolio_withdraw_usdt()
        elif choice == "8":
            auto_all()
        elif choice == "9":
            print(f"{CYAN}{'='*60}{RESET}")
            print(f"{BOLD}{MAGENTA}      Goodbye! Thanks for using Avon Bot{RESET}")
            print(f"{BOLD}{YELLOW}      CREATED BY KAZUHA - VIP ONLY{RESET}")
            print(f"{CYAN}{'='*60}{RESET}")
            sys.exit(0)
        else:
            print(f"{RED}[ERROR] Invalid option!{RESET}")
            time.sleep(1)

if __name__ == "__main__":

    main()
