import time
import random
from web3 import Web3
from colorama import Fore, Style

from .config import CHAIN_ID, EXPLORER_URL, NFT_CONTRACTS
from .utils import short_delay, human_delay, random_wait_message, print_header, print_info, print_success, print_error

def mint_nft(w3, account, nft_key):
    nft_info = NFT_CONTRACTS.get(nft_key)
    if not nft_info:
        print_error("ERROR: Invalid NFT!")
        return False
    
    print_header(f"MINT NFT: {nft_info['name']}")
    
    price = nft_info['price']
    price_wei = int(nft_info['price_wei'], 16)
    
    print_info(f"[0] NFT: {nft_info['name']}")
    print_info(f"    Price: {price} USDC")
    short_delay()
    
    print_info("[1] Checking balance...")
    
    balance = w3.eth.get_balance(account.address)
    balance_formatted = float(w3.from_wei(balance, 'ether'))
    print_success(f"    USDC: {balance_formatted:.6f}")
    
    if price > 0 and balance < price_wei:
        print_error(f"ERROR: Need {price} USDC!")
        return False
    
    human_delay()
    print_info(f"[2] {random_wait_message()}")
    short_delay()
    
    # Build claim calldata
    calldata = "0x84bb1e42"
    calldata += account.address[2:].lower().zfill(64)
    calldata += "0000000000000000000000000000000000000000000000000000000000000001"
    calldata += "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee".zfill(64)
    calldata += hex(price_wei)[2:].zfill(64)
    calldata += "00000000000000000000000000000000000000000000000000000000000000c0"
    calldata += "0000000000000000000000000000000000000000000000000000000000000160"
    calldata += "0000000000000000000000000000000000000000000000000000000000000080"
    calldata += "0000000000000000000000000000000000000000000000000000000000000000"
    calldata += "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    calldata += "0000000000000000000000000000000000000000000000000000000000000000"
    calldata += "0000000000000000000000000000000000000000000000000000000000000000"
    calldata += "0000000000000000000000000000000000000000000000000000000000000000"
    
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    
    tx = {
        'from': account.address,
        'to': Web3.to_checksum_address(nft_info['address']),
        'value': price_wei,
        'data': calldata,
        'nonce': nonce,
        'gas': 250000,
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
            print_success(f"Status: SUCCESS")
            print_success(f"Block: {block}")
            print_success(f"NFT: {nft_info['name']} MINTED!")
            print(Fore.CYAN + Style.BRIGHT + f"Explorer: {EXPLORER_URL}/tx/{tx_hash_hex}")
            return True
        else:
            print_error("Status: FAILED")
            return False
    except Exception as e:
        print_error(f"ERROR: {str(e)}")
        return False

def mint_all_nfts(w3, account):
    print_header("MINT ALL NFTs")
    print()
    
    total = len(NFT_CONTRACTS)
    success = 0
    failed = 0
    
    for idx, (key, nft) in enumerate(NFT_CONTRACTS.items(), 1):
        print(Fore.MAGENTA + Style.BRIGHT + f"[{idx}/{total}] Minting {nft['name']}...")
        print()
        
        result = mint_nft(w3, account, key)
        
        if result:
            success += 1
        else:
            failed += 1
        
        print()
        
        if idx < total:
            wait_time = random.uniform(5, 10)
            print(Fore.YELLOW + Style.BRIGHT + f"Waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
            print()
    
    print_header("ALL NFTs COMPLETED")
    print_success(f"Success: {success}/{total}")
    print_error(f"Failed: {failed}/{total}")