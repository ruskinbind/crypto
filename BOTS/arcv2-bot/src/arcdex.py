import time
import random
from web3 import Web3
from colorama import Fore, Style

from .config import (
    CHAIN_ID, EXPLORER_URL, ARCDEX_POOL, SWAPARC_POOL_V2, SWAPARC_LP_TOKEN,
    USDC_CONTRACT, EURC_TOKEN, SWPRC_TOKEN, ARCDEX_TOKENS, ERC20_ABI
)
from .utils import short_delay, human_delay, random_wait_message, print_header, print_info, print_success, print_error
from .wallet import get_token_balance, approve_token_generic

def get_eurc_balance(w3, account):
    return get_token_balance(w3, account, EURC_TOKEN)

def get_swprc_balance(w3, account):
    return get_token_balance(w3, account, SWPRC_TOKEN)

def get_swaparc_lp_balance(w3, account):
    return get_token_balance(w3, account, SWAPARC_LP_TOKEN)

def approve_token_for_arcdex(w3, account, token_address, token_symbol, amount):
    return approve_token_generic(w3, account, token_address, ARCDEX_POOL, token_symbol, amount)

def approve_token_for_swaparc_pool(w3, account, token_address, token_symbol, amount):
    return approve_token_generic(w3, account, token_address, SWAPARC_POOL_V2, token_symbol, amount)

