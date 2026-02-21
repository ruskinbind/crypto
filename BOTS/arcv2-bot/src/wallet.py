import os
from web3 import Web3
from eth_account import Account
from colorama import Fore, Style

from .config import (
    RPC_URL, CHAIN_ID, WUSDC_CONTRACT, USDC_CONTRACT, USDC_A_TOKEN,
    POOL_TOKEN, EURC_TOKEN, SWPRC_TOKEN, SWAPARC_LP_TOKEN,
    WUSDC_ABI, ERC20_ABI
)

def load_private_keys():
    if not os.path.exists("pv.txt"):
        print(Fore.RED + Style.BRIGHT + "ERROR: pv.txt not found!")
        return []
    
    with open("pv.txt", "r") as f:
        lines = f.readlines()
    
    keys = []
    for line in lines:
        pk = line.strip()
        if not pk:
            continue
        if not pk.startswith("0x"):
            pk = "0x" + pk
        keys.append(pk)
        
    if not keys:
        print(Fore.RED + Style.BRIGHT + "ERROR: No private keys found in pv.txt!")
        return []
        
    return keys

def get_web3():
    return Web3(Web3.HTTPProvider(RPC_URL))

def get_account(pk):
    try:
        return Account.from_key(pk)
    except:
        return None

def get_all_balances(w3, account):
    """Get all token balances"""
    balances = {}
    
    # USDC (native)
    balances['usdc'] = w3.eth.get_balance(account.address)
    
    # WUSDC
    wusdc = w3.eth.contract(address=Web3.to_checksum_address(WUSDC_CONTRACT), abi=WUSDC_ABI)
    balances['wusdc'] = wusdc.functions.balanceOf(account.address).call()
    
    # USDC.a
    usdc_a = w3.eth.contract(address=Web3.to_checksum_address(USDC_A_TOKEN), abi=ERC20_ABI)
    balances['usdc_a'] = usdc_a.functions.balanceOf(account.address).call()
    
    # LP Token
    lp = w3.eth.contract(address=Web3.to_checksum_address(POOL_TOKEN), abi=ERC20_ABI)
    balances['lp'] = lp.functions.balanceOf(account.address).call()
    
    # USDC Token
    usdc_token = w3.eth.contract(address=Web3.to_checksum_address(USDC_CONTRACT), abi=ERC20_ABI)
    balances['usdc_token'] = usdc_token.functions.balanceOf(account.address).call()
    
    # EURC
    eurc = w3.eth.contract(address=Web3.to_checksum_address(EURC_TOKEN), abi=ERC20_ABI)
    balances['eurc'] = eurc.functions.balanceOf(account.address).call()
    
    # SWPRC
    swprc = w3.eth.contract(address=Web3.to_checksum_address(SWPRC_TOKEN), abi=ERC20_ABI)
    balances['swprc'] = swprc.functions.balanceOf(account.address).call()
    
    # SLP
    slp = w3.eth.contract(address=Web3.to_checksum_address(SWAPARC_LP_TOKEN), abi=ERC20_ABI)
    balances['slp'] = slp.functions.balanceOf(account.address).call()
    
    return balances

def get_token_balance(w3, account, token_address):
    contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
    return contract.functions.balanceOf(account.address).call()

def approve_token_generic(w3, account, token_address, spender_address, token_symbol, amount):
    from .utils import short_delay, human_delay, print_info, print_success, print_error
    
    print_info(f"    Checking {token_symbol} approval...")
    short_delay()
    
    token_contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
    allowance = token_contract.functions.allowance(account.address, Web3.to_checksum_address(spender_address)).call()
    
    if allowance >= amount:
        print_success(f"    {token_symbol} already approved!")
        return True
    
    print_info(f"    Approving {token_symbol}...")
    human_delay()
    
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    
    approve_data = "0x095ea7b3"
    approve_data += spender_address[2:].lower().zfill(64)
    approve_data += hex(amount)[2:].zfill(64)
    
    tx = {
        'from': account.address,
        'to': Web3.to_checksum_address(token_address),
        'value': 0,
        'data': approve_data,
        'nonce': nonce,
        'gas': 85000,
        'gasPrice': gas_price,
        'chainId': CHAIN_ID
    }
    
    try:
        signed = w3.eth.account.sign_transaction(tx, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        tx_hash_hex = tx_hash.hex()
        print_success(f"    Approve TX: {tx_hash_hex}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt['status'] == 1:
            print_success(f"    {token_symbol} Approved!")
            return True
        else:
            print_error("    Approval failed!")
            return False
    except Exception as e:
        print_error(f"    ERROR: {str(e)[:50]}")
        return False