from web3 import Web3
from web3.exceptions import TransactionNotFound
from eth_account import Account
from aiohttp import ClientResponseError, ClientSession, ClientTimeout, BasicAuth
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import init, Fore, Style, Back
import asyncio, random, json, re, os, pytz, time

init(autoreset=True)

class Bitverse:
    def __init__(self) -> None:
        self.BASE_API = "https://api.bitverse.zone/bitverse"
        self.RPC_URL = "https://atlantic.dplabs-internal.com/"
        self.EXPLORER = "https://atlantic.pharosscan.xyz/tx/"
        self.USDT_CONTRACT_ADDRESS = "0xE7E84B8B4f39C507499c40B4ac199B050e2882d5"
        self.POSITION_ROUTER_ADDRESS = "0xEcbAc797f28f412ddF0D38B50f5B4a6904d46e0A"
        self.TRADE_ROUTER_ADDRESS = "0xeA2fC1300ac31Afd77Cf5d5D240B69e38308a90C"
        
        self.PHRS_CONTRACT_ADDRESS = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"  
        self.DODO_ROUTER_ADDRESS = "0x819829e5CF6e19F9fED92F6b4CC1edF45a2cC4A2"
        
        self.CONTRACT_ABI = [
            {
                "inputs": [
                    { "internalType": "address", "name": "owner", "type": "address" },
                    { "internalType": "address", "name": "spender", "type": "address" }
                ],
                "name": "allowance",
                "outputs": [
                    { "internalType": "uint256", "name": "", "type": "uint256" }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    { "internalType": "address", "name": "spender", "type": "address" },
                    { "internalType": "uint256", "name": "value", "type": "uint256" }
                ],
                "name": "approve",
                "outputs": [
                    { "internalType": "bool", "name": "", "type": "bool" }
                ],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    { "internalType": "address", "name": "account", "type": "address" }
                ],
                "name": "balanceOf",
                "outputs": [
                    { "internalType": "uint256", "name": "", "type": "uint256" }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "decimals",
                "outputs": [
                    { "internalType": "uint8", "name": "", "type": "uint8" }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    { "name": "token", "type": "address" },
                    { "name": "amount", "type": "uint256" }
                ],
                "name": "deposit",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    { "name": "token", "type": "address" },
                    { "name": "amount", "type": "uint256" }
                ],
                "name": "withdraw",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    { "internalType": "string", "name": "pairId", "type": "string" },
                    { "internalType": "uint256", "name": "price", "type": "uint256" },
                    { "internalType": "uint8", "name": "orderType", "type": "uint8" },
                    { "internalType": "uint64", "name": "leverageE2", "type": "uint64" },
                    { "internalType": "uint8", "name": "side", "type": "uint8" },
                    { "internalType": "uint64", "name": "slippageE6", "type": "uint64" },
                    {
                        "components": [
                            { "internalType": "address", "name": "token", "type": "address" },
                            { "internalType": "uint256", "name": "amount", "type": "uint256" }
                        ],
                        "internalType": "struct Margin[]",
                        "name": "margins",
                        "type": "tuple[]"
                    },
                    { "internalType": "uint256", "name": "takeProfitPrice", "type": "uint256" },
                    { "internalType": "uint256", "name": "stopLossPrice", "type": "uint256" },
                    { "internalType": "uint256", "name": "positionLongOI", "type": "uint256" },
                    { "internalType": "uint256", "name": "positionShortOI", "type": "uint256" },
                    { "internalType": "uint256", "name": "timestamp", "type": "uint256" },
                    { "internalType": "bytes", "name": "signature", "type": "bytes" },
                    { "internalType": "bool", "name": "isExecuteImmediately", "type": "bool" },
                    { "internalType": "uint8", "name": "marginMode", "type": "uint8" }
                ],
                "name": "placeOrder",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]

        self.HEADERS = {}
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.used_nonce = {}
        self.accounts_data = {}
        
        # Fixed parameters
        self.deposit_amount = 5.0
        self.withdraw_amount = 1.5
        self.swap_amount = 0.001
        self.trade_count = 99
        self.min_delay = 3
        self.max_delay = 8
        self.use_proxy = False
        self.current_name = ""

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_banner(self):
        print(Fore.CYAN + Style.BRIGHT + "="*70)
        print(Fore.YELLOW + Style.BRIGHT + "          BITVERSE AUTO BOT v2.0 ")
        print(Fore.GREEN + Style.BRIGHT + "        CREATED BY KAZUHA | VIP ONLY ")
        print(Fore.CYAN + Style.BRIGHT + "="*70)
        print()

    def log_info(self, msg):
        print(f"{Fore.YELLOW + Style.BRIGHT}[{self.current_name}] {Fore.CYAN + Style.BRIGHT}[INFO] {Fore.WHITE + Style.BRIGHT}{msg}")

    def log_success(self, msg):
        print(f"{Fore.YELLOW + Style.BRIGHT}[{self.current_name}] {Fore.GREEN + Style.BRIGHT}[SUCCESS] {Fore.WHITE + Style.BRIGHT}{msg}")

    def log_error(self, msg):
        print(f"{Fore.YELLOW + Style.BRIGHT}[{self.current_name}] {Fore.RED + Style.BRIGHT}[ERROR] {Fore.WHITE + Style.BRIGHT}{msg}")

    def log_warn(self, msg):
        print(f"{Fore.YELLOW + Style.BRIGHT}[{self.current_name}] {Fore.YELLOW + Style.BRIGHT}[WARN] {Fore.WHITE + Style.BRIGHT}{msg}")

    def log_tx(self, tx_hash, block_number):
        """Special logger for transaction details with custom colors"""
        print(f"{Fore.YELLOW + Style.BRIGHT}[{self.current_name}] {Fore.GREEN + Style.BRIGHT}[SUCCESS] {Fore.MAGENTA + Style.BRIGHT}Block: {Fore.WHITE + Style.BRIGHT}{block_number}")
        print(f"{Fore.YELLOW + Style.BRIGHT}[{self.current_name}] {Fore.CYAN + Style.BRIGHT}[TX] {Fore.MAGENTA + Style.BRIGHT}Hash: {tx_hash}")
        print(f"{Fore.YELLOW + Style.BRIGHT}[{self.current_name}] {Fore.CYAN + Style.BRIGHT}[EXPLORER] {Fore.GREEN + Style.BRIGHT}{self.EXPLORER}{tx_hash}")

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    def load_accounts(self):
        """Load accounts from pv.txt in privatekey:name format"""
        try:
            if not os.path.exists('pv.txt'):
                print(Fore.RED + Style.BRIGHT + "[ERROR] File pv.txt Not Found.")
                return []
            
            accounts = []
            with open('pv.txt', 'r') as file:
                for line in file:
                    line = line.strip()
                    if line and ':' in line:
                        private_key, name = line.split(':', 1)
                        private_key = private_key.strip()
                        name = name.strip()
                        accounts.append(private_key)
                        self.accounts_data[private_key] = name
            
            if not accounts:
                print(Fore.RED + Style.BRIGHT + "[ERROR] No valid accounts found in pv.txt")
                return []
            
            print(Fore.GREEN + Style.BRIGHT + f"[SUCCESS] Loaded {Fore.WHITE + Style.BRIGHT}{len(accounts)}{Fore.GREEN + Style.BRIGHT} accounts")
            return accounts
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"[ERROR] Failed to load accounts: {e}")
            return []
    
    async def load_proxies(self):
        filename = "proxy.txt"
        try:
            if not os.path.exists(filename):
                print(Fore.YELLOW + Style.BRIGHT + "[WARN] No proxy.txt found - Running without proxy")
                self.use_proxy = False
                return
            
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                print(Fore.YELLOW + Style.BRIGHT + "[WARN] No proxies in file - Running without proxy")
                self.use_proxy = False
                return

            self.use_proxy = True
            print(Fore.GREEN + Style.BRIGHT + f"[SUCCESS] Loaded {Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Fore.GREEN + Style.BRIGHT} proxies - Running with proxy")
        
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"[ERROR] Failed To Load Proxies: {e} - Running without proxy")
            self.use_proxy = False
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, token):
        if token not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[token] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[token]

    def rotate_proxy_for_account(self, token):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[token] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def build_proxy_config(self, proxy=None):
        if not proxy:
            return None, None, None

        if proxy.startswith("socks"):
            connector = ProxyConnector.from_url(proxy)
            return connector, None, None

        elif proxy.startswith("http"):
            match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
            if match:
                username, password, host_port = match.groups()
                clean_url = f"http://{host_port}"
                auth = BasicAuth(username, password)
                return None, clean_url, auth
            else:
                return None, proxy, None

        raise Exception("Unsupported Proxy Type.")
    
    def generate_address(self, account: str):
        try:
            account = Account.from_key(account)
            address = account.address
            return address
        except Exception as e:
            return None
        
    def mask_account(self, account):
        try:
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            return None
    
    def get_account_name(self, private_key):
        """Get the name associated with a private key"""
        return self.accounts_data.get(private_key, "Unknown")
        
    def generate_trade_option(self):
        trade_pair = random.choice(["BTC-USD", "ETH-USD"])
        return trade_pair, 1  # Always return 1 for Long trades only
    
    def generate_order_payload(self, address: str, trade_pair: str, acceptable_price: int, trade_side: int, trade_amount: float):
        payload = {
            "address": address,
            "pair": trade_pair,
            "price": str(acceptable_price),
            "orderType": 2,
            "leverageE2": 500,
            "side": trade_side,
            "margin": [
                { "denom": "USDT", "amount": str(int(trade_amount)) }
            ],
            "allowedSlippage": "10",
            "isV2": "0"
        }
        return payload
        
    async def get_web3_with_check(self, address: str, use_proxy: bool, retries=3, timeout=60):
        request_kwargs = {"timeout": timeout}

        proxy = self.get_next_proxy_for_account(address) if use_proxy else None

        if use_proxy and proxy:
            request_kwargs["proxies"] = {"http": proxy, "https": proxy}

        for attempt in range(retries):
            try:
                web3 = Web3(Web3.HTTPProvider(self.RPC_URL, request_kwargs=request_kwargs))
                web3.eth.get_block_number()
                return web3
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
                raise Exception(f"Failed to Connect to RPC: {str(e)}")
        
    async def get_token_balance(self, address: str, contract_address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            token_contract = web3.eth.contract(address=web3.to_checksum_address(contract_address), abi=self.CONTRACT_ABI)
            balance = token_contract.functions.balanceOf(address).call()
            decimals = token_contract.functions.decimals().call()

            token_balance = balance / (10 ** decimals)

            return token_balance
        except Exception as e:
            self.log_error(f"Get Token Balance: {str(e)}")
            return None

    async def get_native_balance(self, address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)
            balance = web3.eth.get_balance(address)
            return web3.from_wei(balance, 'ether')
        except Exception as e:
            self.log_error(f"Get Native Balance: {str(e)}")
            return None
    
    async def send_raw_transaction_with_retries(self, account, web3, tx, retries=5):
        for attempt in range(retries):
            try:
                signed_tx = web3.eth.account.sign_transaction(tx, account)
                raw_tx = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                tx_hash = web3.to_hex(raw_tx)
                return tx_hash
            except TransactionNotFound:
                pass
            except Exception as e:
                if "execution reverted" not in str(e).lower():
                    self.log_warn(f"[Attempt {attempt + 1}] Send TX Error: {str(e)}")
                else:
                    raise e
            await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction Hash Not Found After Maximum Retries")

    async def wait_for_receipt_with_retries(self, web3, tx_hash, retries=5):
        for attempt in range(retries):
            try:
                receipt = await asyncio.to_thread(web3.eth.wait_for_transaction_receipt, tx_hash, timeout=300)
                return receipt
            except TransactionNotFound:
                pass
            except Exception as e:
                self.log_warn(f"[Attempt {attempt + 1}] Wait for Receipt Error: {str(e)}")
            await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction Receipt Not Found After Maximum Retries")
    
    async def approving_token(self, account: str, address: str, router_address: str, asset_address: str, amount: int, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)
            
            spender = web3.to_checksum_address(router_address)
            token_contract = web3.eth.contract(address=web3.to_checksum_address(asset_address), abi=self.CONTRACT_ABI)

            allowance = token_contract.functions.allowance(address, spender).call()
            if allowance < amount:
                approve_data = token_contract.functions.approve(spender, amount)
                estimated_gas = approve_data.estimate_gas({"from": address})

                max_priority_fee = web3.to_wei(1, "gwei")
                max_fee = max_priority_fee

                approve_tx = approve_data.build_transaction({
                    "from": address,
                    "gas": int(estimated_gas * 1.2),
                    "maxFeePerGas": int(max_fee),
                    "maxPriorityFeePerGas": int(max_priority_fee),
                    "nonce": self.used_nonce[address],
                    "chainId": web3.eth.chain_id,
                })

                tx_hash = await self.send_raw_transaction_with_retries(account, web3, approve_tx)
                receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)

                block_number = receipt.blockNumber
                self.used_nonce[address] += 1

                self.log_success(f"Approve Success")
                self.log_tx(tx_hash, block_number)
                await asyncio.sleep(5)

            return True
        except Exception as e:
            raise Exception(f"Approving Token Contract Failed: {str(e)}")
        
    async def perform_deposit(self, account: str, address: str, asset: str, amount: float, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            asset_address = web3.to_checksum_address(asset)
            asset_contract = web3.eth.contract(address=asset_address, abi=self.CONTRACT_ABI)
            decimals = asset_contract.functions.decimals().call()

            amount_to_wei = int(amount * (10 ** decimals))

            await self.approving_token(account, address, self.POSITION_ROUTER_ADDRESS, asset_address, amount_to_wei, use_proxy)

            contract_address = web3.to_checksum_address(self.POSITION_ROUTER_ADDRESS)
            token_contract = web3.eth.contract(address=contract_address, abi=self.CONTRACT_ABI)

            deposit_data = token_contract.functions.deposit(asset_address, amount_to_wei)
            estimated_gas = deposit_data.estimate_gas({"from": address})

            max_priority_fee = web3.to_wei(1, "gwei")
            max_fee = max_priority_fee

            deposit_tx = deposit_data.build_transaction({
                "from": web3.to_checksum_address(address),
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id,
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, deposit_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)

            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number
        except Exception as e:
            self.log_error(f"Deposit Failed: {str(e)}")
            return None, None
        
    async def perform_withdraw(self, account: str, address: str, asset: str, amount: float, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            asset_address = web3.to_checksum_address(asset)
            asset_contract = web3.eth.contract(address=asset_address, abi=self.CONTRACT_ABI)
            decimals = asset_contract.functions.decimals().call()

            amount_to_wei = int(amount * (10 ** decimals))

            contract_address = web3.to_checksum_address(self.POSITION_ROUTER_ADDRESS)
            token_contract = web3.eth.contract(address=contract_address, abi=self.CONTRACT_ABI)

            withdraw_data = token_contract.functions.withdraw(asset_address, amount_to_wei)
            estimated_gas = withdraw_data.estimate_gas({"from": address})

            max_priority_fee = web3.to_wei(1, "gwei")
            max_fee = max_priority_fee

            withdraw_tx = withdraw_data.build_transaction({
                "from": web3.to_checksum_address(address),
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id,
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, withdraw_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)

            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number
        except Exception as e:
            self.log_error(f"Withdraw Failed: {str(e)}")
            return None, None
        
    async def perform_trade(self, account: str, address: str, orders: dict, acceptable_price: int, asset: str, amount: float, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            asset_address = web3.to_checksum_address(asset)
            asset_contract = web3.eth.contract(address=asset_address, abi=self.CONTRACT_ABI)
            decimals = asset_contract.functions.decimals().call()

            amount_to_wei = int(amount * (10 ** decimals))

            pair_id = orders["result"]["pair"]
            order_type = 2
            leverage_e2 = int(orders["result"]["leverageE2"])
            side = int(orders["result"]["side"])
            slippage_e6 = int(orders["result"]["allowedSlippage"])
            margins = [(asset_address, amount_to_wei)]
            take_profit_price = 0
            stop_loss_price = 0
            position_long_oi = int(orders["result"]["longOI"])
            position_short_oi = int(orders["result"]["shortOI"])
            timestamp = int(orders["result"]["signTimestamp"])
            signature = bytes.fromhex(orders["result"]["sign"][2:])
            is_execute_immediately = bool(orders["result"]["marketOpening"])
            margin_mode = 1

            contract_address = web3.to_checksum_address(self.TRADE_ROUTER_ADDRESS)
            token_contract = web3.eth.contract(address=contract_address, abi=self.CONTRACT_ABI)

            trade_data = token_contract.functions.placeOrder(
                pair_id, acceptable_price, order_type, leverage_e2, side, slippage_e6, 
                margins, take_profit_price, stop_loss_price, position_long_oi, position_short_oi, 
                timestamp, signature, is_execute_immediately, margin_mode
            )

            estimated_gas = trade_data.estimate_gas({"from": address})

            max_priority_fee = web3.to_wei(1, "gwei")
            max_fee = max_priority_fee

            trade_tx = trade_data.build_transaction({
                "from": web3.to_checksum_address(address),
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id,
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, trade_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)

            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number
        except Exception as e:
            if "execution reverted" in str(e).lower():
                return None, None
            else:
                self.log_error(f"Trade Failed: {str(e)}")
            return None, None

    async def get_swap_route(self, address: str, amount_wei: int, use_proxy: bool):
        """Get swap route from DODO API"""
        url = "https://api.dodoex.io/route-service/v2/widget/getdodoroute"
        params = {
            "chainId": "688689",
            "fromTokenAddress": self.PHRS_CONTRACT_ADDRESS,
            "toTokenAddress": self.USDT_CONTRACT_ADDRESS,
            "fromAmount": str(amount_wei),
            "userAddr": address,
            "slippage": "10",
            "deadLine": str(int(time.time()) + 600),
            "source": "dodoV2AndMixWasm",
            "estimateGas": "true",
            "apikey": "a37546505892e1a952"
        }

        for attempt in range(100):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=40)) as session:
                    async with session.get(url, params=params, proxy=proxy, proxy_auth=proxy_auth) as response:
                        data = await response.json()
                        if data.get("status") == 200:
                            return data["data"]
                        else:
                            self.log_warn(f"No route found (attempt {attempt + 1})")
            except Exception as e:
                self.log_warn(f"Route request failed (attempt {attempt + 1}): {str(e)}")
            
            await asyncio.sleep(2)
        
        return None

    async def perform_swap(self, account: str, address: str, use_proxy: bool):
        """Perform PHRS to USDT swap"""
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)
            
            balance = await self.get_native_balance(address, use_proxy)
            if balance is None:
                return None, None

            if balance < self.swap_amount + 0.0005:
                self.log_warn(f"Insufficient PHRS balance: {balance:.6f}")
                return None, None

            amount_wei = int(self.swap_amount * 1e18)
            route = await self.get_swap_route(address, amount_wei, use_proxy)
            if not route:
                self.log_error("Failed to get swap route")
                return None, None

            swap_tx = {
                'to': web3.to_checksum_address(self.DODO_ROUTER_ADDRESS),
                'data': route["data"],
                'value': int(route["value"]),
                'gas': int(route["gasLimit"]) + 250000,
                'maxFeePerGas': web3.to_wei(random.uniform(3.2, 4.8), 'gwei'),
                'maxPriorityFeePerGas': web3.to_wei(random.uniform(1.6, 3.0), 'gwei'),
                'nonce': self.used_nonce[address],
                'chainId': web3.eth.chain_id
            }

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, swap_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)

            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number

        except Exception as e:
            self.log_error(f"Swap Failed: {str(e)}")
            return None, None
        
    async def print_timer(self):
        delay = random.randint(self.min_delay, self.max_delay)
        for remaining in range(delay, 0, -1):
            print(
                f"{Fore.CYAN + Style.BRIGHT}[TIMER]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} Wait {remaining} seconds for next action...{Style.RESET_ALL}",
                end="\r",
                flush=True
            )
            await asyncio.sleep(1)
        print(" " * 80, end="\r")  # Clear the line
    
    async def check_connection(self, proxy_url=None):
        connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=10)) as session:
                async with session.get(url="https://api.ipify.org?format=json", proxy=proxy, proxy_auth=proxy_auth) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError) as e:
            self.log_error(f"Connection Not 200 OK - {str(e)}")
            return None
        
    async def get_all_balance(self, address: str, use_proxy: bool, retries=5):
        url = f"{self.BASE_API}/trade-data/v1/account/balance/allCoinBalance"
        data = json.dumps({"address":address})
        headers = {
            **self.HEADERS[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries:
                    await asyncio.sleep(5)
                    continue
                self.log_error(f"Fetch Deposited USDT Token Balance Failed - {str(e)}")
                return None
        
    async def get_market_price(self, address: str, trade_pair: str, use_proxy: bool, retries=5):
        url = f"{self.BASE_API}/quote-all-in-one/v1/public/market/ticker?symbol={trade_pair}"
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=self.HEADERS[address], proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries:
                    await asyncio.sleep(5)
                    continue
                self.log_error(f"Fetch {trade_pair} Market Price Failed - {str(e)}")
                return None
        
    async def order_simulation(self, address: str, trade_pair: str, acceptable_price: int, trade_side: int, trade_amount: float, use_proxy: bool, retries=5):
        url = f"{self.BASE_API}/trade-data/v1/order/simulation/pendingOrder"
        data = json.dumps(self.generate_order_payload(address, trade_pair, acceptable_price, trade_side, trade_amount))
        headers = {
            **self.HEADERS[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries:
                    await asyncio.sleep(5)
                    continue
                self.log_error(f"Built Order Simulation Failed - {str(e)}")
                return None
    
    async def run_all_features(self, account: str, address: str):
        """Run all features in sequence: Swap -> Deposit -> Withdraw -> 99 Trades"""
        
        # Initialize nonce
        try:
            web3 = await self.get_web3_with_check(address, self.use_proxy)
            self.used_nonce[address] = web3.eth.get_transaction_count(address, "pending")
        except Exception as e:
            self.log_error(f"Web3 Not Connected - {str(e)}")
            return

        # 1. SWAP (PHRS → USDT)
        print(Fore.YELLOW + Style.BRIGHT + f"\n{'='*70}")
        print(Fore.YELLOW + Style.BRIGHT + f"STEP 1: SWAP PHRS → USDT")
        print(Fore.YELLOW + Style.BRIGHT + f"{'='*70}")
        
        self.log_info(f"Amount: {self.swap_amount} PHRS")
        
        balance = await self.get_native_balance(address, self.use_proxy)
        if balance:
            self.log_info(f"PHRS Balance: {balance:.6f}")
            if balance >= self.swap_amount + 0.0005:
                tx_hash, block_number = await self.perform_swap(account, address, self.use_proxy)
                if tx_hash and block_number:
                    self.log_success(f"Swap Success")
                    self.log_tx(tx_hash, block_number)
                else:
                    self.log_error("Swap Failed")
            else:
                self.log_warn("Insufficient PHRS Balance for swap")
        
        await self.print_timer()

        # 2. DEPOSIT USDT
        print(Fore.YELLOW + Style.BRIGHT + f"\n{'='*70}")
        print(Fore.YELLOW + Style.BRIGHT + f"STEP 2: DEPOSIT USDT")
        print(Fore.YELLOW + Style.BRIGHT + f"{'='*70}")
        
        self.log_info(f"Amount: {self.deposit_amount} USDT")
        
        balance = await self.get_token_balance(address, self.USDT_CONTRACT_ADDRESS, self.use_proxy)
        if balance is not None:
            self.log_info(f"USDT Balance: {balance}")
            if balance >= self.deposit_amount:
                tx_hash, block_number = await self.perform_deposit(account, address, self.USDT_CONTRACT_ADDRESS, self.deposit_amount, self.use_proxy)
                if tx_hash and block_number:
                    self.log_success(f"Deposit Success")
                    self.log_tx(tx_hash, block_number)
                else:
                    self.log_error("Deposit Failed")
            else:
                self.log_warn("Insufficient USDT Balance for deposit")
        
        await self.print_timer()

        # 3. WITHDRAW USDT
        print(Fore.YELLOW + Style.BRIGHT + f"\n{'='*70}")
        print(Fore.YELLOW + Style.BRIGHT + f"STEP 3: WITHDRAW USDT")
        print(Fore.YELLOW + Style.BRIGHT + f"{'='*70}")
        
        self.log_info(f"Amount: {self.withdraw_amount} USDT")
        
        all_balance = await self.get_all_balance(address, self.use_proxy)
        if all_balance and all_balance.get("retCode") == 0:
            coin_balance = all_balance.get("result", {}).get("coinBalance", [])
            usdt_data = next((coin for coin in coin_balance if coin.get("coinName") == "USDT"), None)
            balance = float(usdt_data.get("availableBalanceSize", 0) if usdt_data else 0)
            
            self.log_info(f"Deposited Balance: {balance} USDT")
            
            if balance >= self.withdraw_amount:
                tx_hash, block_number = await self.perform_withdraw(account, address, self.USDT_CONTRACT_ADDRESS, self.withdraw_amount, self.use_proxy)
                if tx_hash and block_number:
                    self.log_success(f"Withdraw Success")
                    self.log_tx(tx_hash, block_number)
                else:
                    self.log_error("Withdraw Failed")
            else:
                self.log_warn("Insufficient deposited USDT Balance for withdrawal")
        else:
            self.log_warn("Could not fetch deposited balance")
        
        await self.print_timer()

        # 4. 99 TRADES (LONG ONLY)
        print(Fore.YELLOW + Style.BRIGHT + f"\n{'='*70}")
        print(Fore.YELLOW + Style.BRIGHT + f"STEP 4: STARTING {self.trade_count} LONG TRADES")
        print(Fore.YELLOW + Style.BRIGHT + f"{'='*70}")
        
        successful_trades = 0
        failed_trades = 0
        
        for i in range(self.trade_count):
            print(Fore.CYAN + Style.BRIGHT + f"\n--- Trade {Fore.WHITE + Style.BRIGHT}{i+1}/{self.trade_count}{Fore.CYAN + Style.BRIGHT} ---")
            
            # Generate random trade amount between 2 and 4
            trade_amount = round(random.uniform(2.0, 4.0), 2)
            
            trade_pair, trade_side = self.generate_trade_option()  # trade_side will always be 1 (Long)
            
            self.log_info(f"Pair: {trade_pair} {Fore.GREEN + Style.BRIGHT}[Long]{Style.RESET_ALL}")
            self.log_info(f"Amount: {trade_amount} USDT")
            
            # Check balance
            all_balance = await self.get_all_balance(address, self.use_proxy)
            if not all_balance or all_balance.get("retCode") != 0:
                self.log_warn("Could not fetch balance, skipping trade")
                failed_trades += 1
                continue
            
            coin_balance = all_balance.get("result", {}).get("coinBalance", [])
            usdt_data = next((coin for coin in coin_balance if coin.get("coinName") == "USDT"), None)
            balance = float(usdt_data.get("availableBalanceSize", 0) if usdt_data else 0)
            
            self.log_info(f"Available Balance: {balance} USDT")
            
            if balance < trade_amount:
                self.log_warn("Insufficient balance for trade")
                failed_trades += 1
                continue
            
            # Get market price
            markets = await self.get_market_price(address, trade_pair, self.use_proxy)
            if not markets or markets.get("retCode") != 0:
                self.log_warn("Could not fetch market price")
                failed_trades += 1
                continue
            
            market_price = float(markets.get("result", {}).get("lastPrice"))
            self.log_info(f"Market Price: {market_price} USDT")
            
            acceptable_price_to_wei = int(market_price * (10**6))
            
            # Build order
            orders = await self.order_simulation(address, trade_pair, acceptable_price_to_wei, trade_side, trade_amount, self.use_proxy)
            if not orders or orders.get("retCode") != 0:
                self.log_warn("Could not build order simulation")
                failed_trades += 1
                continue
            
            # Execute trade
            tx_hash, block_number = await self.perform_trade(account, address, orders, acceptable_price_to_wei, self.USDT_CONTRACT_ADDRESS, trade_amount, self.use_proxy)
            if tx_hash and block_number:
                self.log_success(f"Trade Success")
                self.log_tx(tx_hash, block_number)
                successful_trades += 1
            else:
                self.log_error("Trade Failed")
                failed_trades += 1
            
            # Wait between trades
            if i < self.trade_count - 1:
                await self.print_timer()
        
        # Summary
        print(Fore.GREEN + Style.BRIGHT + f"\n{'='*70}")
        print(Fore.GREEN + Style.BRIGHT + f"ACCOUNT COMPLETED")
        print(Fore.GREEN + Style.BRIGHT + f"{'='*70}")
        print(Fore.WHITE + Style.BRIGHT + f"Successful Trades: {Fore.GREEN + Style.BRIGHT}{successful_trades}{Fore.WHITE + Style.BRIGHT}/{self.trade_count}")
        print(Fore.WHITE + Style.BRIGHT + f"Failed Trades: {Fore.RED + Style.BRIGHT}{failed_trades}{Fore.WHITE + Style.BRIGHT}/{self.trade_count}")
        print(Fore.GREEN + Style.BRIGHT + f"{'='*70}\n")

    async def main(self):
        try:
            accounts = self.load_accounts()
            if not accounts:
                return
            
            # Auto-detect proxy
            await self.load_proxies()
            
            while True:
                self.clear_terminal()
                self.print_banner()
                
                print(Fore.GREEN + Style.BRIGHT + f"[SUCCESS] Total Accounts: {Fore.WHITE + Style.BRIGHT}{len(accounts)}")
                print(Fore.CYAN + Style.BRIGHT + f"[INFO] Mode: {Fore.WHITE + Style.BRIGHT}{'WITH PROXY' if self.use_proxy else 'WITHOUT PROXY'}")
                
                for account in accounts:
                    if account:
                        address = self.generate_address(account)
                        account_name = self.get_account_name(account)
                        self.current_name = account_name

                        print(Fore.MAGENTA + Style.BRIGHT + f"\n{'='*70}")
                        print(Fore.MAGENTA + Style.BRIGHT + f"Processing Account: {Fore.WHITE + Style.BRIGHT}{account_name}")
                        print(Fore.MAGENTA + Style.BRIGHT + f"Address: {Fore.WHITE + Style.BRIGHT}{self.mask_account(address)}")
                        print(Fore.MAGENTA + Style.BRIGHT + f"{'='*70}")

                        if not address:
                            self.log_error("Invalid Private Key")
                            continue

                        # Check connection if using proxy
                        if self.use_proxy:
                            proxy = self.get_next_proxy_for_account(address)
                            self.log_info(f"Using Proxy: {proxy}")
                            is_valid = await self.check_connection(proxy)
                            if not is_valid:
                                self.log_warn("Proxy connection failed, continuing without proxy for this account")
                                use_proxy_for_account = False
                            else:
                                use_proxy_for_account = True
                        else:
                            use_proxy_for_account = False

                        self.HEADERS[address] = {
                            "Accept": "application/json, text/plain, */*",
                            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                            "Chain-Id": "688689",
                            "Origin": "https://testnet.bitverse.zone",
                            "Referer": "https://testnet.bitverse.zone/",
                            "Sec-Fetch-Dest": "empty",
                            "Sec-Fetch-Mode": "cors",
                            "Sec-Fetch-Site": "same-site",
                            "Tenant-Id": "ATLANTIC",
                            "User-Agent": FakeUserAgent().random
                        }

                        # Run all features for this account
                        await self.run_all_features(account, address)
                        
                        # Small delay before next account
                        await asyncio.sleep(5)

                print(Fore.GREEN + Style.BRIGHT + f"\n{'='*70}")
                print(Fore.GREEN + Style.BRIGHT + "=== ALL ACCOUNTS COMPLETED ===")
                print(Fore.GREEN + Style.BRIGHT + f"{'='*70}\n")
                
                # Wait 24 hours before next cycle
                seconds = 24 * 60 * 60
                while seconds > 0:
                    formatted_time = self.format_seconds(seconds)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[WAIT]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} | Next cycle in 24 hours...{Style.RESET_ALL}",
                        end="\r"
                    )
                    await asyncio.sleep(1)
                    seconds -= 1

        except FileNotFoundError:
            print(Fore.RED + Style.BRIGHT + "[ERROR] File 'pv.txt' Not Found.")
            return
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"[ERROR] {e}")
            raise e

if __name__ == "__main__":
    try:
        bot = Bitverse()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(Fore.YELLOW + Style.BRIGHT + "\n\nStopped by user")
        print(Fore.GREEN + Style.BRIGHT + f"{'='*70}")
        print(Fore.RED + Style.BRIGHT + "[ EXIT ] Bitverse Auto BOT")
        print(Fore.GREEN + Style.BRIGHT + f"{'='*70}\n")