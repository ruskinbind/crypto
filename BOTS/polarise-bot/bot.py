import json
import requests
import time
import uuid
import secrets
import os
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import pytz
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
from fake_useragent import FakeUserAgent
from colorama import Fore, Style, init

init(autoreset=True)
wib = pytz.timezone('Asia/Singapore')

def print_banner():
    print("")
    print(f"{Fore.GREEN}{Style.BRIGHT}POLARISE BOT{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}Created by KAZUHA{Style.RESET_ALL}")
    print("")

def load_referral_code(default="UnuFSe"):
    try:
        with open('code.txt', 'r', encoding='utf-8') as f:
            code = f.read().strip()
            if code:
                return code
    except:
        pass
    return default

def load_sctg_key():
    try:
        if os.path.exists("key.txt"):
            with open("key.txt", "r") as f:
                key = f.read().strip()
                if key and len(key) > 5:
                    return key
    except:
        pass
    return None

def generate_random_email():
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "proton.me"]
    username = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
    return f"{username}@{random.choice(domains)}"

REF_CODE = load_referral_code()
MAIN_USER_ID = 687512
MAIN_USER_WALLET = "0xe5e4c6e81c0dafbd76e19d1497c83fcf05a5b9e1"
MAIN_POST_ID = 145837

COMMENT_LIST = [
    "Good", "Great", "Nice", "Awesome", "Cool", "Well done", "Good job", "Solid", "Perfect", "Amazing",
    "GM", "GM Mate", "Good Morning", "Morning Mate", "Morning all", "GM everyone", "Rise and shine",
    "GN", "GN Mate", "Good Night", "Night Mate", "Sleep well", "Sweet dreams", "Rest well",
    "Hello", "Hello Mate", "Hi", "Hi Mate", "Hey", "Hey Mate", "Yo", "Yo Mate", "What's up",
    "Agree", "Totally agree", "Absolutely", "Indeed", "Exactly", "True", "Well said", "Makes sense",
    "LFG", "Let's go", "Keep going", "On fire", "Bullish", "WAGMI", "To the moon", "Big vibes",
    "Follow me", "Follow back", "Let's connect", "Support each other", "Stay connected", "Cheers"
]

POLARISE_TOPICS = {
    "core": ["ERC-1000: The Game-Changer NFT Standard", "NFT Liquidity Crisis: The Problem We're Solving", "Flash Trade Explained: Instant NFT Swaps", "P-Tokens: Your NFT's Liquid Twin"],
    "defi": ["100% LTV Loans: Too Good to Be True?", "Leverage in NFT Trading Without Getting Rekt", "Consignment: Get Paid Now, Sell Later", "Multi-Chain Strategy: Why It Matters"],
    "nft": ["Beyond JPEGs: Real NFT Utility", "Non-Standard Assets (NSA) Market Explained", "NFT Gaming & Metaverse Integration", "Digital Art vs Financial Assets: The Debate"],
    "platform": ["Polarise Testnet: Your First Steps", "From PawnFi to Polarise: The Rebrand Story", "Security First: How We Protect Your Assets", "User Experience Revolution in NFT DeFi"],
    "insights": ["The NFT Market: Dead or Just Getting Started?", "DeFi + NFTs: Why It Took So Long", "Institutional Money & NFT Liquidity", "Web3's Biggest Lie: You Own Your Assets"],
    "hot": ["OpenSea is Dead And That's Good", "Why Most NFT Projects Deserve to Fail", "The Truth About NFT Communities", "Royalties Are Killing NFTs"]
}

