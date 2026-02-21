import time
import random
from web3 import Web3
from colorama import Fore, Style

from .config import CHAIN_ID, WUSDC_CONTRACT, ROUTER_CONTRACT, EXPLORER_URL, SWAP_TOKENS
from .utils import short_delay, human_delay, random_wait_message, get_quote, print_header, print_info, print_success, print_error

def perform_single_swap(w3, account, token_key, amount):
    token_info = SWAP_TOKENS[token_key]
    token_out = token_info["address"]
    token_symbol = token_info["symbol"]
    token_decimals = token_info["decimals"]
    amount_wei = w3.to_wei(amount, 'ether')
    
    print_header(f"SWAP: {amount} USDC -> {token_symbol}")
    
    print_info("[1] Checking USDC balance...")
    short_delay()
    
    balance = w3.eth.get_balance(account.address)
    balance_formatted = float(w3.from_wei(balance, 'ether'))
    print_success(f"    USDC Balance: {balance_formatted:.6f}")
    
    if balance < amount_wei:
        print_error("ERROR: Insufficient USDC!")
        return False
    
    human_delay()
    print_info("[2] Getting quote...")
    short_delay()
    
    quote = get_quote(WUSDC_CONTRACT, token_out, amount_wei)
    if not quote or quote.get("code") != 0:
        print_error("ERROR: Failed to get quote!")
        return False
    
    quote_data = quote["data"]
    expected_out = int(quote_data["amountOut"])
    min_out = int(expected_out * 0.95)
    
    if token_decimals == 6:
        expected_formatted = expected_out / 1e6
    else:
        expected_formatted = expected_out / 1e18
    
    print_success(f"    Expected: {expected_formatted:.6f} {token_symbol}")
    
    human_delay()
    print_info(f"[3] {random_wait_message()}")
    short_delay()
    
    deadline = int(time.time()) + 1800
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    
    calldata = "0x04a5baf1"
    calldata += "00000000000000000000000000000000000000000000000000000000000000c0"
    calldata += token_out[2:].lower().zfill(64)
    calldata += hex(min_out)[2:].zfill(64)
    calldata += hex(expected_out)[2:].zfill(64)
    calldata += account.address[2:].lower().zfill(64)
    calldata += hex(deadline)[2:].zfill(64)
    calldata += "0000000000000000000000000000000000000000000000000000000000000001"
    calldata += "0000000000000000000000000000000000000000000000000000000000000020"
    calldata += "0000000000000000000000000000000000000000000000000000000000000001"
    calldata += WUSDC_CONTRACT[2:].lower().zfill(64)
    calldata += token_out[2:].lower().zfill(64)
    calldata += hex(amount_wei)[2:].zfill(64)
    calldata += "0000000000000000000000000000000000000000000000000000000000000000"
    calldata += "00000000000000000000000000000000000000000000000000000000000000c0"
    calldata += "0000000000000000000000000000000000000000000000000000000000000000"
    
    tx = {
        'from': account.address,
        'to': Web3.to_checksum_address(ROUTER_CONTRACT),
        'value': amount_wei,
        'data': calldata,
        'nonce': nonce,
        'gas': 400000,
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

def swap_all_tokens(w3, account, amount):
    print_header(f"SWAPPING {amount} USDC TO ALL TOKENS")
    print()
    
    total = len(SWAP_TOKENS)
    success = 0
    failed = 0
    
    for key, token in SWAP_TOKENS.items():
        print(Fore.MAGENTA + Style.BRIGHT + f"[{key}/{total}] Swapping to {token['symbol']}...")
        print()
        
        result = perform_single_swap(w3, account, key, amount)
        
        if result:
            success += 1
        else:
            failed += 1
        
        print()
        
        if key != str(total):
            wait_time = random.uniform(5, 10)
            print(Fore.YELLOW + Style.BRIGHT + f"Waiting {wait_time:.1f}s before next swap...")
            time.sleep(wait_time)
            print()
    
    print_header("ALL SWAPS COMPLETED")
    print_success(f"Success: {success}/{total}")
    print_error(f"Failed: {failed}/{total}")