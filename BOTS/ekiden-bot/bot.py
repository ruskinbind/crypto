import os
import sys
import json
import time
import secrets
import base64
import hashlib
import requests
import random

try:
    from nacl.signing import SigningKey
except ImportError:
    os.system('pip install pynacl')
    from nacl.signing import SigningKey

try:
    from colorama import init
    init()
except ImportError:
    os.system('pip install colorama')
    from colorama import init
    init()

# ==================== CONFIGURATION ====================
APTOS_API = "https://api.testnet.aptoslabs.com/v1"
EKIDEN_API = "https://api.dev.ekiden.fi/api/v1"
EKIDEN_CONTRACT = "0x639080a71042d462174cb6664b0e9f4adfb39bff58ee2e8646651666049c4777"
USDC_METADATA = "0x6208945221b7430d1083e5967d812c0f40cc89682923305429704f89f3f28a86"
APT_METADATA = "0xa"
MIN_SIZE = 0.00001

SYMBOLS = ["BTC-USDC", "ETH-USDC", "SOL-USDC", "APT-USDC"]

# ==================== COLORS ====================
class C:
    R = '\033[1;91m'
    G = '\033[1;92m'
    Y = '\033[1;93m'
    B = '\033[1;94m'
    M = '\033[1;95m'
    C = '\033[1;96m'
    W = '\033[1;97m'
    E = '\033[0m'

