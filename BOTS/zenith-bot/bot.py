#!/usr/bin/env python3

import json
import time
import os
from web3 import Web3
from eth_account import Account
from datetime import datetime

class Colors:
    RED = '\033[1;91m'
    GREEN = '\033[1;92m'
    YELLOW = '\033[1;93m'
    BLUE = '\033[1;94m'
    MAGENTA = '\033[1;95m'
    CYAN = '\033[1;96m'
    WHITE = '\033[1;97m'
    RESET = '\033[0m'

RPC_URL = "https://atlantic.dplabs-internal.com"
CHAIN_ID = 688689
EXPLORER_URL = "https://atlantic.pharosscan.xyz/tx/"
LENDING_POOL = "0x62e72185f7deabda9f6a3df3b23d67530b42eff6"
WETH_TOKEN = "0x7d211f77525ea39a0592794f793cc1036eeaccd5"
AWETH_TOKEN = "0x8725ac76a140ec446318cb78c2e6ffd9c3a55fba"
WBTC_TOKEN = "0x0c64f03eea5c30946d5c55b4b532d08ad74638a4"
AWBTC_TOKEN = "0xe85489ea693687c0fb9260fd4a9d419abdbb9a01"

ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}
]

LENDING_POOL_ABI = [
    {"inputs": [{"name": "asset", "type": "address"}, {"name": "amount", "type": "uint256"}, {"name": "onBehalfOf", "type": "address"}, {"name": "referralCode", "type": "uint16"}], "name": "supply", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "asset", "type": "address"}, {"name": "amount", "type": "uint256"}, {"name": "interestRateMode", "type": "uint256"}, {"name": "referralCode", "type": "uint16"}, {"name": "onBehalfOf", "type": "address"}], "name": "borrow", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "user", "type": "address"}], "name": "getUserAccountData", "outputs": [{"name": "totalCollateralBase", "type": "uint256"}, {"name": "totalDebtBase", "type": "uint256"}, {"name": "availableBorrowsBase", "type": "uint256"}, {"name": "currentLiquidationThreshold", "type": "uint256"}, {"name": "ltv", "type": "uint256"}, {"name": "healthFactor", "type": "uint256"}], "stateMutability": "view", "type": "function"}
]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    print(f"{Colors.CYAN}========================================{Colors.RESET}")
    print(f"{Colors.GREEN}       ZENITH SWAP SUPPLY BORROW BOT       {Colors.RESET}")
    print(f"{Colors.YELLOW}            Created by Kazuha            {Colors.RESET}")
    print(f"{Colors.CYAN}========================================{Colors.RESET}")
    print()

