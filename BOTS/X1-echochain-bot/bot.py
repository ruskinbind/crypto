import requests
import json
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
import time
import os
import sys
from datetime import datetime
from colorama import init, Fore, Style
import secrets
import pyfiglet

init(autoreset=False)

Account.enable_unaudited_hdwallet_features()

AUTH_MESSAGE = "X1 Testnet Auth"
SIGNIN_URL = "https://tapi.kod.af/signin"
FAUCET_URL = "https://nft-api.x1.one/testnet/faucet"
QUESTS_URL = "https://tapi.kod.af/quests"
PRIVATE_KEY_FILE = "pv.txt"

CHAIN_ID = 10778
NETWORK_NAME = "X1 EcoChain Testnet (Maculatus)"
RPC_URL = "https://maculatus-rpc.x1eco.com/"
CURRENCY_SYMBOL = "X1T"
EXPLORER_URL = "https://maculatus-scan.x1eco.com/"

GAS_LIMIT = 21000
GAS_PRICE_GWEI = 1

BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
WHITE = "\033[37m"
RESET = "\033[0m"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

HEADERS_BASE = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "origin": "https://testnet.x1ecochain.com",
    "referer": "https://testnet.x1ecochain.com/",
    "user-agent": UA
}

w3 = None
MAIN_WALLET = None


def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')


def set_title():
    sys.stdout.write("\x1b]2;X1 Ecochain Bot\x1b\\")
    sys.stdout.flush()


def log_info(msg):
    print(f"{BOLD}{GREEN}[INFO]{RESET} {BOLD}{WHITE}{msg}{RESET}")


def log_success(msg):
    print(f"{BOLD}{GREEN}[SUCCESS]{RESET} {BOLD}{WHITE}{msg}{RESET}")


def log_error(msg):
    print(f"{BOLD}{RED}[ERROR]{RESET} {BOLD}{WHITE}{msg}{RESET}")


def log_warn(msg):
    print(f"{BOLD}{YELLOW}[WARN]{RESET} {BOLD}{WHITE}{msg}{RESET}")


def log_process(msg):
    print(f"{BOLD}{CYAN}[PROCESS]{RESET} {BOLD}{WHITE}{msg}{RESET}")


def log_tx(tx_hash, block_number, amount_sent):
    print(f"{BOLD}{GREEN}[SUCCESS]{RESET} {BOLD}{MAGENTA}Block:{RESET} {BOLD}{WHITE}{block_number}{RESET}")
    print(f"{BOLD}{GREEN}[SUCCESS]{RESET} {BOLD}{MAGENTA}Amount:{RESET} {BOLD}{WHITE}{amount_sent:.6f} X1T{RESET}")
    print(f"{BOLD}{CYAN}[TX]{RESET} {BOLD}{MAGENTA}Hash:{RESET} {BOLD}{WHITE}{tx_hash}{RESET}")
    print(f"{BOLD}{CYAN}[EXPLORER]{RESET} {BOLD}{GREEN}{EXPLORER_URL}tx/{tx_hash}{RESET}")


def print_banner():
    clear_terminal()
    print(f"{BOLD}{CYAN}======================================================={RESET}")
    print(f"{BOLD}{MAGENTA}            X1 EcoChain Auto Bot{RESET}")
    print(f"{BOLD}{GREEN}          Created by KAZUHA | VIP ONLY {RESET}")
    print(f"{BOLD}{CYAN}======================================================={RESET}")


def show_menu():
    print(f"\n{BOLD}{CYAN}======================================================={RESET}")
    print(f"{BOLD}{MAGENTA}                 MAIN MENU{RESET}")
    print(f"{BOLD}{CYAN}======================================================={RESET}")
    print(f"{BOLD}{GREEN}[1]{RESET} {BOLD}{WHITE}Auto Faucet (Create + Claim + Send){RESET}")
    print(f"{BOLD}{GREEN}[2]{RESET} {BOLD}{WHITE}Daily Check-In (Claim Faucet){RESET}")
    print(f"{BOLD}{GREEN}[3]{RESET} {BOLD}{WHITE}Complete All Quests{RESET}")
    print(f"{BOLD}{GREEN}[4]{RESET} {BOLD}{WHITE}Send X1T Token{RESET}")
    print(f"{BOLD}{GREEN}[5]{RESET} {BOLD}{WHITE}Exit{RESET}")
    print(f"{BOLD}{CYAN}======================================================={RESET}")
    try:
        choice = input(f"{BOLD}{YELLOW}Select option: {RESET}")
        return choice.strip()
    except:
        return "5"


