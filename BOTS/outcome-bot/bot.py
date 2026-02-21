#!/usr/bin/env python3
"""
OUTCOME MARKET AUTO TRADING BOT v7.0
- Multi Account Support
- Proxy Support
- Fixed Market Loading
- Auto Trading
"""

import sys
import time
import requests
from datetime import datetime
from typing import Optional, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

try:
    from eth_account import Account
    from eth_account.messages import encode_defunct
    from colorama import init, Fore, Style
except ImportError:
    print("Install: pip install eth-account requests colorama")
    sys.exit(1)

init(autoreset=True)

G = Fore.GREEN + Style.BRIGHT
R = Fore.RED + Style.BRIGHT
Y = Fore.YELLOW + Style.BRIGHT
C = Fore.CYAN + Style.BRIGHT
W = Fore.WHITE + Style.BRIGHT
M = Fore.MAGENTA + Style.BRIGHT
B = Fore.BLUE + Style.BRIGHT
RST = Style.RESET_ALL

class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"

class Asset(Enum):
    YES = "YES"
    NO = "NO"

def ts():
    return datetime.now().strftime("%H:%M:%S")

def log(level, msg, color=W):
    print(f"{W}[{ts()}] {color}[{level}] {msg}{RST}")

def log_ok(msg): log("OK", msg, G)
def log_err(msg): log("ERROR", msg, R)
def log_warn(msg): log("WARN", msg, Y)
def log_info(msg): log("INFO", msg, C)
def log_step(n, t, msg): log(f"STEP {n}/{t}", msg, Y)
def log_buy(asset, qty, price, market): log("BUY", f"{qty}x {asset} @ ${price:.2f} [{market}]", G)
def log_sell(asset, qty, price, market): log("SELL", f"{qty}x {asset} @ ${price:.2f} [{market}]", R)
def log_balance(amt): log("BALANCE", f"${amt:.2f}", G)
def log_account(idx, addr): log("ACCOUNT", f"#{idx+1} - {addr[:12]}...{addr[-6:]}", M)
def log_market(name, yes_mid, no_mid): log("MARKET", f"{name} | YES ID: {yes_mid} | NO ID: {no_mid}", B)

def header(msg):
    print(f"\n{M}{'='*60}")
    print(f" {msg}")
    print(f"{'='*60}{RST}\n")

def line():
    print(f"{C}{'-'*50}{RST}")

def load_lines(filepath: str) -> List[str]:
    try:
        with open(filepath, 'r') as f:
            return [l.strip() for l in f.readlines() if l.strip()]
    except:
        return []

def load_private_keys() -> List[str]:
    keys = load_lines("pv.txt")
    result = []
    for key in keys:
        key = key.replace("Bearer ", "").strip()
        if not key.startswith("0x"):
            key = f"0x{key}"
        result.append(key)
    return result

def load_tokens() -> List[str]:
    tokens = load_lines("token.txt")
    return [t.replace("Bearer ", "").strip() for t in tokens]

def load_proxies() -> List[str]:
    return load_lines("proxy.txt")