def load_private_key():
    try:
        with open("pv.txt", "r") as f:
            pk = f.read().strip()
            if not pk.startswith("0x"):
                pk = "0x" + pk
            return pk
    except FileNotFoundError:
        print(f"{Colors.RED}[ERROR] pv.txt file not found!{Colors.RESET}")
        exit(1)

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class ZenithSwapBot:
    def __init__(self):
        print(f"{Colors.YELLOW}[INFO] Initializing Bot...{Colors.RESET}")
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not self.w3.is_connected():
            print(f"{Colors.RED}[ERROR] Failed to connect to RPC{Colors.RESET}")
            exit(1)
        print(f"{Colors.GREEN}[SUCCESS] Connected to Pharos Atlantic Testnet{Colors.RESET}")
        private_key = load_private_key()
        self.account = Account.from_key(private_key)
        self.address = self.account.address
        print(f"{Colors.GREEN}[SUCCESS] Wallet: {self.address}{Colors.RESET}")
        self.lending_pool = self.w3.eth.contract(address=Web3.to_checksum_address(LENDING_POOL), abi=LENDING_POOL_ABI)
        self.weth = self.w3.eth.contract(address=Web3.to_checksum_address(WETH_TOKEN), abi=ERC20_ABI)
        self.aweth = self.w3.eth.contract(address=Web3.to_checksum_address(AWETH_TOKEN), abi=ERC20_ABI)
        self.wbtc = self.w3.eth.contract(address=Web3.to_checksum_address(WBTC_TOKEN), abi=ERC20_ABI)
        self.awbtc = self.w3.eth.contract(address=Web3.to_checksum_address(AWBTC_TOKEN), abi=ERC20_ABI)

    def get_all_balances(self):
        phrs_balance = self.w3.eth.get_balance(self.address)
        weth_balance = self.weth.functions.balanceOf(self.address).call()
        wbtc_balance = self.wbtc.functions.balanceOf(self.address).call()
        aweth_balance = self.aweth.functions.balanceOf(self.address).call()
        awbtc_balance = self.awbtc.functions.balanceOf(self.address).call()
        return {'phrs': phrs_balance, 'weth': weth_balance, 'wbtc': wbtc_balance, 'aweth': aweth_balance, 'awbtc': awbtc_balance}

    def print_balances(self):
        balances = self.get_all_balances()
        print(f"{Colors.CYAN}========================================{Colors.RESET}")
        print(f"{Colors.WHITE}            WALLET BALANCES            {Colors.RESET}")
        print(f"{Colors.CYAN}========================================{Colors.RESET}")
        print(f"{Colors.WHITE}PHRS:  {Web3.from_wei(balances['phrs'], 'ether'):.6f}{Colors.RESET}")
        print(f"{Colors.WHITE}WETH:  {Web3.from_wei(balances['weth'], 'ether'):.6f}{Colors.RESET}")
        print(f"{Colors.WHITE}WBTC:  {Web3.from_wei(balances['wbtc'], 'ether'):.6f}{Colors.RESET}")
        print(f"{Colors.WHITE}aWETH: {Web3.from_wei(balances['aweth'], 'ether'):.6f}{Colors.RESET}")
        print(f"{Colors.WHITE}aWBTC: {Web3.from_wei(balances['awbtc'], 'ether'):.6f}{Colors.RESET}")
        print(f"{Colors.CYAN}========================================{Colors.RESET}")

    def check_and_approve(self, token_contract, token_address, amount, token_name):
        print(f"{Colors.YELLOW}[INFO] Checking {token_name} Allowance...{Colors.RESET}")
        allowance = token_contract.functions.allowance(self.address, Web3.to_checksum_address(LENDING_POOL)).call()
        if allowance < amount:
            print(f"{Colors.YELLOW}[INFO] Approving {token_name}...{Colors.RESET}")
            max_amount = 2**256 - 1
            nonce = self.w3.eth.get_transaction_count(self.address)
            approve_tx = token_contract.functions.approve(Web3.to_checksum_address(LENDING_POOL), max_amount).build_transaction({
                'from': self.address,
                'gas': 100000,
                'gasPrice': self.w3.to_wei(1, 'gwei'),
                'nonce': nonce,
                'chainId': CHAIN_ID
            })
            signed_tx = self.w3.eth.account.sign_transaction(approve_tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"{Colors.BLUE}[TX] Approve Hash: {tx_hash.hex()}{Colors.RESET}")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            if receipt.status == 1:
                print(f"{Colors.GREEN}[SUCCESS] {token_name} Approved{Colors.RESET}")
                print(f"{Colors.WHITE}[BLOCK] {receipt.blockNumber}{Colors.RESET}")
                print(f"{Colors.CYAN}[EXPLORER] {EXPLORER_URL}{tx_hash.hex()}{Colors.RESET}")
                time.sleep(3)
                return True
            else:
                print(f"{Colors.RED}[FAILED] Approval Failed{Colors.RESET}")
                return False
        else:
            print(f"{Colors.GREEN}[INFO] {token_name} Already Approved{Colors.RESET}")
            return True

    def supply_token(self, token_address, token_contract, amount, token_name):
        print(f"{Colors.MAGENTA}========================================{Colors.RESET}")
        print(f"{Colors.CYAN}[SUPPLY] {token_name}{Colors.RESET}")
        print(f"{Colors.WHITE}[AMOUNT] {Web3.from_wei(amount, 'ether'):.6f} {token_name}{Colors.RESET}")
        print(f"{Colors.MAGENTA}========================================{Colors.RESET}")
        if not self.check_and_approve(token_contract, token_address, amount, token_name):
            return None
        print(f"{Colors.YELLOW}[INFO] Executing Supply...{Colors.RESET}")
        nonce = self.w3.eth.get_transaction_count(self.address)
        supply_tx = self.lending_pool.functions.supply(Web3.to_checksum_address(token_address), amount, self.address, 0).build_transaction({
            'from': self.address,
            'gas': 300000,
            'gasPrice': self.w3.to_wei(1, 'gwei'),
            'nonce': nonce,
            'chainId': CHAIN_ID
        })
        signed_tx = self.w3.eth.account.sign_transaction(supply_tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"{Colors.BLUE}[TX] Supply Hash: {tx_hash.hex()}{Colors.RESET}")
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt.status == 1:
            print(f"{Colors.GREEN}[SUCCESS] Supply Completed{Colors.RESET}")
            print(f"{Colors.WHITE}[BLOCK] {receipt.blockNumber}{Colors.RESET}")
            print(f"{Colors.WHITE}[GAS USED] {receipt.gasUsed}{Colors.RESET}")
            print(f"{Colors.CYAN}[EXPLORER] {EXPLORER_URL}{tx_hash.hex()}{Colors.RESET}")
            return tx_hash.hex()
        else:
            print(f"{Colors.RED}[FAILED] Supply Failed{Colors.RESET}")
            return None

    def borrow_token(self, token_address, amount, token_name):
        print(f"{Colors.MAGENTA}========================================{Colors.RESET}")
        print(f"{Colors.CYAN}[BORROW] {token_name}{Colors.RESET}")
        print(f"{Colors.WHITE}[AMOUNT] {Web3.from_wei(amount, 'ether'):.6f} {token_name}{Colors.RESET}")
        print(f"{Colors.MAGENTA}========================================{Colors.RESET}")
        print(f"{Colors.YELLOW}[INFO] Executing Borrow...{Colors.RESET}")
        nonce = self.w3.eth.get_transaction_count(self.address)
        borrow_tx = self.lending_pool.functions.borrow(Web3.to_checksum_address(token_address), amount, 2, 0, self.address).build_transaction({
            'from': self.address,
            'gas': 450000,
            'gasPrice': self.w3.to_wei(1, 'gwei'),
            'nonce': nonce,
            'chainId': CHAIN_ID
        })
        signed_tx = self.w3.eth.account.sign_transaction(borrow_tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"{Colors.BLUE}[TX] Borrow Hash: {tx_hash.hex()}{Colors.RESET}")
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt.status == 1:
            print(f"{Colors.GREEN}[SUCCESS] Borrow Completed{Colors.RESET}")
            print(f"{Colors.WHITE}[BLOCK] {receipt.blockNumber}{Colors.RESET}")
            print(f"{Colors.WHITE}[GAS USED] {receipt.gasUsed}{Colors.RESET}")
            print(f"{Colors.CYAN}[EXPLORER] {EXPLORER_URL}{tx_hash.hex()}{Colors.RESET}")
            return tx_hash.hex()
        else:
            print(f"{Colors.RED}[FAILED] Borrow Failed{Colors.RESET}")
            return None

    def execute_weth_supply_and_borrow(self, supply_amount_ether, repeat_count):
        print(f"{Colors.MAGENTA}========================================{Colors.RESET}")
        print(f"{Colors.GREEN}[START] WETH SUPPLY AND BORROW{Colors.RESET}")
        print(f"{Colors.WHITE}[TIME] {get_timestamp()}{Colors.RESET}")
        print(f"{Colors.WHITE}[REPEAT] {repeat_count} times{Colors.RESET}")
        print(f"{Colors.MAGENTA}========================================{Colors.RESET}")
        self.print_balances()
        supply_amount = Web3.to_wei(supply_amount_ether, 'ether')
        balances = self.get_all_balances()
        total_needed = supply_amount * repeat_count
        if balances['weth'] < total_needed:
            print(f"{Colors.RED}[ERROR] Insufficient WETH Balance{Colors.RESET}")
            print(f"{Colors.YELLOW}[INFO] Required: {Web3.from_wei(total_needed, 'ether'):.6f} WETH{Colors.RESET}")
            print(f"{Colors.YELLOW}[INFO] Available: {Web3.from_wei(balances['weth'], 'ether'):.6f} WETH{Colors.RESET}")
            return False
        success_count = 0
        fail_count = 0
        for i in range(repeat_count):
            print(f"{Colors.CYAN}========================================{Colors.RESET}")
            print(f"{Colors.WHITE}[ROUND] {i+1}/{repeat_count}{Colors.RESET}")
            print(f"{Colors.CYAN}========================================{Colors.RESET}")
            supply_result = self.supply_token(WETH_TOKEN, self.weth, supply_amount, "WETH")
            if not supply_result:
                print(f"{Colors.RED}[ERROR] Supply Failed - Skipping Round{Colors.RESET}")
                fail_count += 1
                continue
            print(f"{Colors.YELLOW}[INFO] Waiting 5 seconds before borrowing...{Colors.RESET}")
            time.sleep(5)
            borrow_amount = supply_amount // 10
            print(f"{Colors.WHITE}[CALC] Supply: {Web3.from_wei(supply_amount, 'ether'):.6f} WETH{Colors.RESET}")
            print(f"{Colors.WHITE}[CALC] Borrow 10%: {Web3.from_wei(borrow_amount, 'ether'):.6f} WETH{Colors.RESET}")
            borrow_result = self.borrow_token(WETH_TOKEN, borrow_amount, "WETH")
            if borrow_result:
                success_count += 1
                print(f"{Colors.GREEN}[SUCCESS] Round {i+1} Completed{Colors.RESET}")
            else:
                fail_count += 1
                print(f"{Colors.RED}[FAILED] Round {i+1} Borrow Failed{Colors.RESET}")
            if i < repeat_count - 1:
                print(f"{Colors.YELLOW}[INFO] Waiting 3 seconds before next round...{Colors.RESET}")
                time.sleep(3)
        print(f"{Colors.MAGENTA}========================================{Colors.RESET}")
        print(f"{Colors.GREEN}[SUMMARY] WETH SUPPLY AND BORROW{Colors.RESET}")
        print(f"{Colors.MAGENTA}========================================{Colors.RESET}")
        print(f"{Colors.GREEN}[SUCCESS] {success_count} rounds{Colors.RESET}")
        if fail_count > 0:
            print(f"{Colors.RED}[FAILED] {fail_count} rounds{Colors.RESET}")
        print(f"{Colors.WHITE}[TOTAL SUPPLIED] {Web3.from_wei(supply_amount * success_count, 'ether'):.6f} WETH{Colors.RESET}")
        print(f"{Colors.WHITE}[TOTAL BORROWED] {Web3.from_wei((supply_amount // 10) * success_count, 'ether'):.6f} WETH{Colors.RESET}")
        self.print_balances()
        return True

    def execute_wbtc_supply_and_borrow(self, supply_amount_ether, repeat_count):
        print(f"{Colors.MAGENTA}========================================{Colors.RESET}")
        print(f"{Colors.GREEN}[START] WBTC SUPPLY AND BORROW{Colors.RESET}")
        print(f"{Colors.WHITE}[TIME] {get_timestamp()}{Colors.RESET}")
        print(f"{Colors.WHITE}[REPEAT] {repeat_count} times{Colors.RESET}")
        print(f"{Colors.MAGENTA}========================================{Colors.RESET}")
        self.print_balances()
        supply_amount = Web3.to_wei(supply_amount_ether, 'ether')
        balances = self.get_all_balances()
        total_needed = supply_amount * repeat_count
        if balances['wbtc'] < total_needed:
            print(f"{Colors.RED}[ERROR] Insufficient WBTC Balance{Colors.RESET}")
            print(f"{Colors.YELLOW}[INFO] Required: {Web3.from_wei(total_needed, 'ether'):.6f} WBTC{Colors.RESET}")
            print(f"{Colors.YELLOW}[INFO] Available: {Web3.from_wei(balances['wbtc'], 'ether'):.6f} WBTC{Colors.RESET}")
            return False
        success_count = 0
        fail_count = 0
        for i in range(repeat_count):
            print(f"{Colors.CYAN}========================================{Colors.RESET}")
            print(f"{Colors.WHITE}[ROUND] {i+1}/{repeat_count}{Colors.RESET}")
            print(f"{Colors.CYAN}========================================{Colors.RESET}")
            supply_result = self.supply_token(WBTC_TOKEN, self.wbtc, supply_amount, "WBTC")
            if not supply_result:
                print(f"{Colors.RED}[ERROR] Supply Failed - Skipping Round{Colors.RESET}")
                fail_count += 1
                continue
            print(f"{Colors.YELLOW}[INFO] Waiting 5 seconds before borrowing...{Colors.RESET}")
            time.sleep(5)
            borrow_amount = supply_amount // 10
            print(f"{Colors.WHITE}[CALC] Supply: {Web3.from_wei(supply_amount, 'ether'):.6f} WBTC{Colors.RESET}")
            print(f"{Colors.WHITE}[CALC] Borrow 10%: {Web3.from_wei(borrow_amount, 'ether'):.6f} WBTC{Colors.RESET}")
            borrow_result = self.borrow_token(WBTC_TOKEN, borrow_amount, "WBTC")
            if borrow_result:
                success_count += 1
                print(f"{Colors.GREEN}[SUCCESS] Round {i+1} Completed{Colors.RESET}")
            else:
                fail_count += 1
                print(f"{Colors.RED}[FAILED] Round {i+1} Borrow Failed{Colors.RESET}")
            if i < repeat_count - 1:
                print(f"{Colors.YELLOW}[INFO] Waiting 3 seconds before next round...{Colors.RESET}")
                time.sleep(3)
        print(f"{Colors.MAGENTA}========================================{Colors.RESET}")
        print(f"{Colors.GREEN}[SUMMARY] WBTC SUPPLY AND BORROW{Colors.RESET}")
        print(f"{Colors.MAGENTA}========================================{Colors.RESET}")
        print(f"{Colors.GREEN}[SUCCESS] {success_count} rounds{Colors.RESET}")
        if fail_count > 0:
            print(f"{Colors.RED}[FAILED] {fail_count} rounds{Colors.RESET}")
        print(f"{Colors.WHITE}[TOTAL SUPPLIED] {Web3.from_wei(supply_amount * success_count, 'ether'):.6f} WBTC{Colors.RESET}")
        print(f"{Colors.WHITE}[TOTAL BORROWED] {Web3.from_wei((supply_amount // 10) * success_count, 'ether'):.6f} WBTC{Colors.RESET}")
        self.print_balances()
        return True

