import time
from web3 import Web3
from colorama import Fore, Style

from .config import CHAIN_ID, WUSDC_CONTRACT, ROUTER_CONTRACT, EXPLORER_URL, WUSDC_ABI
from .utils import short_delay, human_delay, random_wait_message, print_header, print_info, print_success, print_error

def wrap_usdc(w3, account, amount):
    print_header(f"WRAP: {amount} USDC -> WUSDC")
    
    amount_wei = w3.to_wei(amount, 'ether')
    
    print_info("[1] Checking USDC balance...")
    short_delay()
    
    balance = w3.eth.get_balance(account.address)
    balance_formatted = float(w3.from_wei(balance, 'ether'))
    print_success(f"    USDC Balance: {balance_formatted:.6f}")
    
    if balance < amount_wei:
        print_error("ERROR: Insufficient USDC!")
        return False
    
    human_delay()
    print_info(f"[2] {random_wait_message()}")
    short_delay()
    
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    
    tx = {
        'from': account.address,
        'to': Web3.to_checksum_address(WUSDC_CONTRACT),
        'value': amount_wei,
        'data': '0xd0e30db0',
        'nonce': nonce,
        'gas': 50000,
        'gasPrice': gas_price,
        'chainId': CHAIN_ID
    }
    
    human_delay()
    print_info("[3] Sending transaction...")
    
    try:
        signed = w3.eth.account.sign_transaction(tx, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        tx_hash_hex = tx_hash.hex()
        print_success(f"    TX: {tx_hash_hex}")
    except Exception as e:
        print_error(f"ERROR: {str(e)[:50]}")
        return False
    
    print_info("[4] Waiting for confirmation...")
    
    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        block = receipt['blockNumber']
        
        print_header("RESULT")
        
        if receipt['status'] == 1:
            print_success(f"Status: SUCCESS")
            print_success(f"Block: {block}")
            print(Fore.CYAN + Style.BRIGHT + f"Explorer: {EXPLORER_URL}/tx/{tx_hash_hex}")
            return True
        else:
            print_error("Status: FAILED")
            return False
    except Exception as e:
        print_error(f"ERROR: {str(e)[:50]}")
        return False

def unwrap_wusdc(w3, account, amount):
    print_header(f"UNWRAP: {amount} WUSDC -> USDC")
    
    amount_wei = w3.to_wei(amount, 'ether')
    wusdc = w3.eth.contract(address=Web3.to_checksum_address(WUSDC_CONTRACT), abi=WUSDC_ABI)
    
    print_info("[1] Checking WUSDC balance...")
    short_delay()
    
    balance = wusdc.functions.balanceOf(account.address).call()
    balance_formatted = float(w3.from_wei(balance, 'ether'))
    print_success(f"    WUSDC Balance: {balance_formatted:.6f}")
    
    if balance < amount_wei:
        print_error("ERROR: Insufficient WUSDC!")
        return False
    
    human_delay()
    print_info("[2] Checking approval...")
    short_delay()
    
    allowance = wusdc.functions.allowance(account.address, Web3.to_checksum_address(ROUTER_CONTRACT)).call()
    
    if allowance < amount_wei:
        print_info("    Approving WUSDC...")
        human_delay()
        
        nonce = w3.eth.get_transaction_count(account.address)
        approve_tx = {
            'from': account.address,
            'to': Web3.to_checksum_address(WUSDC_CONTRACT),
            'data': '0x095ea7b3' + ROUTER_CONTRACT[2:].lower().zfill(64) + 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff',
            'nonce': nonce,
            'gas': 70000,
            'gasPrice': w3.eth.gas_price,
            'chainId': CHAIN_ID
        }
        
        try:
            signed = w3.eth.account.sign_transaction(approve_tx, account.key)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            if receipt['status'] != 1:
                print_error("ERROR: Approval failed!")
                return False
            print_success("    Approved!")
        except Exception as e:
            print_error(f"ERROR: {str(e)[:50]}")
            return False
    
    human_delay()
    print_info(f"[3] {random_wait_message()}")
    short_delay()
    
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    withdraw_data = '0x2e1a7d4d' + hex(amount_wei)[2:].zfill(64)
    
    tx = {
        'from': account.address,
        'to': Web3.to_checksum_address(WUSDC_CONTRACT),
        'value': 0,
        'data': withdraw_data,
        'nonce': nonce,
        'gas': 60000,
        'gasPrice': gas_price,
        'chainId': CHAIN_ID
    }
    
    human_delay()
    print_info("[4] Sending transaction...")
    
    try:
        signed = w3.eth.account.sign_transaction(tx, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        tx_hash_hex = tx_hash.hex()
        print_success(f"    TX: {tx_hash_hex}")
    except Exception as e:
        print_error(f"ERROR: {str(e)[:50]}")
        return False
    
    print_info("[5] Waiting for confirmation...")
    
    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        block = receipt['blockNumber']
        
        print_header("RESULT")
        
        if receipt['status'] == 1:
            print_success(f"Status: SUCCESS")
            print_success(f"Block: {block}")
            print(Fore.CYAN + Style.BRIGHT + f"Explorer: {EXPLORER_URL}/tx/{tx_hash_hex}")
            return True
        else:
            print_error("Status: FAILED")
            return False
    except Exception as e:
        print_error(f"ERROR: {str(e)[:50]}")
        return False