def arcdex_swap(w3, account, from_token, to_token, amount):
    from_info = ARCDEX_TOKENS.get(from_token)
    to_info = ARCDEX_TOKENS.get(to_token)
    
    if not from_info or not to_info:
        print_error(f"ERROR: Invalid pair!")
        return False
    
    print_header(f"SWAPARCDEX: {amount} {from_token} -> {to_token}")
    
    amount_decimal = int(amount * 10**from_info["decimals"])
    
    print_info("[1] Checking balance...")
    
    token_contract = w3.eth.contract(address=Web3.to_checksum_address(from_info["address"]), abi=ERC20_ABI)
    token_balance = token_contract.functions.balanceOf(account.address).call()
    token_formatted = token_balance / 10**from_info["decimals"]
    print_success(f"    {from_token}: {token_formatted:.6f}")
    
    if token_balance < amount_decimal:
        print_error(f"ERROR: Insufficient {from_token}!")
        return False
    
    human_delay()
    print_info("[2] Approving...")
    
    if not approve_token_for_arcdex(w3, account, from_info["address"], from_token, amount_decimal):
        return False
    
    human_delay()
    print_info(f"[3] {random_wait_message()}")
    short_delay()
    
    calldata = "0x9d9892cd"
    calldata += hex(from_info["index"])[2:].zfill(64)
    calldata += hex(to_info["index"])[2:].zfill(64)
    calldata += hex(amount_decimal)[2:].zfill(64)
    
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    
    tx = {
        'from': account.address,
        'to': Web3.to_checksum_address(ARCDEX_POOL),
        'value': 0,
        'data': calldata,
        'nonce': nonce,
        'gas': 300000,
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
        print_error(f"ERROR: {str(e)}")
        return False
    
    print_info("[5] Waiting for confirmation...")
    
    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        block = receipt['blockNumber']
        
        print_header("RESULT")
        
        if receipt['status'] == 1:
            to_balance = get_token_balance(w3, account, to_info["address"])
            to_formatted = to_balance / 10**to_info["decimals"]
            
            print_success(f"Status: SUCCESS")
            print_success(f"Block: {block}")
            print_success(f"{to_token}: {to_formatted:.6f}")
            print(Fore.CYAN + Style.BRIGHT + f"Explorer: {EXPLORER_URL}/tx/{tx_hash_hex}")
            return True
        else:
            print_error("Status: FAILED")
            return False
    except Exception as e:
        print_error(f"ERROR: {str(e)}")
        return False

# Convenience functions
def swap_arcdex_usdc_to_eurc(w3, account, amount):
    return arcdex_swap(w3, account, "USDC", "EURC", amount)

def swap_arcdex_eurc_to_usdc(w3, account, amount):
    return arcdex_swap(w3, account, "EURC", "USDC", amount)

def swap_arcdex_usdc_to_swprc(w3, account, amount):
    return arcdex_swap(w3, account, "USDC", "SWPRC", amount)

def swap_arcdex_swprc_to_usdc(w3, account, amount):
    return arcdex_swap(w3, account, "SWPRC", "USDC", amount)

def swap_arcdex_eurc_to_swprc(w3, account, amount):
    return arcdex_swap(w3, account, "EURC", "SWPRC", amount)

def swap_arcdex_swprc_to_eurc(w3, account, amount):
    return arcdex_swap(w3, account, "SWPRC", "EURC", amount)

def swaparc_add_liquidity(w3, account, usdc_amount, eurc_amount):
    print_header(f"SWAPARCDEX ADD LIQUIDITY")
    
    usdc_amount_6dec = int(usdc_amount * 10**6)
    eurc_amount_6dec = int(eurc_amount * 10**6)
    
    print_info(f"[0] USDC: {usdc_amount} | EURC: {eurc_amount}")
    short_delay()
    
    print_info("[1] Checking balances...")
    
    usdc_contract = w3.eth.contract(address=Web3.to_checksum_address(USDC_CONTRACT), abi=ERC20_ABI)
    usdc_balance = usdc_contract.functions.balanceOf(account.address).call()
    print_success(f"    USDC: {usdc_balance / 10**6:.6f}")
    
    eurc_balance = get_eurc_balance(w3, account)
    print_success(f"    EURC: {eurc_balance / 10**6:.6f}")
    
    if usdc_balance < usdc_amount_6dec:
        print_error(f"ERROR: Insufficient USDC!")
        return False
    
    if eurc_balance < eurc_amount_6dec:
        print_error(f"ERROR: Insufficient EURC!")
        return False
    
    human_delay()
    print_info("[2] Approving tokens...")
    
    if not approve_token_for_swaparc_pool(w3, account, USDC_CONTRACT, "USDC", usdc_amount_6dec):
        return False
    
    human_delay()
    
    if not approve_token_for_swaparc_pool(w3, account, EURC_TOKEN, "EURC", eurc_amount_6dec):
        return False
    
    human_delay()
    print_info(f"[3] {random_wait_message()}")
    short_delay()
    
    calldata = "0x4de59aa3"
    calldata += "0000000000000000000000000000000000000000000000000000000000000020"
    calldata += "0000000000000000000000000000000000000000000000000000000000000002"
    calldata += hex(usdc_amount_6dec)[2:].zfill(64)
    calldata += hex(eurc_amount_6dec)[2:].zfill(64)
    
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    
    tx = {
        'from': account.address,
        'to': Web3.to_checksum_address(SWAPARC_POOL_V2),
        'value': 0,
        'data': calldata,
        'nonce': nonce,
        'gas': 350000,
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
        print_error(f"ERROR: {str(e)}")
        return False
    
    print_info("[5] Waiting for confirmation...")
    
    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        block = receipt['blockNumber']
        
        print_header("RESULT")
        
        if receipt['status'] == 1:
            slp_balance = get_swaparc_lp_balance(w3, account)
            print_success(f"Status: SUCCESS")
            print_success(f"Block: {block}")
            print_success(f"SLP: {slp_balance / 10**6:.6f}")
            print(Fore.CYAN + Style.BRIGHT + f"Explorer: {EXPLORER_URL}/tx/{tx_hash_hex}")
            return True
        else:
            print_error("Status: FAILED")
            return False
    except Exception as e:
        print_error(f"ERROR: {str(e)}")
        return False

def swaparc_remove_liquidity(w3, account, lp_amount=None):
    print_header("SWAPARCDEX REMOVE LIQUIDITY")
    
    print_info("[1] Checking SLP balance...")
    short_delay()
    
    slp_balance = get_swaparc_lp_balance(w3, account)
    slp_formatted = slp_balance / 10**6
    print_success(f"    SLP: {slp_formatted:.6f}")
    
    if slp_balance == 0:
        print_error("ERROR: No SLP tokens!")
        return False
    
    if lp_amount is None:
        lp_amount_raw = slp_balance
        lp_amount = slp_formatted
    else:
        lp_amount_raw = int(lp_amount * 10**6)
        if lp_amount_raw > slp_balance:
            print_error(f"ERROR: Insufficient SLP!")
            return False
    
    print_info(f"    Removing: {lp_amount:.6f}")
    
    human_delay()
    print_info(f"[2] {random_wait_message()}")
    short_delay()
    
    calldata = "0x9c8f9f23"
    calldata += hex(lp_amount_raw)[2:].zfill(64)
    
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    
    tx = {
        'from': account.address,
        'to': Web3.to_checksum_address(SWAPARC_POOL_V2),
        'value': 0,
        'data': calldata,
        'nonce': nonce,
        'gas': 300000,
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
        print_error(f"ERROR: {str(e)}")
        return False
    
    print_info("[4] Waiting for confirmation...")
    
    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        block = receipt['blockNumber']
        
        print_header("RESULT")
        
        if receipt['status'] == 1:
            usdc_contract = w3.eth.contract(address=Web3.to_checksum_address(USDC_CONTRACT), abi=ERC20_ABI)
            usdc_balance = usdc_contract.functions.balanceOf(account.address).call()
            eurc_balance = get_eurc_balance(w3, account)
            
            print_success(f"Status: SUCCESS")
            print_success(f"Block: {block}")
            print_success(f"USDC: {usdc_balance / 10**6:.6f}")
            print_success(f"EURC: {eurc_balance / 10**6:.6f}")
            print(Fore.CYAN + Style.BRIGHT + f"Explorer: {EXPLORER_URL}/tx/{tx_hash_hex}")
            return True
        else:
            print_error("Status: FAILED")
            return False
    except Exception as e:
        print_error(f"ERROR: {str(e)}")
        return False