TOPIC_CONTENTS = {
    "ERC-1000: The Game-Changer NFT Standard": {"title": "ERC-1000: This Changes Everything for NFTs", "description": "Remember when ERC-20 changed DeFi forever? ERC-1000 is about to do the same for NFTs. Forget about illiquid JPEGs collecting digital dust. ERC-1000 introduces native liquidity pools, instant swaps, and fractional ownership baked right into the standard. What's your take?"},
    "NFT Liquidity Crisis: The Problem We're Solving": {"title": "The Dirty Secret No One Talks About: NFT Liquidity", "description": "Here's a hard truth: 95% of NFTs are basically worthless because they CAN'T BE SOLD. Floor prices? Meaningless when there's zero volume. Polarise isn't just another platform. We're solving the fundamental flaw in the NFT market."},
    "Flash Trade Explained: Instant NFT Swaps": {"title": "NFT Trading at Light Speed: Flash Trades Explained", "description": "Ever tried to sell an NFT and waited days for a buyer? Those days are OVER. Flash trades = instant NFT swaps with zero slippage. It's like Uniswap for NFTs, but faster and smarter."},
    "P-Tokens: Your NFT's Liquid Twin": {"title": "Unlock Your NFT's Value Instantly with P-Tokens", "description": "Your NFT is stuck in your wallet? Not anymore. P-Tokens = instant liquidity for ANY NFT. Wrap your NFT, Get P-Tokens, Trade lend or leverage immediately."},
    "100% LTV Loans: Too Good to Be True?": {"title": "100% LTV on NFTs: Revolutionary or Reckless?", "description": "100% loan-to-value on NFTs sounds impossible until now. Traditional finance would call this crazy. We call it innovation. This could unlock BILLIONS in trapped NFT value."},
    "Leverage in NFT Trading Without Getting Rekt": {"title": "NFT Leverage: Your Fast Track to Gains or Losses", "description": "Leverage trading NFTs = 10x your gains or 100x your losses. Polarise gives you the tools but YOU need the strategy. Key rules: Never go all-in, Set stop losses."},
    "Consignment: Get Paid Now, Sell Later": {"title": "Consignment: The Smart NFT Seller's Secret Weapon", "description": "Why wait months to sell your NFT when you can get paid NOW? Consignment = instant liquidity + future upside. Perfect for projects with long-term potential."},
    "Multi-Chain Strategy: Why It Matters": {"title": "Stuck on One Chain? You're Missing the Big Picture", "description": "Ethereum maxis vs Solana degens vs Polygon enthusiasts. Why choose when you can have ALL of them? Multi-chain isn't just a feature it's a survival strategy."},
    "Beyond JPEGs: Real NFT Utility": {"title": "NFTs Are More Than JPEGs Despite What Critics Say", "description": "JPEGs were just the beginning. Real NFT utility: Access tokens, Identity verification, Royalty streams, Governance rights, Real-world asset ownership."},
    "Non-Standard Assets (NSA) Market Explained": {"title": "NSA: The Hidden Gem of NFT Markets", "description": "Forget boring standards. NSA = Non-Standard Assets. These are the weird unique complex digital assets that don't fit in boxes. NSA market could be 10x larger than regular NFTs."},
    "NFT Gaming & Metaverse Integration": {"title": "NFT Gaming: The Next Billion-Dollar Industry", "description": "Gaming + NFTs = perfect match. Finally TRUE digital ownership in games. Cross-game assets, player-driven economies, actual value creation."},
    "Digital Art vs Financial Assets: The Debate": {"title": "Are NFTs Art or Financial Assets? Answer: BOTH", "description": "The eternal debate: Art vs Finance. Why can't they be both? Great art has ALWAYS been a financial asset. Digital art NFTs just make it accessible and liquid."},
    "Polarise Testnet: Your First Steps": {"title": "Polarise Testnet: Play with Real Money But Not Really", "description": "Testnets are boring until you're playing with real concepts. Polarise testnet = risk-free experimentation with REAL features. Zero risk maximum learning."},
    "From PawnFi to Polarise: The Rebrand Story": {"title": "PawnFi to Polarise: More Than Just a Name Change", "description": "PawnFi was good but Polarise is GREAT. Why rebrand? Broader vision, Beyond just pawn services, Complete NFT finance ecosystem."},
    "Security First: How We Protect Your Assets": {"title": "NFT Security: Our Number 1 Priority", "description": "Lose your NFTs = lose everything. Our security approach: Multi-sig everything, Regular audits, Insurance funds, Bug bounties. NOT YOUR KEYS NOT YOUR NFTS."},
    "User Experience Revolution in NFT DeFi": {"title": "NFT DeFi Doesn't Have to Be Complicated", "description": "Most DeFi platforms look like airplane dashboards. Ours? Simple intuitive HUMAN. Good UX isn't a luxury it's a requirement for mass adoption."},
    "The NFT Market: Dead or Just Getting Started?": {"title": "NFT Market Report: Far From Dead", "description": "Headlines say NFTs are dead. Data says otherwise. Less speculation more utility, Institutional interest growing, Real-world use cases emerging."},
    "DeFi + NFTs: Why It Took So Long": {"title": "DeFi + NFTs: The Marriage That Should Have Happened Years Ago", "description": "Why did it take so long to combine DeFi and NFTs? Technical challenges: Non-fungible vs fungible, Valuation problems, Liquidity issues."},
    "Institutional Money & NFT Liquidity": {"title": "Institutional Money Is Coming to NFTs", "description": "When institutions enter NFTs liquidity problems disappear. But there's a catch: They need infrastructure. That's where we come in."},
    "Web3's Biggest Lie: You Own Your Assets": {"title": "The Hard Truth: You Don't Really Own Your Web3 Assets", "description": "Full ownership in Web3 is a myth. Reality: Protocol risk, Smart contract risk, Centralized exchange risk, Regulatory risk."},
    "OpenSea is Dead And That's Good": {"title": "OpenSea's Decline: Natural Evolution or Failure?", "description": "OpenSea dominated until it didn't. What happened? Complacency, High fees, Stagnant innovation, Competition."},
    "Why Most NFT Projects Deserve to Fail": {"title": "Hard Truth: 99% of NFT Projects SHOULD Fail", "description": "Not every project deserves to succeed. Many are: Cash grabs, Copycats, No utility, Bad teams. Survival of the fittest."},
    "The Truth About NFT Communities": {"title": "NFT Communities: Real Connection or Illusion?", "description": "NFT communities promise connection but often deliver hype. Real community = shared values + mutual support."},
    "Royalties Are Killing NFTs": {"title": "Royalty Debate: Necessary Incentive or Growth Killer?", "description": "Royalties sounded great until they didn't. Problem: They discourage trading. Creators deserve rewards but not at the cost of LIQUIDITY."}
}

def log_success(msg):
    print(f"{Fore.WHITE}[{datetime.now().astimezone(wib).strftime('%H:%M:%S')}]{Style.RESET_ALL} {Fore.GREEN}{Style.BRIGHT}{msg}{Style.RESET_ALL}")

def log_error(msg):
    print(f"{Fore.WHITE}[{datetime.now().astimezone(wib).strftime('%H:%M:%S')}]{Style.RESET_ALL} {Fore.RED}{Style.BRIGHT}{msg}{Style.RESET_ALL}")

