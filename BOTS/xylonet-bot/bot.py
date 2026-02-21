import time
import requests
from web3 import Web3
from eth_account import Account
import os
import sys
import random

# Enable ANSI colors on Windows
if sys.platform == "win32":
    os.system("color")
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        pass

# ANSI Bold Colors
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
WHITE = "\033[97m"
MAGENTA = "\033[95m"
RESET = "\033[0m"

# Network Configuration
ARC_RPC = "https://rpc.testnet.arc.network/"
SEPOLIA_RPC = "https://sepolia.drpc.org/"
ARC_CHAIN_ID = 5042002
SEPOLIA_CHAIN_ID = 11155111

# Contract Addresses - Arc Testnet
USDC_ADDRESS = Web3.to_checksum_address("0x3600000000000000000000000000000000000000")
EURC_ADDRESS = Web3.to_checksum_address("0x89B50855Aa3bE2F677cD6303Cec089B5F319D72a")
XYLO_ROUTER = Web3.to_checksum_address("0x73742278c31a76dBb0D2587d03ef92E6E2141023")
BRIDGE_CONTRACT = Web3.to_checksum_address("0xC5567a5E3370d4DBfB0540025078e283e36A363d")
XYLO_STABLE_POOL = Web3.to_checksum_address("0x3DF3966F5138143dce7a9cFDdC2c0310ce083BB1")
XYLO_VAULT = Web3.to_checksum_address("0x240Eb85458CD41361bd8C3773253a1D78054f747")

# Sepolia Addresses
SEPOLIA_MESSAGE_TRANSMITTER = Web3.to_checksum_address("0xe737e5cebeeba77efe34d4aa090756590b1ce275")

# Points API
POINTS_API = "https://www.xylonet.xyz/api/points?wallet="