class API:
    BASE = "https://testnet.outcome.market"
    CHAIN = 999
    
    def __init__(self, pk: str, token: str, proxy: str = None):
        self.pk = pk
        self.acc = Account.from_key(pk)
        self.addr = self.acc.address
        self.jwt = token
        self.proxy = proxy
        self.contract = ""
        self.balance = 0.0
        self.trading_enabled = False
        self.sess = requests.Session()
        self._setup()
    
    def _setup(self):
        self.sess.headers.update({
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": self.BASE,
            "referer": f"{self.BASE}/events",
            "authorization": f"Bearer {self.jwt}",
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        })
        
        if self.proxy:
            self.sess.proxies = {"http": self.proxy, "https": self.proxy}
    
    def _req(self, method: str, ep: str, data: dict = None) -> Tuple[bool, Any]:
        url = f"{self.BASE}{ep}"
        try:
            if method == "GET":
                r = self.sess.get(url, timeout=30)
            else:
                r = self.sess.post(url, json=data, timeout=30)
            
            if r.status_code == 200:
                try:
                    return True, r.json()
                except:
                    return True, {}
            elif r.status_code == 500:
                try:
                    return False, r.json()
                except:
                    return False, {}
            return False, {}
        except Exception as e:
            log_err(f"Request error: {e}")
            return False, {}
    
    def validate(self) -> bool:
        ok, data = self._req("GET", "/api/auth/validate")
        return ok and data.get("valid", False)
    
    def get_me(self) -> bool:
        ok, data = self._req("GET", "/api/me")
        if ok and data.get("id"):
            self.contract = data.get("contract_address", "")
            self.trading_enabled = data.get("trading_enabled", False)
            return True
        return False
    
    def get_balance(self) -> float:
        ok, data = self._req("GET", "/api/me/balance")
        if ok and "balance" in data:
            self.balance = int(data["balance"].get("available", 0)) / 1_000_000
            return self.balance
        return 0
    
    def _sign(self, msg: str) -> str:
        h = encode_defunct(text=msg)
        sig = self.acc.sign_message(h)
        s = sig.signature.hex()
        return s if s.startswith("0x") else f"0x{s}"
    
    def enable_trading(self) -> bool:
        if self.trading_enabled:
            return True
        msg = f"Enable Trading on Outcome Market\nAddress: {self.addr}\nChain ID: {self.CHAIN}"
        sig = self._sign(msg)
        ok, data = self._req("POST", "/api/enable-trading", {"signature": sig})
        if ok and data.get("success"):
            tx = data.get("data", {}).get("transactionHash", "")
            log_ok(f"Enable TX: {tx[:30]}...")
            time.sleep(3)
            self._req("POST", "/api/enable-trading/enable-trading-status", {"transactionHash": tx})
            self.trading_enabled = True
            return True
        return False
    
    def faucet(self, amt: int = 100) -> Tuple[bool, str]:
        addr = self.contract if self.contract else self.addr
        ok, data = self._req("POST", "/api/faucet", {"address": addr, "amount": amt})
        if ok and data.get("txHash"):
            return True, data['txHash'][:30]
        error = data.get("error", "") if data else ""
        if "maximum" in error.lower() or "3 mints" in error.lower():
            return False, "Daily limit (3/3)"
        return False, error if error else "Failed"
    
    def get_events(self) -> List[dict]:
        """Get all active events"""
        ok, data = self._req("GET", "/api/events?status=ACTIVE")
        if ok:
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get("events", data.get("data", []))
        return []
    
    def get_event_detail(self, event_id: int) -> dict:
        """Get event details with markets"""
        ok, data = self._req("GET", f"/api/events/{event_id}")
        if ok and data:
            return data
        return {}
    
    def order(self, mid: int, side: Side, asset: Asset, qty: int, price: float, nick: str) -> bool:
        payload = {
            "market_id": mid,
            "OrderSide": side.value,
            "OrderType": "MARKET",
            "limit_price": f"{price:.2f}",
            "quantity": str(qty),
            "asset": asset.value,
            "slippage": 0.2,
            "eventNickname": nick
        }
        ok, data = self._req("POST", "/api/orders", payload)
        if ok and (data.get("status") == 200 or data.get("orderId")):
            log_ok(f"Order: {data.get('orderId', 'OK')}")
            return True
        log_err(f"Order failed: {data}")
        return False