def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""{C.C}
    ============================================================
              EKIDEN DEX TRADING BOT - APTOS TESTNET
                  CREATED BY KAZUHA - VIP ONLY
    ============================================================{C.E}
    """)

def menu():
    print(f"""
    {C.G}[1]{C.W} Claim Faucet
    {C.G}[2]{C.W} Deposit
    {C.G}[3]{C.W} Withdrawal
    {C.G}[4]{C.W} Transfer
    {C.G}[5]{C.W} Open Position
    {C.G}[6]{C.W} Close Position / Cancel Orders
    {C.G}[7]{C.W} Auto All
    {C.G}[8]{C.W} Exit
    """)

def ok(m): print(f"    {C.G}[OK]{C.W} {m}{C.E}")
def err(m): print(f"    {C.R}[ERROR]{C.W} {m}{C.E}")
def info(m): print(f"    {C.C}[INFO]{C.W} {m}{C.E}")
def warn(m): print(f"    {C.Y}[WAIT]{C.W} {m}{C.E}")

# ==================== LOAD KEYS ====================
def load_keys():
    keys = []
    
    if not os.path.exists("pv.txt"):
        err("pv.txt not found!")
        print(f"""
    {C.Y}Create pv.txt with your Aptos private keys (one per line):{C.E}
    
    {C.W}0xPRIVATE_KEY_1{C.E}
    {C.W}0xPRIVATE_KEY_2{C.E}
    {C.W}0xPRIVATE_KEY_3{C.E}
        """)
        return []
    
    with open("pv.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            key = line.strip()
            if key and not key.startswith('#'):
                keys.append(key)
    
    if not keys:
        err("No private keys found in pv.txt!")
    
    return keys

# ==================== LOAD PROXIES ====================
def load_proxies():
    proxies = []
    
    if not os.path.exists("proxy.txt"):
        info("proxy.txt not found, running without proxy")
        return []
    
    with open("proxy.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            proxy = line.strip()
            if proxy and not proxy.startswith('#'):
                proxies.append(proxy)
    
    if proxies:
        ok(f"Loaded {len(proxies)} proxies")
    
    return proxies

def parse_proxy(proxy_str):
    """
    Supports formats:
    - ip:port
    - ip:port:user:pass
    - user:pass@ip:port
    - http://ip:port
    - http://user:pass@ip:port
    """
    if not proxy_str:
        return None
    
    proxy_str = proxy_str.strip()
    
    # Remove http:// or https:// prefix
    if proxy_str.startswith('http://'):
        proxy_str = proxy_str[7:]
    elif proxy_str.startswith('https://'):
        proxy_str = proxy_str[8:]
    
    # Format: user:pass@ip:port
    if '@' in proxy_str:
        auth, host = proxy_str.rsplit('@', 1)
        if ':' in auth:
            user, passwd = auth.split(':', 1)
            proxy_url = f"http://{user}:{passwd}@{host}"
        else:
            proxy_url = f"http://{proxy_str}"
    # Format: ip:port:user:pass
    elif proxy_str.count(':') == 3:
        parts = proxy_str.split(':')
        ip, port, user, passwd = parts
        proxy_url = f"http://{user}:{passwd}@{ip}:{port}"
    # Format: ip:port
    else:
        proxy_url = f"http://{proxy_str}"
    
    return {
        "http": proxy_url,
        "https": proxy_url
    }

# ==================== APTOS ACCOUNT ====================
class AptosAccount:
    def __init__(self, private_key_hex):
        if private_key_hex.startswith('0x'):
            private_key_hex = private_key_hex[2:]
        
        key_bytes = bytes.fromhex(private_key_hex)
        
        if len(key_bytes) == 64:
            key_bytes = key_bytes[:32]
        
        self.signing_key = SigningKey(key_bytes)
        self.verify_key = self.signing_key.verify_key
        self.private_key = key_bytes
        self.public_key = bytes(self.verify_key)
        
        hasher = hashlib.sha3_256()
        hasher.update(self.public_key + b'\x00')
        self.address = '0x' + hasher.hexdigest()
    
    def get_public_key_hex(self):
        return '0x' + self.public_key.hex()
    
    def sign(self, message):
        if isinstance(message, str):
            message = message.encode('utf-8')
        signed = self.signing_key.sign(message)
        return signed.signature
    
    def sign_hex(self, message):
        sig = self.sign(message)
        return '0x' + sig.hex()

# ==================== EKIDEN CLIENT ====================
class EkidenClient:
    def __init__(self, account, proxy=None):
        self.account = account
        self.session = requests.Session()
        self.proxy = parse_proxy(proxy) if proxy else None
        self.token = None
        self.funding_address = None
        self.trading_address = None
        
        if self.proxy:
            self.session.proxies.update(self.proxy)
    
    def headers(self, auth=False):
        h = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Origin': 'https://app.ekiden.fi',
            'Referer': 'https://app.ekiden.fi/',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36'
        }
        if auth and self.token:
            h['Authorization'] = f'Bearer {self.token}'
        return h
    
    def aptos_headers(self):
        return {
            'Content-Type': 'application/json',
            'x-aptos-client': 'aptos-typescript-sdk/5.2.0'
        }
    
    def authorize(self):
        warn("Authorizing...")
        
        try:
            timestamp_ms = int(time.time() * 1000)
            nonce = base64.urlsafe_b64encode(secrets.token_bytes(16)).decode().rstrip('=')
            full_message = f"APTOS\nmessage: AUTHORIZE|{timestamp_ms}|{nonce}\nnonce: {nonce}"
            signature = self.account.sign_hex(full_message)
            
            payload = {
                "signature": signature,
                "public_key": self.account.get_public_key_hex(),
                "timestamp_ms": timestamp_ms,
                "nonce": nonce,
                "full_message": full_message
            }
            
            resp = self.session.post(f"{EKIDEN_API}/authorize", json=payload, headers=self.headers(), timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get('token')
                ok("Authorized")
                return True
            else:
                err(f"Auth failed: {resp.text}")
                return False
        except Exception as e:
            err(f"Auth error: {e}")
            return False
    
    def claim_faucet(self):
        warn("Claiming faucet...")
        
        try:
            payload = {
                "receiver": self.account.address,
                "metadatas": [USDC_METADATA, APT_METADATA],
                "amounts": [10000000, 50000000]
            }
            
            resp = self.session.post(f"{EKIDEN_API}/account/fund", json=payload, headers=self.headers(auth=True), timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                txid = data.get('txid', '')
                ok(f"Faucet: {txid[:30]}...")
                return True
            else:
                err(f"Faucet failed: {resp.text}")
                return False
        except Exception as e:
            err(f"Faucet error: {e}")
            return False
    
    def get_balance(self):
        try:
            resp = self.session.get(f"{EKIDEN_API}/account/balance", headers=self.headers(auth=True), timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                for bal in data.get('list', []):
                    if bal.get('account_type') == 'funding':
                        self.funding_address = bal.get('sub_account_address')
                    elif bal.get('account_type') == 'cross':
                        self.trading_address = bal.get('sub_account_address')
                return data
            return None
        except Exception as e:
            err(f"Balance error: {e}")
            return None
    
    def show_balance(self):
        data = self.get_balance()
        if not data:
            err("Failed to get balance")
            return
        
        print(f"    {C.C}{'-'*50}{C.E}")
        for bal in data.get('list', []):
            acc_type = bal.get('account_type', 'unknown').upper()
            equity = float(bal.get('equity', 0))
            available = float(bal.get('available_balance', 0))
            print(f"    {C.G}{acc_type}:{C.W} ${equity:.4f} (Avail: ${available:.4f}){C.E}")
    
    def get_account_info(self):
        try:
            resp = self.session.get(f"{APTOS_API}/accounts/{self.account.address}", headers=self.aptos_headers(), timeout=30)
            if resp.status_code == 200:
                return resp.json()
            return None
        except:
            return None
    
    def submit_transaction(self, payload):
        try:
            account_info = self.get_account_info()
            if not account_info:
                err("Failed to get account info")
                return None
            
            seq_num = int(account_info.get('sequence_number', 0))
            expiration = int(time.time()) + 600
            
            txn_request = {
                "sender": self.account.address,
                "sequence_number": str(seq_num),
                "max_gas_amount": "10000",
                "gas_unit_price": "100",
                "expiration_timestamp_secs": str(expiration),
                "payload": payload
            }
            
            encode_resp = self.session.post(
                f"{APTOS_API}/transactions/encode_submission",
                json=txn_request,
                headers=self.aptos_headers(),
                timeout=30
            )
            
            if encode_resp.status_code != 200:
                err(f"Encode failed")
                return None
            
            encoded_hex = encode_resp.json()
            if encoded_hex.startswith('0x'):
                encoded_hex = encoded_hex[2:]
            
            to_sign = bytes.fromhex(encoded_hex)
            signature = self.account.sign(to_sign)
            
            signed_txn = {
                **txn_request,
                "signature": {
                    "type": "ed25519_signature",
                    "public_key": self.account.get_public_key_hex(),
                    "signature": "0x" + signature.hex()
                }
            }
            
            submit_resp = self.session.post(
                f"{APTOS_API}/transactions",
                json=signed_txn,
                headers=self.aptos_headers(),
                timeout=30
            )
            
            if submit_resp.status_code in [200, 202]:
                return submit_resp.json().get('hash')
            else:
                err(f"Submit failed")
                return None
        except Exception as e:
            err(f"TX error: {e}")
            return None
    
    def wait_tx(self, tx_hash, timeout=30):
        warn("Confirming...")
        start = time.time()
        
        while time.time() - start < timeout:
            try:
                resp = self.session.get(f"{APTOS_API}/transactions/by_hash/{tx_hash}", headers=self.aptos_headers(), timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('success') == True:
                        ok(f"TX: {tx_hash[:25]}...")
                        return True
                    elif data.get('success') == False:
                        err(f"TX failed")
                        return False
                
                time.sleep(1)
            except:
                time.sleep(1)
        
        err("TX timeout")
        return False
    
    def deposit(self, amount):
        if not self.funding_address:
            self.get_balance()
        
        if not self.funding_address:
            err("Funding address not found")
            return False
        
        warn(f"Depositing {amount} USDC...")
        
        amount_raw = int(amount * 1_000_000)
        
        payload = {
            "type": "entry_function_payload",
            "function": f"{EKIDEN_CONTRACT}::vault::deposit_into_funding",
            "type_arguments": [],
            "arguments": [
                self.funding_address,
                USDC_METADATA,
                str(amount_raw)
            ]
        }
        
        tx_hash = self.submit_transaction(payload)
        if tx_hash:
            return self.wait_tx(tx_hash)
        return False
    
    def withdraw(self, amount):
        if not self.funding_address:
            self.get_balance()
        
        if not self.funding_address:
            err("Funding address not found")
            return False
        
        warn(f"Withdrawing {amount} USDC...")
        
        amount_raw = int(amount * 1_000_000)
        
        payload = {
            "type": "entry_function_payload",
            "function": f"{EKIDEN_CONTRACT}::vault::withdraw_from_funding",
            "type_arguments": [],
            "arguments": [
                self.funding_address,
                USDC_METADATA,
                str(amount_raw)
            ]
        }
        
        tx_hash = self.submit_transaction(payload)
        if tx_hash:
            return self.wait_tx(tx_hash)
        return False
    
    def transfer(self, amount, to_trading=True):
        if not self.funding_address or not self.trading_address:
            self.get_balance()
        
        if not self.funding_address or not self.trading_address:
            err("Addresses not found")
            return False
        
        direction = "Funding->Trading" if to_trading else "Trading->Funding"
        warn(f"Transfer {amount} USDC ({direction})...")
        
        amount_raw = int(amount * 1_000_000)
        
        if to_trading:
            from_addr = self.funding_address
            to_addr = self.trading_address
            type_arg = f"{EKIDEN_CONTRACT}::vault_types::Cross"
        else:
            from_addr = self.trading_address
            to_addr = self.funding_address
            type_arg = f"{EKIDEN_CONTRACT}::vault_types::Funding"
        
        payload = {
            "type": "entry_function_payload",
            "function": f"{EKIDEN_CONTRACT}::vault::transfer_request",
            "type_arguments": [type_arg],
            "arguments": [
                from_addr,
                to_addr,
                str(amount_raw)
            ]
        }
        
        tx_hash = self.submit_transaction(payload)
        if tx_hash:
            return self.wait_tx(tx_hash)
        return False
    
    def get_ticker(self, symbol="BTC-USDC"):
        try:
            resp = self.session.get(f"{EKIDEN_API}/market/tickers?symbol={symbol}", headers=self.headers(), timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('list'):
                    return data['list'][0]
            return None
        except:
            return None
    
    def place_order(self, symbol, side, qty, price, order_type="Limit", reduce_only=False):
        if not self.trading_address:
            self.get_balance()
        
        if not self.trading_address:
            err("Trading address not found")
            return None
        
        warn(f"Placing {side} {symbol}...")
        
        try:
            payload = {
                "sub_account_address": self.trading_address,
                "symbol": symbol,
                "side": side,
                "order_type": order_type,
                "qty": f"{qty:.14f}",
                "price": f"{price:.6f}" if order_type == "Limit" else "0",
                "margin_mode": "Cross",
                "time_in_force": "GTC" if order_type == "Limit" else "IOC",
                "post_only": False,
                "reduce_only": reduce_only,
                "close_on_trigger": False
            }
            
            resp = self.session.post(f"{EKIDEN_API}/order/place", json=payload, headers=self.headers(auth=True), timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                order_id = data.get('order_id')
                ok(f"Order: {order_id[:20]}...")
                return order_id
            else:
                err(f"Order failed: {resp.text[:50]}")
                return None
        except Exception as e:
            err(f"Order error: {e}")
            return None
    
    def get_open_orders(self):
        if not self.trading_address:
            self.get_balance()
        
        if not self.trading_address:
            return []
        
        try:
            resp = self.session.get(
                f"{EKIDEN_API}/order/realtime?sub_account_address={self.trading_address}&open_only=true",
                headers=self.headers(auth=True),
                timeout=15
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return data.get('list', [])
            return []
        except:
            return []
    
    def cancel_orders(self, orders):
        if not orders:
            return False
        
        warn(f"Cancelling {len(orders)} orders...")
        
        try:
            request_list = []
            for order in orders:
                request_list.append({
                    "sub_account_address": self.trading_address,
                    "symbol": order.get('symbol'),
                    "order_id": order.get('order_id')
                })
            
            payload = {"request": request_list}
            
            resp = self.session.post(
                f"{EKIDEN_API}/order/cancel-batch",
                json=payload,
                headers=self.headers(auth=True),
                timeout=30
            )
            
            if resp.status_code == 200:
                ok(f"Cancelled {len(orders)} orders")
                return True
            else:
                err(f"Cancel failed")
                return False
        except Exception as e:
            err(f"Cancel error: {e}")
            return False
    
    def get_open_positions(self):
        if not self.trading_address:
            self.get_balance()
        
        if not self.trading_address:
            return []
        
        try:
            resp = self.session.get(
                f"{EKIDEN_API}/position/list?sub_account_address={self.trading_address}",
                headers=self.headers(auth=True),
                timeout=15
            )
            
            if resp.status_code == 200:
                data = resp.json()
                positions = []
                for pos in data.get('list', []):
                    if float(pos.get('size', 0)) > 0:
                        positions.append(pos)
                return positions
            return []
        except:
            return []
    
    def close_position(self, symbol, size, side):
        close_side = "Sell" if side == "Buy" else "Buy"
        return self.place_order(
            symbol=symbol,
            side=close_side,
            qty=size,
            price=0,
            order_type="Market",
            reduce_only=True
        )

# ==================== HELPER ====================
def get_float(prompt):
    while True:
        try:
            val = input(f"    {C.Y}{prompt}:{C.E} ").replace(',', '').strip()
            if val == '':
                continue
            return float(val)
        except ValueError:
            err("Invalid number")

def show_accounts(accounts):
    print(f"\n    {C.C}{'='*55}{C.E}")
    print(f"    {C.Y}LOADED ACCOUNTS: {len(accounts)}{C.E}")
    print(f"    {C.C}{'='*55}{C.E}")
    for i, acc in enumerate(accounts, 1):
        print(f"    {C.G}[{i}]{C.W} {acc['address'][:20]}...{acc['address'][-8:]}{C.E}")
        if acc['proxy']:
            print(f"        {C.M}Proxy: {acc['proxy'][:30]}...{C.E}")
    print(f"    {C.C}{'='*55}{C.E}")

# ==================== PROCESS FOR ALL ACCOUNTS ====================
def process_all(clients, action, **kwargs):
    print(f"\n    {C.M}Processing {len(clients)} account(s)...{C.E}\n")
    
    for i, client in enumerate(clients, 1):
        print(f"    {C.C}{'='*55}{C.E}")
        print(f"    {C.Y}[Account {i}/{len(clients)}]{C.E}")
        print(f"    {C.W}Address: {client.account.address[:25]}...{C.E}")
        print(f"    {C.C}{'-'*55}{C.E}")
        
        try:
            action(client, **kwargs)
        except Exception as e:
            err(f"Error: {e}")
        
        if i < len(clients):
            delay = random.randint(3, 7)
            info(f"Waiting {delay}s...")
            time.sleep(delay)
    
    print(f"\n    {C.G}{'='*55}{C.E}")
    ok(f"All {len(clients)} accounts processed!")
    print(f"    {C.G}{'='*55}{C.E}")

def action_faucet(client):
    client.claim_faucet()

def action_deposit(client, amount):
    if client.deposit(amount):
        ok("Deposit complete")

def action_withdraw(client, amount):
    if client.withdraw(amount):
        ok("Withdraw complete")

def action_transfer(client, amount, to_trading):
    if client.transfer(amount, to_trading):
        ok("Transfer complete")

def action_open(client, symbol, side, amount):
    ticker = client.get_ticker(symbol)
    if not ticker:
        err("Failed to get price")
        return
    
    price = float(ticker.get('mark_price', 0))
    qty = amount / price
    if qty < MIN_SIZE:
        qty = MIN_SIZE
    
    side_name = "LONG" if side == "Buy" else "SHORT"
    info(f"{side_name} {symbol}: {qty:.8f} @ ${price:,.2f}")
    
    order_id = client.place_order(symbol, side, qty, price, "Limit")
    if order_id:
        ok(f"{side_name} opened")

def action_close(client):
    # Cancel all orders first
    orders = client.get_open_orders()
    if orders:
        client.cancel_orders(orders)
    
    # Close all positions
    positions = client.get_open_positions()
    if positions:
        for pos in positions:
            symbol = pos.get('symbol')
            side = pos.get('side')
            size = float(pos.get('size', 0))
            if size > 0:
                client.close_position(symbol, size, side)
    else:
        info("No positions to close")

def action_auto(client, amount):
    symbol = random.choice(SYMBOLS)
    
    # Step 1: Faucet
    info("Step 1: Faucet")
    client.claim_faucet()
    time.sleep(2)
    
    # Step 2: Deposit
    info("Step 2: Deposit")
    client.deposit(amount)
    time.sleep(2)
    
    # Step 3: Transfer
    info("Step 3: Transfer to Trading")
    client.transfer(amount, to_trading=True)
    time.sleep(2)
    
    # Step 4: Open
    info(f"Step 4: Open Position ({symbol})")
    ticker = client.get_ticker(symbol)
    if ticker:
        price = float(ticker.get('mark_price', 0))
        qty = amount / price
        if qty < MIN_SIZE:
            qty = MIN_SIZE
        
        side = random.choice(["Buy", "Sell"])
        client.place_order(symbol, side, qty, price, "Limit")
    time.sleep(3)
    
    # Step 5: Cancel Orders
    info("Step 5: Cancel Orders")
    orders = client.get_open_orders()
    if orders:
        client.cancel_orders(orders)
    time.sleep(2)
    
    # Step 6: Close Positions
    info("Step 6: Close Positions")
    positions = client.get_open_positions()
    for pos in positions:
        if pos.get('symbol') == symbol:
            size = float(pos.get('size', 0))
            if size > 0:
                client.close_position(symbol, size, pos.get('side'))
    time.sleep(2)
    
    # Step 7: Transfer back
    info("Step 7: Transfer to Funding")
    client.get_balance()
    balance_data = client.get_balance()
    if balance_data:
        for bal in balance_data.get('list', []):
            if bal.get('account_type') == 'cross':
                avail = float(bal.get('available_balance', 0))
                if avail > 0.01:
                    client.transfer(avail * 0.99, to_trading=False)
    time.sleep(2)
    
    # Step 8: Withdraw
    info("Step 8: Withdraw")
    client.get_balance()
    balance_data = client.get_balance()
    if balance_data:
        for bal in balance_data.get('list', []):
            if bal.get('account_type') == 'funding':
                avail = float(bal.get('available_balance', 0))
                if avail > 0.01:
                    client.withdraw(avail * 0.99)
    
    ok("Auto complete!")

# ==================== MAIN ====================
def main():
    banner()
    
    # Load keys
    keys = load_keys()
    if not keys:
        input(f"\n    {C.Y}Press Enter to exit...{C.E}")
        return
    
    ok(f"Loaded {len(keys)} private key(s)")
    
    # Load proxies
    proxies = load_proxies()
    
    # Create accounts
    accounts = []
    clients = []
    
    for i, key in enumerate(keys):
        try:
            account = AptosAccount(key)
            proxy = proxies[i] if i < len(proxies) else None
            
            accounts.append({
                "address": account.address,
                "proxy": proxy
            })
            
            client = EkidenClient(account, proxy)
            clients.append(client)
            
        except Exception as e:
            err(f"Invalid key #{i+1}: {e}")
    
    if not clients:
        err("No valid accounts!")
        input(f"\n    {C.Y}Press Enter to exit...{C.E}")
        return
    
    show_accounts(accounts)
    
    # Authorize all
    print(f"\n    {C.M}Authorizing all accounts...{C.E}\n")
    valid_clients = []
    
    for i, client in enumerate(clients, 1):
        print(f"    {C.Y}[{i}/{len(clients)}]{C.W} {client.account.address[:25]}...{C.E}")
        if client.authorize():
            client.get_balance()
            valid_clients.append(client)
        time.sleep(1)
    
    if not valid_clients:
        err("No accounts authorized!")
        input(f"\n    {C.Y}Press Enter to exit...{C.E}")
        return
    
    ok(f"{len(valid_clients)}/{len(clients)} accounts ready")
    clients = valid_clients
    
    # Main loop
    while True:
        menu()
        choice = input(f"    {C.Y}Choice [1-8]:{C.E} ").strip()
        
        if choice == '1':
            print(f"\n    {C.C}{'='*55}{C.E}")
            print(f"    {C.Y}CLAIM FAUCET{C.E}")
            print(f"    {C.C}{'='*55}{C.E}")
            process_all(clients, action_faucet)
        
        elif choice == '2':
            print(f"\n    {C.C}{'='*55}{C.E}")
            print(f"    {C.Y}DEPOSIT{C.E}")
            print(f"    {C.C}{'='*55}{C.E}")
            amount = get_float("Amount (USDC)")
            if amount > 0:
                process_all(clients, action_deposit, amount=amount)
        
        elif choice == '3':
            print(f"\n    {C.C}{'='*55}{C.E}")
            print(f"    {C.Y}WITHDRAW{C.E}")
            print(f"    {C.C}{'='*55}{C.E}")
            amount = get_float("Amount (USDC)")
            if amount > 0:
                process_all(clients, action_withdraw, amount=amount)
        
        elif choice == '4':
            print(f"\n    {C.C}{'='*55}{C.E}")
            print(f"    {C.Y}TRANSFER{C.E}")
            print(f"    {C.C}{'='*55}{C.E}")
            print(f"    {C.G}[1]{C.W} Funding -> Trading{C.E}")
            print(f"    {C.G}[2]{C.W} Trading -> Funding{C.E}")
            d = input(f"    {C.Y}Select [1-2]:{C.E} ").strip()
            if d in ['1', '2']:
                amount = get_float("Amount (USDC)")
                if amount > 0:
                    process_all(clients, action_transfer, amount=amount, to_trading=(d=='1'))
        
        elif choice == '5':
            print(f"\n    {C.C}{'='*55}{C.E}")
            print(f"    {C.Y}OPEN POSITION{C.E}")
            print(f"    {C.C}{'='*55}{C.E}")
            print(f"    {C.G}[1]{C.W} BTC-USDC{C.E}")
            print(f"    {C.G}[2]{C.W} ETH-USDC{C.E}")
            print(f"    {C.G}[3]{C.W} SOL-USDC{C.E}")
            print(f"    {C.G}[4]{C.W} APT-USDC{C.E}")
            sym = input(f"    {C.Y}Select symbol [1-4]:{C.E} ").strip()
            symbol_map = {'1': 'BTC-USDC', '2': 'ETH-USDC', '3': 'SOL-USDC', '4': 'APT-USDC'}
            if sym in symbol_map:
                print(f"    {C.G}[1]{C.W} LONG{C.E}")
                print(f"    {C.G}[2]{C.W} SHORT{C.E}")
                sd = input(f"    {C.Y}Select [1-2]:{C.E} ").strip()
                if sd in ['1', '2']:
                    side = "Buy" if sd == '1' else "Sell"
                    amount = get_float("USDC Amount")
                    if amount > 0:
                        process_all(clients, action_open, symbol=symbol_map[sym], side=side, amount=amount)
        
        elif choice == '6':
            print(f"\n    {C.C}{'='*55}{C.E}")
            print(f"    {C.Y}CLOSE ALL POSITIONS & CANCEL ORDERS{C.E}")
            print(f"    {C.C}{'='*55}{C.E}")
            process_all(clients, action_close)
        
        elif choice == '7':
            print(f"\n    {C.C}{'='*55}{C.E}")
            print(f"    {C.Y}AUTO ALL{C.E}")
            print(f"    {C.C}{'='*55}{C.E}")
            amount = get_float("USDC Amount")
            num_trades = 1
            try:
                n = input(f"    {C.Y}Number of trades [1-10]:{C.E} ").strip()
                if n:
                    num_trades = max(1, min(10, int(n)))
            except:
                pass
            
            if amount > 0:
                for t in range(num_trades):
                    print(f"\n    {C.M}=== TRADE {t+1}/{num_trades} ==={C.E}")
                    process_all(clients, action_auto, amount=amount)
                    if t < num_trades - 1:
                        delay = random.randint(5, 10)
                        info(f"Waiting {delay}s before next trade...")
                        time.sleep(delay)
        
        elif choice == '8':
            print(f"\n    {C.M}Goodbye! - KAZUHA VIP{C.E}")
            break
        
        else:
            err("Invalid choice")
        
        input(f"\n    {C.Y}Press Enter...{C.E}")
        banner()
        show_accounts(accounts)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n    {C.M}Goodbye!{C.E}")
        sys.exit(0)