def init_web3():
    global w3
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 60}))
        return w3.is_connected()
    except:
        return False


def get_balance(address):
    global w3
    try:
        if not w3 or not w3.is_connected():
            init_web3()
        balance_wei = w3.eth.get_balance(Web3.to_checksum_address(address))
        balance_x1t = float(w3.from_wei(balance_wei, 'ether'))
        return balance_x1t, balance_wei
    except:
        return 0.0, 0


def send_transaction(from_address, private_key, to_address, amount_wei):
    global w3
    try:
        if not w3 or not w3.is_connected():
            if not init_web3():
                return False, None, None, 0
        from_address = Web3.to_checksum_address(from_address)
        to_address = Web3.to_checksum_address(to_address)
        nonce = w3.eth.get_transaction_count(from_address)
        gas_price = w3.to_wei(GAS_PRICE_GWEI, 'gwei')
        gas_cost = GAS_LIMIT * gas_price
        if amount_wei <= gas_cost:
            return False, None, None, 0
        send_amount = amount_wei - gas_cost
        tx = {
            'chainId': CHAIN_ID,
            'nonce': nonce,
            'to': to_address,
            'value': send_amount,
            'gas': GAS_LIMIT,
            'maxFeePerGas': gas_price,
            'maxPriorityFeePerGas': gas_price,
        }
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        block_number = receipt.blockNumber
        sent_x1t = float(w3.from_wei(send_amount, 'ether'))
        return True, tx_hash.hex(), block_number, sent_x1t
    except Exception as e:
        log_error(f"TX Error: {str(e)}")
        return False, None, None, 0


def send_specific_amount(from_address, private_key, to_address, amount_x1t):
    global w3
    try:
        if not w3 or not w3.is_connected():
            if not init_web3():
                return False, None, None, 0
        from_address = Web3.to_checksum_address(from_address)
        to_address = Web3.to_checksum_address(to_address)
        nonce = w3.eth.get_transaction_count(from_address)
        gas_price = w3.to_wei(GAS_PRICE_GWEI, 'gwei')
        send_amount = w3.to_wei(amount_x1t, 'ether')
        tx = {
            'chainId': CHAIN_ID,
            'nonce': nonce,
            'to': to_address,
            'value': send_amount,
            'gas': GAS_LIMIT,
            'maxFeePerGas': gas_price,
            'maxPriorityFeePerGas': gas_price,
        }
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        block_number = receipt.blockNumber
        return True, tx_hash.hex(), block_number, amount_x1t
    except Exception as e:
        log_error(f"TX Error: {str(e)}")
        return False, None, None, 0


def create_wallet():
    try:
        account = Account.create()
        address = Web3.to_checksum_address(account.address)
        private_key = account.key.hex()
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key
        return address, private_key
    except:
        private_key = "0x" + secrets.token_hex(32)
        account = Account.from_key(private_key)
        address = Web3.to_checksum_address(account.address)
        return address, private_key


def generate_random_address():
    account = Account.create()
    return Web3.to_checksum_address(account.address)