class Bot:
    # Known working markets - fallback if API fails
    KNOWN_MARKETS = [
        {"name": "BTC3", "yes_mid": 402, "no_mid": 403, "yes_p": 0.20, "no_p": 0.80},
        {"name": "HYPE3", "yes_mid": 410, "no_mid": 411, "yes_p": 0.19, "no_p": 0.85},
        {"name": "DOGE", "yes_mid": 412, "no_mid": 413, "yes_p": 0.61, "no_p": 0.40},
        {"name": "BTC>=110K", "yes_mid": 450, "no_mid": 451, "yes_p": 0.48, "no_p": 0.53},
    ]
    
    def __init__(self):
        self.accounts: List[API] = []
        self.markets: List[dict] = []
        self.total = 0
        self.success = 0
        self.failed = 0
    
    def load_accounts(self, keys: List[str], tokens: List[str], proxies: List[str]):
        for i, key in enumerate(keys):
            token = tokens[i] if i < len(tokens) else ""
            proxy = proxies[i] if i < len(proxies) else None
            if not token:
                log_warn(f"Account #{i+1} - No token")
                continue
            try:
                self.accounts.append(API(key, token, proxy))
            except Exception as e:
                log_err(f"Account #{i+1} load error: {e}")
    
    def init_account(self, api: API, idx: int) -> bool:
        log_account(idx, api.addr)
        
        if not api.validate():
            log_err("Token invalid/expired")
            return False
        
        if not api.get_me():
            log_err("Failed to get user")
            return False
        
        api.get_balance()
        log_balance(api.balance)
        
        if not api.trading_enabled:
            log_info("Enabling trading...")
            api.enable_trading()
        
        log_ok("Ready")
        return True
    
    def load_markets(self, api: API) -> List[dict]:
        """Load markets from API or use known markets"""
        log_info("Loading markets...")
        
        markets = []
        events = api.get_events()
        
        if events:
            log_info(f"Found {len(events)} events from API")
            
            for event in events[:15]:
                event_id = event.get("id")
                if not event_id:
                    continue
                
                # Get event details
                detail = api.get_event_detail(event_id)
                if not detail:
                    continue
                
                name = detail.get("nickname", detail.get("title", f"Event{event_id}"))[:20]
                event_markets = detail.get("markets", [])
                
                if len(event_markets) >= 2:
                    # Get YES and NO market
                    yes_market = None
                    no_market = None
                    
                    for m in event_markets:
                        outcome = m.get("outcome", m.get("asset", ""))
                        if outcome == "YES":
                            yes_market = m
                        elif outcome == "NO":
                            no_market = m
                    
                    # If not found by outcome, use first two
                    if not yes_market and len(event_markets) >= 1:
                        yes_market = event_markets[0]
                    if not no_market and len(event_markets) >= 2:
                        no_market = event_markets[1]
                    
                    if yes_market and no_market:
                        yes_mid = yes_market.get("id")
                        no_mid = no_market.get("id")
                        yes_p = float(yes_market.get("lastPrice", yes_market.get("last_price", 0.50)))
                        no_p = float(no_market.get("lastPrice", no_market.get("last_price", 0.50)))
                        
                        if yes_mid and no_mid:
                            markets.append({
                                "name": name,
                                "yes_mid": yes_mid,
                                "no_mid": no_mid,
                                "yes_p": yes_p if yes_p > 0 else 0.50,
                                "no_p": no_p if no_p > 0 else 0.50
                            })
                            log_market(name, yes_mid, no_mid)
                
                time.sleep(0.3)  # Rate limit
        
        # Fallback to known markets if none found
        if not markets:
            log_warn("Using known markets (API returned none)")
            markets = self.KNOWN_MARKETS.copy()
            for m in markets:
                log_market(m["name"], m["yes_mid"], m["no_mid"])
        
        log_ok(f"Total {len(markets)} markets loaded")
        return markets
    
    def claim_faucet(self, api: API, times: int):
        if times <= 0:
            return
        
        header(f"FAUCET - {times} claims")
        claimed = 0
        
        for i in range(1, times + 1):
            log_step(i, times, "Claiming...")
            ok, msg = api.faucet(100)
            
            if ok:
                claimed += 1
                log_ok(f"TX: {msg}")
                api.get_balance()
                log_balance(api.balance)
            else:
                log_warn(msg)
                if "limit" in msg.lower() or "3/3" in msg:
                    break
            
            if i < times:
                time.sleep(3)
        
        log_info(f"Claimed {claimed} times")
    
    def trade_cycle(self, api: API, market: dict, qty: int):
        """Single trade cycle on a market"""
        name = market["name"]
        yes_mid = market["yes_mid"]
        no_mid = market["no_mid"]
        yes_p = market.get("yes_p", 0.50)
        no_p = market.get("no_p", 0.50)
        
        if yes_p <= 0: yes_p = 0.50
        if no_p <= 0: no_p = 0.50
        
        # BUY YES
        log_step(1, 4, "Buy YES")
        buy_yes = min(yes_p + 0.05, 0.95)
        log_buy("YES", qty, buy_yes, name)
        if api.order(yes_mid, Side.BUY, Asset.YES, qty, buy_yes, name):
            self.success += 1
        else:
            self.failed += 1
        self.total += 1
        time.sleep(2)
        
        # BUY NO
        log_step(2, 4, "Buy NO")
        buy_no = min(no_p + 0.05, 0.95)
        log_buy("NO", qty, buy_no, name)
        if api.order(no_mid, Side.BUY, Asset.NO, qty, buy_no, name):
            self.success += 1
        else:
            self.failed += 1
        self.total += 1
        time.sleep(2)
        
        # SELL YES
        log_step(3, 4, "Sell YES")
        sell_yes = max(yes_p - 0.05, 0.05)
        log_sell("YES", qty, sell_yes, name)
        if api.order(yes_mid, Side.SELL, Asset.YES, qty, sell_yes, name):
            self.success += 1
        else:
            self.failed += 1
        self.total += 1
        time.sleep(2)
        
        # SELL NO
        log_step(4, 4, "Sell NO")
        sell_no = max(no_p - 0.05, 0.05)
        log_sell("NO", qty, sell_no, name)
        if api.order(no_mid, Side.SELL, Asset.NO, qty, sell_no, name):
            self.success += 1
        else:
            self.failed += 1
        self.total += 1
    
    def run_account(self, api: API, idx: int, faucet: int, cycles: int, qty: int, delay: int):
        header(f"ACCOUNT #{idx+1}")
        
        if not self.init_account(api, idx):
            log_err("Skip account")
            return
        
        # Faucet
        self.claim_faucet(api, faucet)
        
        # Load markets
        self.markets = self.load_markets(api)
        
        if not self.markets:
            log_err("No markets")
            return
        
        # Trading
        header(f"TRADING - {len(self.markets)} markets x {cycles} cycles")
        
        market_count = 0
        for market in self.markets:
            market_count += 1
            
            for c in range(1, cycles + 1):
                log_info(f"[{market_count}/{len(self.markets)}] {market['name']} - Cycle {c}/{cycles}")
                line()
                
                self.trade_cycle(api, market, qty)
                
                if c < cycles:
                    log_info(f"Wait {delay}s...")
                    time.sleep(delay)
            
            time.sleep(1)
        
        api.get_balance()
        log_balance(api.balance)
    
    def stats(self):
        header("STATS")
        print(f"  Total: {W}{self.total}{RST}")
        print(f"  {G}Success: {self.success}{RST}")
        print(f"  {R}Failed: {self.failed}{RST}")
        if self.total > 0:
            print(f"  {C}Rate: {(self.success/self.total)*100:.1f}%{RST}")
        line()