def log_warning(msg):
    print(f"{Fore.WHITE}[{datetime.now().astimezone(wib).strftime('%H:%M:%S')}]{Style.RESET_ALL} {Fore.YELLOW}{Style.BRIGHT}{msg}{Style.RESET_ALL}")

def log_info(msg):
    print(f"{Fore.WHITE}[{datetime.now().astimezone(wib).strftime('%H:%M:%S')}]{Style.RESET_ALL} {Fore.CYAN}{Style.BRIGHT}{msg}{Style.RESET_ALL}")

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_line():
    print(f"{Fore.CYAN}{Style.BRIGHT}{'─'*60}{Style.RESET_ALL}")

def print_menu():
    print("")
    print(f"{Fore.WHITE}{Style.BRIGHT}[1]{Style.RESET_ALL} Claim Faucet (Main Wallet)")
    print(f"{Fore.WHITE}{Style.BRIGHT}[2]{Style.RESET_ALL} Auto Referral (Reff + Faucet Only)")
    print(f"{Fore.WHITE}{Style.BRIGHT}[3]{Style.RESET_ALL} Complete Tasks (Main Wallet)")
    print(f"{Fore.WHITE}{Style.BRIGHT}[4]{Style.RESET_ALL} Reff Tasks (All Reff Wallets)")
    print(f"{Fore.WHITE}{Style.BRIGHT}[5]{Style.RESET_ALL} Exit")
    print("")