def main():
    if os.name == 'nt':
        os.system('color')
    clear_screen()
    print_banner()
    bot = ZenithSwapBot()
    time.sleep(2)
    while True:
        clear_screen()
        print_banner()
        print(f"{Colors.WHITE}Wallet: {bot.address}{Colors.RESET}")
        print()
        print(f"{Colors.MAGENTA}============== MENU =============={Colors.RESET}")
        print(f"{Colors.CYAN}1. WETH SUPPLY AND BORROW{Colors.RESET}")
        print(f"{Colors.CYAN}2. WBTC SUPPLY AND BORROW{Colors.RESET}")
        print(f"{Colors.CYAN}3. EXIT{Colors.RESET}")
        print(f"{Colors.MAGENTA}=================================={Colors.RESET}")
        print()
        choice = input(f"{Colors.YELLOW}Select option: {Colors.RESET}")
        if choice == "1":
            clear_screen()
            print_banner()
            print(f"{Colors.GREEN}[WETH SUPPLY AND BORROW]{Colors.RESET}")
            print()
            bot.print_balances()
            print()
            try:
                amount = float(input(f"{Colors.CYAN}Enter WETH amount to supply: {Colors.RESET}"))
                if amount <= 0:
                    print(f"{Colors.RED}[ERROR] Amount must be greater than 0{Colors.RESET}")
                    input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
                    continue
                repeat = int(input(f"{Colors.CYAN}How many times to perform: {Colors.RESET}"))
                if repeat <= 0:
                    print(f"{Colors.RED}[ERROR] Repeat count must be greater than 0{Colors.RESET}")
                    input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
                    continue
                print()
                print(f"{Colors.YELLOW}========================================{Colors.RESET}")
                print(f"{Colors.WHITE}[PREVIEW]{Colors.RESET}")
                print(f"{Colors.WHITE}Supply: {amount} WETH x {repeat} times{Colors.RESET}")
                print(f"{Colors.WHITE}Borrow: {amount * 0.1} WETH x {repeat} times [10%]{Colors.RESET}")
                print(f"{Colors.WHITE}Total Supply: {amount * repeat} WETH{Colors.RESET}")
                print(f"{Colors.WHITE}Total Borrow: {amount * 0.1 * repeat} WETH{Colors.RESET}")
                print(f"{Colors.YELLOW}========================================{Colors.RESET}")
                print()
                confirm = input(f"{Colors.GREEN}Proceed [Y/N]: {Colors.RESET}")
                if confirm.lower() == 'y':
                    bot.execute_weth_supply_and_borrow(amount, repeat)
            except ValueError:
                print(f"{Colors.RED}[ERROR] Invalid input{Colors.RESET}")
            print()
            input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
        elif choice == "2":
            clear_screen()
            print_banner()
            print(f"{Colors.GREEN}[WBTC SUPPLY AND BORROW]{Colors.RESET}")
            print()
            bot.print_balances()
            print()
            try:
                amount = float(input(f"{Colors.CYAN}Enter WBTC amount to supply: {Colors.RESET}"))
                if amount <= 0:
                    print(f"{Colors.RED}[ERROR] Amount must be greater than 0{Colors.RESET}")
                    input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
                    continue
                repeat = int(input(f"{Colors.CYAN}How many times to perform: {Colors.RESET}"))
                if repeat <= 0:
                    print(f"{Colors.RED}[ERROR] Repeat count must be greater than 0{Colors.RESET}")
                    input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
                    continue
                print()
                print(f"{Colors.YELLOW}========================================{Colors.RESET}")
                print(f"{Colors.WHITE}[PREVIEW]{Colors.RESET}")
                print(f"{Colors.WHITE}Supply: {amount} WBTC x {repeat} times{Colors.RESET}")
                print(f"{Colors.WHITE}Borrow: {amount * 0.1} WBTC x {repeat} times [10%]{Colors.RESET}")
                print(f"{Colors.WHITE}Total Supply: {amount * repeat} WBTC{Colors.RESET}")
                print(f"{Colors.WHITE}Total Borrow: {amount * 0.1 * repeat} WBTC{Colors.RESET}")
                print(f"{Colors.YELLOW}========================================{Colors.RESET}")
                print()
                confirm = input(f"{Colors.GREEN}Proceed [Y/N]: {Colors.RESET}")
                if confirm.lower() == 'y':
                    bot.execute_wbtc_supply_and_borrow(amount, repeat)
            except ValueError:
                print(f"{Colors.RED}[ERROR] Invalid input{Colors.RESET}")
            print()
            input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
        elif choice == "3":
            print(f"{Colors.GREEN}Goodbye!{Colors.RESET}")
            print(f"{Colors.YELLOW}Created by Kazuha{Colors.RESET}")
            break
        else:
            print(f"{Colors.RED}Invalid option{Colors.RESET}")
            time.sleep(1)

if __name__ == "__main__":
    main()