def get_int(prompt: str, default: int) -> int:
    try:
        val = input(f"{C}{prompt} [{default}]: {RST}").strip()
        return int(val) if val else default
    except:
        return default


def main():
    print(f"""
{M}============================================================
   OUTCOME MARKET AUTO TRADING BOT v1.0
        CREATED BY KAZUHA VIP ONLY 
============================================================{RST}
""")
    
    keys = load_private_keys()
    tokens = load_tokens()
    proxies = load_proxies()
    
    if not keys:
        print(f"{R}Create pv.txt with private keys{RST}")
        sys.exit(1)
    
    if not tokens:
        print(f"{R}Create token.txt with JWT tokens{RST}")
        sys.exit(1)
    
    log_ok(f"{len(keys)} accounts, {len(tokens)} tokens" + (f", {len(proxies)} proxies" if proxies else ""))
    
    bot = Bot()
    bot.load_accounts(keys, tokens, proxies)
    
    if not bot.accounts:
        log_err("No valid accounts")
        sys.exit(1)
    
    # Config
    header("CONFIG")
    cycles = get_int("How many trading cycles per market", 1)
    
    # Fixed config
    faucet = 3  # Max daily
    qty = 1     # Quantity per trade
    delay = 3   # Delay between cycles
    
    line()
    print(f"\n{W}Settings:{RST}")
    print(f"  Accounts: {Y}{len(bot.accounts)}{RST}")
    print(f"  Cycles/market: {Y}{cycles}{RST}")
    print(f"  Faucet: {Y}3 (max){RST}")
    print(f"  Quantity: {Y}1{RST}")
    print(f"  Delay: {Y}3s{RST}")
    line()
    
    if input(f"\n{C}Start? (y/n): {RST}").lower() != 'y':
        print(f"{Y}Cancelled{RST}")
        sys.exit(0)
    
    # Run
    try:
        for i, api in enumerate(bot.accounts):
            bot.run_account(api, i, faucet, cycles, qty, delay)
            
            if i < len(bot.accounts) - 1:
                log_info("Next account...")
                time.sleep(5)
        
        bot.stats()
        
    except KeyboardInterrupt:
        print(f"\n{Y}Stopped{RST}")
        bot.stats()
    
    print(f"\n{G}Done!{RST}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Y}Bye{RST}")
    except Exception as e:
        print(f"{R}Error: {e}{RST}")