class PolariseBot:
    def __init__(self):
        self.base_url = "https://apia.polarise.org/api/app/v1"
        self.faucet_url = "https://apifaucet-t.polarise.org"
        self.rpc_url = "https://chainrpc.polarise.org"
        self.headers = {'accept': '*/*', 'content-type': 'application/json', 'origin': 'https://app.polarise.org', 'referer': 'https://app.polarise.org/', 'user-agent': FakeUserAgent().random}
        self.ref_code = REF_CODE
        self.main_user_wallet = MAIN_USER_WALLET
        self.main_post_id = MAIN_POST_ID
        self.sctg_key = None
        self.proxies = []
        self.all_topics = [t for topics in POLARISE_TOPICS.values() for t in topics]
        self.lock = threading.Lock()
        
        self.transfer_config = {"amount": 0.001, "gas_fee": 0.0021, "recepient": "0x9c4324156bA59a70FFbc67b98eE2EF45AEE4e19F"}
        self.donate_config = {"amount": 1, "recepient": "0x1d1afc2d015963017bed1de13e4ed6c3d3ed1618", "token_address": "0x351EF49f811776a3eE26f3A1fBc202915B8f2945", "contract_address": "0x639A8A05DAD556256046709317c76927b053a85D"}
        self.discussion_config = {"contract_address": "0x58477a0e15ae82E9839f209b13EFF25eC06c252B"}
        self.contract_abi = [
            {"inputs": [{"internalType": "address", "name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [{"internalType": "address", "name": "owner", "type": "address"}, {"internalType": "address", "name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [{"internalType": "address", "name": "spender", "type": "address"}, {"internalType": "uint256", "name": "value", "type": "uint256"}], "name": "approve", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
            {"inputs": [{"name": "receiver", "type": "address", "internalType": "address"}, {"name": "amount", "type": "uint256", "internalType": "uint256"}], "name": "donate", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
            {"type": "function", "name": "createDiscussionEvent", "inputs": [{"name": "questionId", "type": "bytes32"}, {"name": "nftMint", "type": "bool"}, {"name": "communityRecipient", "type": "address"}, {"name": "collateralToken", "type": "address"}, {"name": "endTime", "type": "uint64"}, {"name": "outcomeSlots", "type": "bytes32[]"}], "outputs": [], "stateMutability": "nonpayable"}
        ]
    
    def initialize(self):
        log_info("Initializing...")
        self.sctg_key = load_sctg_key()
        if self.sctg_key:
            log_success(f"SCTG key: {self.sctg_key[:6]}...{self.sctg_key[-4:]}")
        else:
            log_warning("No key.txt found")
        
        if os.path.exists("proxy.txt"):
            with open("proxy.txt", "r") as f:
                self.proxies = [l.strip() for l in f if l.strip()]
            if self.proxies:
                log_success(f"Proxies: {len(self.proxies)}")
        
        log_info(f"Ref code: {self.ref_code}")
        print_line()
    
    def get_proxy(self):
        if self.proxies:
            p = random.choice(self.proxies)
            return {"http": p if "://" in p else f"http://{p}", "https": p if "://" in p else f"http://{p}"}
        return None
    
    def create_wallet(self):
        pk = "0x" + secrets.token_hex(32)
        return pk, Account.from_key(pk).address
    
    def get_address(self, pk):
        try:
            return Account.from_key(pk).address
        except:
            return None
    
    def get_nonce(self, addr):
        for _ in range(3):
            try:
                r = requests.post(f"{self.base_url}/profile/getnonce", headers=self.headers, json={"wallet": addr.lower(), "chain_name": "polarise"}, timeout=30, proxies=self.get_proxy())
                if r.status_code == 200 and r.json().get("code") == "200":
                    return r.json().get("signed_nonce")
            except:
                pass
            time.sleep(2)
        return None
    
    def login(self, pk, addr, retries=3):
        for i in range(retries):
            try:
                nonce = self.get_nonce(addr)
                if not nonce:
                    time.sleep(3)
                    continue
                
                msg = f"Nonce to confirm: {nonce}"
                sig = '0x' + Account.from_key(pk).sign_message(encode_defunct(text=msg)).signature.hex()
                sid = str(uuid.uuid4())
                
                r = requests.post(f"{self.base_url}/profile/login", headers=self.headers, json={
                    "signature": sig, "chain_name": "polarise", "name": addr[:8], "nonce": nonce,
                    "wallet": addr.lower(), "sid": sid, "sub_id": sid, "inviter_code": self.ref_code
                }, timeout=30, proxies=self.get_proxy())
                
                if r.status_code == 200 and r.json().get("code") == "200":
                    token = r.json().get("data", {}).get("auth_token_info", {}).get("auth_token")
                    if token:
                        return token, sid
            except:
                pass
            if i < retries - 1:
                time.sleep(5)
        return None, None
    
    def solve_captcha(self):
        if not self.sctg_key:
            return None
        
        for api in ["https://sctg.xyz", "https://ru.sctg.xyz"]:
            try:
                r = requests.post(f"{api}/createTask", json={"clientKey": self.sctg_key, "task": {"type": "NoCaptchaTaskProxyless", "websiteURL": "https://faucet.polarise.org", "websiteKey": "6Le97hIsAAAAAFsmmcgy66F9YbLnwgnWBILrMuqn"}}, timeout=30)
                if r.json().get("errorId", 0) != 0:
                    continue
                tid = r.json().get("taskId")
                if not tid:
                    continue
                
                for _ in range(60):
                    time.sleep(3)
                    try:
                        c = requests.post(f"{api}/getTaskResult", json={"clientKey": self.sctg_key, "taskId": tid}, timeout=30).json()
                        if c.get("status") == "ready":
                            return c.get("solution", {}).get("gRecaptchaResponse")
                        elif c.get("status") == "failed":
                            break
                    except:
                        continue
            except:
                continue
        return None
    
    def claim_faucet(self, addr, captcha):
        try:
            r = requests.post(f"{self.faucet_url}/claim", headers={'content-type': 'application/json', 'origin': 'https://faucet.polarise.org', 'user-agent': FakeUserAgent().random}, json={"address": addr.lower(), "denom": "uluna", "amount": "1", "response": captcha}, timeout=60, proxies=self.get_proxy())
            if r.status_code == 200:
                return r.json().get("txhash")
        except:
            pass
        return None
    
    def get_profile(self, addr, auth, sid):
        try:
            r = requests.post(f"{self.base_url}/profile/profileinfo", headers={**self.headers, 'accesstoken': sid, 'authorization': f'Bearer {auth} {sid} {addr.lower()} polarise'}, json={"chain_name": "polarise"}, timeout=30, proxies=self.get_proxy())
            if r.status_code == 200 and r.json().get("code") == "200":
                return r.json().get("data", {})
        except:
            pass
        return None
    
    def get_tasks(self, addr, auth, sid):
        try:
            r = requests.post(f"{self.base_url}/points/tasklist", headers={**self.headers, 'accesstoken': sid, 'authorization': f'Bearer {auth} {sid} {addr.lower()} polarise'}, json={"user_wallet": addr.lower(), "chain_name": "polarise"}, timeout=30, proxies=self.get_proxy())
            if r.status_code == 200 and r.json().get("code") == "200":
                return r.json().get("data", {}).get("list", [])
        except:
            pass
        return []
    
    def complete_task(self, addr, auth, sid, tid, extra=None):
        data = {"user_wallet": addr.lower(), "task_id": tid, "chain_name": "polarise"}
        if extra:
            data["extra_info"] = extra
        try:
            r = requests.post(f"{self.base_url}/points/completetask", headers={**self.headers, 'accesstoken': sid, 'authorization': f'Bearer {auth} {sid} {addr.lower()} polarise'}, json=data, timeout=30, proxies=self.get_proxy())
            if r.status_code == 200 and r.json().get("code") == "200":
                return r.json().get("data", {}).get("finish_status")
        except:
            pass
        return None
    
    def bind_email(self, addr, auth, sid, email):
        return self.complete_task(addr, auth, sid, 3, json.dumps({"email": email})) in [1, -1]
    
    def swap_points(self, addr, auth, sid, pk, uid, uname, pts):
        nonce = self.get_nonce(addr)
        if not nonce:
            return None
        msg = f"Nonce to confirm: {nonce}"
        sig = '0x' + Account.from_key(pk).sign_message(encode_defunct(text=msg)).signature.hex()
        try:
            r = requests.post(f"{self.base_url}/profile/swappoints", headers={**self.headers, 'accesstoken': sid, 'authorization': f'Bearer {auth} {sid} {addr.lower()} polarise'}, json={"user_id": uid, "user_name": uname, "user_wallet": addr.lower(), "used_points": pts, "token_symbol": "GRISE", "chain_name": "polarise", "signature": sig, "sign_msg": msg}, timeout=30, proxies=self.get_proxy())
            if r.status_code == 200 and r.json().get("code") == "200":
                return r.json().get("data", {})
        except:
            pass
        return None
    
    def get_balance(self, addr, token=None):
        try:
            w3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={"timeout": 60}))
            if token:
                c = w3.eth.contract(address=w3.to_checksum_address(token), abi=self.contract_abi)
                return float(w3.from_wei(c.functions.balanceOf(addr).call(), "ether"))
            return float(w3.from_wei(w3.eth.get_balance(addr), "ether"))
        except:
            return 0
    
    def transfer(self, pk, addr):
        try:
            w3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={"timeout": 60}))
            amt = w3.to_wei(self.transfer_config['amount'], "ether")
            fee = w3.to_wei(100, "gwei")
            tx = {"from": w3.to_checksum_address(addr), "to": w3.to_checksum_address(self.transfer_config['recepient']), "value": amt, "gas": 21000, "maxFeePerGas": int(fee), "maxPriorityFeePerGas": int(fee), "nonce": w3.eth.get_transaction_count(addr, "pending"), "chainId": w3.eth.chain_id}
            signed = w3.eth.account.sign_transaction(tx, pk)
            txh = w3.to_hex(w3.eth.send_raw_transaction(signed.raw_transaction))
            w3.eth.wait_for_transaction_receipt(txh, timeout=300)
            return amt, txh
        except:
            return None, None
    
    def donate(self, pk, addr):
        try:
            w3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={"timeout": 60}))
            amt = w3.to_wei(self.donate_config['amount'], "ether")
            token = w3.to_checksum_address(self.donate_config['token_address'])
            contract = w3.to_checksum_address(self.donate_config['contract_address'])
            receiver = w3.to_checksum_address(self.donate_config['recepient'])
            
            tc = w3.eth.contract(address=token, abi=self.contract_abi)
            if tc.functions.allowance(addr, contract).call() < amt:
                ap = tc.functions.approve(contract, 2**256 - 1)
                fee = w3.to_wei(100, "gwei")
                tx = ap.build_transaction({"from": addr, "gas": int(ap.estimate_gas({"from": addr}) * 1.2), "maxFeePerGas": int(fee), "maxPriorityFeePerGas": int(fee), "nonce": w3.eth.get_transaction_count(addr, "pending"), "chainId": w3.eth.chain_id})
                w3.eth.wait_for_transaction_receipt(w3.eth.send_raw_transaction(w3.eth.account.sign_transaction(tx, pk).raw_transaction), timeout=300)
                time.sleep(3)
            
            dc = w3.eth.contract(address=contract, abi=self.contract_abi)
            df = dc.functions.donate(receiver, amt)
            fee = w3.to_wei(100, "gwei")
            tx = df.build_transaction({"from": addr, "gas": int(df.estimate_gas({"from": addr}) * 1.2), "maxFeePerGas": int(fee), "maxPriorityFeePerGas": int(fee), "nonce": w3.eth.get_transaction_count(addr, "pending"), "chainId": w3.eth.chain_id})
            txh = w3.to_hex(w3.eth.send_raw_transaction(w3.eth.account.sign_transaction(tx, pk).raw_transaction))
            w3.eth.wait_for_transaction_receipt(txh, timeout=300)
            return txh
        except:
            return None
    
    def gen_biz_id(self, addr, auth, sid, inp):
        try:
            r = requests.post(f"{self.base_url}/discussion/generatebizid", headers={**self.headers, 'accesstoken': sid, 'authorization': f'Bearer {auth}'}, json={"biz_input": inp, "biz_type": "discussion_question", "chain_name": "polarise"}, timeout=30, proxies=self.get_proxy())
            if r.status_code == 200 and r.json().get("code") == "200":
                return r.json().get("data", {}).get("Biz_Id")
        except:
            pass
        return None
    
    def create_discussion(self, pk, addr, data):
        try:
            from eth_utils import keccak, to_bytes
            w3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={"timeout": 60}))
            contract = w3.to_checksum_address(self.discussion_config['contract_address'])
            collateral = w3.to_checksum_address(self.donate_config['token_address'])
            slots = ["0x" + keccak(to_bytes(text=o.get("title"))).hex() for o in data['options']]
            
            c = w3.eth.contract(address=contract, abi=self.contract_abi)
            f = c.functions.createDiscussionEvent("0x" + data['question_id'], False, "0x0000000000000000000000000000000000000000", collateral, data['end_time'], slots)
            fee = w3.to_wei(100, "gwei")
            tx = f.build_transaction({"from": addr, "gas": int(f.estimate_gas({"from": addr}) * 1.2), "maxFeePerGas": int(fee), "maxPriorityFeePerGas": int(fee), "nonce": w3.eth.get_transaction_count(addr, "pending"), "chainId": w3.eth.chain_id})
            txh = w3.to_hex(w3.eth.send_raw_transaction(w3.eth.account.sign_transaction(tx, pk).raw_transaction))
            w3.eth.wait_for_transaction_receipt(txh, timeout=300)
            return txh
        except:
            return None
    
    def save_post(self, addr, auth, sid, uid, content):
        try:
            r = requests.post(f"{self.base_url}/posts/savepost", headers={**self.headers, 'accesstoken': sid, 'authorization': f'Bearer {auth} {sid} {addr.lower()} polarise'}, json={"user_id": uid, "chain_name": "polarise", "community_id": 0, "community_name": "", "title": content.get("title", ""), "tags": [], "description": content.get("description", ""), "published_time": int(time.time() * 1000), "media_links": "[]", "is_subscribe_enable": False}, timeout=30, proxies=self.get_proxy())
            if r.status_code == 200 and r.json().get("code") == "200":
                return r.json().get("data", {}).get("id")
        except:
            pass
        return None
    
    def save_discussion(self, addr, auth, sid, uid, data):
        try:
            r = requests.post(f"{self.base_url}/discussion/savediscussion", headers={**self.headers, 'accesstoken': sid, 'authorization': f'Bearer {auth} {sid} {addr.lower()} polarise'}, json={"user_id": uid, "community_id": 0, "community_name": "", "title": data['title'], "options": json.dumps(data['options']), "tags": [], "description": data["description"], "published_time": data['published_time'], "tx_hash": data['tx_hash'], "chain_name": "polarise", "media_links": "[]", "question_id": data['question_id'], "end_time": data['end_time']}, timeout=30, proxies=self.get_proxy())
            return r.status_code == 200 and r.json().get("code") == "200"
        except:
            return False
    
    def comment(self, addr, auth, sid, uid, pid, text):
        try:
            r = requests.post(f"{self.base_url}/posts/savecomment", headers={**self.headers, 'accesstoken': sid, 'authorization': f'Bearer {auth} {sid} {addr.lower()} polarise'}, json={"user_id": uid, "post_id": pid, "content": text, "tags": [], "published_time": int(time.time() * 1000), "chain_name": "polarise"}, timeout=30, proxies=self.get_proxy())
            return r.status_code == 200 and r.json().get("code") == "200"
        except:
            return False
    
    def subscribe(self, addr, auth, sid, sub_addr):
        try:
            r = requests.post(f"{self.base_url}/subscription/savesuborder", headers={**self.headers, 'accesstoken': sid, 'authorization': f'Bearer {auth} {sid} {addr.lower()} polarise'}, json={"subed_addr": sub_addr.lower(), "sub_id": sid, "order_time": int(time.time()), "chain_name": "polarise"}, timeout=30, proxies=self.get_proxy())
            return r.status_code == 200 and r.json().get("code") == "200"
        except:
            return False
    
    def like(self, addr, auth, sid, pid, uid):
        try:
            r = requests.post(f"{self.base_url}/posts/likepost", headers={**self.headers, 'accesstoken': sid, 'authorization': f'Bearer {auth} {sid} {addr.lower()} polarise'}, json={"user_id": uid, "post_id": pid, "chain_name": "polarise"}, timeout=30, proxies=self.get_proxy())
            return r.status_code == 200 and r.json().get("code") == "200"
        except:
            return False
    
    def get_content(self, topic):
        return TOPIC_CONTENTS.get(topic, {"title": topic, "description": f"Discussion about {topic}"})
    
    def save_pv(self, pk):
        with open("pv.txt", "a") as f:
            f.write(pk + "\n")
    
    def save_reff(self, data):
        with self.lock:
            refs = []
            if os.path.exists("reff.json"):
                try:
                    with open("reff.json", "r") as f:
                        refs = json.load(f)
                except:
                    pass
            refs.append(data)
            with open("reff.json", "w") as f:
                json.dump(refs, f, indent=2)
    
    def load_pv(self):
        if os.path.exists("pv.txt"):
            with open("pv.txt", "r") as f:
                return [l.strip() for l in f if l.strip()]
        return []
    
    def load_reff(self):
        if os.path.exists("reff.json"):
            try:
                with open("reff.json", "r") as f:
                    return json.load(f)
            except:
                pass
        return []

    def run_faucet(self):
        clear_terminal()
        print_banner()
        print_line()
        log_info("CLAIM FAUCET - Main Wallet Only")
        print_line()
        
        wallets = self.load_pv()
        if not wallets:
            log_warning("No pv.txt - Creating wallet")
            pk, addr = self.create_wallet()
            log_success(f"Wallet: {addr}")
            self.save_pv(pk)
            wallets = [pk]
        
        for i, pk in enumerate(wallets, 1):
            addr = self.get_address(pk)
            if not addr:
                continue
            
            print_line()
            log_info(f"[{i}/{len(wallets)}] {addr[:20]}...")
            
            auth, sid = self.login(pk, addr)
            if not auth:
                log_error("Login failed")
                continue
            log_success("Logged in")
            
            log_info("Solving captcha...")
            cap = self.solve_captcha()
            if not cap:
                log_error("Captcha failed")
                continue
            log_success("Captcha solved")
            
            tx = self.claim_faucet(addr, cap)
            if tx:
                log_success(f"Faucet: {tx[:16]}...")
                self.complete_task(addr, auth, sid, 1, json.dumps({"tx_hash": tx, "from": addr.lower(), "to": addr.lower(), "value": "1000000"}))
            else:
                log_error("Faucet failed")
            
            time.sleep(3)
        
        print_line()
        log_success("Done")
        input(f"\n{Fore.CYAN}Press Enter...{Style.RESET_ALL}")

    def run_auto_reff(self):
        clear_terminal()
        print_banner()
        print_line()
        log_info("AUTO REFERRAL - Reff + Faucet Only")
        log_info(f"Code: {self.ref_code}")
        print_line()
        
        try:
            num = int(input(f"{Fore.CYAN}How many: {Style.RESET_ALL}"))
            if num <= 0:
                return
        except:
            return
        
        ok, fail = 0, 0
        
        for i in range(num):
            print_line()
            log_info(f"[{i+1}/{num}] Creating...")
            
            pk, addr = self.create_wallet()
            log_success(f"Wallet: {addr[:20]}...")
            
            auth, sid = self.login(pk, addr)
            if not auth:
                log_error("Login failed")
                fail += 1
                self.save_reff({"address": addr, "private_key": pk, "status": "failed", "created_at": datetime.now().isoformat()})
                time.sleep(3)
                continue
            
            log_success(f"Reff applied: {self.ref_code}")
            
            profile = self.get_profile(addr, auth, sid)
            uid = profile.get("id") if profile else None
            
            # Faucet only
            log_info("Claiming faucet...")
            tx = None
            cap = self.solve_captcha()
            if cap:
                tx = self.claim_faucet(addr, cap)
                if tx:
                    log_success(f"Faucet: {tx[:16]}...")
                    self.complete_task(addr, auth, sid, 1, json.dumps({"tx_hash": tx, "from": addr.lower(), "to": addr.lower(), "value": "1000000"}))
            
            self.save_reff({"address": addr, "private_key": pk, "user_id": uid, "tx_hash": tx, "status": "success", "created_at": datetime.now().isoformat()})
            
            ok += 1
            log_success(f"Account {i+1} done")
            
            if i < num - 1:
                w = random.randint(3, 6)
                log_warning(f"Wait {w}s...")
                time.sleep(w)
        
        print_line()
        log_success(f"Done - OK: {ok} | Fail: {fail}")
        input(f"\n{Fore.CYAN}Press Enter...{Style.RESET_ALL}")

    def run_complete_task(self):
        clear_terminal()
        print_banner()
        print_line()
        log_info("COMPLETE TASKS - Main Wallet")
        print_line()
        
        wallets = self.load_pv()
        if not wallets:
            log_error("No pv.txt")
            input(f"\n{Fore.CYAN}Press Enter...{Style.RESET_ALL}")
            return
        
        for i, pk in enumerate(wallets, 1):
            addr = self.get_address(pk)
            if not addr:
                continue
            
            print_line()
            log_info(f"[{i}/{len(wallets)}] {addr[:20]}...")
            
            auth, sid = self.login(pk, addr)
            if not auth:
                log_error("Login failed")
                continue
            
            profile = self.get_profile(addr, auth, sid)
            uid = profile.get("id") if profile else None
            uname = profile.get("user_name") if profile else None
            pts = profile.get("exchange_total_points", 0) if profile else 0
            
            if pts >= 100:
                log_info(f"Swapping {(pts//100)*100} pts...")
                if self.swap_points(addr, auth, sid, pk, uid, uname, (pts//100)*100):
                    log_success("Swapped")
            
            tasks = self.get_tasks(addr, auth, sid)
            for t in tasks:
                tid, name, state = t.get("id"), t.get("name"), t.get("state")
                if state == 1:
                    continue
                
                log_info(f"Task {tid}: {name[:30]}...")
                
                if tid == 1:
                    cap = self.solve_captcha()
                    if cap:
                        tx = self.claim_faucet(addr, cap)
                        if tx and self.complete_task(addr, auth, sid, tid, json.dumps({"tx_hash": tx, "from": addr.lower(), "to": addr.lower(), "value": "1000000"})) == 1:
                            log_success("Done")
                
                elif tid == 2:
                    if self.get_balance(addr) >= 0.003:
                        amt, tx = self.transfer(pk, addr)
                        if tx and self.complete_task(addr, auth, sid, tid, json.dumps({"tx_hash": tx, "from": addr.lower(), "to": self.transfer_config['recepient'].lower(), "value": str(amt)})) == 1:
                            log_success("Done")
                
                elif tid == 3:
                    if self.bind_email(addr, auth, sid, generate_random_email()):
                        log_success("Done")
                
                elif tid in [4, 5, 6]:
                    if self.complete_task(addr, auth, sid, tid) == 1:
                        log_success("Done")
                
                elif tid == 7:
                    topic = random.choice(self.all_topics)
                    content = self.get_content(topic)
                    ts = int(time.time()) * 1000
                    qid = self.gen_biz_id(addr, auth, sid, f"{content['title'].lower()}{ts}-agree-not agree")
                    if qid:
                        opts = [{"index": 0, "title": "Agree", "price": 0, "total_buy_share": 0, "total_sell_share": 0, "total_held_share": 0}, {"index": 1, "title": "Not Agree", "price": 0, "total_buy_share": 0, "total_sell_share": 0, "total_held_share": 0}]
                        now = int(time.time())
                        data = {"title": content['title'], "description": content['description'], "question_id": qid, "options": opts, "published_time": now * 1000, "end_time": now + 1209600}
                        tx = self.create_discussion(pk, addr, data)
                        if tx:
                            data["tx_hash"] = tx
                            if self.save_discussion(addr, auth, sid, uid, data) and self.complete_task(addr, auth, sid, tid) == 1:
                                log_success("Done")
                
                elif tid == 8:
                    pid = self.save_post(addr, auth, sid, uid, self.get_content(random.choice(self.all_topics)))
                    if pid and self.complete_task(addr, auth, sid, tid) == 1:
                        log_success("Done")
                
                elif tid == 9:
                    if self.get_balance(addr, self.donate_config['token_address']) >= 1:
                        tx = self.donate(pk, addr)
                        if tx and self.complete_task(addr, auth, sid, tid) == 1:
                            log_success("Done")
                
                elif tid == 10:
                    if self.comment(addr, auth, sid, uid, self.main_post_id, random.choice(COMMENT_LIST)) and self.complete_task(addr, auth, sid, tid) == 1:
                        log_success("Done")
                
                elif tid == 11:
                    if self.subscribe(addr, auth, sid, self.main_user_wallet) and self.complete_task(addr, auth, sid, tid) == 1:
                        log_success("Done")
                
                time.sleep(1)
            
            self.like(addr, auth, sid, self.main_post_id, uid)
            time.sleep(3)
        
        print_line()
        log_success("All done")
        input(f"\n{Fore.CYAN}Press Enter...{Style.RESET_ALL}")

    def process_reff_wallet(self, reff, idx, total):
        addr = reff.get("address")
        pk = reff.get("private_key")
        
        if not addr or not pk:
            return False
        
        with self.lock:
            log_info(f"[{idx}/{total}] {addr[:20]}...")
        
        auth, sid = self.login(pk, addr)
        if not auth:
            with self.lock:
                log_error(f"[{idx}] Login failed")
            return False
        
        profile = self.get_profile(addr, auth, sid)
        uid = profile.get("id") if profile else None
        uname = profile.get("user_name") if profile else None
        pts = profile.get("exchange_total_points", 0) if profile else 0
        
        if pts >= 100:
            self.swap_points(addr, auth, sid, pk, uid, uname, (pts//100)*100)
        
        tasks = self.get_tasks(addr, auth, sid)
        for t in tasks:
            tid, state = t.get("id"), t.get("state")
            if state == 1:
                continue
            
            if tid == 1:
                cap = self.solve_captcha()
                if cap:
                    tx = self.claim_faucet(addr, cap)
                    if tx:
                        self.complete_task(addr, auth, sid, tid, json.dumps({"tx_hash": tx, "from": addr.lower(), "to": addr.lower(), "value": "1000000"}))
            
            elif tid == 2:
                if self.get_balance(addr) >= 0.003:
                    amt, tx = self.transfer(pk, addr)
                    if tx:
                        self.complete_task(addr, auth, sid, tid, json.dumps({"tx_hash": tx, "from": addr.lower(), "to": self.transfer_config['recepient'].lower(), "value": str(amt)}))
            
            elif tid == 3:
                self.bind_email(addr, auth, sid, generate_random_email())
            
            elif tid in [4, 5, 6]:
                self.complete_task(addr, auth, sid, tid)
            
            elif tid == 7:
                topic = random.choice(self.all_topics)
                content = self.get_content(topic)
                ts = int(time.time()) * 1000
                qid = self.gen_biz_id(addr, auth, sid, f"{content['title'].lower()}{ts}-agree-not agree")
                if qid:
                    opts = [{"index": 0, "title": "Agree", "price": 0, "total_buy_share": 0, "total_sell_share": 0, "total_held_share": 0}, {"index": 1, "title": "Not Agree", "price": 0, "total_buy_share": 0, "total_sell_share": 0, "total_held_share": 0}]
                    now = int(time.time())
                    data = {"title": content['title'], "description": content['description'], "question_id": qid, "options": opts, "published_time": now * 1000, "end_time": now + 1209600}
                    tx = self.create_discussion(pk, addr, data)
                    if tx:
                        data["tx_hash"] = tx
                        self.save_discussion(addr, auth, sid, uid, data)
                        self.complete_task(addr, auth, sid, tid)
            
            elif tid == 8:
                pid = self.save_post(addr, auth, sid, uid, self.get_content(random.choice(self.all_topics)))
                if pid:
                    self.complete_task(addr, auth, sid, tid)
            
            elif tid == 9:
                if self.get_balance(addr, self.donate_config['token_address']) >= 1:
                    tx = self.donate(pk, addr)
                    if tx:
                        self.complete_task(addr, auth, sid, tid)
            
            elif tid == 10:
                if self.comment(addr, auth, sid, uid, self.main_post_id, random.choice(COMMENT_LIST)):
                    self.complete_task(addr, auth, sid, tid)
            
            elif tid == 11:
                if self.subscribe(addr, auth, sid, self.main_user_wallet):
                    self.complete_task(addr, auth, sid, tid)
            
            time.sleep(0.5)
        
        self.like(addr, auth, sid, self.main_post_id, uid)
        
        with self.lock:
            log_success(f"[{idx}] Done")
        return True

    def run_reff_task(self):
        clear_terminal()
        print_banner()
        print_line()
        log_info("REFF TASKS - All Reff Wallets")
        print_line()
        
        reffs = self.load_reff()
        if not reffs:
            log_error("No reff.json")
            input(f"\n{Fore.CYAN}Press Enter...{Style.RESET_ALL}")
            return
        
        log_info(f"Found {len(reffs)} reff wallets")
        
        try:
            threads = int(input(f"{Fore.CYAN}Threads (1-10): {Style.RESET_ALL}"))
            threads = max(1, min(10, threads))
        except:
            threads = 1
        
        log_info(f"Using {threads} threads")
        print_line()
        
        ok, fail = 0, 0
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(self.process_reff_wallet, r, i+1, len(reffs)): r for i, r in enumerate(reffs)}
            for future in as_completed(futures):
                try:
                    if future.result():
                        ok += 1
                    else:
                        fail += 1
                except:
                    fail += 1
        
        print_line()
        log_success(f"Done - OK: {ok} | Fail: {fail}")
        input(f"\n{Fore.CYAN}Press Enter...{Style.RESET_ALL}")


def main():
    clear_terminal()
    print_banner()
    
    bot = PolariseBot()
    bot.initialize()
    
    while True:
        clear_terminal()
        print_banner()
        print_menu()
        
        c = input(f"{Fore.CYAN}Select [1-5]: {Style.RESET_ALL}").strip()
        
        if c == "1":
            bot.run_faucet()
        elif c == "2":
            bot.run_auto_reff()
        elif c == "3":
            bot.run_complete_task()
        elif c == "4":
            bot.run_reff_task()
        elif c == "5":
            log_warning("Exiting...")
            break
        else:
            log_error("Invalid")
            time.sleep(1)


if __name__ == "__main__":
    main()