def load_private_keys():
    if not os.path.exists(PRIVATE_KEY_FILE):
        log_error(f"File {PRIVATE_KEY_FILE} not found")
        return []
    private_keys = []
    with open(PRIVATE_KEY_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            clean_key = line.replace('0x', '')
            if len(clean_key) == 64:
                if not line.startswith('0x'):
                    line = '0x' + line
                private_keys.append(line)
    return private_keys


def sign_message(private_key, message=AUTH_MESSAGE):
    try:
        msg = encode_defunct(text=message)
        signed = Account.sign_message(msg, private_key=private_key)
        signature = signed.signature.hex()
        if not signature.startswith("0x"):
            signature = "0x" + signature
        return signature
    except:
        return None


def authenticate(private_key):
    for attempt in range(3):
        try:
            signature = sign_message(private_key)
            if not signature:
                continue
            payload = {"signature": signature}
            response = requests.post(SIGNIN_URL, json=payload, headers=HEADERS_BASE, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get("token") or data.get("access_token")
        except:
            time.sleep(1)
    return None


def claim_faucet(address, token):
    for attempt in range(3):
        try:
            params = {"address": address}
            headers = {**HEADERS_BASE, "authorization": token}
            response = requests.get(FAUCET_URL, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                return True, "Faucet claimed"
            elif response.status_code == 400:
                error_msg = response.text
                if "24 hours" in error_msg or "once every" in error_msg:
                    return False, "Already claimed (24h)"
                return False, error_msg
            elif response.status_code == 500:
                return False, response.text
            return False, f"Status {response.status_code}"
        except:
            time.sleep(1)
    return False, "Failed"


def get_quests(token):
    try:
        headers = {**HEADERS_BASE, "authorization": token}
        response = requests.get(QUESTS_URL, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


def complete_quest(token, quest_id):
    try:
        headers = {**HEADERS_BASE, "authorization": token, "content-length": "0"}
        url = f"{QUESTS_URL}?quest_id={quest_id}"
        response = requests.post(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            reward = data.get('reward', 0)
            return True, f"Reward: {reward} pts"
        else:
            try:
                error_data = response.json()
                return False, error_data.get('message', 'Failed')
            except:
                return False, "Failed"
    except Exception as e:
        return False, str(e)


def auto_complete_quests(token):
    log_process("Fetching quests...")
    quests = get_quests(token)
    if not quests or not isinstance(quests, list):
        log_warn("No quests found")
        return
    completed = sum(1 for q in quests if q.get('is_completed', False))
    pending = len(quests) - completed
    log_info(f"Found {len(quests)} quests | Done: {completed} | Pending: {pending}")
    for idx, quest in enumerate(quests, 1):
        quest_id = quest.get('id')
        title = quest.get('title', 'Unknown')
        reward = quest.get('reward', 0)
        is_completed = quest.get('is_completed', False)
        is_completed_today = quest.get('is_completed_today', False)
        periodicity = quest.get('periodicity', 'one_time')
        requirements = quest.get('requirements', {})
        print(f"{BOLD}{CYAN}[{idx}/{len(quests)}]{RESET} {BOLD}{WHITE}{title}{RESET} {BOLD}{MAGENTA}({reward} pts){RESET}")
        if is_completed and periodicity == 'one_time':
            log_warn("Already completed")
            continue
        if is_completed_today and periodicity == 'daily':
            log_warn("Completed today")
            continue
        if requirements.get('linked_discord', False):
            log_warn("Requires Discord - Skip")
            continue
        log_process("Completing...")
        time.sleep(1)
        success, msg = complete_quest(token, quest_id)
        if success:
            log_success(msg)
        else:
            log_warn(msg)
        time.sleep(0.5)


def option_auto_faucet():
    global MAIN_WALLET
    print(f"\n{BOLD}{CYAN}======================================================={RESET}")
    print(f"{BOLD}{MAGENTA}AUTO FAUCET - CREATE + CLAIM + SEND{RESET}")
    print(f"{BOLD}{CYAN}======================================================={RESET}")
    log_info("Connecting to RPC...")
    if not init_web3():
        log_error("Failed to connect")
        return
    log_success("Connected")
    MAIN_WALLET = input(f"{BOLD}{YELLOW}Enter MAIN wallet: {RESET}").strip()
    if not MAIN_WALLET:
        log_error("Address required")
        return
    try:
        MAIN_WALLET = Web3.to_checksum_address(MAIN_WALLET)
    except:
        log_error("Invalid address")
        return
    main_balance, _ = get_balance(MAIN_WALLET)
    log_info(f"Main: {MAIN_WALLET[:8]}...{MAIN_WALLET[-6:]}")
    log_info(f"Balance: {main_balance:.6f} X1T")
    try:
        claim_count = int(input(f"{BOLD}{YELLOW}Claim count: {RESET}").strip())
    except:
        log_error("Invalid count")
        return
    if claim_count <= 0:
        return
    print(f"{BOLD}{CYAN}======================================================={RESET}")
    log_info(f"Starting {claim_count} claims")
    print(f"{BOLD}{CYAN}======================================================={RESET}")
    start_time = time.time()
    success_count = 0
    fail_count = 0
    total_sent = 0.0
    for i in range(1, claim_count + 1):
        print(f"\n{BOLD}{MAGENTA}[CLAIM {i}/{claim_count}]{RESET}")
        address, private_key = create_wallet()
        log_info(f"Wallet: {address[:8]}...{address[-6:]}")
        log_process("Auth...")
        token = authenticate(private_key)
        if not token:
            log_error("Auth failed")
            fail_count += 1
            continue
        log_success("Authenticated")
        log_process("Claiming...")
        success, msg = claim_faucet(address, token)
        if not success:
            log_error(msg)
            fail_count += 1
            continue
        log_success("Claimed")
        log_process("Waiting balance...")
        time.sleep(3)
        balance_x1t, balance_wei = get_balance(address)
        if balance_wei <= 0:
            log_warn("No balance")
            fail_count += 1
            continue
        log_info(f"Balance: {balance_x1t:.6f} X1T")
        log_process("Sending...")
        tx_ok, tx_hash, block, sent = send_transaction(address, private_key, MAIN_WALLET, balance_wei)
        if tx_ok:
            success_count += 1
            total_sent += sent
            log_tx(tx_hash, block, sent)
        else:
            log_error("Transfer failed")
            fail_count += 1
        time.sleep(1)
    elapsed = time.time() - start_time
    print(f"\n{BOLD}{GREEN}======================================================={RESET}")
    print(f"{BOLD}{WHITE}SUMMARY{RESET}")
    print(f"{BOLD}{GREEN}======================================================={RESET}")
    log_info(f"Time: {elapsed:.2f}s")
    log_success(f"Success: {success_count}/{claim_count}")
    if fail_count > 0:
        log_error(f"Failed: {fail_count}")
    log_success(f"Total sent: {total_sent:.6f} X1T")
    new_bal, _ = get_balance(MAIN_WALLET)
    log_success(f"Main balance: {new_bal:.6f} X1T")


def option_daily_checkin():
    print(f"\n{BOLD}{CYAN}======================================================={RESET}")
    print(f"{BOLD}{MAGENTA}DAILY CHECK-IN{RESET}")
    print(f"{BOLD}{CYAN}======================================================={RESET}")
    private_keys = load_private_keys()
    if not private_keys:
        log_error(f"No keys in {PRIVATE_KEY_FILE}")
        return
    log_success(f"Loaded {len(private_keys)} accounts")
    for idx, pk in enumerate(private_keys, 1):
        print(f"\n{BOLD}{MAGENTA}[Account {idx}/{len(private_keys)}]{RESET}")
        try:
            account = Account.from_key(pk)
            address = account.address
            log_info(f"Address: {address[:8]}...{address[-6:]}")
            log_process("Auth...")
            token = authenticate(pk)
            if not token:
                log_error("Auth failed")
                continue
            log_success("Authenticated")
            log_process("Claiming...")
            success, msg = claim_faucet(address, token)
            if success:
                log_success(msg)
            else:
                log_warn(msg)
        except Exception as e:
            log_error(str(e))
        time.sleep(1)
    print(f"\n{BOLD}{GREEN}======================================================={RESET}")
    log_success("Daily check-in done")


def option_quests():
    print(f"\n{BOLD}{CYAN}======================================================={RESET}")
    print(f"{BOLD}{MAGENTA}COMPLETE QUESTS{RESET}")
    print(f"{BOLD}{CYAN}======================================================={RESET}")
    private_keys = load_private_keys()
    if not private_keys:
        log_error(f"No keys in {PRIVATE_KEY_FILE}")
        return
    log_success(f"Loaded {len(private_keys)} accounts")
    for idx, pk in enumerate(private_keys, 1):
        print(f"\n{BOLD}{MAGENTA}[Account {idx}/{len(private_keys)}]{RESET}")
        try:
            account = Account.from_key(pk)
            address = account.address
            log_info(f"Address: {address[:8]}...{address[-6:]}")
            log_process("Auth...")
            token = authenticate(pk)
            if not token:
                log_error("Auth failed")
                continue
            log_success("Authenticated")
            auto_complete_quests(token)
        except Exception as e:
            log_error(str(e))
        time.sleep(1)
    print(f"\n{BOLD}{GREEN}======================================================={RESET}")
    log_success("Quest completion done")


def option_send_token():
    print(f"\n{BOLD}{CYAN}======================================================={RESET}")
    print(f"{BOLD}{MAGENTA}SEND X1T TOKEN{RESET}")
    print(f"{BOLD}{CYAN}======================================================={RESET}")
    log_info("Connecting to RPC...")
    if not init_web3():
        log_error("Failed to connect")
        return
    log_success("Connected")
    private_keys = load_private_keys()
    if not private_keys:
        log_error(f"No keys in {PRIVATE_KEY_FILE}")
        return
    log_success(f"Loaded {len(private_keys)} accounts")
    print(f"{BOLD}{YELLOW}Address options:{RESET}")
    print(f"{BOLD}{GREEN}[1]{RESET} {BOLD}{WHITE}Enter address manually{RESET}")
    print(f"{BOLD}{GREEN}[2]{RESET} {BOLD}{WHITE}Random address{RESET}")
    addr_choice = input(f"{BOLD}{YELLOW}Select (1/2): {RESET}").strip()
    if addr_choice == "1":
        to_address = input(f"{BOLD}{YELLOW}Recipient address: {RESET}").strip()
        if not to_address:
            log_error("Address required")
            return
        try:
            to_address = Web3.to_checksum_address(to_address)
        except:
            log_error("Invalid address")
            return
    elif addr_choice == "2":
        to_address = generate_random_address()
        log_info(f"Random: {to_address[:8]}...{to_address[-6:]}")
    else:
        log_error("Invalid choice")
        return
    try:
        amount = float(input(f"{BOLD}{YELLOW}Amount (X1T): {RESET}").strip())
    except:
        log_error("Invalid amount")
        return
    if amount <= 0:
        log_error("Amount must be > 0")
        return
    try:
        tx_count = int(input(f"{BOLD}{YELLOW}TX count: {RESET}").strip())
    except:
        tx_count = 1
    if tx_count <= 0:
        tx_count = 1
    print(f"{BOLD}{CYAN}======================================================={RESET}")
    log_info(f"Sending {amount} X1T x {tx_count} times")
    print(f"{BOLD}{CYAN}======================================================={RESET}")
    success_count = 0
    fail_count = 0
    for idx, pk in enumerate(private_keys, 1):
        print(f"\n{BOLD}{MAGENTA}[Account {idx}/{len(private_keys)}]{RESET}")
        try:
            account = Account.from_key(pk)
            address = account.address
            balance, _ = get_balance(address)
            log_info(f"Address: {address[:8]}...{address[-6:]}")
            log_info(f"Balance: {balance:.6f} X1T")
            for tx_num in range(1, tx_count + 1):
                if addr_choice == "2":
                    to_address = generate_random_address()
                    log_info(f"TX {tx_num} -> {to_address[:8]}...{to_address[-6:]}")
                log_process(f"Sending TX {tx_num}/{tx_count}...")
                tx_ok, tx_hash, block, sent = send_specific_amount(address, pk, to_address, amount)
                if tx_ok:
                    success_count += 1
                    log_tx(tx_hash, block, sent)
                else:
                    log_error("Failed")
                    fail_count += 1
                time.sleep(1)
        except Exception as e:
            log_error(str(e))
            fail_count += 1
        time.sleep(1)
    print(f"\n{BOLD}{GREEN}======================================================={RESET}")
    log_success(f"Success: {success_count}")
    if fail_count > 0:
        log_error(f"Failed: {fail_count}")


def main():
    set_title()
    while True:
        print_banner()
        choice = show_menu()
        if choice == "1":
            option_auto_faucet()
        elif choice == "2":
            option_daily_checkin()
        elif choice == "3":
            option_quests()
        elif choice == "4":
            option_send_token()
        elif choice == "5":
            print(f"\n{BOLD}{GREEN}======================================================={RESET}")
            log_info("Goodbye!")
            print(f"{BOLD}{RED}[ EXIT ]{RESET}")
            print(f"{BOLD}{GREEN}======================================================={RESET}\n")
            break
        else:
            log_error("Invalid option")
        input(f"\n{BOLD}{YELLOW}Press Enter...{RESET}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{BOLD}{YELLOW}Stopped{RESET}")
        print(f"{BOLD}{GREEN}======================================================={RESET}")
        print(f"{BOLD}{RED}[ EXIT ]{RESET}")
        print(f"{BOLD}{GREEN}======================================================={RESET}\n")