# ABIs
ERC20_ABI = [
    {"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"spender","type":"address"},{"name":"addedValue","type":"uint256"}],"name":"increaseAllowance","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]

ROUTER_ABI = [
    {"inputs":[{"components":[{"name":"tokenIn","type":"address"},{"name":"tokenOut","type":"address"},{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"name":"params","type":"tuple"}],"name":"swap","outputs":[{"name":"amountOut","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}
]

MESSAGE_TRANSMITTER_ABI = [
    {"inputs":[{"name":"message","type":"bytes"},{"name":"attestation","type":"bytes"}],"name":"receiveMessage","outputs":[{"name":"success","type":"bool"}],"stateMutability":"nonpayable","type":"function"}
]

STABLE_POOL_ABI = [
    {
        "inputs": [
            {"name": "amounts", "type": "uint256[]"},
            {"name": "minLpTokens", "type": "uint256"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"}
        ],
        "name": "addLiquidity",
        "outputs": [{"name": "lpTokensMinted", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "lpTokenAmount", "type": "uint256"},
            {"name": "minAmounts", "type": "uint256[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"}
        ],
        "name": "removeLiquidity",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]

VAULT_ABI = [
    {
        "inputs": [
            {"name": "assets", "type": "uint256"},
            {"name": "receiver", "type": "address"}
        ],
        "name": "deposit",
        "outputs": [{"name": "shares", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]


def clear_screen():
    os.system('cls' if sys.platform == 'win32' else 'clear')


class HumanBehavior:
    """Simulates human-like behavior to avoid sybil detection"""
    
    @staticmethod
    def random_delay(min_sec=2, max_sec=8):
        """Random delay between actions like a human would take"""
        delay = random.uniform(min_sec, max_sec)
        print(f"{YELLOW}⏳ Waiting {delay:.1f}s...{RESET}")
        time.sleep(delay)
    
    @staticmethod
    def typing_delay():
        """Simulate human typing/thinking delay"""
        time.sleep(random.uniform(0.5, 2.0))
    
    @staticmethod
    def randomize_amount(base_amount, variance_percent=15):
        """Add random variance to amounts to avoid pattern detection"""
        variance = base_amount * (variance_percent / 100)
        randomized = base_amount + random.uniform(-variance, variance)
        return round(randomized, 6)
    
    @staticmethod
    def should_skip_action(skip_chance=10):
        """Randomly skip some actions like humans do"""
        return random.randint(1, 100) <= skip_chance
    
    @staticmethod
    def get_random_gas_multiplier():
        """Random gas multiplier to avoid same gas patterns"""
        return random.uniform(1.8, 2.5)
    
    @staticmethod
    def get_human_delay_between_loops():
        """Longer random delays between loops"""
        return random.randint(30, 120)
    
    @staticmethod
    def shuffle_tasks(tasks):
        """Shuffle task order to avoid predictable patterns"""
        shuffled = tasks.copy()
        random.shuffle(shuffled)
        return shuffled
    
    @staticmethod
    def get_random_deadline():
        """Random deadline between 30min to 2hours"""
        return int(time.time()) + random.randint(1800, 7200)


class XyloNetBot:
    def __init__(self):
        self.arc_web3 = Web3(Web3.HTTPProvider(ARC_RPC))
        self.sepolia_web3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC))
        self.account = None
        self.address = None
        self.human = HumanBehavior()
        self.points_data = None
        
    def load_private_key(self):
        try:
            if not os.path.exists("pv.txt"):
                print(f"{RED}ERROR: pv.txt file not found!{RESET}")
                return False
            with open("pv.txt", "r") as f:
                private_key = f.read().strip()
            if not private_key.startswith("0x"):
                private_key = "0x" + private_key
            self.account = Account.from_key(private_key)
            self.address = self.account.address
            return True
        except Exception as e:
            print(f"{RED}ERROR loading private key: {e}{RESET}")
            return False
    
    def fetch_points_data(self):
        """Fetch points and sybil status from API"""
        try:
            response = requests.get(
                f"{POINTS_API}{self.address}",
                headers={
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36 Edg/144.0.0.0',
                    'Referer': 'https://www.xylonet.xyz/points'
                },
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    self.points_data = data['data']
                    return True
        except Exception as e:
            print(f"{YELLOW}Warning: Could not fetch points data: {e}{RESET}")
        return False
    
    def get_sybil_status_display(self):
        """Get formatted sybil status display"""
        if not self.points_data:
            return f"{YELLOW}Unknown{RESET}", f"{YELLOW}N/A{RESET}"
        
        sybil_risk = self.points_data.get('sybil_risk', 'unknown')
        quality_score = self.points_data.get('quality_score', 0)
        quality_tier = self.points_data.get('quality_tier', {})
        tier_name = quality_tier.get('tier', 'Unknown')
        multiplier = quality_tier.get('multiplier', 0)
        
        # Color code based on risk
        if sybil_risk == 'low':
            risk_color = GREEN
        elif sybil_risk == 'medium':
            risk_color = YELLOW
        else:
            risk_color = RED
        
        # Color code based on tier
        if tier_name == 'Organic':
            tier_color = GREEN
        elif tier_name == 'Verified':
            tier_color = CYAN
        elif tier_name == 'Suspected':
            tier_color = RED
        else:
            tier_color = YELLOW
        
        risk_display = f"{risk_color}{sybil_risk.upper()}{RESET}"
        tier_display = f"{tier_color}{tier_name} (Score: {quality_score}, Multiplier: {multiplier}x){RESET}"
        
        return risk_display, tier_display
    
    def get_points_display(self):
        """Get formatted points display"""
        if not self.points_data:
            return "N/A"
        
        total = self.points_data.get('total_points', 0)
        volume = self.points_data.get('volume_points', 0)
        milestone = self.points_data.get('milestone_points', 0)
        referral = self.points_data.get('referral_points', 0)
        
        return f"Total: {total} | Volume: {volume} | Milestone: {milestone} | Referral: {referral}"
    
    def get_volumes_display(self):
        """Get formatted volumes display"""
        if not self.points_data:
            return "N/A"
        
        volumes = self.points_data.get('volumes', {})
        swap = volumes.get('swap', 0)
        bridge = volumes.get('bridge', 0)
        vault = volumes.get('vault', 0)
        
        return f"Swap: ${swap} | Bridge: ${bridge} | Vault: ${vault}"
    
    def get_balance(self):
        try:
            usdc = self.arc_web3.eth.contract(address=USDC_ADDRESS, abi=ERC20_ABI)
            balance = usdc.functions.balanceOf(self.address).call()
            return balance / 10**6
        except:
            return 0
    
    def get_eurc_balance(self):
        try:
            eurc = self.arc_web3.eth.contract(address=EURC_ADDRESS, abi=ERC20_ABI)
            balance = eurc.functions.balanceOf(self.address).call()
            return balance / 10**6
        except:
            return 0
    
    def get_lp_balance(self):
        try:
            pool = self.arc_web3.eth.contract(address=XYLO_STABLE_POOL, abi=STABLE_POOL_ABI)
            balance = pool.functions.balanceOf(self.address).call()
            return balance / 10**18
        except:
            return 0
    
    def get_vault_balance(self):
        try:
            vault = self.arc_web3.eth.contract(address=XYLO_VAULT, abi=VAULT_ABI)
            balance = vault.functions.balanceOf(self.address).call()
            return balance / 10**6
        except:
            return 0
    
    def get_nonce(self, web3):
        return web3.eth.get_transaction_count(self.address)
    
    def get_gas_price(self, web3):
        return web3.eth.gas_price
    
    def send_transaction(self, web3, tx):
        try:
            # Add small random delay before sending (human-like)
            time.sleep(random.uniform(0.5, 1.5))
            
            signed = self.account.sign_transaction(tx)
            tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
            print(f"{YELLOW}📤 TX Sent: {tx_hash.hex()[:20]}...{RESET}")
            print(f"{YELLOW}⏳ Waiting for confirmation...{RESET}")
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            if receipt['status'] == 1:
                print(f"{GREEN}✅ Transaction Confirmed!{RESET}")
                return tx_hash.hex()
            else:
                print(f"{RED}❌ Transaction Failed!{RESET}")
                return None
        except Exception as e:
            print(f"{RED}❌ Transaction Error: {e}{RESET}")
            return None
    
    def approve_token(self, token_address, spender, amount):
        print(f"{CYAN}🔐 Approving token...{RESET}")
        token = self.arc_web3.eth.contract(address=token_address, abi=ERC20_ABI)
        
        try:
            current_allowance = token.functions.allowance(self.address, spender).call()
            if current_allowance >= amount:
                print(f"{GREEN}✅ Already approved!{RESET}")
                return True
        except:
            pass
        
        # Human-like delay before approval
        self.human.random_delay(1, 3)
        
        nonce = self.get_nonce(self.arc_web3)
        gas_price = self.get_gas_price(self.arc_web3)
        gas_multiplier = self.human.get_random_gas_multiplier()
        
        tx = token.functions.approve(spender, amount).build_transaction({
            'chainId': ARC_CHAIN_ID,
            'gas': random.randint(95000, 105000),  # Random gas limit
            'maxFeePerGas': int(gas_price * gas_multiplier),
            'maxPriorityFeePerGas': gas_price,
            'nonce': nonce,
        })
        
        result = self.send_transaction(self.arc_web3, tx)
        return result is not None

    def swap(self, auto_amount=None):
        print(f"\n{BOLD}{CYAN}═══════════ 🔄 SWAP ═══════════{RESET}")
        
        usdc_bal = self.get_balance()
        eurc_bal = self.get_eurc_balance()
        print(f"{WHITE}💰 USDC Balance: {usdc_bal:.6f}{RESET}")
        print(f"{WHITE}💶 EURC Balance: {eurc_bal:.6f}{RESET}")
        
        if auto_amount is not None:
            # Randomize the amount for human-like behavior
            amount = self.human.randomize_amount(auto_amount)
            print(f"{YELLOW}🎲 Randomized Swap Amount: {amount:.6f} USDC{RESET}")
        else:
            self.human.typing_delay()
            try:
                amount_str = input(f"{WHITE}Enter USDC amount to swap: {RESET}")
                amount = float(amount_str)
            except:
                print(f"{RED}❌ Invalid amount!{RESET}")
                return False
        
        if amount <= 0:
            print(f"{RED}❌ Invalid amount!{RESET}")
            return False
        if amount > usdc_bal:
            print(f"{RED}❌ Insufficient balance!{RESET}")
            return False
        
        amount_wei = int(amount * 10**6)
        
        print(f"{YELLOW}🔄 Swapping {amount:.6f} USDC to EURC...{RESET}")
        
        # Human-like delay before starting
        self.human.random_delay(2, 5)
        
        print(f"{CYAN}📝 Step 1/2: Approving USDC...{RESET}")
        max_approval = 2**256 - 1
        if not self.approve_token(USDC_ADDRESS, XYLO_ROUTER, max_approval):
            return False
        
        # Human delay between steps
        self.human.random_delay(3, 7)
        
        print(f"{CYAN}📝 Step 2/2: Executing Swap...{RESET}")
        
        min_out = int(amount_wei * random.uniform(0.02, 0.05))  # Random slippage
        deadline = self.human.get_random_deadline()
        
        swap_params = (
            USDC_ADDRESS,
            EURC_ADDRESS,
            amount_wei,
            min_out,
            self.address,
            deadline
        )
        
        router = self.arc_web3.eth.contract(address=XYLO_ROUTER, abi=ROUTER_ABI)
        
        nonce = self.get_nonce(self.arc_web3)
        gas_price = self.get_gas_price(self.arc_web3)
        gas_multiplier = self.human.get_random_gas_multiplier()
        
        try:
            tx = router.functions.swap(swap_params).build_transaction({
                'chainId': ARC_CHAIN_ID,
                'gas': random.randint(280000, 320000),
                'maxFeePerGas': int(gas_price * gas_multiplier),
                'maxPriorityFeePerGas': gas_price,
                'nonce': nonce,
            })
            
            result = self.send_transaction(self.arc_web3, tx)
            if result:
                print(f"{GREEN}✅ Swap completed successfully!{RESET}")
                print(f"{GREEN}🔗 TX: https://testnet.arcscan.app/tx/{result}{RESET}")
                return True
        except Exception as e:
            print(f"{RED}❌ Swap Error: {e}{RESET}")
        return False

    def bridge(self, auto_amount=None):
        print(f"\n{BOLD}{CYAN}═══════════ 🌉 BRIDGE (Arc → Sepolia) ═══════════{RESET}")
        
        usdc_bal = self.get_balance()
        print(f"{WHITE}💰 USDC Balance on Arc: {usdc_bal:.6f}{RESET}")
        
        if auto_amount is not None:
            amount = self.human.randomize_amount(auto_amount)
            print(f"{YELLOW}🎲 Randomized Bridge Amount: {amount:.6f} USDC{RESET}")
        else:
            self.human.typing_delay()
            try:
                amount_str = input(f"{WHITE}Enter USDC amount to bridge: {RESET}")
                amount = float(amount_str)
            except:
                print(f"{RED}❌ Invalid amount!{RESET}")
                return False
        
        if amount <= 0:
            print(f"{RED}❌ Invalid amount!{RESET}")
            return False
        if amount > usdc_bal:
            print(f"{RED}❌ Insufficient balance!{RESET}")
            return False
        
        amount_wei = int(amount * 10**6)
        
        print(f"{YELLOW}🌉 Bridging {amount:.6f} USDC to Sepolia...{RESET}")
        
        self.human.random_delay(2, 5)
        
        print(f"{CYAN}📝 Step 1/4: Approving USDC...{RESET}")
        
        usdc = self.arc_web3.eth.contract(address=USDC_ADDRESS, abi=ERC20_ABI)
        nonce = self.get_nonce(self.arc_web3)
        gas_price = self.get_gas_price(self.arc_web3)
        gas_multiplier = self.human.get_random_gas_multiplier()
        
        approve_tx = usdc.functions.increaseAllowance(BRIDGE_CONTRACT, amount_wei).build_transaction({
            'chainId': ARC_CHAIN_ID,
            'gas': random.randint(95000, 105000),
            'maxFeePerGas': int(gas_price * gas_multiplier),
            'maxPriorityFeePerGas': gas_price,
            'nonce': nonce,
        })
        
        if not self.send_transaction(self.arc_web3, approve_tx):
            return False
        
        self.human.random_delay(3, 7)
        
        print(f"{CYAN}📝 Step 2/4: Initiating bridge...{RESET}")
        
        mint_recipient_padded = self.address[2:].lower().zfill(64)
        destination_caller_padded = "0" * 64
        burn_token_padded = USDC_ADDRESS[2:].lower().zfill(64)
        message_sender_padded = BRIDGE_CONTRACT[2:].lower().zfill(64)
        
        bridge_calldata = "0xd0d4229a"
        bridge_calldata += hex(amount_wei)[2:].zfill(64)
        bridge_calldata += "0" * 64
        bridge_calldata += "0" * 64
        bridge_calldata += mint_recipient_padded
        bridge_calldata += destination_caller_padded
        bridge_calldata += burn_token_padded
        bridge_calldata += message_sender_padded
        bridge_calldata += "0" * 64
        bridge_calldata += hex(1000)[2:].zfill(64)
        
        nonce = self.get_nonce(self.arc_web3)
        
        bridge_tx = {
            'chainId': ARC_CHAIN_ID,
            'to': BRIDGE_CONTRACT,
            'gas': random.randint(280000, 320000),
            'maxFeePerGas': int(gas_price * gas_multiplier),
            'maxPriorityFeePerGas': gas_price,
            'nonce': nonce,
            'data': bridge_calldata,
            'value': 0
        }
        
        arc_tx_hash = self.send_transaction(self.arc_web3, bridge_tx)
        if not arc_tx_hash:
            return False
        
        if not arc_tx_hash.startswith('0x'):
            arc_tx_hash = '0x' + arc_tx_hash
        
        print(f"{GREEN}✅ Bridge initiated on Arc!{RESET}")
        print(f"{CYAN}🔗 Arc TX: https://testnet.arcscan.app/tx/{arc_tx_hash}{RESET}")
        
        print(f"{CYAN}📝 Step 3/4: Waiting for Circle attestation...{RESET}")
        
        attestation_data = self.wait_for_attestation(arc_tx_hash)
        if not attestation_data:
            print(f"{RED}❌ Failed to get attestation! Try claiming manually later.{RESET}")
            print(f"{YELLOW}🔗 Check: https://iris-api-sandbox.circle.com/v2/messages/26?transactionHash={arc_tx_hash}{RESET}")
            return False
        
        print(f"{GREEN}✅ Attestation received!{RESET}")
        
        self.human.random_delay(2, 5)
        
        print(f"{CYAN}📝 Step 4/4: Claiming on Sepolia...{RESET}")
        
        message = attestation_data['message']
        attestation = attestation_data['attestation']
        
        msg_transmitter = self.sepolia_web3.eth.contract(
            address=SEPOLIA_MESSAGE_TRANSMITTER, 
            abi=MESSAGE_TRANSMITTER_ABI
        )
        
        if message.startswith('0x'):
            message_bytes = bytes.fromhex(message[2:])
        else:
            message_bytes = bytes.fromhex(message)
            
        if attestation.startswith('0x'):
            attestation_bytes = bytes.fromhex(attestation[2:])
        else:
            attestation_bytes = bytes.fromhex(attestation)
        
        nonce = self.get_nonce(self.sepolia_web3)
        gas_price = self.sepolia_web3.eth.gas_price
        
        try:
            claim_tx = msg_transmitter.functions.receiveMessage(
                message_bytes,
                attestation_bytes
            ).build_transaction({
                'chainId': SEPOLIA_CHAIN_ID,
                'gas': random.randint(280000, 320000),
                'maxFeePerGas': int(gas_price * self.human.get_random_gas_multiplier()),
                'maxPriorityFeePerGas': gas_price,
                'nonce': nonce,
            })
            
            sepolia_tx_hash = self.send_transaction(self.sepolia_web3, claim_tx)
            if sepolia_tx_hash:
                print(f"{GREEN}✅ Bridge completed successfully!{RESET}")
                print(f"{GREEN}🔗 Sepolia TX: https://sepolia.etherscan.io/tx/{sepolia_tx_hash}{RESET}")
                return True
        except Exception as e:
            print(f"{RED}❌ Claim Error: {e}{RESET}")
        return False
    
    def wait_for_attestation(self, tx_hash, max_attempts=60):
        if not tx_hash.startswith('0x'):
            tx_hash = '0x' + tx_hash
        
        api_url = f"https://iris-api-sandbox.circle.com/v2/messages/26?transactionHash={tx_hash}"
        
        for i in range(max_attempts):
            try:
                response = requests.get(api_url, headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'x-user-agent': 'bridge-kit/1.2.0 (browser/Edge)'
                }, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('messages') and len(data['messages']) > 0:
                        msg = data['messages'][0]
                        status = msg.get('status', '')
                        attestation = msg.get('attestation', '')
                        
                        if status == 'complete' and attestation and attestation != 'PENDING':
                            return {
                                'message': msg.get('message'),
                                'attestation': attestation
                            }
                        
                        print(f"{YELLOW}⏳ Status: {status} - Waiting... ({i+1}/{max_attempts}){RESET}")
                    else:
                        print(f"{YELLOW}⏳ Indexing... ({i+1}/{max_attempts}){RESET}")
                        
                elif response.status_code == 404:
                    print(f"{YELLOW}⏳ Indexing... ({i+1}/{max_attempts}){RESET}")
                else:
                    print(f"{YELLOW}⏳ Waiting... ({i+1}/{max_attempts}){RESET}")
                
                time.sleep(random.randint(8, 12))  # Random wait time
                
            except:
                print(f"{YELLOW}🔄 Retrying... ({i+1}/{max_attempts}){RESET}")
                time.sleep(random.randint(8, 12))
        
        return None

    def vault_deposit(self, auto_amount=None):
        print(f"\n{BOLD}{CYAN}═══════════ 🏦 VAULT DEPOSIT ═══════════{RESET}")
        
        usdc_bal = self.get_balance()
        vault_bal = self.get_vault_balance()
        print(f"{WHITE}💰 USDC Balance: {usdc_bal:.6f}{RESET}")
        print(f"{WHITE}🏦 xyUSDC (Vault) Balance: {vault_bal:.6f}{RESET}")
        
        if auto_amount is not None:
            amount = self.human.randomize_amount(auto_amount)
            print(f"{YELLOW}🎲 Randomized Deposit Amount: {amount:.6f} USDC{RESET}")
        else:
            self.human.typing_delay()
            try:
                amount_str = input(f"{WHITE}Enter USDC amount to deposit: {RESET}")
                amount = float(amount_str)
            except:
                print(f"{RED}❌ Invalid amount!{RESET}")
                return False
        
        if amount <= 0:
            print(f"{RED}❌ Invalid amount!{RESET}")
            return False
        if amount > usdc_bal:
            print(f"{RED}❌ Insufficient balance!{RESET}")
            return False
        
        amount_wei = int(amount * 10**6)
        
        print(f"{YELLOW}🏦 Depositing {amount:.6f} USDC to Vault...{RESET}")
        
        self.human.random_delay(2, 5)
        
        print(f"{CYAN}📝 Step 1/2: Approving USDC for Vault...{RESET}")
        max_approval = 2**256 - 1
        if not self.approve_token(USDC_ADDRESS, XYLO_VAULT, max_approval):
            return False
        
        self.human.random_delay(3, 7)
        
        print(f"{CYAN}📝 Step 2/2: Depositing to Vault...{RESET}")
        
        vault = self.arc_web3.eth.contract(address=XYLO_VAULT, abi=VAULT_ABI)
        
        nonce = self.get_nonce(self.arc_web3)
        gas_price = self.get_gas_price(self.arc_web3)
        gas_multiplier = self.human.get_random_gas_multiplier()
        
        try:
            tx = vault.functions.deposit(amount_wei, self.address).build_transaction({
                'chainId': ARC_CHAIN_ID,
                'gas': random.randint(140000, 160000),
                'maxFeePerGas': int(gas_price * gas_multiplier),
                'maxPriorityFeePerGas': gas_price,
                'nonce': nonce,
            })
            
            result = self.send_transaction(self.arc_web3, tx)
            if result:
                print(f"{GREEN}✅ Vault deposit completed successfully!{RESET}")
                print(f"{GREEN}🔗 TX: https://testnet.arcscan.app/tx/{result}{RESET}")
                return True
        except Exception as e:
            print(f"{RED}❌ Vault Deposit Error: {e}{RESET}")
        return False

    def add_liquidity(self, auto_usdc=None, auto_eurc=None):
        print(f"\n{BOLD}{CYAN}═══════════ 💧 ADD LIQUIDITY ═══════════{RESET}")
        
        usdc_bal = self.get_balance()
        eurc_bal = self.get_eurc_balance()
        lp_bal = self.get_lp_balance()
        print(f"{WHITE}💰 USDC Balance: {usdc_bal:.6f}{RESET}")
        print(f"{WHITE}💶 EURC Balance: {eurc_bal:.6f}{RESET}")
        print(f"{WHITE}🎫 LP Token Balance: {lp_bal:.18f}{RESET}")
        
        if auto_usdc is not None and auto_eurc is not None:
            usdc_amount = self.human.randomize_amount(auto_usdc)
            eurc_amount = self.human.randomize_amount(auto_eurc)
            print(f"{YELLOW}🎲 Randomized: {usdc_amount:.6f} USDC + {eurc_amount:.6f} EURC{RESET}")
        else:
            self.human.typing_delay()
            try:
                usdc_str = input(f"{WHITE}Enter USDC amount: {RESET}")
                usdc_amount = float(usdc_str)
                self.human.typing_delay()
                eurc_str = input(f"{WHITE}Enter EURC amount: {RESET}")
                eurc_amount = float(eurc_str)
            except:
                print(f"{RED}❌ Invalid amount!{RESET}")
                return False
        
        if usdc_amount <= 0 or eurc_amount <= 0:
            print(f"{RED}❌ Invalid amounts!{RESET}")
            return False
        if usdc_amount > usdc_bal:
            print(f"{RED}❌ Insufficient USDC balance!{RESET}")
            return False
        if eurc_amount > eurc_bal:
            print(f"{RED}❌ Insufficient EURC balance!{RESET}")
            return False
        
        usdc_wei = int(usdc_amount * 10**6)
        eurc_wei = int(eurc_amount * 10**6)
        
        print(f"{YELLOW}💧 Adding Liquidity: {usdc_amount:.6f} USDC + {eurc_amount:.6f} EURC...{RESET}")
        
        self.human.random_delay(2, 5)
        
        print(f"{CYAN}📝 Step 1/3: Approving USDC...{RESET}")
        if not self.approve_token(USDC_ADDRESS, XYLO_STABLE_POOL, usdc_wei):
            return False
        
        self.human.random_delay(3, 6)
        
        print(f"{CYAN}📝 Step 2/3: Approving EURC...{RESET}")
        if not self.approve_token(EURC_ADDRESS, XYLO_STABLE_POOL, eurc_wei):
            return False
        
        self.human.random_delay(3, 7)
        
        print(f"{CYAN}📝 Step 3/3: Adding Liquidity...{RESET}")
        
        pool = self.arc_web3.eth.contract(address=XYLO_STABLE_POOL, abi=STABLE_POOL_ABI)
        
        amounts = [usdc_wei, eurc_wei]
        min_lp_tokens = 0
        deadline = self.human.get_random_deadline()
        
        nonce = self.get_nonce(self.arc_web3)
        gas_price = self.get_gas_price(self.arc_web3)
        gas_multiplier = self.human.get_random_gas_multiplier()
        
        try:
            tx = pool.functions.addLiquidity(
                amounts,
                min_lp_tokens,
                self.address,
                deadline
            ).build_transaction({
                'chainId': ARC_CHAIN_ID,
                'gas': random.randint(280000, 320000),
                'maxFeePerGas': int(gas_price * gas_multiplier),
                'maxPriorityFeePerGas': gas_price,
                'nonce': nonce,
            })
            
            result = self.send_transaction(self.arc_web3, tx)
            if result:
                print(f"{GREEN}✅ Add Liquidity completed successfully!{RESET}")
                print(f"{GREEN}🔗 TX: https://testnet.arcscan.app/tx/{result}{RESET}")
                return True
        except Exception as e:
            print(f"{RED}❌ Add Liquidity Error: {e}{RESET}")
        return False

    def remove_liquidity(self, auto_amount=None):
        print(f"\n{BOLD}{CYAN}═══════════ 🔥 REMOVE LIQUIDITY ═══════════{RESET}")
        
        usdc_bal = self.get_balance()
        eurc_bal = self.get_eurc_balance()
        lp_bal = self.get_lp_balance()
        print(f"{WHITE}💰 USDC Balance: {usdc_bal:.6f}{RESET}")
        print(f"{WHITE}💶 EURC Balance: {eurc_bal:.6f}{RESET}")
        print(f"{WHITE}🎫 LP Token Balance: {lp_bal:.18f}{RESET}")
        
        if lp_bal <= 0:
            print(f"{RED}❌ No LP tokens to remove!{RESET}")
            return False
        
        if auto_amount is not None:
            lp_amount = self.human.randomize_amount(auto_amount)
            if lp_amount > lp_bal:
                lp_amount = lp_bal * 0.9  # Use 90% if exceeds
            print(f"{YELLOW}🎲 Randomized LP Amount: {lp_amount:.18f}{RESET}")
        else:
            self.human.typing_delay()
            try:
                lp_str = input(f"{WHITE}Enter LP token amount to remove (max: {lp_bal:.18f}): {RESET}")
                lp_amount = float(lp_str)
            except:
                print(f"{RED}❌ Invalid amount!{RESET}")
                return False
        
        if lp_amount <= 0:
            print(f"{RED}❌ Invalid amount!{RESET}")
            return False
        if lp_amount > lp_bal:
            print(f"{RED}❌ Insufficient LP token balance!{RESET}")
            return False
        
        lp_wei = int(lp_amount * 10**18)
        
        print(f"{YELLOW}🔥 Removing {lp_amount:.18f} LP Tokens...{RESET}")
        
        self.human.random_delay(2, 5)
        
        pool = self.arc_web3.eth.contract(address=XYLO_STABLE_POOL, abi=STABLE_POOL_ABI)
        
        min_amounts = [0, 0]
        deadline = self.human.get_random_deadline()
        
        nonce = self.get_nonce(self.arc_web3)
        gas_price = self.get_gas_price(self.arc_web3)
        gas_multiplier = self.human.get_random_gas_multiplier()
        
        try:
            tx = pool.functions.removeLiquidity(
                lp_wei,
                min_amounts,
                self.address,
                deadline
            ).build_transaction({
                'chainId': ARC_CHAIN_ID,
                'gas': random.randint(180000, 220000),
                'maxFeePerGas': int(gas_price * gas_multiplier),
                'maxPriorityFeePerGas': gas_price,
                'nonce': nonce,
            })
            
            result = self.send_transaction(self.arc_web3, tx)
            if result:
                print(f"{GREEN}✅ Remove Liquidity completed successfully!{RESET}")
                print(f"{GREEN}🔗 TX: https://testnet.arcscan.app/tx/{result}{RESET}")
                return True
        except Exception as e:
            print(f"{RED}❌ Remove Liquidity Error: {e}{RESET}")
        return False

    def auto_all(self):
        print(f"\n{BOLD}{CYAN}═══════════ 🤖 HUMAN-LIKE AUTO MODE ═══════════{RESET}")
        print(f"{WHITE}This mode simulates human behavior to avoid sybil detection:{RESET}")
        print(f"{WHITE}  • Random delays between actions{RESET}")
        print(f"{WHITE}  • Randomized transaction amounts{RESET}")
        print(f"{WHITE}  • Shuffled task order{RESET}")
        print(f"{WHITE}  • Random gas values{RESET}")
        print(f"{WHITE}  • Occasional task skipping{RESET}")
        print(f"{BLUE}══════════════════════════════════════════════════{RESET}")
        print(f"{WHITE}Tasks available:{RESET}")
        print(f"{WHITE}  1. Swap USDC to EURC{RESET}")
        print(f"{WHITE}  2. Bridge to Sepolia{RESET}")
        print(f"{WHITE}  3. Vault Deposit{RESET}")
        print(f"{WHITE}  4. Add Liquidity{RESET}")
        print(f"{WHITE}  5. Remove Liquidity{RESET}")
        print(f"{BLUE}══════════════════════════════════════════════════{RESET}")
        
        self.human.typing_delay()
        
        try:
            loops_str = input(f"{WHITE}Enter number of loops (default 1): {RESET}")
            loops = int(loops_str) if loops_str.strip() else 1
            if loops <= 0:
                loops = 1
        except:
            loops = 1
        
        self.human.typing_delay()
        
        try:
            swap_amt_str = input(f"{WHITE}Base SWAP amount (will be randomized ±15%): {RESET}")
            swap_amount = float(swap_amt_str) if swap_amt_str.strip() else 0.1
        except:
            swap_amount = 0.1
        
        self.human.typing_delay()
        
        try:
            bridge_amt_str = input(f"{WHITE}Base BRIDGE amount (will be randomized ±15%): {RESET}")
            bridge_amount = float(bridge_amt_str) if bridge_amt_str.strip() else 0.1
        except:
            bridge_amount = 0.1
        
        self.human.typing_delay()
        
        try:
            vault_amt_str = input(f"{WHITE}Base VAULT DEPOSIT amount (will be randomized ±15%): {RESET}")
            vault_amount = float(vault_amt_str) if vault_amt_str.strip() else 0.1
        except:
            vault_amount = 0.1
        
        self.human.typing_delay()
        
        try:
            liq_usdc_str = input(f"{WHITE}Base ADD LIQUIDITY USDC amount: {RESET}")
            liq_usdc = float(liq_usdc_str) if liq_usdc_str.strip() else 0.1
        except:
            liq_usdc = 0.1
        
        self.human.typing_delay()
        
        try:
            liq_eurc_str = input(f"{WHITE}Base ADD LIQUIDITY EURC amount: {RESET}")
            liq_eurc = float(liq_eurc_str) if liq_eurc_str.strip() else 0.0001
        except:
            liq_eurc = 0.0001
        
        self.human.typing_delay()
        
        try:
            remove_lp_str = input(f"{WHITE}Base REMOVE LIQUIDITY LP amount: {RESET}")
            remove_lp = float(remove_lp_str) if remove_lp_str.strip() else 0.1
        except:
            remove_lp = 0.1
        
        print(f"\n{BOLD}{YELLOW}══════════════════════════════════════════════════{RESET}")
        print(f"{YELLOW}🎲 HUMAN-LIKE SETTINGS:{RESET}")
        print(f"{WHITE}Loops: {loops}{RESET}")
        print(f"{WHITE}Base Amounts (±15% randomized):{RESET}")
        print(f"{WHITE}  • Swap: ~{swap_amount} USDC{RESET}")
        print(f"{WHITE}  • Bridge: ~{bridge_amount} USDC{RESET}")
        print(f"{WHITE}  • Vault: ~{vault_amount} USDC{RESET}")
        print(f"{WHITE}  • Add Liq: ~{liq_usdc} USDC + ~{liq_eurc} EURC{RESET}")
        print(f"{WHITE}  • Remove Liq: ~{remove_lp} LP{RESET}")
        print(f"{WHITE}Delays: 30-120s between loops, 2-8s between tasks{RESET}")
        print(f"{WHITE}Task Order: Shuffled each loop{RESET}")
        print(f"{BOLD}{YELLOW}══════════════════════════════════════════════════{RESET}")
        
        self.human.typing_delay()
        confirm = input(f"{WHITE}Start Human-Like Auto Mode? (y/n): {RESET}")
        if confirm.lower() != 'y':
            print(f"{YELLOW}Auto Mode cancelled.{RESET}")
            return
        
        successful = 0
        failed = 0
        skipped = 0
        
        for loop in range(1, loops + 1):
            print(f"\n{BOLD}{BLUE}═══════════════════ LOOP {loop}/{loops} ═══════════════════{RESET}")
            
            # Refresh points data
            self.fetch_points_data()
            risk_display, tier_display = self.get_sybil_status_display()
            print(f"{MAGENTA}📊 Current Sybil Risk: {risk_display}{RESET}")
            print(f"{MAGENTA}📊 Quality Tier: {tier_display}{RESET}")
            
            # Define tasks with their functions and parameters
            tasks = [
                ('SWAP', lambda: self.swap(auto_amount=swap_amount)),
                ('BRIDGE', lambda: self.bridge(auto_amount=bridge_amount)),
                ('VAULT DEPOSIT', lambda: self.vault_deposit(auto_amount=vault_amount)),
                ('ADD LIQUIDITY', lambda: self.add_liquidity(auto_usdc=liq_usdc, auto_eurc=liq_eurc)),
                ('REMOVE LIQUIDITY', lambda: self.remove_liquidity(auto_amount=remove_lp)),
            ]
            
            # Shuffle tasks for human-like behavior
            random.shuffle(tasks)
            print(f"{YELLOW}🔀 Task order for this loop: {[t[0] for t in tasks]}{RESET}")
            
            for idx, (task_name, task_func) in enumerate(tasks, 1):
                # Random chance to skip a task (10% chance)
                if self.human.should_skip_action(skip_chance=10):
                    print(f"\n{YELLOW}⏭️ [{loop}/{loops}] Skipping {task_name} (human-like behavior){RESET}")
                    skipped += 1
                    continue
                
                print(f"\n{BOLD}{CYAN}🔄 [{loop}/{loops}] Task {idx}/5: {task_name}{RESET}")
                
                try:
                    if task_func():
                        print(f"{GREEN}✅ [{loop}/{loops}] {task_name} SUCCESS{RESET}")
                        successful += 1
                    else:
                        print(f"{RED}❌ [{loop}/{loops}] {task_name} FAILED{RESET}")
                        failed += 1
                except Exception as e:
                    print(f"{RED}❌ [{loop}/{loops}] {task_name} ERROR: {e}{RESET}")
                    failed += 1
                
                # Random delay between tasks
                if idx < len(tasks):
                    self.human.random_delay(5, 15)
            
            if loop < loops:
                delay = self.human.get_human_delay_between_loops()
                print(f"\n{YELLOW}😴 Waiting {delay} seconds before next loop (human-like)...{RESET}")
                
                # Show countdown
                for remaining in range(delay, 0, -10):
                    print(f"{YELLOW}⏳ {remaining}s remaining...{RESET}")
                    time.sleep(min(10, remaining))
        
        # Final stats
        print(f"\n{BOLD}{GREEN}══════════════════════════════════════════════════{RESET}")
        print(f"{GREEN}🎉 HUMAN-LIKE AUTO MODE COMPLETED!{RESET}")
        print(f"{WHITE}Total Loops: {loops}{RESET}")
        print(f"{GREEN}✅ Successful: {successful}{RESET}")
        print(f"{RED}❌ Failed: {failed}{RESET}")
        print(f"{YELLOW}⏭️ Skipped: {skipped}{RESET}")
        
        # Refresh and show final sybil status
        self.fetch_points_data()
        risk_display, tier_display = self.get_sybil_status_display()
        print(f"\n{MAGENTA}📊 Final Sybil Risk: {risk_display}{RESET}")
        print(f"{MAGENTA}📊 Final Quality Tier: {tier_display}{RESET}")
        print(f"{MAGENTA}📊 Points: {self.get_points_display()}{RESET}")
        print(f"{MAGENTA}📊 Volumes: {self.get_volumes_display()}{RESET}")
        print(f"{BOLD}{GREEN}══════════════════════════════════════════════════{RESET}")

    def show_menu(self):
        clear_screen()
        
        # Fetch latest points/sybil data
        self.fetch_points_data()
        
        balance = self.get_balance()
        eurc_balance = self.get_eurc_balance()
        lp_balance = self.get_lp_balance()
        vault_balance = self.get_vault_balance()
        
        risk_display, tier_display = self.get_sybil_status_display()
        
        print(f"{BOLD}{BLUE}══════════════════════════════════════════════════{RESET}")
        print(f"{BOLD}{CYAN}           🌐 XYLONET TESTNET BOT 🌐{RESET}")
        print(f"{BOLD}{WHITE}              Created by KAZUHA{RESET}")
        print(f"{BOLD}{BLUE}══════════════════════════════════════════════════{RESET}")
        print(f"{WHITE}👛 Wallet: {self.address[:20]}...{self.address[-8:]}{RESET}")
        print(f"{BLUE}──────────────────────────────────────────────────{RESET}")
        print(f"{WHITE}💰 USDC Balance: {balance:.6f}{RESET}")
        print(f"{WHITE}💶 EURC Balance: {eurc_balance:.6f}{RESET}")
        print(f"{WHITE}🎫 LP Token Balance: {lp_balance:.10f}{RESET}")
        print(f"{WHITE}🏦 xyUSDC (Vault): {vault_balance:.6f}{RESET}")
        print(f"{BLUE}──────────────────────────────────────────────────{RESET}")
        print(f"{MAGENTA}📊 SYBIL STATUS{RESET}")
        print(f"{WHITE}   Risk Level: {risk_display}{RESET}")
        print(f"{WHITE}   Quality: {tier_display}{RESET}")
        print(f"{WHITE}   Points: {self.get_points_display()}{RESET}")
        print(f"{WHITE}   Volumes: {self.get_volumes_display()}{RESET}")
        print(f"{BLUE}══════════════════════════════════════════════════{RESET}")
        print(f"{BOLD}{WHITE}1. 🔄 SWAP (USDC → EURC){RESET}")
        print(f"{BOLD}{WHITE}2. 🌉 BRIDGE (Arc → Sepolia){RESET}")
        print(f"{BOLD}{YELLOW}3. 🏦 VAULT DEPOSIT{RESET}")
        print(f"{BOLD}{YELLOW}4. 💧 ADD LIQUIDITY{RESET}")
        print(f"{BOLD}{YELLOW}5. 🔥 REMOVE LIQUIDITY{RESET}")
        print(f"{BOLD}{GREEN}6. 🤖 AUTO MODE (Human-Like){RESET}")
        print(f"{BOLD}{CYAN}7. 📊 REFRESH SYBIL STATUS{RESET}")
        print(f"{BOLD}{WHITE}8. 🚪 EXIT{RESET}")
        print(f"{BLUE}══════════════════════════════════════════════════{RESET}")

    def refresh_sybil_status(self):
        print(f"\n{BOLD}{CYAN}═══════════ 📊 SYBIL STATUS ═══════════{RESET}")
        print(f"{YELLOW}Fetching latest data...{RESET}")
        
        if self.fetch_points_data():
            print(f"{GREEN}✅ Data fetched successfully!{RESET}\n")
            
            risk_display, tier_display = self.get_sybil_status_display()
            
            print(f"{MAGENTA}📊 SYBIL ANALYSIS{RESET}")
            print(f"{BLUE}──────────────────────────────────────────────────{RESET}")
            print(f"{WHITE}Risk Level: {risk_display}{RESET}")
            print(f"{WHITE}Quality Tier: {tier_display}{RESET}")
            print(f"{BLUE}──────────────────────────────────────────────────{RESET}")
            
            print(f"\n{MAGENTA}📈 POINTS BREAKDOWN{RESET}")
            print(f"{BLUE}──────────────────────────────────────────────────{RESET}")
            if self.points_data:
                print(f"{WHITE}Total Points: {self.points_data.get('total_points', 0)}{RESET}")
                print(f"{WHITE}Volume Points: {self.points_data.get('volume_points', 0)}{RESET}")
                print(f"{WHITE}Milestone Points: {self.points_data.get('milestone_points', 0)}{RESET}")
                print(f"{WHITE}First Interaction Points: {self.points_data.get('first_interaction_points', 0)}{RESET}")
                print(f"{WHITE}Referral Points: {self.points_data.get('referral_points', 0)}{RESET}")
                print(f"{WHITE}Social Points: {self.points_data.get('social_points', 0)}{RESET}")
            print(f"{BLUE}──────────────────────────────────────────────────{RESET}")
            
            print(f"\n{MAGENTA}📊 VOLUME STATISTICS{RESET}")
            print(f"{BLUE}──────────────────────────────────────────────────{RESET}")
            if self.points_data:
                volumes = self.points_data.get('volumes', {})
                print(f"{WHITE}Swap Volume: ${volumes.get('swap', 0)}{RESET}")
                print(f"{WHITE}Bridge Volume: ${volumes.get('bridge', 0)}{RESET}")
                print(f"{WHITE}Vault Volume: ${volumes.get('vault', 0)}{RESET}")
                print(f"{WHITE}PayX Sent: ${volumes.get('payx_sent', 0)}{RESET}")
            print(f"{BLUE}──────────────────────────────────────────────────{RESET}")
            
            print(f"\n{MAGENTA}🏆 ACTIVITY STATS{RESET}")
            print(f"{BLUE}──────────────────────────────────────────────────{RESET}")
            if self.points_data:
                activity = self.points_data.get('activity', {})
                print(f"{WHITE}Products Used: {activity.get('products_used', 0)}{RESET}")
                print(f"{WHITE}Active Days: {activity.get('active_days', 0)}{RESET}")
                print(f"{WHITE}First Activity: {activity.get('first_activity_at', 'N/A')}{RESET}")
                print(f"{WHITE}Last Activity: {activity.get('last_activity_at', 'N/A')}{RESET}")
                print(f"{WHITE}Referral Code: {self.points_data.get('referral_code', 'N/A')}{RESET}")
                print(f"{WHITE}Successful Referrals: {self.points_data.get('successful_referrals', 0)}{RESET}")
            print(f"{BLUE}──────────────────────────────────────────────────{RESET}")
            
            # Tips based on tier
            if self.points_data:
                tier = self.points_data.get('quality_tier', {}).get('tier', '')
                print(f"\n{YELLOW}💡 TIPS TO IMPROVE SCORE:{RESET}")
                if tier == 'Suspected':
                    print(f"{WHITE}  • Use different amounts for each transaction{RESET}")
                    print(f"{WHITE}  • Add more delay between transactions{RESET}")
                    print(f"{WHITE}  • Use all products (swap, bridge, vault, liquidity){RESET}")
                    print(f"{WHITE}  • Spread activity across multiple days{RESET}")
                    print(f"{WHITE}  • Avoid repetitive patterns{RESET}")
                elif tier == 'Organic':
                    print(f"{WHITE}  • Great job! Keep using the platform naturally{RESET}")
                    print(f"{WHITE}  • Refer friends to earn more points{RESET}")
                else:
                    print(f"{WHITE}  • Continue using the platform regularly{RESET}")
                    print(f"{WHITE}  • Try different features{RESET}")
        else:
            print(f"{RED}❌ Failed to fetch data!{RESET}")

    def run(self):
        clear_screen()
        
        print(f"{BOLD}{BLUE}══════════════════════════════════════════════════{RESET}")
        print(f"{BOLD}{CYAN}           🌐 XYLONET TESTNET BOT 🌐{RESET}")
        print(f"{BOLD}{WHITE}              Created by KAZUHA{RESET}")
        print(f"{BOLD}{BLUE}══════════════════════════════════════════════════{RESET}")
        
        if not self.load_private_key():
            return
        
        if not self.arc_web3.is_connected():
            print(f"{RED}❌ ERROR: Cannot connect to Arc Testnet RPC!{RESET}")
            return
        
        print(f"{GREEN}✅ Wallet: {self.address}{RESET}")
        print(f"{GREEN}✅ Connected to Arc Testnet{RESET}")
        
        # Fetch initial sybil status
        print(f"{YELLOW}📊 Fetching sybil status...{RESET}")
        self.fetch_points_data()
        
        risk_display, tier_display = self.get_sybil_status_display()
        print(f"{MAGENTA}📊 Sybil Risk: {risk_display}{RESET}")
        print(f"{MAGENTA}📊 Quality Tier: {tier_display}{RESET}")
        
        time.sleep(3)
        
        while True:
            self.show_menu()
            choice = input(f"{BOLD}{WHITE}Select option (1-8): {RESET}")
            
            if choice == "1":
                self.swap()
            elif choice == "2":
                self.bridge()
            elif choice == "3":
                self.vault_deposit()
            elif choice == "4":
                self.add_liquidity()
            elif choice == "5":
                self.remove_liquidity()
            elif choice == "6":
                self.auto_all()
            elif choice == "7":
                self.refresh_sybil_status()
            elif choice == "8":
                clear_screen()
                print(f"{GREEN}👋 Goodbye!{RESET}")
                break
            else:
                print(f"{RED}❌ Invalid option! Please select 1-8{RESET}")
            
            input(f"\n{WHITE}Press Enter to continue...{RESET}")


if __name__ == "__main__":
    bot = XyloNetBot()
    bot.run()
