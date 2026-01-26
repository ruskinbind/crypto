import os
import sys
import time
import random
import requests
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

# Bold Colors
class Colors:
    RED = '\033[1;91m'
    GREEN = '\033[1;92m'
    YELLOW = '\033[1;93m'
    BLUE = '\033[1;94m'
    MAGENTA = '\033[1;95m'
    CYAN = '\033[1;96m'
    WHITE = '\033[1;97m'
    RESET = '\033[0m'

# Constants
RPC_URL = "https://atlantic.dplabs-internal.com/"
API_BASE = "https://nftapi.aquaflux.pro/api/v1"
CHAIN_ID = 688689
SWAP_ROUTER = "0x857ebd1558198d4153a559338b6c08f79456b51b"
POSITION_MANAGER = "0x1d54de652e089e35653f3e20b2e22809055fd094"
SPLIT_COMBINE_CONTRACT = "0x62fdbc600e8badf8127e6298dd12b961edf08b5f"

# Staking Contract
STAKING_CONTRACT = "0x3eaef8f467059915a6eeb985a0d08de063ab16f9"

# Asset ID for Private Credit
PRIVATE_CREDIT_ASSET_ID = "0x8b79ddf5ff2f0db54884b06a0b748a687abe7eb723e676eac22a5a811e9312ae"

# Split/Combine Token addresses
SPLIT_COMBINE_TOKENS = {
    "PCT": "0x4f848d61b35033619ce558a2fce8447cedd38d0d",
    "P-PCT": "0x1f9a5b9dc6e237cfd37864b6eb982a35a9deaebf",
    "C-PCT": "0x38db6433f57a6701a18fabccf738212af6d8ca42",
    "S-PCT": "0xc1cf3cf3a86807e8319c0ab1754413c854ab5b7d"
}

# Wrap/Unwrap Token addresses
WRAP_TOKENS = {
    "PCT": "0x4f848d61b35033619ce558a2fce8447cedd38d0d",
    "AQ-PCT": "0x62fdbc600e8badf8127e6298dd12b961edf08b5f"
}

# All Swap pairs with pool addresses
SWAP_PAIRS = {
    "USDC-CPCT": {
        "name": "USDC -> C-PCT 31MAR2026",
        "tokenIn": "0xb691f00682feef63bc73f41c380ff648d73c6a2c",
        "tokenOut": "0x38db6433f57a6701a18fabccf738212af6d8ca42",
        "pool": "0x2089c8f5434ebba2b233943bbe9846cfc88b25a8",
        "fee": 500,
        "decimals": 6
    },
    "USDC-SPCT": {
        "name": "USDC -> S-PCT 31MAR2026",
        "tokenIn": "0xb691f00682feef63bc73f41c380ff648d73c6a2c",
        "tokenOut": "0xc1cf3cf3a86807e8319c0ab1754413c854ab5b7d",
        "pool": "0xeb52adfda65bf62887f463b79742adaa7600c3eb",
        "fee": 500,
        "decimals": 6
    },
    "USDC-SSPCT": {
        "name": "USDC -> SS-PCT-10JAN2026",
        "tokenIn": "0xb691f00682feef63bc73f41c380ff648d73c6a2c",
        "tokenOut": "0x10386be3d18b32a26c13894b147261e09f900e98",
        "pool": "0x7a573fdb1b1e63ed539a58a71b92f8234045311a",
        "fee": 500,
        "decimals": 6
    }
}

# Liquidity Pools - Updated with both pools
LIQUIDITY_POOLS = {
    "PPCT-USDC": {
        "name": "P-PCT / USDC",
        "token0": "0x1f9a5b9dc6e237cfd37864b6eb982a35a9deaebf",
        "token1": "0xb691f00682feef63bc73f41c380ff648d73c6a2c",
        "token0_name": "P-PCT",
        "token1_name": "USDC",
        "token0_decimals": 18,
        "token1_decimals": 6,
        "fee": 500,
        "tickLower": -276320,
        "tickUpper": -260230,
        "pool": "0x7d060eec3a7f5203881cb7ebb50a9e0e2c011226",
        "default_amount": 1.48
    },
    "CPCT-USDC": {
        "name": "C-PCT / USDC",
        "token0": "0x38db6433f57a6701a18fabccf738212af6d8ca42",
        "token1": "0xb691f00682feef63bc73f41c380ff648d73c6a2c",
        "token0_name": "C-PCT",
        "token1_name": "USDC",
        "token0_decimals": 18,
        "token1_decimals": 6,
        "fee": 500,
        "tickLower": -276320,  # 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffbc8a0
        "tickUpper": -248600,  # 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc34e8
        "pool": "0x2089c8f5434ebba2b233943bbe9846cfc88b25a8",
        "default_amount": 1.0
    }
}

