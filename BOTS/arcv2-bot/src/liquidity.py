import time
from web3 import Web3
from colorama import Fore, Style

from .config import (
    CHAIN_ID, EXPLORER_URL, LIQUIDITY_ROUTER, POOL_TOKEN, USDC_A_TOKEN, ERC20_ABI
)
from .utils import short_delay, human_delay, random_wait_message, print_header, print_info, print_success, print_error
from .wallet import get_token_balance, approve_token_generic

def get_lp_balance(w3, account):
    return get_token_balance(w3, account, POOL_TOKEN)

def approve_usdc_a(w3, account, amount_6dec):
    print_info("[*] Checking USDC.a approval...")
    short_delay()
    
    usdc_a = w3.eth.contract(address=Web3.to_checksum_address(USDC_A_TOKEN), abi=ERC20_ABI)
    allowance = usdc_a.functions.allowance(account.address, Web3.to_checksum_address(LIQUIDITY_ROUTER)).call()
    
    if allowance >= amount_6dec:
        print_success("    Already approved!")
        return True
    
    print_info("    Approving USDC.a...")
    human_delay()
    
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    
    approve_data = "0x095ea7b3"
    approve_data += LIQUIDITY_ROUTER[2:].lower().zfill(64)
    approve_data += "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    
    tx = {
        'from': account.address,
        'to': Web3.to_checksum_address(USDC_A_TOKEN),
        'value': 0,
        'data': approve_data,
        'nonce': nonce,
        'gas': 70000,
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
            print_success("    Approved!")
            return True
        else:
            print_error("    Approval failed!")
            return False
    except Exception as e:
        print_error(f"    ERROR: {str(e)[:50]}")
        return False

def approve_lp_token(w3, account, amount):
    print_info("[*] Checking LP token approval...")
    short_delay()
    
    lp_contract = w3.eth.contract(address=Web3.to_checksum_address(POOL_TOKEN), abi=ERC20_ABI)
    allowance = lp_contract.functions.allowance(account.address, Web3.to_checksum_address(LIQUIDITY_ROUTER)).call()
    
    if allowance >= amount:
        print_success("    Already approved!")
        return True
    
    print_info("    Approving LP token...")
    human_delay()
    
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    
    approve_data = "0x095ea7b3"
    approve_data += LIQUIDITY_ROUTER[2:].lower().zfill(64)
    approve_data += "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    
    tx = {
        'from': account.address,
        'to': Web3.to_checksum_address(POOL_TOKEN),
        'value': 0,
        'data': approve_data,
        'nonce': nonce,
        'gas': 70000,
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
            print_success("    Approved!")
            return True
        else:
            print_error("    Approval failed!")
            return False
    except Exception as e:
        print_error(f"    ERROR: {str(e)[:50]}")
        return False

def add_liquidity(w3, account, token_amount):
    print_header(f"ADD LIQUIDITY: {token_amount} USDC.a")
    
    # Convert to 6 decimals (USDC.a has 6 decimals)
    token_amount_6dec = int(token_amount * 10**6)
    
    # Execution fee in 18 decimals (native USDC)
    execution_fee = token_amount * 2
    execution_fee_wei = int(execution_fee * 10**18)
    
    # Minimum LP calculation
    min_lp_ratio = 985561450000
    min_lp = int(token_amount_6dec * min_lp_ratio)
    
    print_info(f"[0] Details:")
    print_info(f"    Amount: {token_amount} USDC.a ({token_amount_6dec} raw)")
    print_info(f"    Fee: {execution_fee} USDC")
    short_delay()
    
    print_info("[1] Checking balances...")
    
    balance = w3.eth.get_balance(account.address)
    balance_formatted = float(w3.from_wei(balance, 'ether'))
    print_success(f"    USDC (native): {balance_formatted:.6f}")
    
    usdc_a = w3.eth.contract(address=Web3.to_checksum_address(USDC_A_TOKEN), abi=ERC20_ABI)
    usdc_a_balance = usdc_a.functions.balanceOf(account.address).call()
    usdc_a_formatted = usdc_a_balance / 10**6
    print_success(f"    USDC.a: {usdc_a_formatted:.6f}")
    
    if balance_formatted < execution_fee:
        print_error(f"ERROR: Need {execution_fee} USDC for fee!")
        return False
    
    if usdc_a_balance < token_amount_6dec:
        print_error(f"ERROR: Need {token_amount} USDC.a!")
        return False
    
    human_delay()
    
    if not approve_usdc_a(w3, account, token_amount_6dec):
        return False
    
    human_delay()
    print_info(f"[2] {random_wait_message()}")
    short_delay()
    
    # Build calldata for addLiquidity
    # Function: addLiquidity(address pool, address token, uint256 amount, uint256 minAmount, uint256 minLpAmount, uint256 executionFee)
    calldata = "0xbc820125"  # addLiquidity selector
    calldata += POOL_TOKEN[2:].lower().zfill(64)  # pool address
    calldata += USDC_A_TOKEN[2:].lower().zfill(64)  # token address
    calldata += hex(token_amount_6dec)[2:].zfill(64)  # amount
    calldata += "0000000000000000000000000000000000000000000000000000000000000000"  # minAmount (0)
    calldata += hex(min_lp)[2:].zfill(64)  # minLpAmount
    calldata += hex(execution_fee_wei)[2:].zfill(64)  # executionFee
    
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    
    tx = {
        'from': account.address,
        'to': Web3.to_checksum_address(LIQUIDITY_ROUTER),
        'value': execution_fee_wei,
        'data': calldata,
        'nonce': nonce,
        'gas': 600000,  # Increased gas
        'gasPrice': gas_price,
        'chainId': CHAIN_ID
    }
    
    human_delay()
    print_info("[3] Sending transaction...")
    
    try:
        # Estimate gas first
        try:
            estimated_gas = w3.eth.estimate_gas(tx)
            tx['gas'] = int(estimated_gas * 1.3)  # Add 30% buffer
            print_info(f"    Estimated gas: {estimated_gas}")
        except Exception as e:
            print_warning(f"    Gas estimation failed: {str(e)[:30]}")
            tx['gas'] = 800000  # Use higher default
        
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
        gas_used = receipt['gasUsed']
        
        print_header("RESULT")
        
        if receipt['status'] == 1:
            print_success(f"Status: SUCCESS")
            print_success(f"Block: {block}")
            print_success(f"Gas Used: {gas_used}")
            print(Fore.CYAN + Style.BRIGHT + f"Explorer: {EXPLORER_URL}/tx/{tx_hash_hex}")
            return True
        else:
            print_error("Status: FAILED")
            print_error(f"Gas Used: {gas_used}")
            # Try to get revert reason
            try:
                tx_data = w3.eth.get_transaction(tx_hash)
                w3.eth.call({
                    'from': tx_data['from'],
                    'to': tx_data['to'],
                    'data': tx_data['input'],
                    'value': tx_data['value'],
                }, block - 1)
            except Exception as revert_e:
                print_error(f"Revert reason: {str(revert_e)[:100]}")
            return False
    except Exception as e:
        print_error(f"ERROR: {str(e)}")
        return False

def remove_liquidity(w3, account, lp_amount_float=None, wait_for_cooldown=True):
    print_header("REMOVE LIQUIDITY")
    
    print_info("[1] Checking LP balance...")
    short_delay()
    
    lp_balance = get_lp_balance(w3, account)
    lp_balance_formatted = lp_balance / 10**18
    print_success(f"    LP: {lp_balance_formatted:.18f}")
    
    if lp_balance == 0:
        print_error("ERROR: No LP tokens!")
        if wait_for_cooldown:
            print(Fore.YELLOW + Style.BRIGHT + "\n[!] Waiting 20 min for cooldown...")
            for remaining in range(1200, 0, -1):
                mins = remaining // 60
                secs = remaining % 60
                print(Fore.CYAN + Style.BRIGHT + f"    {mins:02d}:{secs:02d}    ", end='\r')
                time.sleep(1)
            print()
            lp_balance = get_lp_balance(w3, account)
            lp_balance_formatted = lp_balance / 10**18
            if lp_balance == 0:
                print_error("ERROR: Still no LP!")
                return False
        else:
            return False
    
    if lp_amount_float is None:
        lp_amount = lp_balance
        lp_amount_float = lp_balance_formatted
    else:
        lp_amount = int(lp_amount_float * 10**18)
        if lp_amount > lp_balance:
            print_error(f"ERROR: Insufficient LP!")
            return False
    
    print_info(f"    Removing: {lp_amount_float:.18f}")
    
    balance = w3.eth.get_balance(account.address)
    balance_formatted = float(w3.from_wei(balance, 'ether'))
    
    execution_fee = 0.2
    execution_fee_wei = int(execution_fee * 10**18)
    
    if balance_formatted < execution_fee:
        print_error(f"ERROR: Need {execution_fee} USDC for fee!")
        return False
    
    human_delay()
    
    if not approve_lp_token(w3, account, lp_amount):
        return False
    
    human_delay()
    print_info(f"[2] {random_wait_message()}")
    short_delay()
    
    # Calculate minimum output
    expected_usdc_a = (lp_amount / 10**18) * 0.984
    min_out = int(expected_usdc_a * 10**6)
    
    # Build calldata for removeLiquidity
    calldata = "0xf4f013b3"  # removeLiquidity selector
    calldata += POOL_TOKEN[2:].lower().zfill(64)  # pool
    calldata += USDC_A_TOKEN[2:].lower().zfill(64)  # token
    calldata += hex(lp_amount)[2:].zfill(64)  # lpAmount
    calldata += hex(min_out)[2:].zfill(64)  # minAmount
    calldata += account.address[2:].lower().zfill(64)  # receiver
    calldata += hex(execution_fee_wei)[2:].zfill(64)  # executionFee
    
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    
    tx = {
        'from': account.address,
        'to': Web3.to_checksum_address(LIQUIDITY_ROUTER),
        'value': execution_fee_wei,
        'data': calldata,
        'nonce': nonce,
        'gas': 600000,
        'gasPrice': gas_price,
        'chainId': CHAIN_ID
    }
    
    human_delay()
    print_info("[3] Sending transaction...")
    
    try:
        # Estimate gas
        try:
            estimated_gas = w3.eth.estimate_gas(tx)
            tx['gas'] = int(estimated_gas * 1.3)
            print_info(f"    Estimated gas: {estimated_gas}")
        except Exception as e:
            print_warning(f"    Gas estimation failed: {str(e)[:30]}")
            tx['gas'] = 800000
        
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
        gas_used = receipt['gasUsed']
        
        print_header("RESULT")
        
        if receipt['status'] == 1:
            print_success(f"Status: SUCCESS")
            print_success(f"Block: {block}")
            print_success(f"Gas Used: {gas_used}")
            print(Fore.CYAN + Style.BRIGHT + f"Explorer: {EXPLORER_URL}/tx/{tx_hash_hex}")
            return True
        else:
            print_error("Status: FAILED")
            print_error(f"Gas Used: {gas_used}")
            return False
    except Exception as e:
        print_error(f"ERROR: {str(e)}")
        return False