# ABIs
ERC20_ABI = [
    {"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]

SWAP_ROUTER_ABI = [
    {"inputs":[{"components":[{"name":"tokenIn","type":"address"},{"name":"tokenOut","type":"address"},{"name":"fee","type":"uint24"},{"name":"recipient","type":"address"},{"name":"deadline","type":"uint256"},{"name":"amountIn","type":"uint256"},{"name":"amountOutMinimum","type":"uint256"},{"name":"sqrtPriceLimitX96","type":"uint160"}],"name":"params","type":"tuple"}],"name":"exactInputSingle","outputs":[{"name":"amountOut","type":"uint256"}],"stateMutability":"payable","type":"function"}
]

POSITION_MANAGER_ABI = [
    {"inputs":[{"components":[{"name":"token0","type":"address"},{"name":"token1","type":"address"},{"name":"fee","type":"uint24"},{"name":"tickLower","type":"int24"},{"name":"tickUpper","type":"int24"},{"name":"amount0Desired","type":"uint256"},{"name":"amount1Desired","type":"uint256"},{"name":"amount0Min","type":"uint256"},{"name":"amount1Min","type":"uint256"},{"name":"recipient","type":"address"},{"name":"deadline","type":"uint256"}],"name":"params","type":"tuple"}],"name":"mint","outputs":[{"name":"tokenId","type":"uint256"},{"name":"liquidity","type":"uint128"},{"name":"amount0","type":"uint256"},{"name":"amount1","type":"uint256"}],"stateMutability":"payable","type":"function"}
]

# Staking ABI
STAKING_ABI = [
    {"inputs":[{"name":"amount","type":"uint256"}],"name":"stake","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"name":"claimReward","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"account","type":"address"}],"name":"stakedBalance","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"account","type":"address"}],"name":"earned","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    print(f"{Colors.CYAN}========================================{Colors.RESET}")
    print(f"{Colors.GREEN}         AQUAFLUX x PHAROS TESTNET BOT          {Colors.RESET}")
    print(f"{Colors.YELLOW}         Created by Kazuha VIP ONLY       {Colors.RESET}")
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
        sys.exit(1)

def get_wallet_address(private_key):
    account = Account.from_key(private_key)
    return account.address

def sign_message(private_key, message):
    account = Account.from_key(private_key)
    message_encoded = encode_defunct(text=message)
    signed = account.sign_message(message_encoded)
    return signed.signature.hex()

def wallet_login(address, private_key):
    timestamp = int(time.time() * 1000)
    message = f"Sign in to AquaFlux Faucet with timestamp: {timestamp}"
    signature = sign_message(private_key, message)
    
    if not signature.startswith("0x"):
        signature = "0x" + signature
    
    payload = {
        "address": address,
        "message": message,
        "signature": signature
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Origin": "https://testnet.aquaflux.pro",
        "Referer": "https://testnet.aquaflux.pro/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.post(f"{API_BASE}/users/wallet-login", json=payload, headers=headers, timeout=30)
        data = response.json()
        
        if data.get("status") == "success":
            return data["data"]["accessToken"]
        else:
            return None
    except Exception as e:
        return None

def check_allowance(w3, token_address, owner, spender):
    contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
    allowance = contract.functions.allowance(
        Web3.to_checksum_address(owner),
        Web3.to_checksum_address(spender)
    ).call()
    return allowance

def approve_token(w3, private_key, address, token_address, spender, token_name="Token"):
    contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
    
    max_amount = 2**256 - 1
    
    try:
        nonce = w3.eth.get_transaction_count(address)
        
        tx = contract.functions.approve(
            Web3.to_checksum_address(spender),
            max_amount
        ).build_transaction({
            'from': address,
            'gas': 60000,
            'maxFeePerGas': w3.to_wei(1, 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei(1, 'gwei'),
            'nonce': nonce,
            'chainId': CHAIN_ID
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"{Colors.BLUE}[TX] Approve {token_name} Hash: {tx_hash.hex()}{Colors.RESET}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            print(f"{Colors.GREEN}[SUCCESS] {token_name} Approval successful!{Colors.RESET}")
            return True
        return False
        
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Approve failed: {str(e)}{Colors.RESET}")
        return False

def get_token_balance(w3, token_address, wallet_address, decimals=18):
    contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
    balance = contract.functions.balanceOf(Web3.to_checksum_address(wallet_address)).call()
    return balance / (10 ** decimals)

def stake_spct(w3, private_key, address, amount):
    """Stake S-PCT tokens"""
    print(f"{Colors.MAGENTA}{'='*50}{Colors.RESET}")
    print(f"{Colors.CYAN}[STAKE] S-PCT 31MAR2026{Colors.RESET}")
    print(f"{Colors.WHITE}[AMOUNT] {amount} S-PCT{Colors.RESET}")
    
    spct_address = SPLIT_COMBINE_TOKENS["S-PCT"]
    spct_balance = get_token_balance(w3, spct_address, address, 18)
    
    if spct_balance < amount:
        print(f"{Colors.RED}[ERROR] Insufficient S-PCT balance!{Colors.RESET}")
        print(f"{Colors.RED}[INFO] You have: {spct_balance:.4f}, Need: {amount}{Colors.RESET}")
        return False
    
    amount_wei = int(amount * (10 ** 18))
    
    # Step 1: Check and approve
    print(f"\n{Colors.YELLOW}[STEP 1/2] Checking S-PCT approval...{Colors.RESET}")
    
    current_allowance = check_allowance(w3, spct_address, address, STAKING_CONTRACT)
    
    if current_allowance < amount_wei:
        print(f"{Colors.YELLOW}[INFO] Approving S-PCT for Staking contract...{Colors.RESET}")
        if not approve_token(w3, private_key, address, spct_address, STAKING_CONTRACT, "S-PCT"):
            print(f"{Colors.RED}[ERROR] Approval failed{Colors.RESET}")
            return False
        time.sleep(3)
    else:
        print(f"{Colors.GREEN}[INFO] S-PCT already approved{Colors.RESET}")
    
    # Step 2: Stake
    print(f"\n{Colors.YELLOW}[STEP 2/2] Executing stake...{Colors.RESET}")
    
    try:
        nonce = w3.eth.get_transaction_count(address)
        
        contract = w3.eth.contract(address=Web3.to_checksum_address(STAKING_CONTRACT), abi=STAKING_ABI)
        
        tx = contract.functions.stake(amount_wei).build_transaction({
            'from': address,
            'gas': 200000,
            'maxFeePerGas': w3.to_wei(1, 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei(1, 'gwei'),
            'nonce': nonce,
            'chainId': CHAIN_ID,
            'value': 0
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"{Colors.BLUE}[TX] Stake Hash: {tx_hash.hex()}{Colors.RESET}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            print(f"{Colors.GREEN}[SUCCESS] Staked {amount} S-PCT successfully!{Colors.RESET}")
            print(f"{Colors.CYAN}[EXPLORER] https://atlantic.pharosscan.xyz/tx/{tx_hash.hex()}{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}[FAILED] Stake failed{Colors.RESET}")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Stake failed: {str(e)}{Colors.RESET}")
        return False

def claim_staking_reward(w3, private_key, address):
    """Claim staking rewards (SS-PCT)"""
    print(f"{Colors.MAGENTA}{'='*50}{Colors.RESET}")
    print(f"{Colors.CYAN}[CLAIM REWARD] Staking Rewards{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW}[INFO] Claiming rewards...{Colors.RESET}")
    
    try:
        nonce = w3.eth.get_transaction_count(address)
        
        contract = w3.eth.contract(address=Web3.to_checksum_address(STAKING_CONTRACT), abi=STAKING_ABI)
        
        tx = contract.functions.claimReward().build_transaction({
            'from': address,
            'gas': 150000,
            'maxFeePerGas': w3.to_wei(1, 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei(1, 'gwei'),
            'nonce': nonce,
            'chainId': CHAIN_ID,
            'value': 0
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"{Colors.BLUE}[TX] Claim Reward Hash: {tx_hash.hex()}{Colors.RESET}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            print(f"{Colors.GREEN}[SUCCESS] Rewards claimed successfully!{Colors.RESET}")
            print(f"{Colors.GREEN}[INFO] You received SS-PCT-10JAN2026 tokens{Colors.RESET}")
            print(f"{Colors.CYAN}[EXPLORER] https://atlantic.pharosscan.xyz/tx/{tx_hash.hex()}{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}[FAILED] Claim reward failed{Colors.RESET}")
            return False
            
    except Exception as e:
        error_msg = str(e)
        if "no rewards" in error_msg.lower() or "nothing to claim" in error_msg.lower():
            print(f"{Colors.YELLOW}[INFO] No rewards available to claim yet{Colors.RESET}")
        else:
            print(f"{Colors.RED}[ERROR] Claim reward failed: {error_msg}{Colors.RESET}")
        return False

def swap_single_pair(w3, private_key, address, pair_key, amount, need_approval=True):
    pair = SWAP_PAIRS[pair_key]
    
    print(f"{Colors.MAGENTA}{'='*50}{Colors.RESET}")
    print(f"{Colors.CYAN}[SWAP] {pair['name']}{Colors.RESET}")
    print(f"{Colors.WHITE}[AMOUNT] {amount} USDC{Colors.RESET}")
    
    if need_approval:
        current_allowance = check_allowance(w3, pair["tokenIn"], address, SWAP_ROUTER)
        amount_in = int(amount * (10 ** pair["decimals"]))
        
        if current_allowance < amount_in:
            print(f"{Colors.YELLOW}[INFO] Approving token for swap...{Colors.RESET}")
            if not approve_token(w3, private_key, address, pair["tokenIn"], SWAP_ROUTER, "USDC"):
                return False
            time.sleep(3)
        else:
            print(f"{Colors.GREEN}[INFO] Already approved, skipping approval...{Colors.RESET}")
    
    print(f"{Colors.YELLOW}[INFO] Executing swap...{Colors.RESET}")
    
    contract = w3.eth.contract(address=Web3.to_checksum_address(SWAP_ROUTER), abi=SWAP_ROUTER_ABI)
    
    amount_in = int(amount * (10 ** pair["decimals"]))
    deadline = int(time.time()) + 1800
    
    params = (
        Web3.to_checksum_address(pair["tokenIn"]),
        Web3.to_checksum_address(pair["tokenOut"]),
        pair["fee"],
        address,
        deadline,
        amount_in,
        0,
        0
    )
    
    try:
        nonce = w3.eth.get_transaction_count(address)
        
        tx = contract.functions.exactInputSingle(params).build_transaction({
            'from': address,
            'gas': 200000,
            'maxFeePerGas': w3.to_wei(1, 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei(1, 'gwei'),
            'nonce': nonce,
            'chainId': CHAIN_ID,
            'value': 0
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"{Colors.BLUE}[TX] Swap Hash: {tx_hash.hex()}{Colors.RESET}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            print(f"{Colors.GREEN}[SUCCESS] Swap completed!{Colors.RESET}")
            print(f"{Colors.CYAN}[EXPLORER] https://atlantic.pharosscan.xyz/tx/{tx_hash.hex()}{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}[FAILED] Swap failed{Colors.RESET}")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Swap failed: {str(e)}{Colors.RESET}")
        return False

def swap_all_pairs(w3, private_key, address):
    clear_screen()
    print_banner()
    print(f"{Colors.GREEN}[AUTO SWAP] Starting all swaps...{Colors.RESET}")
    print()
    
    usdc_address = "0xb691f00682feef63bc73f41c380ff648d73c6a2c"
    current_allowance = check_allowance(w3, usdc_address, address, SWAP_ROUTER)
    
    if current_allowance < 10**18:
        print(f"{Colors.YELLOW}[INFO] First time - Approving USDC for swap router...{Colors.RESET}")
        if not approve_token(w3, private_key, address, usdc_address, SWAP_ROUTER, "USDC"):
            print(f"{Colors.RED}[ERROR] Approval failed, cannot proceed{Colors.RESET}")
            return
        time.sleep(3)
    else:
        print(f"{Colors.GREEN}[INFO] USDC already approved, proceeding with swaps...{Colors.RESET}")
    
    print()
    
    swap_order = [
        ("USDC-CPCT", random.randint(8, 12)),
        ("USDC-SPCT", random.randint(8, 12)),
        ("USDC-SSPCT", 1)
    ]
    
    successful = 0
    failed = 0
    
    for i, (pair_key, amount) in enumerate(swap_order):
        pair = SWAP_PAIRS[pair_key]
        
        print(f"\n{Colors.WHITE}[{i+1}/3] Processing: {pair['name']}{Colors.RESET}")
        
        result = swap_single_pair(w3, private_key, address, pair_key, amount, need_approval=False)
        
        if result:
            successful += 1
        else:
            failed += 1
        
        if i < len(swap_order) - 1:
            wait_time = random.randint(3, 6)
            print(f"{Colors.YELLOW}[WAIT] Waiting {wait_time} seconds before next swap...{Colors.RESET}")
            time.sleep(wait_time)
    
    print()
    print(f"{Colors.MAGENTA}{'='*50}{Colors.RESET}")
    print(f"{Colors.GREEN}[SUMMARY] Swaps completed!{Colors.RESET}")
    print(f"{Colors.GREEN}[SUCCESS] {successful} swaps{Colors.RESET}")
    if failed > 0:
        print(f"{Colors.RED}[FAILED] {failed} swaps{Colors.RESET}")
    print(f"{Colors.MAGENTA}{'='*50}{Colors.RESET}")

def add_liquidity(w3, private_key, address, pool_key):
    pool = LIQUIDITY_POOLS[pool_key]
    
    # For C-PCT pool, use 1 token
    if pool_key == "CPCT-USDC":
        amount0_wei = int(1 * (10 ** 18))  # 1 C-PCT
        amount0_display = 1.0
    else:
        amount0_wei = 1479999999999317743
        amount0_display = amount0_wei / (10 ** 18)
    
    print(f"{Colors.MAGENTA}{'='*50}{Colors.RESET}")
    print(f"{Colors.CYAN}[ADD LIQUIDITY] {pool['name']}{Colors.RESET}")
    print(f"{Colors.WHITE}[AMOUNT] {amount0_display:.2f} {pool['token0_name']}{Colors.RESET}")
    
    current_balance = get_token_balance(w3, pool["token0"], address, 18)
    if current_balance < amount0_display:
        print(f"{Colors.RED}[ERROR] Insufficient {pool['token0_name']} balance!{Colors.RESET}")
        print(f"{Colors.RED}[INFO] You have: {current_balance:.4f}, Need: {amount0_display:.2f}{Colors.RESET}")
        return False
    
    print(f"\n{Colors.YELLOW}[STEP 1/2] Checking {pool['token0_name']} approval...{Colors.RESET}")
    
    current_allowance = check_allowance(w3, pool["token0"], address, POSITION_MANAGER)
    
    if current_allowance < amount0_wei:
        print(f"{Colors.YELLOW}[INFO] Approving {pool['token0_name']} for Position Manager...{Colors.RESET}")
        if not approve_token(w3, private_key, address, pool["token0"], POSITION_MANAGER, pool['token0_name']):
            print(f"{Colors.RED}[ERROR] Approval failed{Colors.RESET}")
            return False
        time.sleep(3)
    else:
        print(f"{Colors.GREEN}[INFO] {pool['token0_name']} already approved{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW}[STEP 2/2] Adding liquidity...{Colors.RESET}")
    
    contract = w3.eth.contract(address=Web3.to_checksum_address(POSITION_MANAGER), abi=POSITION_MANAGER_ABI)
    
    deadline = int(time.time()) + 1800
    amount0_min = int(amount0_wei * 0.995)  # 0.5% slippage
    
    params = (
        Web3.to_checksum_address(pool["token0"]),
        Web3.to_checksum_address(pool["token1"]),
        pool["fee"],
        pool["tickLower"],
        pool["tickUpper"],
        amount0_wei,
        0,
        amount0_min,
        0,
        address,
        deadline
    )
    
    try:
        nonce = w3.eth.get_transaction_count(address)
        
        tx = contract.functions.mint(params).build_transaction({
            'from': address,
            'gas': 500000,
            'maxFeePerGas': w3.to_wei(1, 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei(1, 'gwei'),
            'nonce': nonce,
            'chainId': CHAIN_ID,
            'value': 0
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"{Colors.BLUE}[TX] Add Liquidity Hash: {tx_hash.hex()}{Colors.RESET}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            print(f"{Colors.GREEN}[SUCCESS] Liquidity added successfully!{Colors.RESET}")
            print(f"{Colors.CYAN}[EXPLORER] https://atlantic.pharosscan.xyz/tx/{tx_hash.hex()}{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}[FAILED] Add liquidity failed{Colors.RESET}")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Add liquidity failed: {str(e)}{Colors.RESET}")
        return False

def split_tokens(w3, private_key, address, amount):
    print(f"{Colors.MAGENTA}{'='*50}{Colors.RESET}")
    print(f"{Colors.CYAN}[SPLIT] Private Credit (RWA -> P + C + S){Colors.RESET}")
    print(f"{Colors.WHITE}[AMOUNT] {amount} PCT{Colors.RESET}")
    
    pct_balance = get_token_balance(w3, SPLIT_COMBINE_TOKENS["PCT"], address, 18)
    if pct_balance < amount:
        print(f"{Colors.RED}[ERROR] Insufficient PCT balance!{Colors.RESET}")
        print(f"{Colors.RED}[INFO] You have: {pct_balance:.4f}, Need: {amount}{Colors.RESET}")
        return False
    
    amount_wei = int(amount * (10 ** 18))
    
    print(f"\n{Colors.YELLOW}[STEP 1/2] Checking PCT approval...{Colors.RESET}")
    
    current_allowance = check_allowance(w3, SPLIT_COMBINE_TOKENS["PCT"], address, SPLIT_COMBINE_CONTRACT)
    
    if current_allowance < amount_wei:
        print(f"{Colors.YELLOW}[INFO] Approving PCT for Split/Combine contract...{Colors.RESET}")
        if not approve_token(w3, private_key, address, SPLIT_COMBINE_TOKENS["PCT"], SPLIT_COMBINE_CONTRACT, "PCT"):
            print(f"{Colors.RED}[ERROR] Approval failed{Colors.RESET}")
            return False
        time.sleep(3)
    else:
        print(f"{Colors.GREEN}[INFO] PCT already approved{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW}[STEP 2/2] Executing split...{Colors.RESET}")
    
    try:
        nonce = w3.eth.get_transaction_count(address)
        
        method_id = "0xef272020"
        asset_id = PRIVATE_CREDIT_ASSET_ID[2:]
        amount_hex = hex(amount_wei)[2:].zfill(64)
        
        data = method_id + asset_id + amount_hex
        
        tx = {
            'from': address,
            'to': Web3.to_checksum_address(SPLIT_COMBINE_CONTRACT),
            'gas': 350000,
            'maxFeePerGas': w3.to_wei(1, 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei(1, 'gwei'),
            'nonce': nonce,
            'chainId': CHAIN_ID,
            'value': 0,
            'data': data
        }
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"{Colors.BLUE}[TX] Split Hash: {tx_hash.hex()}{Colors.RESET}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            print(f"{Colors.GREEN}[SUCCESS] Split completed!{Colors.RESET}")
            print(f"{Colors.GREEN}[INFO] You received:{Colors.RESET}")
            print(f"{Colors.WHITE}  - {amount} P-PCT{Colors.RESET}")
            print(f"{Colors.WHITE}  - {amount} C-PCT{Colors.RESET}")
            print(f"{Colors.WHITE}  - {amount} S-PCT{Colors.RESET}")
            print(f"{Colors.CYAN}[EXPLORER] https://atlantic.pharosscan.xyz/tx/{tx_hash.hex()}{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}[FAILED] Split failed{Colors.RESET}")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Split failed: {str(e)}{Colors.RESET}")
        return False

def combine_tokens(w3, private_key, address, amount):
    print(f"{Colors.MAGENTA}{'='*50}{Colors.RESET}")
    print(f"{Colors.CYAN}[COMBINE] (P + C + S -> RWA){Colors.RESET}")
    print(f"{Colors.WHITE}[AMOUNT] {amount} of each token{Colors.RESET}")
    
    ppct_balance = get_token_balance(w3, SPLIT_COMBINE_TOKENS["P-PCT"], address, 18)
    cpct_balance = get_token_balance(w3, SPLIT_COMBINE_TOKENS["C-PCT"], address, 18)
    spct_balance = get_token_balance(w3, SPLIT_COMBINE_TOKENS["S-PCT"], address, 18)
    
    print(f"\n{Colors.WHITE}Your balances:{Colors.RESET}")
    print(f"{Colors.WHITE}  P-PCT: {ppct_balance:.4f}{Colors.RESET}")
    print(f"{Colors.WHITE}  C-PCT: {cpct_balance:.4f}{Colors.RESET}")
    print(f"{Colors.WHITE}  S-PCT: {spct_balance:.4f}{Colors.RESET}")
    
    if ppct_balance < amount or cpct_balance < amount or spct_balance < amount:
        print(f"{Colors.RED}[ERROR] Insufficient balance! Need {amount} of each token{Colors.RESET}")
        return False
    
    amount_wei = int(amount * (10 ** 18))
    
    print(f"\n{Colors.YELLOW}[STEP 1/4] Checking P-PCT approval...{Colors.RESET}")
    current_allowance = check_allowance(w3, SPLIT_COMBINE_TOKENS["P-PCT"], address, SPLIT_COMBINE_CONTRACT)
    if current_allowance < amount_wei:
        print(f"{Colors.YELLOW}[INFO] Approving P-PCT...{Colors.RESET}")
        if not approve_token(w3, private_key, address, SPLIT_COMBINE_TOKENS["P-PCT"], SPLIT_COMBINE_CONTRACT, "P-PCT"):
            return False
        time.sleep(3)
    else:
        print(f"{Colors.GREEN}[INFO] P-PCT already approved{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW}[STEP 2/4] Checking C-PCT approval...{Colors.RESET}")
    current_allowance = check_allowance(w3, SPLIT_COMBINE_TOKENS["C-PCT"], address, SPLIT_COMBINE_CONTRACT)
    if current_allowance < amount_wei:
        print(f"{Colors.YELLOW}[INFO] Approving C-PCT...{Colors.RESET}")
        if not approve_token(w3, private_key, address, SPLIT_COMBINE_TOKENS["C-PCT"], SPLIT_COMBINE_CONTRACT, "C-PCT"):
            return False
        time.sleep(3)
    else:
        print(f"{Colors.GREEN}[INFO] C-PCT already approved{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW}[STEP 3/4] Checking S-PCT approval...{Colors.RESET}")
    current_allowance = check_allowance(w3, SPLIT_COMBINE_TOKENS["S-PCT"], address, SPLIT_COMBINE_CONTRACT)
    if current_allowance < amount_wei:
        print(f"{Colors.YELLOW}[INFO] Approving S-PCT...{Colors.RESET}")
        if not approve_token(w3, private_key, address, SPLIT_COMBINE_TOKENS["S-PCT"], SPLIT_COMBINE_CONTRACT, "S-PCT"):
            return False
        time.sleep(3)
    else:
        print(f"{Colors.GREEN}[INFO] S-PCT already approved{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW}[STEP 4/4] Executing combine...{Colors.RESET}")
    
    try:
        nonce = w3.eth.get_transaction_count(address)
        
        method_id = "0x66fc6e9a"
        asset_id = PRIVATE_CREDIT_ASSET_ID[2:]
        amount_hex = hex(amount_wei)[2:].zfill(64)
        
        data = method_id + asset_id + amount_hex
        
        tx = {
            'from': address,
            'to': Web3.to_checksum_address(SPLIT_COMBINE_CONTRACT),
            'gas': 350000,
            'maxFeePerGas': w3.to_wei(1, 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei(1, 'gwei'),
            'nonce': nonce,
            'chainId': CHAIN_ID,
            'value': 0,
            'data': data
        }
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"{Colors.BLUE}[TX] Combine Hash: {tx_hash.hex()}{Colors.RESET}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            received = amount * 0.996004
            print(f"{Colors.GREEN}[SUCCESS] Combine completed!{Colors.RESET}")
            print(f"{Colors.GREEN}[INFO] You burned:{Colors.RESET}")
            print(f"{Colors.WHITE}  - {amount} P-PCT{Colors.RESET}")
            print(f"{Colors.WHITE}  - {amount} C-PCT{Colors.RESET}")
            print(f"{Colors.WHITE}  - {amount} S-PCT{Colors.RESET}")
            print(f"{Colors.GREEN}[INFO] You received: ~{received:.4f} PCT (RWA){Colors.RESET}")
            print(f"{Colors.CYAN}[EXPLORER] https://atlantic.pharosscan.xyz/tx/{tx_hash.hex()}{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}[FAILED] Combine failed{Colors.RESET}")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Combine failed: {str(e)}{Colors.RESET}")
        return False

def wrap_tokens(w3, private_key, address, amount):
    print(f"{Colors.MAGENTA}{'='*50}{Colors.RESET}")
    print(f"{Colors.CYAN}[WRAP] PCT -> AQ-PCT{Colors.RESET}")
    print(f"{Colors.WHITE}[AMOUNT] {amount} PCT{Colors.RESET}")
    
    pct_balance = get_token_balance(w3, WRAP_TOKENS["PCT"], address, 18)
    if pct_balance < amount:
        print(f"{Colors.RED}[ERROR] Insufficient PCT balance!{Colors.RESET}")
        print(f"{Colors.RED}[INFO] You have: {pct_balance:.4f}, Need: {amount}{Colors.RESET}")
        return False
    
    amount_wei = int(amount * (10 ** 18))
    
    print(f"\n{Colors.YELLOW}[STEP 1/2] Checking PCT approval...{Colors.RESET}")
    
    current_allowance = check_allowance(w3, WRAP_TOKENS["PCT"], address, SPLIT_COMBINE_CONTRACT)
    
    if current_allowance < amount_wei:
        print(f"{Colors.YELLOW}[INFO] Approving PCT for Wrap contract...{Colors.RESET}")
        if not approve_token(w3, private_key, address, WRAP_TOKENS["PCT"], SPLIT_COMBINE_CONTRACT, "PCT"):
            print(f"{Colors.RED}[ERROR] Approval failed{Colors.RESET}")
            return False
        time.sleep(3)
    else:
        print(f"{Colors.GREEN}[INFO] PCT already approved{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW}[STEP 2/2] Executing wrap...{Colors.RESET}")
    
    try:
        nonce = w3.eth.get_transaction_count(address)
        
        method_id = "0xf616a549"
        asset_id = PRIVATE_CREDIT_ASSET_ID[2:]
        amount_hex = hex(amount_wei)[2:].zfill(64)
        
        data = method_id + asset_id + amount_hex
        
        tx = {
            'from': address,
            'to': Web3.to_checksum_address(SPLIT_COMBINE_CONTRACT),
            'gas': 200000,
            'maxFeePerGas': w3.to_wei(1, 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei(1, 'gwei'),
            'nonce': nonce,
            'chainId': CHAIN_ID,
            'value': 0,
            'data': data
        }
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"{Colors.BLUE}[TX] Wrap Hash: {tx_hash.hex()}{Colors.RESET}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            print(f"{Colors.GREEN}[SUCCESS] Wrap completed!{Colors.RESET}")
            print(f"{Colors.GREEN}[INFO] You sent: {amount} PCT{Colors.RESET}")
            print(f"{Colors.GREEN}[INFO] You received: {amount} AQ-PCT{Colors.RESET}")
            print(f"{Colors.CYAN}[EXPLORER] https://atlantic.pharosscan.xyz/tx/{tx_hash.hex()}{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}[FAILED] Wrap failed{Colors.RESET}")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Wrap failed: {str(e)}{Colors.RESET}")
        return False

def unwrap_tokens(w3, private_key, address, amount):
    print(f"{Colors.MAGENTA}{'='*50}{Colors.RESET}")
    print(f"{Colors.CYAN}[UNWRAP] AQ-PCT -> PCT{Colors.RESET}")
    print(f"{Colors.WHITE}[AMOUNT] {amount} AQ-PCT{Colors.RESET}")
    
    amount_wei = int(amount * (10 ** 18))
    
    print(f"\n{Colors.YELLOW}[STEP 1/1] Executing unwrap...{Colors.RESET}")
    
    try:
        nonce = w3.eth.get_transaction_count(address)
        
        method_id = "0x7a6631de"
        asset_id = PRIVATE_CREDIT_ASSET_ID[2:]
        amount_hex = hex(amount_wei)[2:].zfill(64)
        
        data = method_id + asset_id + amount_hex
        
        tx = {
            'from': address,
            'to': Web3.to_checksum_address(SPLIT_COMBINE_CONTRACT),
            'gas': 200000,
            'maxFeePerGas': w3.to_wei(1, 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei(1, 'gwei'),
            'nonce': nonce,
            'chainId': CHAIN_ID,
            'value': 0,
            'data': data
        }
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"{Colors.BLUE}[TX] Unwrap Hash: {tx_hash.hex()}{Colors.RESET}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            received = amount * 0.998
            print(f"{Colors.GREEN}[SUCCESS] Unwrap completed!{Colors.RESET}")
            print(f"{Colors.GREEN}[INFO] You sent: {amount} AQ-PCT{Colors.RESET}")
            print(f"{Colors.GREEN}[INFO] You received: ~{received:.4f} PCT (0.2% fee){Colors.RESET}")
            print(f"{Colors.CYAN}[EXPLORER] https://atlantic.pharosscan.xyz/tx/{tx_hash.hex()}{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}[FAILED] Unwrap failed{Colors.RESET}")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Unwrap failed: {str(e)}{Colors.RESET}")
        return False

def auto_wrap_unwrap(w3, private_key, address):
    clear_screen()
    print_banner()
    print(f"{Colors.GREEN}[AUTO WRAP/UNWRAP] Starting...{Colors.RESET}")
    print()
    
    pct_balance = get_token_balance(w3, WRAP_TOKENS["PCT"], address, 18)
    print(f"{Colors.WHITE}Your PCT Balance: {pct_balance:.4f}{Colors.RESET}")
    
    if pct_balance < 1:
        print(f"{Colors.RED}[ERROR] Insufficient PCT balance! Need at least 1 PCT{Colors.RESET}")
        return
    
    max_amount = min(5, int(pct_balance))
    amount = random.randint(1, max_amount)
    
    print(f"{Colors.YELLOW}[INFO] Selected amount: {amount} PCT{Colors.RESET}")
    print()
    
    print(f"{Colors.MAGENTA}[STEP 1/2] WRAPPING...{Colors.RESET}")
    wrap_result = wrap_tokens(w3, private_key, address, amount)
    
    if not wrap_result:
        print(f"{Colors.RED}[ERROR] Wrap failed, stopping auto process{Colors.RESET}")
        return
    
    wait_time = random.randint(3, 6)
    print(f"\n{Colors.YELLOW}[WAIT] Waiting {wait_time} seconds before unwrap...{Colors.RESET}")
    time.sleep(wait_time)
    
    print(f"\n{Colors.MAGENTA}[STEP 2/2] UNWRAPPING...{Colors.RESET}")
    unwrap_result = unwrap_tokens(w3, private_key, address, amount)
    
    print()
    print(f"{Colors.MAGENTA}{'='*50}{Colors.RESET}")
    if wrap_result and unwrap_result:
        print(f"{Colors.GREEN}[SUMMARY] Auto Wrap/Unwrap completed successfully!{Colors.RESET}")
    else:
        print(f"{Colors.RED}[SUMMARY] Auto Wrap/Unwrap completed with errors{Colors.RESET}")
    print(f"{Colors.MAGENTA}{'='*50}{Colors.RESET}")

def swap_menu(w3, private_key, address):
    clear_screen()
    print_banner()
    print(f"{Colors.GREEN}[SWAP MENU]{Colors.RESET}")
    print()
    print(f"{Colors.CYAN}1. Swap All Pairs (Auto - Random Amounts){Colors.RESET}")
    print(f"{Colors.CYAN}2. USDC -> C-PCT (Manual Amount){Colors.RESET}")
    print(f"{Colors.CYAN}3. USDC -> S-PCT (Manual Amount){Colors.RESET}")
    print(f"{Colors.CYAN}4. USDC -> SS-PCT (Manual Amount){Colors.RESET}")
    print(f"{Colors.CYAN}5. Back to Main Menu{Colors.RESET}")
    print()
    
    choice = input(f"{Colors.YELLOW}Select option: {Colors.RESET}")
    
    if choice == "1":
        swap_all_pairs(w3, private_key, address)
        print()
        input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
    elif choice == "2":
        try:
            amount = float(input(f"{Colors.CYAN}Enter USDC amount to swap: {Colors.RESET}"))
            swap_single_pair(w3, private_key, address, "USDC-CPCT", amount, need_approval=True)
        except ValueError:
            print(f"{Colors.RED}[ERROR] Invalid amount{Colors.RESET}")
        print()
        input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
    elif choice == "3":
        try:
            amount = float(input(f"{Colors.CYAN}Enter USDC amount to swap: {Colors.RESET}"))
            swap_single_pair(w3, private_key, address, "USDC-SPCT", amount, need_approval=True)
        except ValueError:
            print(f"{Colors.RED}[ERROR] Invalid amount{Colors.RESET}")
        print()
        input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
    elif choice == "4":
        try:
            amount = float(input(f"{Colors.CYAN}Enter USDC amount to swap: {Colors.RESET}"))
            swap_single_pair(w3, private_key, address, "USDC-SSPCT", amount, need_approval=True)
        except ValueError:
            print(f"{Colors.RED}[ERROR] Invalid amount{Colors.RESET}")
        print()
        input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
    elif choice == "5":
        return
    else:
        print(f"{Colors.RED}Invalid option{Colors.RESET}")
        time.sleep(1)

def liquidity_menu(w3, private_key, address):
    clear_screen()
    print_banner()
    print(f"{Colors.GREEN}[ADD LIQUIDITY]{Colors.RESET}")
    print()
    
    ppct_address = "0x1f9a5b9dc6e237cfd37864b6eb982a35a9deaebf"
    cpct_address = "0x38db6433f57a6701a18fabccf738212af6d8ca42"
    
    ppct_balance = get_token_balance(w3, ppct_address, address, 18)
    cpct_balance = get_token_balance(w3, cpct_address, address, 18)
    
    print(f"{Colors.WHITE}Your Balances:{Colors.RESET}")
    print(f"{Colors.WHITE}  P-PCT: {ppct_balance:.4f}{Colors.RESET}")
    print(f"{Colors.WHITE}  C-PCT: {cpct_balance:.4f}{Colors.RESET}")
    print()
    
    print(f"{Colors.CYAN}1. Add Liquidity P-PCT/USDC (1.48 P-PCT){Colors.RESET}")
    print(f"{Colors.CYAN}2. Add Liquidity C-PCT/USDC (1 C-PCT){Colors.RESET}")
    print(f"{Colors.CYAN}3. Back to Main Menu{Colors.RESET}")
    print()
    
    choice = input(f"{Colors.YELLOW}Select option: {Colors.RESET}")
    
    if choice == "1":
        if ppct_balance < 1.48:
            print(f"{Colors.RED}[ERROR] Insufficient P-PCT balance! Need at least 1.48 P-PCT{Colors.RESET}")
        else:
            add_liquidity(w3, private_key, address, "PPCT-USDC")
        print()
        input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
    elif choice == "2":
        if cpct_balance < 1:
            print(f"{Colors.RED}[ERROR] Insufficient C-PCT balance! Need at least 1 C-PCT{Colors.RESET}")
        else:
            add_liquidity(w3, private_key, address, "CPCT-USDC")
        print()
        input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
    elif choice == "3":
        return
    else:
        print(f"{Colors.RED}Invalid option{Colors.RESET}")
        time.sleep(1)

def split_combine_menu(w3, private_key, address):
    clear_screen()
    print_banner()
    print(f"{Colors.GREEN}[SPLIT / COMBINE]{Colors.RESET}")
    print()
    
    pct_balance = get_token_balance(w3, SPLIT_COMBINE_TOKENS["PCT"], address, 18)
    ppct_balance = get_token_balance(w3, SPLIT_COMBINE_TOKENS["P-PCT"], address, 18)
    cpct_balance = get_token_balance(w3, SPLIT_COMBINE_TOKENS["C-PCT"], address, 18)
    spct_balance = get_token_balance(w3, SPLIT_COMBINE_TOKENS["S-PCT"], address, 18)
    
    print(f"{Colors.WHITE}Your Balances:{Colors.RESET}")
    print(f"{Colors.WHITE}  PCT (RWA): {pct_balance:.4f}{Colors.RESET}")
    print(f"{Colors.WHITE}  P-PCT:     {ppct_balance:.4f}{Colors.RESET}")
    print(f"{Colors.WHITE}  C-PCT:     {cpct_balance:.4f}{Colors.RESET}")
    print(f"{Colors.WHITE}  S-PCT:     {spct_balance:.4f}{Colors.RESET}")
    print()
    
    print(f"{Colors.MAGENTA}Select Asset: Private Credit{Colors.RESET}")
    print()
    print(f"{Colors.CYAN}1. Split (RWA -> P + C + S){Colors.RESET}")
    print(f"{Colors.CYAN}2. Combine (P + C + S -> RWA){Colors.RESET}")
    print(f"{Colors.CYAN}3. Back to Main Menu{Colors.RESET}")
    print()
    
    choice = input(f"{Colors.YELLOW}Select option: {Colors.RESET}")
    
    if choice == "1":
        print()
        print(f"{Colors.WHITE}Available PCT: {pct_balance:.4f}{Colors.RESET}")
        try:
            amount = float(input(f"{Colors.CYAN}Enter PCT amount to split: {Colors.RESET}"))
            if amount <= 0:
                print(f"{Colors.RED}[ERROR] Amount must be greater than 0{Colors.RESET}")
            elif amount > pct_balance:
                print(f"{Colors.RED}[ERROR] Insufficient balance{Colors.RESET}")
            else:
                split_tokens(w3, private_key, address, amount)
        except ValueError:
            print(f"{Colors.RED}[ERROR] Invalid amount{Colors.RESET}")
        print()
        input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
        
    elif choice == "2":
        print()
        min_balance = min(ppct_balance, cpct_balance, spct_balance)
        print(f"{Colors.WHITE}Max combinable amount: {min_balance:.4f}{Colors.RESET}")
        try:
            amount = float(input(f"{Colors.CYAN}Enter amount to combine (each token): {Colors.RESET}"))
            if amount <= 0:
                print(f"{Colors.RED}[ERROR] Amount must be greater than 0{Colors.RESET}")
            elif amount > min_balance:
                print(f"{Colors.RED}[ERROR] Insufficient balance in one or more tokens{Colors.RESET}")
            else:
                combine_tokens(w3, private_key, address, amount)
        except ValueError:
            print(f"{Colors.RED}[ERROR] Invalid amount{Colors.RESET}")
        print()
        input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
        
    elif choice == "3":
        return
    else:
        print(f"{Colors.RED}Invalid option{Colors.RESET}")
        time.sleep(1)

def staking_menu(w3, private_key, address):
    clear_screen()
    print_banner()
    print(f"{Colors.GREEN}[STAKING MENU]{Colors.RESET}")
    print()
    
    spct_address = SPLIT_COMBINE_TOKENS["S-PCT"]
    spct_balance = get_token_balance(w3, spct_address, address, 18)
    
    print(f"{Colors.WHITE}Your S-PCT Balance: {spct_balance:.4f}{Colors.RESET}")
    print()
    
    print(f"{Colors.CYAN}1. Stake S-PCT{Colors.RESET}")
    print(f"{Colors.CYAN}2. Claim Rewards (SS-PCT){Colors.RESET}")
    print(f"{Colors.CYAN}3. Back to Main Menu{Colors.RESET}")
    print()
    
    choice = input(f"{Colors.YELLOW}Select option: {Colors.RESET}")
    
    if choice == "1":
        print()
        print(f"{Colors.WHITE}Available S-PCT: {spct_balance:.4f}{Colors.RESET}")
        try:
            amount = float(input(f"{Colors.CYAN}Enter S-PCT amount to stake: {Colors.RESET}"))
            if amount <= 0:
                print(f"{Colors.RED}[ERROR] Amount must be greater than 0{Colors.RESET}")
            elif amount > spct_balance:
                print(f"{Colors.RED}[ERROR] Insufficient balance{Colors.RESET}")
            else:
                stake_spct(w3, private_key, address, amount)
        except ValueError:
            print(f"{Colors.RED}[ERROR] Invalid amount{Colors.RESET}")
        print()
        input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
        
    elif choice == "2":
        print()
        claim_staking_reward(w3, private_key, address)
        print()
        input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
        
    elif choice == "3":
        return
    else:
        print(f"{Colors.RED}Invalid option{Colors.RESET}")
        time.sleep(1)

def wrap_menu(w3, private_key, address):
    clear_screen()
    print_banner()
    print(f"{Colors.GREEN}[WRAP] PCT -> AQ-PCT{Colors.RESET}")
    print()
    
    pct_balance = get_token_balance(w3, WRAP_TOKENS["PCT"], address, 18)
    
    print(f"{Colors.WHITE}Your PCT Balance: {pct_balance:.4f}{Colors.RESET}")
    print()
    
    print(f"{Colors.WHITE}Available PCT: {pct_balance:.4f}{Colors.RESET}")
    try:
        amount = float(input(f"{Colors.CYAN}Enter PCT amount to wrap: {Colors.RESET}"))
        if amount <= 0:
            print(f"{Colors.RED}[ERROR] Amount must be greater than 0{Colors.RESET}")
        elif amount > pct_balance:
            print(f"{Colors.RED}[ERROR] Insufficient balance{Colors.RESET}")
        else:
            wrap_tokens(w3, private_key, address, amount)
    except ValueError:
        print(f"{Colors.RED}[ERROR] Invalid amount{Colors.RESET}")
    print()
    input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")

def unwrap_menu(w3, private_key, address):
    clear_screen()
    print_banner()
    print(f"{Colors.GREEN}[UNWRAP] AQ-PCT -> PCT{Colors.RESET}")
    print()
    
    print(f"{Colors.YELLOW}Note: 0.2% fee will be deducted{Colors.RESET}")
    print()
    
    try:
        amount = float(input(f"{Colors.CYAN}Enter AQ-PCT amount to unwrap: {Colors.RESET}"))
        if amount <= 0:
            print(f"{Colors.RED}[ERROR] Amount must be greater than 0{Colors.RESET}")
        else:
            unwrap_tokens(w3, private_key, address, amount)
    except ValueError:
        print(f"{Colors.RED}[ERROR] Invalid amount{Colors.RESET}")
    print()
    input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")

def show_adding_soon():
    clear_screen()
    print_banner()
    print(f"{Colors.YELLOW}{'='*50}{Colors.RESET}")
    print(f"{Colors.YELLOW}         🚧 ADDING SOON 🚧{Colors.RESET}")
    print(f"{Colors.YELLOW}{'='*50}{Colors.RESET}")
    print()
    print(f"{Colors.WHITE}This feature is coming soon!{Colors.RESET}")
    print(f"{Colors.WHITE}Stay tuned for updates.{Colors.RESET}")
    print()
    input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")

def main():
    if os.name == 'nt':
        os.system('color')
    
    clear_screen()
    print_banner()
    
    private_key = load_private_key()
    address = get_wallet_address(private_key)
    
    print(f"{Colors.WHITE}Wallet: {address}{Colors.RESET}")
    print()
    
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    if not w3.is_connected():
        print(f"{Colors.RED}[ERROR] Cannot connect to RPC{Colors.RESET}")
        sys.exit(1)
    
    print(f"{Colors.GREEN}[SUCCESS] Connected to RPC{Colors.RESET}")
    
    print(f"{Colors.YELLOW}[INFO] Logging in...{Colors.RESET}")
    access_token = wallet_login(address, private_key)
    
    if not access_token:
        print(f"{Colors.YELLOW}[WARNING] Login failed, some features may not work{Colors.RESET}")
    else:
        print(f"{Colors.GREEN}[SUCCESS] Login successful!{Colors.RESET}")
    
    time.sleep(2)
    
    while True:
        clear_screen()
        print_banner()
        print(f"{Colors.WHITE}Wallet: {address}{Colors.RESET}")
        print()
        print(f"{Colors.MAGENTA}============== MENU =============={Colors.RESET}")
        print(f"{Colors.CYAN}1. SWAP{Colors.RESET}")
        print(f"{Colors.CYAN}2. ADD LIQUIDITY{Colors.RESET}")
        print(f"{Colors.CYAN}3. SPLIT / COMBINE{Colors.RESET}")
        print(f"{Colors.CYAN}4. STAKE (S-PCT){Colors.RESET}")
        print(f"{Colors.CYAN}5. CLAIM REWARDS{Colors.RESET}")
        print(f"{Colors.CYAN}6. WRAP (PCT -> AQ-PCT){Colors.RESET}")
        print(f"{Colors.CYAN}7. UNWRAP (AQ-PCT -> PCT){Colors.RESET}")
        print(f"{Colors.CYAN}8. AUTO WRAP + UNWRAP{Colors.RESET}")
        print(f"{Colors.CYAN}9. EXIT{Colors.RESET}")
        print(f"{Colors.MAGENTA}=================================={Colors.RESET}")
        print()
        
        choice = input(f"{Colors.YELLOW}Select option: {Colors.RESET}")
        
        if choice == "1":
            swap_menu(w3, private_key, address)
        elif choice == "2":
            liquidity_menu(w3, private_key, address)
        elif choice == "3":
            split_combine_menu(w3, private_key, address)
        elif choice == "4":
            staking_menu(w3, private_key, address)
        elif choice == "5":
            clear_screen()
            print_banner()
            claim_staking_reward(w3, private_key, address)
            print()
            input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
        elif choice == "6":
            wrap_menu(w3, private_key, address)
        elif choice == "7":
            unwrap_menu(w3, private_key, address)
        elif choice == "8":
            auto_wrap_unwrap(w3, private_key, address)
            print()
            input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
        elif choice == "9":
            print(f"{Colors.GREEN}Goodbye!{Colors.RESET}")
            break
        else:
            print(f"{Colors.RED}Invalid option{Colors.RESET}")
            time.sleep(1)

if __name__ == "__main__":
    main()