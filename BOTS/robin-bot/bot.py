import json
import os
import sys
import time
import hmac
import hashlib
import random
import string
import requests

RESET = "\033[0m"
BOLD_GREEN = "\033[1;32m"
BOLD_YELLOW = "\033[1;33m"
BOLD_RED = "\033[1;31m"
BOLD_CYAN = "\033[1;36m"
BOLD_MAGENTA = "\033[1;35m"
BOLD_WHITE = "\033[1;37m"
BOLD_BLUE = "\033[1;34m"

def log_success(msg): print(f"{BOLD_GREEN}[SUCCESS] {msg}{RESET}")
def log_error(msg): print(f"{BOLD_RED}[ERROR] {msg}{RESET}")
def log_info(msg): print(f"{BOLD_YELLOW}[INFO] {msg}{RESET}")
def log_process(msg): print(f"{BOLD_CYAN}[PROCESS] {msg}{RESET}")
def log_warn(msg): print(f"{BOLD_YELLOW}[WARNING] {msg}{RESET}")

RPC_URL = "https://rpc.testnet.chain.robinhood.com/rpc"
CHAIN_ID = 46630
EXPLORER_URL = "https://explorer.testnet.chain.robinhood.com"
GAS_MULTIPLIER = 1.5
PK_FILE = "pv.txt"
PROXY_FILE = "proxy.txt"
TOKEN_FILE = "token.txt"
KEY_FILE = "key.txt"

CONTRACT_INFINITYNAME = "0x76a816EFa69e3183972ff7a231F5C8d7b065d9De"
CONTRACT_GMCARDS = "0xC21dF1Bb620ebe7f5aE0144df50DE28ce0D47ae7"
CONTRACT_DEPLOY = "0xa3d9Fbd0edB10327ECB73D2C72622E505dF468a2"
CONTRACT_BADGE = "0x016ef0F56D7344d0E55f6BC2A20618E02DAE8BE0"
CONTRACT_FLAMENCO = "0xA3571B4D683Db03E4B936E88Fba17C3b8cbdA273"
CONTRACT_FLAMENCO_MINTER = "0x00000000009a1E02f00E280dcfA4C81c55724212"
CONTRACT_OMNIHUB = "0xe289E522864f018D18E0f6b1a714e728774128e2"

BRIDGE_CONTRACT = "0xF2939afA86F6f933A3CE17fCAB007907B6b0B7a4"
SEPOLIA_CHAIN_ID = 11155111
SEPOLIA_RPC = "https://eth-sepolia.g.alchemy.com/v2/4Thn5oesl1ZQOE4UtNvJqhqajyiKhNIm"
SEPOLIA_EXPLORER = "https://sepolia.etherscan.io"
BRIDGE_SELECTOR = "679b6ded"
BRIDGE_L2_GAS_LIMIT = 0x6b77
BRIDGE_MAX_FEE_PER_GAS = 0x3938700
BRIDGE_MAX_SUBMISSION_COST = 0x19d8c27c3260

CONTRACT_SYNTHRA_ROUTER = "0x6F308B834595312f734e65e273F2210f43Fc48F8"
CONTRACT_SYNTHRA_POSITION_MANAGER = "0x54A0EF7da351cb8fD1998E7945cc51E5825fB233"
CONTRACT_WETH = "0x33e4191705c386532ba27cBF171Db86919200B94"

# Edel Finance (Aave V3 fork)
CONTRACT_EDEL_POOL = "0x0064394b61942924d63dB20192652CddBCcA745d"
EDEL_ORIGIN = "https://robinhood.edel.finance"
EDEL_REFERER = "https://robinhood.edel.finance/"

TOKENS = {
    "WETH":  {"address": "0x33e4191705c386532ba27cBF171Db86919200B94", "symbol": "WETH",  "name": "Wrapped ETH"},
    "USDC":  {"address": "0xbf4479C07Dc6fdc6dAa764A0ccA06969e894275F", "symbol": "USDC",  "name": "USDC"},
    "SYN":   {"address": "0xC5124C846c6e6307986988dFb7e743327aA05F19", "symbol": "SYN",   "name": "Synthra"},
    "AMZN":  {"address": "0x5884ad2f920c162cfbbacc88c9c51aa75ec09e02", "symbol": "AMZN",  "name": "Amazon"},
    "AMD":   {"address": "0x71178bac73cbeb415514eb542a8995b82669778d", "symbol": "AMD",   "name": "AMD"},
    "TSLA":  {"address": "0xc9f9c86933092bbbfff3ccb4b105a4a94bf3bd4e", "symbol": "TSLA",  "name": "Tesla"},
    "NFLX":  {"address": "0x3b8262a63d25f0477c4dde23f83cfe22cb768c93", "symbol": "NFLX",  "name": "Netflix"},
    "PLTR":  {"address": "0x1fbe1a0e43594b3455993b5de5fd0a7a266298d0", "symbol": "PLTR",  "name": "Palantir Technologies"},
}

# Edel Finance lending tokens (supply -> get aToken, borrow -> get variableDebtToken)
EDEL_TOKENS = {
    "TSLA": {"address": "0xC9f9c86933092BbbfFF3CCb4b105A4A94bf3Bd4E", "symbol": "TSLA", "name": "Tesla",      "aToken": "0xdCa54Ba552dc8F7dD4296b8d2dF304d9918032Cd", "debtToken": "0x1F29BB87028c757E354403928E86c91F92cC8CD6"},
    "AMD":  {"address": "0x71178BAc73cBeb415514eB542a8995b82669778d", "symbol": "AMD",  "name": "AMD",         "aToken": None, "debtToken": None},
    "AMZN": {"address": "0x5884aD2f920c162CFBbACc88C9C51AA75eC09E02", "symbol": "AMZN", "name": "Amazon",      "aToken": None, "debtToken": None},
    "NFLX": {"address": "0x3b8262A63d25f0477c4DDE23F83cfe22Cb768C93", "symbol": "NFLX", "name": "Netflix",     "aToken": None, "debtToken": None},
    "PLTR": {"address": "0x1FBE1a0e43594b3455993B5dE5Fd0A7A266298d0", "symbol": "PLTR", "name": "Palantir",    "aToken": None, "debtToken": None},
}

LIQUIDITY_POOLS = {
    "WETH/USDC": {"token0": "0x33e4191705c386532ba27cBF171Db86919200B94","token1": "0xbf4479C07Dc6fdc6dAa764A0ccA06969e894275F","fee": 3000,"tickLower": -92100,"tickUpper": -23040,"pool": "0x9640AFcBc2310d011B7b71a76975e919D9B6Fa4A"},
    "WETH/SYN": {"token0": "0x33e4191705c386532ba27cBF171Db86919200B94","token1": "0xC5124C846c6e6307986988dFb7e743327aA05F19","fee": 3000,"tickLower": -69060,"tickUpper": -45540,"pool": "0x2Daa36EA45d5BB50249a1a16dFD21cB027bCa666"},
}

SWAP_PATHS = {
    "USDC": {"path": "33e4191705c386532ba27cbf171db86919200b94" + "000bb8" + "bf4479c07dc6fdc6daa764a0cca06969e894275f","fee": 3000},
    "SYN":  {"path": "33e4191705c386532ba27cbf171db86919200b94" + "000bb8" + "c5124c846c6e6307986988dfb7e743327aa05f19","fee": 3000},
    "AMZN": {"path": "33e4191705c386532ba27cbf171db86919200b94" + "000bb8" + "5884ad2f920c162cfbbacc88c9c51aa75ec09e02","fee": 3000},
    "AMD":  {"path": "33e4191705c386532ba27cbf171db86919200b94" + "000bb8" + "71178bac73cbeb415514eb542a8995b82669778d","fee": 3000},
    "TSLA": {"path": "33e4191705c386532ba27cbf171db86919200b94" + "000bb8" + "c9f9c86933092bbbfff3ccb4b105a4a94bf3bd4e","fee": 3000},
    "NFLX": {"path": "33e4191705c386532ba27cbf171db86919200b94" + "000bb8" + "3b8262a63d25f0477c4dde23f83cfe22cb768c93","fee": 3000},
    "PLTR": {"path": "33e4191705c386532ba27cbf171db86919200b94" + "000bb8" + "1fbe1a0e43594b3455993b5de5fd0a7a266298d0","fee": 3000},
}

FAUCET_API_BASE = "https://faucet.testnet.chain.robinhood.com"
OMNIHUB_API = "https://api-v2.omnihub.xyz"
TURNSTILE_SITEKEY = "0x4AAAAAACYlB6bEmjnFNUnJ"
TURNSTILE_PAGE_URL = "https://faucet.testnet.chain.robinhood.com/"
CAPTCHA_SERVERS = ["https://api.sctg.xyz","https://sctg.xyz","https://ru.sctg.xyz","http://157.180.15.203","http://109.248.207.94"]

VALUE_MINT_DOMAIN = 0x12309ce540000
VALUE_GM = 0x1a6016b2d000
VALUE_DEPLOY = 0x1fd512913000
VALUE_BADGE = 0x12c221cc6a000
VALUE_OMNIHUB = 0x2386f26fc10000

SELECTOR_MINT_DOMAIN = "1e59c529"
SELECTOR_GM = "84a3bb6b"
SELECTOR_DEPLOY = "775c300c"
SELECTOR_BADGE = "26092b83"

# Watchoor
WATCHOOR_TO = "0xa4a4f8b6aa81abe7616cc4d1000c61a066d1106e"
WATCHOOR_VALUE_WEI = int("364bfd4b0800", 16)
WATCHOOR_GM_SELECTOR = bytes.fromhex("92d0214c")
WATCHOOR_GN_SELECTOR = bytes.fromhex("00f76b87")
WATCHOOR_DEPLOY_NFT_SELECTOR = bytes.fromhex("f399e81c")
WATCHOOR_DEPLOY_ERC20_SELECTOR = bytes.fromhex("64d346cd")
WATCHOOR_DEPLOY_COUNTER_SELECTOR = bytes.fromhex("acbd0c47")

# ZNS (Znz Connect) - Robinhood Testnet
ZNS_SAY_GM_TO   = "0x780ae565a4104b3099dab72d9610656b94f1389f"
ZNS_DEPLOY_TO   = "0x673e15dc75d7a6e2409f310dee5c6b27e95906d2"
ZNS_MINT_TO     = "0xdfcf6c734d1821ddc7bf4f64c6f11db069ddbc1d"
ZNS_SAY_GM_VALUE  = int("32ee841b8000", 16)
ZNS_DEPLOY_VALUE  = int("32ee841b8000", 16)
ZNS_MINT_VALUE    = int("38d7ea4c68000", 16)

REVERT_ERRORS = {"0x7a4ab730": "Already claimed today","0x08c379a0": "Contract reverted","0xe2517d3f": "Access denied","0x646cf558": "Already minted"}

SUPABASE_URL = "https://nvasbkkskipzdfnbgxus.supabase.co/rest/v1/domain_mints"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52YXNia2tza2lwemRmbmJneHVzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjgzMTY4OTAsImV4cCI6MjA4Mzg5Mjg5MH0.qTOWm3cwatsrylOYJMLY7yXIp8cI8RLXMtOAe6iNFoc"

loaded_proxies = []
loaded_accounts = []
accounts_loaded = False
captcha_api_key = ""

def clear_screen(): os.system("cls" if os.name == "nt" else "clear")
def set_title():
    try: sys.stdout.write("\x1b]2;Robinhood Testnet Tool - By KAZUHA VIP\x1b\\"); sys.stdout.flush()
    except: pass

def banner():
    clear_screen()
    print(f"{BOLD_CYAN}======================================================================{RESET}")
    print(f"{BOLD_GREEN}       ROBINHOOD CHAIN TESTNET{RESET}")
    print(f"{BOLD_MAGENTA}       Created by KAZUHA VIP ONLY{RESET}")
    print(f"{BOLD_CYAN}======================================================================{RESET}")

def display_menu():
    print(f"\n{BOLD_CYAN}----------------------------------------------------------------------{RESET}")
    print(f"{BOLD_WHITE}                         MAIN MENU{RESET}")
    print(f"{BOLD_CYAN}----------------------------------------------------------------------{RESET}")
    print(f"  {BOLD_GREEN}[1]{RESET}  {BOLD_WHITE}On Chain GM{RESET}")
    print(f"  {BOLD_BLUE}[2]{RESET}  {BOLD_WHITE}Deploy Contract{RESET}")
    print(f"  {BOLD_MAGENTA}[3]{RESET}  {BOLD_WHITE}Mint Domain{RESET}")
    print(f"  {BOLD_YELLOW}[4]{RESET}  {BOLD_WHITE}Mint Badge{RESET}")
    print(f"  {BOLD_CYAN}[5]{RESET}  {BOLD_WHITE}Mint NFT (Flamenco + OmniHub){RESET}")
    print(f"  {BOLD_GREEN}[6]{RESET}  {BOLD_WHITE}Claim Faucet{RESET}")
    print(f"  {BOLD_BLUE}[7]{RESET}  {BOLD_WHITE}Bridge ETH (Sepolia -> Robinhood){RESET}")
    print(f"  {BOLD_YELLOW}[8]{RESET}  {BOLD_WHITE}Swap (Synthra DEX){RESET}")
    print(f"  {BOLD_CYAN}[9]{RESET}  {BOLD_WHITE}Add Liquidity (Synthra DEX){RESET}")
    print(f"  {BOLD_GREEN}[10]{RESET} {BOLD_WHITE}Lending (Edel Finance - Supply/Borrow/Repay){RESET}")
    print(f"  {BOLD_BLUE}[11]{RESET} {BOLD_WHITE}Watchoor (GM+GN+Deploy NFT/ERC20/Counter){RESET}")
    print(f"  {BOLD_MAGENTA}[12]{RESET} {BOLD_WHITE}ZNS - Znz Connect (GM+Deploy+Mint NFT){RESET}")
    print(f"  {BOLD_WHITE}[13]{RESET} {BOLD_WHITE}Auto All (GM+Deploy+Domain+Badge+NFT+Watchoor+ZNS){RESET}")
    print(f"  {BOLD_RED}[14]{RESET} {BOLD_WHITE}Exit{RESET}")
    print(f"{BOLD_CYAN}----------------------------------------------------------------------{RESET}")

def ask_repeat_count(name):
    while True:
        try:
            c = int(input(f"\n  {BOLD_YELLOW}How many times to perform {name}? : {RESET}").strip())
            if c > 0: return c
            log_error("Must be > 0")
        except ValueError: log_error("Enter a valid number")

def generate_random_domain():
    styles = [lambda: ''.join(random.choices(string.ascii_lowercase, k=random.randint(6,10))),lambda: ''.join(random.choices(string.ascii_lowercase, k=random.randint(4,6)))+str(random.randint(10,9999)),lambda: random.choice(["cool","super","mega","ultra","fast","dark","moon","star","fire","ice","sky","sun","wild","gold","neo","zen","max","pro","top","web","dev","nft","eth","sol","dex","dao","gm","gg","alpha","beta","sigma","chad","vip","og","king","queen","lord","ninja","cyber","pixel"])+''.join(random.choices(string.ascii_lowercase,k=random.randint(3,6)))+str(random.randint(1,999)),lambda: random.choice(["the","my","its","got","big","lil","ser","anon"])+random.choice(["wizard","punk","ape","dragon","wolf","hawk","bear","tiger","lion","fox","eagle","viper","shark","whale","knight","king","queen","chief","boss","legend"])+str(random.randint(1,99)),lambda: ''.join(random.choices(string.ascii_lowercase+string.digits,k=random.randint(7,12)))]
    name=''.join(c for c in random.choice(styles)().lower() if c.isalnum())
    return name if len(name)>=3 else name+''.join(random.choices(string.ascii_lowercase,k=3))

def generate_unique_domains(count):
    d=set()
    while len(d)<count: d.add(generate_random_domain())
    return list(d)

def load_proxies():
    global loaded_proxies; loaded_proxies=[]
    if not os.path.exists(PROXY_FILE): return
    try:
        with open(PROXY_FILE) as f: loaded_proxies=[l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
        if loaded_proxies: log_success(f"Loaded {len(loaded_proxies)} proxies")
    except Exception as e: log_warn(f"Proxy error: {e}")

def get_random_proxy():
    if not loaded_proxies: return None
    return format_proxy(random.choice(loaded_proxies))

def format_proxy(p):
    p=p.strip()
    if "://" in p: return {"http":p,"https":p}
    parts=p.split(":")
    if len(parts)==4: url=f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
    elif len(parts)==2: url=f"http://{parts[0]}:{parts[1]}"
    else: url=f"http://{p}"
    return {"http":url,"https":url}

def mask_proxy(pd):
    if not pd: return "Direct"
    url=pd.get("http","")
    if "@" in url: return f"***@{url.split('@')[-1]}"
    return url[:30]+"..." if len(url)>30 else url

def load_accounts():
    global loaded_accounts, accounts_loaded
    loaded_accounts=[]; accounts_loaded=False
    if not os.path.exists(PK_FILE): log_error(f"{PK_FILE} not found!"); return False
    try:
        with open(PK_FILE) as f:
            for idx,line in enumerate(f,1):
                line=line.strip()
                if not line or line.startswith("#"): continue
                pk=line if line.startswith("0x") else "0x"+line
                if len(pk[2:])!=64: log_warn(f"Line {idx}: bad length"); continue
                try: int(pk[2:],16)
                except: log_warn(f"Line {idx}: bad hex"); continue
                loaded_accounts.append(pk)
        if loaded_accounts: log_success(f"Loaded {len(loaded_accounts)} accounts"); accounts_loaded=True; return True
        log_error(f"No valid keys"); return False
    except Exception as e: log_error(f"Load failed: {e}"); return False

def load_captcha_key():
    global captcha_api_key; captcha_api_key=""
    if not os.path.exists(KEY_FILE): return
    try:
        with open(KEY_FILE) as f:
            for line in f:
                line=line.strip()
                if line and not line.startswith("#"): captcha_api_key=line; break
        if captcha_api_key: log_success(f"Captcha key: {captcha_api_key[:6]}***{captcha_api_key[-4:]}")
    except: pass

def load_faucet_tokens():
    tokens=[]
    if not os.path.exists(TOKEN_FILE): log_error(f"{TOKEN_FILE} not found!"); return tokens
    try:
        with open(TOKEN_FILE) as f: tokens=[l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
        if tokens: log_success(f"Loaded {len(tokens)} faucet tokens")
    except Exception as e: log_error(f"Token error: {e}")
    return tokens

def ensure_accounts_loaded(): return True if accounts_loaded else load_accounts()

# ============================================
# CAPTCHA
# ============================================
def solve_turnstile(proxy=None):
    if not captcha_api_key: log_error("No captcha key!"); return None
    log_process("Solving Turnstile captcha...")
    task_id=None; ws=None
    for base in CAPTCHA_SERVERS:
        try:
            log_info(f"Trying: {base}")
            resp=requests.get(f"{base}/in.php",params={"key":captcha_api_key,"method":"turnstile","sitekey":TURNSTILE_SITEKEY,"pageurl":TURNSTILE_PAGE_URL,"json":1},timeout=20)
            if resp.status_code==200:
                try:
                    data=resp.json()
                    if data.get("status")==1: task_id=str(data["request"]); ws=base; log_success(f"Task: {task_id}"); break
                    else: log_warn(f"Error: {data.get('request','?')}")
                except:
                    t=resp.text.strip()
                    if t.startswith("OK|"): task_id=t.split("|")[1]; ws=base; log_success(f"Task: {task_id}"); break
        except Exception as e: log_warn(f"{base}: {e}")
    if not task_id: log_error("All servers failed!"); return None
    log_process(f"Polling {ws}...")
    for a in range(1,61):
        time.sleep(3)
        try:
            resp=requests.get(f"{ws}/res.php",params={"key":captcha_api_key,"action":"get","id":task_id,"json":1},timeout=15)
            if resp.status_code==200:
                try:
                    data=resp.json()
                    if data.get("status")==1: print(); log_success(f"Solved! ({len(data['request'])} chars)"); return data["request"]
                    elif data.get("request")=="CAPCHA_NOT_READY": sys.stdout.write(f"\r  {BOLD_YELLOW}[SOLVING] {a*3}s...{RESET}    "); sys.stdout.flush(); continue
                    else:
                        err=data.get("request","?")
                        if err!="CAPCHA_NOT_READY": print(); log_error(f"Error: {err}"); return None
                except:
                    t=resp.text.strip()
                    if t.startswith("OK|"): print(); log_success(f"Solved!"); return t.split("|",1)[1]
                    elif t=="CAPCHA_NOT_READY": sys.stdout.write(f"\r  {BOLD_YELLOW}[SOLVING] {a*3}s...{RESET}    "); sys.stdout.flush()
        except: pass
        sys.stdout.write(f"\r  {BOLD_YELLOW}[SOLVING] {a*3}s...{RESET}    "); sys.stdout.flush()
    print(); log_error("Timeout!"); return None

# ============================================
# CRYPTO
# ============================================
def keccak256(data):
    if isinstance(data,str): data=bytes.fromhex(data.replace("0x",""))
    bs=136; padded=bytearray(data); padded.append(0x01)
    while len(padded)%bs!=0: padded.append(0x00)
    padded[-1]|=0x80
    state=[[0]*5 for _ in range(5)]
    RC=[0x0000000000000001,0x0000000000008082,0x800000000000808A,0x8000000080008000,0x000000000000808B,0x0000000080000001,0x8000000080008081,0x8000000000008009,0x000000000000008A,0x0000000000000088,0x0000000080008009,0x000000008000000A,0x000000008000808B,0x800000000000008B,0x8000000000008089,0x8000000000008003,0x8000000000008002,0x8000000000000080,0x000000000000800A,0x800000008000000A,0x8000000080008081,0x8000000000008080,0x0000000080000001,0x8000000080008008]
    ROT=[[0,36,3,41,18],[1,44,10,45,2],[62,6,43,15,61],[28,55,25,21,56],[27,20,39,8,14]]
    M=0xFFFFFFFFFFFFFFFF
    def r64(v,n): n%=64; return((v<<n)|(v>>(64-n)))&M
    def kf(st):
        for rd in range(24):
            C=[st[x][0]^st[x][1]^st[x][2]^st[x][3]^st[x][4] for x in range(5)]
            D=[C[(x-1)%5]^r64(C[(x+1)%5],1) for x in range(5)]
            for x in range(5):
                for y in range(5): st[x][y]^=D[x]
            B=[[0]*5 for _ in range(5)]
            for x in range(5):
                for y in range(5): B[y][(2*x+3*y)%5]=r64(st[x][y],ROT[x][y])
            for x in range(5):
                for y in range(5): st[x][y]=B[x][y]^((~B[(x+1)%5][y])&B[(x+2)%5][y])
            st[0][0]^=RC[rd]
        return st
    for bk in range(0,len(padded),bs):
        block=padded[bk:bk+bs]; i=0
        for y in range(5):
            for x in range(5):
                if i<bs: v=int.from_bytes(block[i:i+8],'little') if i+8<=len(block) else 0; state[x][y]^=v; i+=8
        state=kf(state)
    out=bytearray()
    for y in range(5):
        for x in range(5):
            out.extend(state[x][y].to_bytes(8,'little'))
            if len(out)>=32: return bytes(out[:32])
    return bytes(out[:32])

P=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx=0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy=0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

def egcd(a,b):
    if a==0: return b,0,1
    g,x,y=egcd(b%a,a); return g,y-(b//a)*x,x
def modinv(a,m=P):
    if a<0: a%=m
    g,x,_=egcd(a,m); return x%m
def padd(p1,p2):
    if p1 is None: return p2
    if p2 is None: return p1
    x1,y1=p1; x2,y2=p2
    if x1==x2 and y1==y2: lam=(3*x1*x1*modinv(2*y1))%P
    elif x1==x2: return None
    else: lam=((y2-y1)*modinv(x2-x1))%P
    x3=(lam*lam-x1-x2)%P; return(x3,(lam*(x1-x3)-y1)%P)
def pmul(k,pt=None):
    if pt is None: pt=(Gx,Gy)
    r=None; a=pt
    while k:
        if k&1: r=padd(r,a)
        a=padd(a,a); k>>=1
    return r
def pk2addr(pk):
    if pk.startswith("0x"): pk=pk[2:]
    pub=pmul(int(pk,16)); return "0x"+keccak256(pub[0].to_bytes(32,'big')+pub[1].to_bytes(32,'big'))[-20:].hex()
def pub2addr(pub): return "0x"+keccak256(pub[0].to_bytes(32,'big')+pub[1].to_bytes(32,'big'))[-20:].hex()
def detk(mh,pki):
    x=pki.to_bytes(32,'big'); h1=mh if isinstance(mh,bytes) else bytes.fromhex(mh)
    v=b'\x01'*32; k=b'\x00'*32
    k=hmac.new(k,v+b'\x00'+x+h1,hashlib.sha256).digest(); v=hmac.new(k,v,hashlib.sha256).digest()
    k=hmac.new(k,v+b'\x01'+x+h1,hashlib.sha256).digest(); v=hmac.new(k,v,hashlib.sha256).digest()
    while True:
        v=hmac.new(k,v,hashlib.sha256).digest(); c=int.from_bytes(v,'big')
        if 1<=c<N: return c
        k=hmac.new(k,v+b'\x00',hashlib.sha256).digest(); v=hmac.new(k,v,hashlib.sha256).digest()
def recpub(mh,r,s,ri):
    try:
        ysq=(pow(r,3,P)+7)%P; y=pow(ysq,(P+1)//4,P)
        if y%2!=ri%2: y=P-y
        mi=int.from_bytes(mh,'big') if isinstance(mh,bytes) else int(mh,16)
        rinv=modinv(r,N); sR=pmul(s,(r,y)); eG=pmul(mi,(Gx,Gy))
        return pmul(rinv,padd(sR,(eG[0],(P-eG[1])%P)))
    except: return None

def sign_message(msg,pk):
    if pk.startswith("0x"): pk=pk[2:]
    pki=int(pk,16); mb=msg.encode('utf-8') if isinstance(msg,str) else msg
    mh=keccak256(f"\x19Ethereum Signed Message:\n{len(mb)}".encode('utf-8')+mb)
    mi=int.from_bytes(mh,'big'); k=detk(mh,pki); pt=pmul(k)
    r=pt[0]%N; s=((mi+r*pki)*modinv(k,N))%N
    if s>N//2: s=N-s
    ri=0; rec=recpub(mh,r,s,0)
    if rec is None or pub2addr(rec).lower()!=pk2addr("0x"+pk).lower(): ri=1
    return "0x"+(r.to_bytes(32,'big')+s.to_bytes(32,'big')+bytes([27+ri])).hex()

def rlp_encode(val):
    if isinstance(val,bytes):
        if len(val)==1 and val[0]<0x80: return val
        return enc_len(len(val),0x80)+val
    elif isinstance(val,int):
        if val==0: return b'\x80'
        vb=val.to_bytes((val.bit_length()+7)//8,'big')
        if len(vb)==1 and vb[0]<0x80: return vb
        return enc_len(len(vb),0x80)+vb
    elif isinstance(val,list): out=b''.join(rlp_encode(i) for i in val); return enc_len(len(out),0xc0)+out
    elif isinstance(val,str): return rlp_encode(val.encode())
    else: raise TypeError(f"Cannot RLP encode {type(val)}")
def enc_len(l,o):
    if l<56: return bytes([l+o])
    bl=l.to_bytes((l.bit_length()+7)//8,'big'); return bytes([len(bl)+o+55])+bl
def h2b(h): return bytes.fromhex(h[2:] if h.startswith("0x") else h)
def b2h(b): return "0x"+b.hex()

def sign_tx(tx,pk,chain_id=CHAIN_ID):
    if pk.startswith("0x"): pk=pk[2:]
    pki=int(pk,16)
    items=[tx["nonce"],tx["gasPrice"],tx["gas"],h2b(tx["to"]),tx["value"],h2b(tx["data"]),chain_id,0,0]
    mh=keccak256(rlp_encode(items)); mi=int.from_bytes(mh,'big')
    k=detk(mh,pki); pt=pmul(k); r=pt[0]%N; s=((mi+r*pki)*modinv(k,N))%N
    if s>N//2: s=N-s
    ri=0; rec=recpub(mh,r,s,0)
    if rec is None or pub2addr(rec).lower()!=pk2addr("0x"+pk).lower(): ri=1
    v=chain_id*2+35+ri
    return b2h(rlp_encode([tx["nonce"],tx["gasPrice"],tx["gas"],h2b(tx["to"]),tx["value"],h2b(tx["data"]),v,r,s]))

# ============================================
# RPC
# ============================================
def rpc_call(method,params=None,origin="https://onchaingm.com",referer="https://onchaingm.com/",proxy=None):
    if params is None: params=[]
    headers={"Content-Type":"application/json","Accept":"*/*","User-Agent":"Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36","Origin":origin,"Referer":referer}
    try:
        resp=requests.post(RPC_URL,json=[{"jsonrpc":"2.0","id":1,"method":method,"params":params}],headers=headers,timeout=30,proxies=proxy)
        r=resp.json(); return r[0] if isinstance(r,list) else r
    except Exception as e: log_error(f"RPC: {e}"); return None

def rpc_direct(method,params=None,origin="https://onchaingm.com",referer="https://onchaingm.com/",proxy=None):
    if params is None: params=[]
    headers={"Content-Type":"application/json","Accept":"*/*","User-Agent":"Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36","Origin":origin,"Referer":referer}
    try:
        resp=requests.post("https://rpc.testnet.chain.robinhood.com/",json={"jsonrpc":"2.0","id":1,"method":method,"params":params},headers=headers,timeout=30,proxies=proxy)
        return resp.json()
    except Exception as e: log_error(f"RPC Direct: {e}"); return None

def sepolia_rpc(method,params=None,proxy=None):
    if params is None: params=[]
    headers={"Content-Type":"application/json","Accept":"*/*","User-Agent":"Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36","Origin":"https://portal.arbitrum.io","Referer":"https://portal.arbitrum.io/"}
    try:
        resp=requests.post(SEPOLIA_RPC,json={"jsonrpc":"2.0","id":1,"method":method,"params":params},headers=headers,timeout=30,proxies=proxy)
        return resp.json()
    except Exception as e: log_error(f"Sepolia RPC: {e}"); return None

def get_nonce(addr,proxy=None):
    r=rpc_call("eth_getTransactionCount",[addr,"latest"],proxy=proxy)
    return int(r["result"],16) if r and "result" in r else None
def get_nonce_direct(addr,origin,referer,proxy=None):
    r=rpc_direct("eth_getTransactionCount",[addr,"latest"],origin,referer,proxy)
    return int(r["result"],16) if r and "result" in r else None
def get_balance(addr,proxy=None):
    r=rpc_call("eth_getBalance",[addr,"latest"],proxy=proxy)
    return int(r["result"],16)/10**18 if r and "result" in r else 0
def get_block_number(proxy=None):
    r=rpc_call("eth_blockNumber",[],proxy=proxy)
    return int(r["result"],16) if r and "result" in r else 0

def sepolia_get_nonce(addr,proxy=None):
    r=sepolia_rpc("eth_getTransactionCount",[addr,"latest"],proxy)
    return int(r["result"],16) if r and "result" in r else None
def sepolia_get_balance(addr,proxy=None):
    r=sepolia_rpc("eth_getBalance",[addr,"latest"],proxy)
    return int(r["result"],16)/10**18 if r and "result" in r else 0
def sepolia_get_gas_price(proxy=None):
    r=sepolia_rpc("eth_gasPrice",[],proxy)
    return int(r["result"],16) if r and "result" in r else 0x16b0c4d89
def sepolia_estimate_gas(tx,proxy=None):
    r=sepolia_rpc("eth_estimateGas",[tx],proxy)
    if r and "result" in r: return int(r["result"],16),None
    if r and "error" in r: return None,r["error"]
    return None,{"message":"Unknown"}
def sepolia_send_raw(stx,proxy=None):
    r=sepolia_rpc("eth_sendRawTransaction",[stx],proxy)
    if r:
        if "result" in r: return r["result"],None
        if "error" in r: return None,r["error"]
    return None,{"message":"No response"}
def sepolia_get_receipt(tx_hash,proxy=None):
    r=sepolia_rpc("eth_getTransactionReceipt",[tx_hash],proxy)
    return r.get("result") if r else None

def estimate_gas(tx,origin="https://onchaingm.com",referer="https://onchaingm.com/",proxy=None):
    r=rpc_call("eth_estimateGas",[tx],origin,referer,proxy)
    if r and "result" in r: return int(r["result"],16),None
    if r and "error" in r: return None,r["error"]
    return None,{"message":"Unknown","data":""}
def estimate_gas_direct(tx,origin,referer,proxy=None):
    r=rpc_direct("eth_estimateGas",[tx],origin,referer,proxy)
    if r and "result" in r: return int(r["result"],16),None
    if r and "error" in r: return None,r["error"]
    return None,{"message":"Unknown","data":""}
def send_raw_tx(stx,proxy=None):
    r=rpc_call("eth_sendRawTransaction",[stx],proxy=proxy)
    if r:
        if "result" in r: return r["result"],None
        if "error" in r: return None,r["error"]
    return None,{"message":"No response"}
def send_raw_direct(stx,origin,referer,proxy=None):
    r=rpc_direct("eth_sendRawTransaction",[stx],origin,referer,proxy)
    if r:
        if "result" in r: return r["result"],None
        if "error" in r: return None,r["error"]
    return None,{"message":"No response"}
def get_receipt(tx_hash,proxy=None):
    r=rpc_call("eth_getTransactionReceipt",[tx_hash],proxy=proxy)
    return r.get("result") if r else None
def get_receipt_direct(tx_hash,origin,referer,proxy=None):
    r=rpc_direct("eth_getTransactionReceipt",[tx_hash],origin,referer,proxy)
    return r.get("result") if r else None
def get_gas_price(proxy=None):
    r=rpc_call("eth_gasPrice",[],proxy=proxy)
    return int(r["result"],16) if r and "result" in r else 0xb71b00
def decode_revert(ed):
    if isinstance(ed,str):
        for c,m in REVERT_ERRORS.items():
            if ed.startswith(c): return m
    return None

def get_token_balance(token_addr, wallet_addr, proxy=None):
    data = "0x70a08231" + pad(wallet_addr.lower().replace("0x",""))
    r = rpc_direct("eth_call", [{"to": token_addr.lower(), "data": data}, "latest"], EDEL_ORIGIN, EDEL_REFERER, proxy)
    if r and "result" in r:
        return int(r["result"], 16)
    return 0

def get_debt_balance(debt_token_addr, wallet_addr, proxy=None):
    """Get variable debt token balance (how much user owes)"""
    data = "0x70a08231" + pad(wallet_addr.lower().replace("0x",""))
    r = rpc_direct("eth_call", [{"to": debt_token_addr.lower(), "data": data}, "latest"], EDEL_ORIGIN, EDEL_REFERER, proxy)
    if r and "result" in r:
        return int(r["result"], 16)
    return 0

# ============================================
# CALLDATA
# ============================================
def pad(h,l=64):
    if h.startswith("0x"): h=h[2:]
    return h.zfill(l)

def pad_int(v, l=64):
    if v >= 0: return hex(v)[2:].zfill(l)
    else: return hex((1 << 256) + v)[2:].zfill(l)

def build_gm(): return "0x"+SELECTOR_GM+pad("0")
def build_deploy(): return "0x"+SELECTOR_DEPLOY
def build_badge(): return "0x"+SELECTOR_BADGE
def build_domain(dn):
    nb=dn.encode("utf-8"); nl=len(nb); nh=nb.hex()
    return "0x"+SELECTOR_MINT_DOMAIN+pad("40")+pad("0")+pad(hex(nl)[2:])+nh.ljust(((nl+31)//32)*64,"0")
def build_flamenco(addr):
    a=addr.lower().replace("0x",""); inner="449a52f8"+pad(a)+pad("1")
    nft=CONTRACT_FLAMENCO.lower().replace("0x",""); il=len(inner)//2
    return "0x"+"b510391f"+pad(nft)+pad("40")+pad(hex(il)[2:])+inner.ljust(((il+31)//32)*64,"0")
def build_omnihub():
    return "0x"+"a25ffea8"+pad("0")+pad("1")+pad("0")+pad("80")+pad("0")

def build_watchoor_simple(selector: bytes) -> bytes:
    return selector + int(0).to_bytes(32, 'big')
def build_watchoor_deploy_data(selector: bytes, name: str, symbol: str) -> bytes:
    name_b = name.encode(); sym_b = symbol.encode()
    def enc_str(s):
        sb = s.encode() if isinstance(s, str) else s
        off = b'\x00'*32; ln = len(sb).to_bytes(32,'big')
        padded = sb + b'\x00'*((32-len(sb)%32)%32)
        return ln + padded
    names_enc = enc_str(name); sym_enc = enc_str(symbol)
    name_offset = (64).to_bytes(32,'big')
    sym_offset = (64 + 32 + len(names_enc)).to_bytes(32,'big')
    uint_zero = (0).to_bytes(32,'big')
    uint_offset = (64 + 32 + len(names_enc) + 32 + len(sym_enc)).to_bytes(32,'big')
    return selector + name_offset + sym_offset + uint_offset + names_enc + sym_enc + uint_zero
def random_letters(length: int, uppercase: bool) -> str:
    import secrets as _sec
    alphabet = string.ascii_uppercase if uppercase else string.ascii_lowercase
    return ''.join(_sec.choice(alphabet) for _ in range(length))

# ZNS calldata builders
def build_zns_gm() -> str:
    """d371cd50 + uint256(0)"""
    return "0xd371cd50" + "00" * 32
def build_zns_deploy() -> str:
    """deploy(address) with zero address"""
    sel = keccak256(b"deploy(address)")[:4].hex()
    return "0x" + sel + pad("0") * 0 + "00" * 12 + "00" * 20  # 32-byte zero addr
def build_zns_mint() -> str:
    sel = keccak256(b"mint()")[:4].hex()
    return "0x" + sel

def build_bridge_calldata(addr, l2_call_value):
    a = addr.lower().replace("0x", "")
    calldata = BRIDGE_SELECTOR+pad(a)+pad(hex(l2_call_value)[2:])+pad(hex(BRIDGE_MAX_SUBMISSION_COST)[2:])+pad(a)+pad(a)+pad(hex(BRIDGE_L2_GAS_LIMIT)[2:])+pad(hex(BRIDGE_MAX_FEE_PER_GAS)[2:])+pad(hex(0x100)[2:])+pad("0")
    return "0x" + calldata

def calculate_bridge_value(l2_call_value):
    return l2_call_value + BRIDGE_MAX_SUBMISSION_COST + BRIDGE_L2_GAS_LIMIT * BRIDGE_MAX_FEE_PER_GAS

def build_approve_calldata(spender):
    return "0x095ea7b3" + pad(spender.lower().replace("0x","")) + "f" * 64

def build_swap_exact_calldata(amount_in, path_hex, deadline):
    selector = "3593564c"
    wrap_data = pad("0000000000000000000000000000000000000000000000000000000000000002") + pad(hex(amount_in)[2:])
    swap_data = pad("0000000000000000000000000000000000000000000000000000000000000001") + pad(hex(amount_in)[2:]) + pad("0") + pad(hex(0xa0)[2:]) + pad("0")
    path_bytes = bytes.fromhex(path_hex); path_len = len(path_bytes)
    swap_data += pad(hex(path_len)[2:]) + path_hex.ljust(((path_len + 31) // 32) * 64, "0")
    data = selector + pad(hex(0x60)[2:]) + pad(hex(0xa0)[2:]) + pad(hex(deadline)[2:])
    data += pad(hex(2)[2:]) + "0b00" + "0" * 60
    data += pad(hex(2)[2:])
    wrap_data_len = len(wrap_data) // 2; swap_data_len = len(swap_data) // 2
    inputs0_offset = 0x40; wrap_padded_size = ((wrap_data_len + 31) // 32) * 32
    inputs1_offset = inputs0_offset + 32 + wrap_padded_size
    data += pad(hex(inputs0_offset)[2:]) + pad(hex(inputs1_offset)[2:])
    data += pad(hex(wrap_data_len)[2:]) + wrap_data
    data += pad(hex(swap_data_len)[2:]) + swap_data
    return "0x" + data

def build_mint_calldata(token0, token1, fee, tick_lower, tick_upper, amount0_desired, amount1_desired, amount0_min, amount1_min, recipient, deadline):
    selector = "88316456"
    data = selector + pad(token0.lower().replace("0x","")) + pad(token1.lower().replace("0x",""))
    data += pad(hex(fee)[2:]) + pad_int(tick_lower) + pad_int(tick_upper)
    data += pad(hex(amount0_desired)[2:]) + pad(hex(amount1_desired)[2:])
    data += pad(hex(amount0_min)[2:]) + pad(hex(amount1_min)[2:])
    data += pad(recipient.lower().replace("0x","")) + pad(hex(deadline)[2:])
    return "0x" + data

# ============================================
# EDEL FINANCE CALLDATA BUILDERS
# ============================================
def build_supply_calldata(asset_addr, amount, on_behalf_of):
    """supply(address asset, uint256 amount, address onBehalfOf, uint16 referralCode)"""
    selector = "617ba037"
    data = selector
    data += pad(asset_addr.lower().replace("0x",""))
    data += pad(hex(amount)[2:])
    data += pad(on_behalf_of.lower().replace("0x",""))
    data += pad("0")  # referralCode = 0
    return "0x" + data

def build_borrow_calldata(asset_addr, amount, on_behalf_of):
    """borrow(address asset, uint256 amount, uint256 interestRateMode, uint16 referralCode, address onBehalfOf)"""
    selector = "a415bcad"
    data = selector
    data += pad(asset_addr.lower().replace("0x",""))
    data += pad(hex(amount)[2:])
    data += pad(hex(2)[2:])  # interestRateMode = 2 (variable)
    data += pad("0")  # referralCode = 0
    data += pad(on_behalf_of.lower().replace("0x",""))
    return "0x" + data

def build_repay_calldata(asset_addr, on_behalf_of):
    """repay(address asset, uint256 amount, uint256 interestRateMode, address onBehalfOf)
    amount = uint256 max (repay all)"""
    selector = "573ade81"
    data = selector
    data += pad(asset_addr.lower().replace("0x",""))
    data += "f" * 64  # uint256 max = repay full debt
    data += pad(hex(2)[2:])  # interestRateMode = 2 (variable)
    data += pad(on_behalf_of.lower().replace("0x",""))
    return "0x" + data

# ============================================
# HELPERS
# ============================================
def log_to_supabase(dn,wa,tx):
    try: requests.post(SUPABASE_URL,json={"domain_name":dn+".hood","wallet_address":wa.lower(),"chain_id":CHAIN_ID,"chain_name":"Robinhood Testnet","tx_hash":tx,"price":None},headers={"Content-Type":"application/json","apikey":SUPABASE_KEY,"Authorization":f"Bearer {SUPABASE_KEY}","content-profile":"public","x-client-info":"supabase-js-web/2.82.0","Origin":"https://infinityname.com","Referer":"https://infinityname.com/"},timeout=15)
    except: pass

def omnihub_login(addr,pk,proxy=None):
    h={"Accept":"application/json","Content-Type":"application/json","Origin":"https://omnihub.xyz","Referer":"https://omnihub.xyz/","User-Agent":"Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36"}
    log_process("OmniHub auth...")
    try:
        resp=requests.post(f"{OMNIHUB_API}/auth/request-nonce",json={"address":addr},headers=h,timeout=15,proxies=proxy)
        if resp.status_code!=200: return None
        nm=resp.json().get("nonce","")
        if not nm: return None
    except: return None
    sig=sign_message(nm,pk)
    try:
        resp=requests.post(f"{OMNIHUB_API}/auth/login",json={"address":addr,"signature":sig},headers=h,timeout=15,proxies=proxy)
        if resp.status_code!=200: return None
        t=resp.json().get("token",{}).get("token","")
        if t: log_success("OmniHub OK"); return t
        return None
    except: return None

def omnihub_verify(bearer,proxy=None):
    try: requests.get(f"{OMNIHUB_API}/collections/862561/phases/verify",headers={"Accept":"application/json","Authorization":f"Bearer {bearer}","Origin":"https://omnihub.xyz","Referer":"https://omnihub.xyz/"},timeout=15,proxies=proxy)
    except: pass

def classify_result(r):
    if r=="REVERTED": return "skip"
    elif r=="FAILED": return "fail"
    elif r: return "success"
    return "fail"

def print_result(a,r):
    print()
    if r=="REVERTED": print(f"{BOLD_RED}  {a} - SKIPPED{RESET}")
    elif r=="FAILED": print(f"{BOLD_RED}  {a} - FAILED{RESET}")
    elif r: print(f"{BOLD_GREEN}  {a} - SUCCESS{RESET}"); print(f"  {BOLD_WHITE}TX: {BOLD_CYAN}{r}{RESET}")
    else: print(f"{BOLD_RED}  {a} - FAILED{RESET}")

def print_account_header(idx,total,addr,bal,proxy,extra=None):
    print(f"\n{BOLD_MAGENTA}{'─'*70}{RESET}")
    print(f"{BOLD_WHITE}  Account {idx}/{total}{RESET}")
    print(f"  {BOLD_WHITE}Wallet  : {BOLD_CYAN}{addr}{RESET}")
    print(f"  {BOLD_WHITE}Balance : {BOLD_GREEN}{bal:.10f} ETH{RESET}")
    print(f"  {BOLD_WHITE}Proxy   : {BOLD_YELLOW}{mask_proxy(proxy)}{RESET}")
    if extra:
        for k,v in extra.items(): print(f"  {BOLD_WHITE}{k:<9}: {BOLD_GREEN}{v}{RESET}")
    print(f"{BOLD_MAGENTA}{'─'*70}{RESET}")

def print_round_header(cr,tr,name):
    print(f"\n{BOLD_CYAN}{'='*70}{RESET}")
    print(f"{BOLD_WHITE}  ROUND {cr}/{tr} - {name}{RESET}")
    print(f"{BOLD_CYAN}{'='*70}{RESET}")

def add_result(R,key,result):
    r=classify_result(result); R[f"{key}_{'success' if r=='success' else 'skip' if r=='skip' else 'fail'}"]+=1

def wait_confirm(tx_hash,proxy=None,timeout=180,ud=False,origin="https://onchaingm.com",referer="https://onchaingm.com/"):
    log_process("Waiting...")
    for i in range(timeout//3):
        time.sleep(3)
        receipt=get_receipt_direct(tx_hash,origin,referer,proxy) if ud else get_receipt(tx_hash,proxy)
        if receipt:
            status=int(receipt.get("status","0x0"),16); bn=int(receipt.get("blockNumber","0x0"),16); gu=int(receipt.get("gasUsed","0x0"),16)
            print()
            if status==1:
                log_success("CONFIRMED!")
                print(f"  {BOLD_WHITE}Block: {BOLD_CYAN}{bn}{RESET}  Gas: {BOLD_YELLOW}{gu}{RESET}")
                for le in receipt.get("logs",[]):
                    t=le.get("topics",[])
                    if len(t)>=4 and t[0]=="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef" and t[1]=="0x"+"0"*64:
                        print(f"  {BOLD_WHITE}Token: {BOLD_GREEN}{int(t[3],16)}{RESET} NFT: {BOLD_CYAN}{le.get('address','')}{RESET}")
                return True,bn,gu
            else: log_error("REVERTED!"); return False,bn,gu
        sys.stdout.write(f"\r  {BOLD_YELLOW}[WAIT] {(i+1)*3}s...{RESET}    "); sys.stdout.flush()
    print(); log_warn("Timeout"); return None,0,0

def wait_sepolia_confirm(tx_hash,proxy=None,timeout=120):
    log_process("Waiting for Sepolia confirmation...")
    for i in range(timeout//5):
        time.sleep(5)
        receipt=sepolia_get_receipt(tx_hash,proxy)
        if receipt:
            status=int(receipt.get("status","0x0"),16); bn=int(receipt.get("blockNumber","0x0"),16); gu=int(receipt.get("gasUsed","0x0"),16)
            print()
            if status==1: log_success("BRIDGE TX CONFIRMED ON SEPOLIA!"); print(f"  {BOLD_WHITE}Block: {BOLD_CYAN}{bn}{RESET}  Gas: {BOLD_YELLOW}{gu}{RESET}"); return True,bn,gu
            else: log_error("BRIDGE TX REVERTED!"); return False,bn,gu
        sys.stdout.write(f"\r  {BOLD_YELLOW}[WAIT] {(i+1)*5}s...{RESET}    "); sys.stdout.flush()
    print(); log_warn("Timeout"); return None,0,0

def send_transaction(pk,addr,to,val,data,name,origin="https://onchaingm.com",referer="https://onchaingm.com/",proxy=None):
    ud=origin in ["https://robinhood-flamenco.testnet.nfts2.me","https://omnihub.xyz","https://app.synthra.org","https://robinhood.edel.finance"]
    print(f"\n  {BOLD_CYAN}--- {name} ---{RESET}")
    cb=get_block_number(proxy)
    if cb: print(f"  {BOLD_WHITE}Block: {BOLD_CYAN}{cb}{RESET}")
    nonce=get_nonce_direct(addr,origin,referer,proxy) if ud else get_nonce(addr,proxy)
    if nonce is None: log_error("Nonce failed!"); return None
    gp=get_gas_price(proxy)
    print(f"  {BOLD_WHITE}Nonce: {nonce}  GasPrice: {gp/10**9:.4f} Gwei{RESET}")
    etx={"from":addr,"to":to.lower(),"value":hex(val),"data":data}
    eg,ee=estimate_gas_direct(etx,origin,referer,proxy) if ud else estimate_gas(etx,origin,referer,proxy)
    if eg is None:
        if ee:
            ed=ee.get("data",""); rr=decode_revert(ed)
            if rr: log_error(rr); return "REVERTED"
            log_error(f"Gas est: {ee.get('message','?')}")
        return "REVERTED"
    gl=int(eg*GAS_MULTIPLIER)
    print(f"  {BOLD_WHITE}Gas: {eg}->{gl}  Value: {val/10**18:.6f} ETH{RESET}")
    tx={"nonce":nonce,"gasPrice":gp,"gas":gl,"to":to,"value":val,"data":data}
    log_process("Signing...")
    try: stx=sign_tx(tx,pk); log_success("Signed")
    except Exception as e: log_error(f"Sign: {e}"); return None
    log_process("Broadcasting...")
    th,se=send_raw_direct(stx,origin,referer,proxy) if ud else send_raw_tx(stx,proxy)
    if not th:
        if se: log_error(f"Broadcast: {se.get('message','?')}")
        return None
    print(f"\n{BOLD_GREEN}{'='*70}{RESET}")
    log_success(f"TX: {name}")
    print(f"  {BOLD_WHITE}Hash: {BOLD_CYAN}{th}{RESET}")
    print(f"  {BOLD_WHITE}Link: {BOLD_CYAN}{EXPLORER_URL}/tx/{th}{RESET}")
    print(f"{BOLD_GREEN}{'='*70}{RESET}\n")
    ok,_,_=wait_confirm(th,proxy,180,ud,origin,referer)
    if ok is True: return th
    elif ok is False: return "FAILED"
    return th

# ============================================
# ACTION: LENDING (Edel Finance)
# ============================================
def action_lending():
    print(f"\n{BOLD_CYAN}{'='*70}{RESET}")
    print(f"{BOLD_GREEN}  EDEL FINANCE - LENDING (Supply / Borrow / Repay){RESET}")
    print(f"{BOLD_CYAN}{'='*70}{RESET}")
    print(f"  {BOLD_WHITE}Pool Contract : {BOLD_CYAN}{CONTRACT_EDEL_POOL}{RESET}")
    print(f"  {BOLD_WHITE}Protocol      : Edel Finance (Aave V3 Fork){RESET}")
    print(f"  {BOLD_WHITE}Site          : {BOLD_CYAN}robinhood.edel.finance{RESET}")
    print(f"{BOLD_CYAN}{'='*70}{RESET}")

    # Show tokens
    edel_list = list(EDEL_TOKENS.keys())
    print(f"\n  {BOLD_WHITE}Available Tokens:{RESET}")
    for i, tk in enumerate(edel_list, 1):
        info = EDEL_TOKENS[tk]
        print(f"    {BOLD_GREEN}[{i}]{RESET} {BOLD_WHITE}{info['symbol']:<6} - {info['name']}{RESET}  ({info['address'][:10]}...)")

    while True:
        try:
            tc = int(input(f"\n  {BOLD_YELLOW}Select token [1-{len(edel_list)}]: {RESET}").strip())
            if 1 <= tc <= len(edel_list): break
            log_error(f"Select 1-{len(edel_list)}")
        except: log_error("Enter a valid number")

    selected_token = edel_list[tc-1]
    token_info = EDEL_TOKENS[selected_token]
    token_addr = token_info["address"]

    print(f"\n  {BOLD_WHITE}Selected: {BOLD_GREEN}{token_info['symbol']} ({token_info['name']}){RESET}")
    print(f"  {BOLD_WHITE}Address : {BOLD_CYAN}{token_addr}{RESET}")

    # Action selection
    print(f"\n  {BOLD_WHITE}Actions:{RESET}")
    print(f"    {BOLD_GREEN}[1]{RESET} {BOLD_WHITE}Supply (Deposit token as collateral){RESET}")
    print(f"    {BOLD_BLUE}[2]{RESET} {BOLD_WHITE}Borrow (Borrow token against collateral){RESET}")
    print(f"    {BOLD_YELLOW}[3]{RESET} {BOLD_WHITE}Repay (Repay borrowed debt){RESET}")
    print(f"    {BOLD_MAGENTA}[4]{RESET} {BOLD_WHITE}Full Cycle (Supply -> Borrow -> Repay){RESET}")

    while True:
        try:
            ac = int(input(f"\n  {BOLD_YELLOW}Select action [1-4]: {RESET}").strip())
            if 1 <= ac <= 4: break
            log_error("Select 1-4")
        except: log_error("Enter a valid number")

    # Ask amounts
    if ac in [1, 4]:
        while True:
            try:
                sup_str = input(f"\n  {BOLD_YELLOW}Supply amount in {selected_token} (e.g. 0.1): {RESET}").strip()
                supply_amount = float(sup_str)
                if supply_amount <= 0: log_error("Must be > 0"); continue
                break
            except: log_error("Enter a valid number")
        supply_wei = int(supply_amount * 10**18)
    else:
        supply_wei = 0; supply_amount = 0

    if ac in [2, 4]:
        while True:
            try:
                bor_str = input(f"\n  {BOLD_YELLOW}Borrow amount in {selected_token} (e.g. 0.01): {RESET}").strip()
                borrow_amount = float(bor_str)
                if borrow_amount <= 0: log_error("Must be > 0"); continue
                break
            except: log_error("Enter a valid number")
        borrow_wei = int(borrow_amount * 10**18)
    else:
        borrow_wei = 0; borrow_amount = 0

    if not ensure_accounts_loaded(): return
    repeat = ask_repeat_count("Lending")

    total_s, total_f, total_sk = 0, 0, 0

    for rnd in range(1, repeat+1):
        print_round_header(rnd, repeat, "EDEL LENDING")
        for idx, pk in enumerate(loaded_accounts, 1):
            proxy = get_random_proxy()
            addr = pk2addr(pk)
            bal = get_balance(addr, proxy)
            token_bal = get_token_balance(token_addr, addr, proxy)

            extra_info = {
                "Token": f"{selected_token} ({token_info['name']})",
                f"{selected_token}": f"{token_bal/10**18:.10f}"
            }

            # Show debt balance if we have debt token info
            debt_bal = 0
            if token_info.get("debtToken"):
                debt_bal = get_debt_balance(token_info["debtToken"], addr, proxy)
                extra_info["Debt"] = f"{debt_bal/10**18:.10f} {selected_token}"

            print_account_header(idx, len(loaded_accounts), addr, bal, proxy, extra_info)

            # ===== SUPPLY =====
            if ac in [1, 4]:
                print(f"\n  {BOLD_GREEN}━━━ STEP: SUPPLY {supply_amount} {selected_token} ━━━{RESET}")

                if token_bal < supply_wei:
                    log_error(f"Insufficient {selected_token}! Have {token_bal/10**18:.10f}, need {supply_amount}")
                    log_info(f"Use Swap option first to get {selected_token}")
                    total_f += 1
                    continue

                # Approve token for Pool
                print(f"\n  {BOLD_CYAN}--- Approve {selected_token} for Pool ---{RESET}")
                approve_data = build_approve_calldata(CONTRACT_EDEL_POOL)
                approve_result = send_transaction(pk, addr, token_addr, 0, approve_data,
                    f"APPROVE {selected_token}", EDEL_ORIGIN, EDEL_REFERER, proxy)

                if classify_result(approve_result) != "success":
                    log_error(f"Approve failed!")
                    total_f += 1
                    print_result(f"APPROVE {selected_token}", approve_result)
                    continue
                print_result(f"APPROVE {selected_token}", approve_result)
                time.sleep(3)

                # Supply
                print(f"\n  {BOLD_CYAN}--- Supply {supply_amount} {selected_token} ---{RESET}")
                supply_data = build_supply_calldata(token_addr, supply_wei, addr)
                supply_result = send_transaction(pk, addr, CONTRACT_EDEL_POOL, 0, supply_data,
                    f"SUPPLY {supply_amount} {selected_token}", EDEL_ORIGIN, EDEL_REFERER, proxy)

                r = classify_result(supply_result)
                if r == "success":
                    total_s += 1
                    log_success(f"Supplied {supply_amount} {selected_token} -> Got e{selected_token} (aToken)")
                elif r == "skip": total_sk += 1
                else: total_f += 1
                print_result(f"SUPPLY {selected_token}", supply_result)
                time.sleep(3)

                # Refresh balance
                token_bal = get_token_balance(token_addr, addr, proxy)

            # ===== BORROW =====
            if ac in [2, 4]:
                print(f"\n  {BOLD_BLUE}━━━ STEP: BORROW {borrow_amount} {selected_token} ━━━{RESET}")

                borrow_data = build_borrow_calldata(token_addr, borrow_wei, addr)
                borrow_result = send_transaction(pk, addr, CONTRACT_EDEL_POOL, 0, borrow_data,
                    f"BORROW {borrow_amount} {selected_token}", EDEL_ORIGIN, EDEL_REFERER, proxy)

                r = classify_result(borrow_result)
                if r == "success":
                    total_s += 1
                    log_success(f"Borrowed {borrow_amount} {selected_token}")
                    # Show updated balances
                    new_token_bal = get_token_balance(token_addr, addr, proxy)
                    print(f"  {BOLD_WHITE}{selected_token} Balance: {BOLD_GREEN}{new_token_bal/10**18:.10f}{RESET}")
                    if token_info.get("debtToken"):
                        new_debt = get_debt_balance(token_info["debtToken"], addr, proxy)
                        print(f"  {BOLD_WHITE}Debt Balance : {BOLD_RED}{new_debt/10**18:.10f} {selected_token}{RESET}")
                elif r == "skip": total_sk += 1
                else: total_f += 1
                print_result(f"BORROW {selected_token}", borrow_result)
                time.sleep(3)

            # ===== REPAY =====
            if ac in [3, 4]:
                print(f"\n  {BOLD_YELLOW}━━━ STEP: REPAY ALL {selected_token} DEBT ━━━{RESET}")

                # Check debt first
                if token_info.get("debtToken"):
                    current_debt = get_debt_balance(token_info["debtToken"], addr, proxy)
                    print(f"  {BOLD_WHITE}Current Debt: {BOLD_RED}{current_debt/10**18:.10f} {selected_token}{RESET}")
                    if current_debt == 0:
                        log_info("No debt to repay!")
                        total_sk += 1
                        continue

                # Check token balance for repay
                current_token_bal = get_token_balance(token_addr, addr, proxy)
                print(f"  {BOLD_WHITE}{selected_token} Available: {BOLD_GREEN}{current_token_bal/10**18:.10f}{RESET}")

                if token_info.get("debtToken") and current_token_bal < current_debt:
                    log_warn(f"Token balance ({current_token_bal/10**18:.10f}) < Debt ({current_debt/10**18:.10f})")
                    log_warn("Will repay what we can (may leave small dust)")

                # Approve for repay
                print(f"\n  {BOLD_CYAN}--- Approve {selected_token} for Repay ---{RESET}")
                approve_data = build_approve_calldata(CONTRACT_EDEL_POOL)
                approve_result = send_transaction(pk, addr, token_addr, 0, approve_data,
                    f"APPROVE {selected_token} (Repay)", EDEL_ORIGIN, EDEL_REFERER, proxy)

                if classify_result(approve_result) != "success":
                    log_error("Approve for repay failed!")
                    total_f += 1
                    print_result(f"APPROVE {selected_token} (Repay)", approve_result)
                    continue
                print_result(f"APPROVE {selected_token} (Repay)", approve_result)
                time.sleep(3)

                # Repay (max uint256 = repay all)
                print(f"\n  {BOLD_CYAN}--- Repay All Debt ---{RESET}")
                repay_data = build_repay_calldata(token_addr, addr)
                repay_result = send_transaction(pk, addr, CONTRACT_EDEL_POOL, 0, repay_data,
                    f"REPAY ALL {selected_token}", EDEL_ORIGIN, EDEL_REFERER, proxy)

                r = classify_result(repay_result)
                if r == "success":
                    total_s += 1
                    log_success(f"Repaid all {selected_token} debt!")
                    # Show final balances
                    final_token_bal = get_token_balance(token_addr, addr, proxy)
                    print(f"  {BOLD_WHITE}{selected_token} Balance: {BOLD_GREEN}{final_token_bal/10**18:.10f}{RESET}")
                    if token_info.get("debtToken"):
                        final_debt = get_debt_balance(token_info["debtToken"], addr, proxy)
                        print(f"  {BOLD_WHITE}Debt Balance : {BOLD_GREEN}{final_debt/10**18:.10f} {selected_token}{RESET}")
                elif r == "skip": total_sk += 1
                else: total_f += 1
                print_result(f"REPAY {selected_token}", repay_result)

            if idx < len(loaded_accounts):
                time.sleep(random.randint(5, 10))

        if rnd < repeat:
            time.sleep(random.randint(10, 20))

    # Summary
    action_names = {1: "SUPPLY", 2: "BORROW", 3: "REPAY", 4: "FULL CYCLE"}
    print(f"\n{BOLD_GREEN}{'='*70}{RESET}")
    print(f"{BOLD_GREEN}  EDEL LENDING SUMMARY - {action_names[ac]}{RESET}")
    print(f"{BOLD_GREEN}{'─'*70}{RESET}")
    print(f"  {BOLD_WHITE}Accounts : {BOLD_CYAN}{len(loaded_accounts)}{RESET}")
    print(f"  {BOLD_WHITE}Token    : {BOLD_CYAN}{selected_token} ({token_info['name']}){RESET}")
    if ac in [1, 4]: print(f"  {BOLD_WHITE}Supply   : {BOLD_GREEN}{supply_amount} {selected_token}{RESET}")
    if ac in [2, 4]: print(f"  {BOLD_WHITE}Borrow   : {BOLD_GREEN}{borrow_amount} {selected_token}{RESET}")
    if ac in [3, 4]: print(f"  {BOLD_WHITE}Repay    : {BOLD_GREEN}All Debt{RESET}")
    print(f"  {BOLD_GREEN}Success  : {total_s}{RESET}")
    print(f"  {BOLD_YELLOW}Skipped  : {total_sk}{RESET}")
    print(f"  {BOLD_RED}Failed   : {total_f}{RESET}")
    print(f"{BOLD_GREEN}{'='*70}{RESET}")


# ============================================
# ACTION: SWAP
# ============================================
def action_swap():
    print(f"\n{BOLD_CYAN}{'='*70}{RESET}")
    print(f"{BOLD_YELLOW}  SWAP ETH -> TOKENS (Synthra DEX){RESET}")
    print(f"{BOLD_CYAN}{'='*70}{RESET}")
    swap_tokens = list(SWAP_PATHS.keys())
    print(f"\n  {BOLD_WHITE}Available tokens:{RESET}")
    for i, tk in enumerate(swap_tokens, 1):
        info = TOKENS[tk]
        print(f"    {BOLD_GREEN}[{i}]{RESET} {BOLD_WHITE}{info['symbol']:<6} - {info['name']}{RESET}")
    print(f"    {BOLD_GREEN}[{len(swap_tokens)+1}]{RESET} {BOLD_WHITE}ALL TOKENS{RESET}")
    while True:
        try:
            tc = int(input(f"\n  {BOLD_YELLOW}Select [1-{len(swap_tokens)+1}]: {RESET}").strip())
            if 1 <= tc <= len(swap_tokens)+1: break
        except: pass
        log_error("Invalid")
    selected_tokens = swap_tokens if tc == len(swap_tokens)+1 else [swap_tokens[tc-1]]
    while True:
        try:
            swap_amount = float(input(f"\n  {BOLD_YELLOW}ETH per swap (e.g. 0.0001): {RESET}").strip())
            if swap_amount > 0: break
        except: pass
        log_error("Invalid")
    swap_value = int(swap_amount * 10**18)
    if not ensure_accounts_loaded(): return
    repeat = ask_repeat_count("Swap")
    total_s, total_f, total_sk = 0, 0, 0
    for rnd in range(1, repeat+1):
        print_round_header(rnd, repeat, "SWAP")
        for idx, pk in enumerate(loaded_accounts, 1):
            proxy = get_random_proxy(); addr = pk2addr(pk); bal = get_balance(addr, proxy)
            print_account_header(idx, len(loaded_accounts), addr, bal, proxy, {"Tokens": ', '.join(selected_tokens)})
            for token_sym in selected_tokens:
                path_info = SWAP_PATHS[token_sym]; deadline = int(time.time()) + 1800
                calldata = build_swap_exact_calldata(swap_value, path_info["path"], deadline)
                result = send_transaction(pk, addr, CONTRACT_SYNTHRA_ROUTER, swap_value, calldata,
                    f"SWAP ETH->{token_sym}", "https://app.synthra.org", "https://app.synthra.org/", proxy)
                r = classify_result(result)
                if r == "success": total_s += 1
                elif r == "skip": total_sk += 1
                else: total_f += 1
                print_result(f"SWAP ETH->{token_sym}", result)
                time.sleep(random.randint(2, 5))
            if idx < len(loaded_accounts): time.sleep(random.randint(3, 8))
        if rnd < repeat: time.sleep(random.randint(5, 15))
    print(f"\n{BOLD_GREEN}{'='*70}\n  SWAP: {BOLD_GREEN}{total_s} OK  {BOLD_YELLOW}{total_sk} Skip  {BOLD_RED}{total_f} Fail{RESET}\n{BOLD_GREEN}{'='*70}{RESET}")

# ============================================
# ACTION: ADD LIQUIDITY
# ============================================
def action_add_liquidity():
    print(f"\n{BOLD_CYAN}{'='*70}{RESET}")
    print(f"{BOLD_CYAN}  ADD LIQUIDITY (Synthra DEX){RESET}")
    print(f"{BOLD_CYAN}{'='*70}{RESET}")
    if not ensure_accounts_loaded(): return
    print(f"\n    {BOLD_GREEN}[1]{RESET} WETH/USDC  {BOLD_GREEN}[2]{RESET} WETH/SYN  {BOLD_GREEN}[3]{RESET} ALL")
    while True:
        try:
            pc = int(input(f"\n  {BOLD_YELLOW}Select [1-3]: {RESET}").strip())
            if 1 <= pc <= 3: break
        except: pass
    selected_pools = ["WETH/USDC"] if pc==1 else ["WETH/SYN"] if pc==2 else ["WETH/USDC","WETH/SYN"]
    while True:
        try:
            liq_amount = int(input(f"\n  {BOLD_YELLOW}Token amount wei (e.g. 10000000000000): {RESET}").strip())
            if liq_amount > 0: break
        except: pass
    repeat = ask_repeat_count("Add Liquidity")
    total_s, total_f, total_sk = 0, 0, 0
    for rnd in range(1, repeat+1):
        print_round_header(rnd, repeat, "ADD LIQUIDITY")
        for idx, pk in enumerate(loaded_accounts, 1):
            proxy = get_random_proxy(); addr = pk2addr(pk); bal = get_balance(addr, proxy)
            print_account_header(idx, len(loaded_accounts), addr, bal, proxy)
            for pool_name in selected_pools:
                pool_info = LIQUIDITY_POOLS[pool_name]; token1 = pool_info["token1"]
                token1_symbol = pool_name.split("/")[1]
                token1_bal = get_token_balance(token1, addr, proxy)
                if token1_bal < liq_amount:
                    log_error(f"Low {token1_symbol}!"); total_f += 1; continue
                approve_data = build_approve_calldata(CONTRACT_SYNTHRA_POSITION_MANAGER)
                ar = send_transaction(pk, addr, token1, 0, approve_data, f"APPROVE {token1_symbol}", "https://app.synthra.org", "https://app.synthra.org/", proxy)
                if classify_result(ar) != "success": total_f += 1; continue
                time.sleep(3)
                deadline = int(time.time()) + 1800
                mint_data = build_mint_calldata(pool_info["token0"], token1, pool_info["fee"], pool_info["tickLower"], pool_info["tickUpper"], 0, liq_amount, 0, liq_amount, addr, deadline)
                mr = send_transaction(pk, addr, CONTRACT_SYNTHRA_POSITION_MANAGER, 0, mint_data, f"ADD LIQ {pool_name}", "https://app.synthra.org", "https://app.synthra.org/", proxy)
                r = classify_result(mr)
                if r == "success": total_s += 1
                elif r == "skip": total_sk += 1
                else: total_f += 1
                print_result(f"ADD LIQ {pool_name}", mr)
                time.sleep(random.randint(3, 6))
            if idx < len(loaded_accounts): time.sleep(random.randint(5, 10))
        if rnd < repeat: time.sleep(random.randint(10, 20))
    print(f"\n{BOLD_GREEN}{'='*70}\n  LIQUIDITY: {BOLD_GREEN}{total_s} OK  {BOLD_YELLOW}{total_sk} Skip  {BOLD_RED}{total_f} Fail{RESET}\n{BOLD_GREEN}{'='*70}{RESET}")

# ============================================
# ACTION: BRIDGE
# ============================================
def action_bridge():
    print(f"\n{BOLD_CYAN}{'='*70}{RESET}\n{BOLD_BLUE}  BRIDGE ETH: Sepolia -> Robinhood{RESET}\n{BOLD_CYAN}{'='*70}{RESET}")
    if not ensure_accounts_loaded(): return
    while True:
        try:
            bridge_amount = float(input(f"\n  {BOLD_YELLOW}ETH to bridge (e.g. 0.001): {RESET}").strip())
            if bridge_amount > 0: break
        except: pass
    l2_call_value = int(bridge_amount * 10**18); total_value = calculate_bridge_value(l2_call_value)
    repeat = ask_repeat_count("Bridge"); total_s, total_f = 0, 0
    for rnd in range(1, repeat+1):
        print_round_header(rnd, repeat, "BRIDGE")
        for idx, pk in enumerate(loaded_accounts, 1):
            proxy = get_random_proxy(); addr = pk2addr(pk)
            sep_bal = sepolia_get_balance(addr, proxy); rh_bal = get_balance(addr, proxy)
            print(f"\n{BOLD_MAGENTA}{'─'*70}{RESET}\n{BOLD_WHITE}  Account {idx}/{len(loaded_accounts)}{RESET}")
            print(f"  Sepolia: {sep_bal:.10f}  Robinhood: {rh_bal:.10f}")
            if sep_bal < total_value/10**18 + 0.001: log_error("Low Sepolia bal"); total_f += 1; continue
            calldata = build_bridge_calldata(addr, l2_call_value)
            nonce = sepolia_get_nonce(addr, proxy)
            if nonce is None: total_f += 1; continue
            gas_price = sepolia_get_gas_price(proxy)
            est_tx = {"from": addr, "to": BRIDGE_CONTRACT.lower(), "value": hex(total_value), "data": calldata}
            eg, ee = sepolia_estimate_gas(est_tx, proxy)
            if eg is None: total_f += 1; continue
            gl = int(eg * GAS_MULTIPLIER)
            tx = {"nonce": nonce, "gasPrice": gas_price, "gas": gl, "to": BRIDGE_CONTRACT, "value": total_value, "data": calldata}
            try: stx = sign_tx(tx, pk, SEPOLIA_CHAIN_ID)
            except: total_f += 1; continue
            th, se = sepolia_send_raw(stx, proxy)
            if not th: total_f += 1; continue
            log_success(f"Bridge TX: {th}")
            ok, _, _ = wait_sepolia_confirm(th, proxy)
            if ok: total_s += 1
            else: total_f += 1
            if idx < len(loaded_accounts): time.sleep(random.randint(5, 10))
    print(f"\n{BOLD_GREEN}{'='*70}\n  BRIDGE: {BOLD_GREEN}{total_s} OK  {BOLD_RED}{total_f} Fail{RESET}\n{BOLD_GREEN}{'='*70}{RESET}")

# ============================================
# ACTION: WATCHOOR
# ============================================
def action_watchoor():
    print(f"\n{BOLD_CYAN}{'='*70}{RESET}")
    print(f"{BOLD_GREEN}  WATCHOOR - Robinhood Testnet{RESET}")
    print(f"{BOLD_CYAN}{'='*70}{RESET}")
    print(f"  {BOLD_WHITE}Contract : {BOLD_CYAN}{WATCHOOR_TO}{RESET}")
    print(f"  {BOLD_WHITE}Actions  : GM + GN + Deploy Counter{RESET}")
    print(f"{BOLD_CYAN}{'='*70}{RESET}")
    if not ensure_accounts_loaded(): return
    repeat = ask_repeat_count("Watchoor")
    total_s, total_f = 0, 0
    for rnd in range(1, repeat+1):
        print_round_header(rnd, repeat, "WATCHOOR")
        for idx, pk in enumerate(loaded_accounts, 1):
            proxy = get_random_proxy(); addr = pk2addr(pk); bal = get_balance(addr, proxy)
            print_account_header(idx, len(loaded_accounts), addr, bal, proxy)
            value_eth = WATCHOOR_VALUE_WEI / 10**18
            if bal < value_eth * 3 + 0.0005:
                log_error(f"Low balance for Watchoor (need ~{value_eth*3:.6f} ETH)"); total_f += 1; continue
            ok_count = 0
            # Say GM
            gm_data = "0x" + build_watchoor_simple(WATCHOOR_GM_SELECTOR).hex()
            r = send_transaction(pk, addr, WATCHOOR_TO, WATCHOOR_VALUE_WEI, gm_data, "WATCHOOR SAY GM", "https://watchoor.robinhood.com", "https://watchoor.robinhood.com/", proxy)
            if classify_result(r) == "success": ok_count += 1
            else: log_warn("Watchoor GM skipped/failed")
            print_result("WATCHOOR GM", r); time.sleep(2)
            # Say GN
            gn_data = "0x" + build_watchoor_simple(WATCHOOR_GN_SELECTOR).hex()
            r = send_transaction(pk, addr, WATCHOOR_TO, WATCHOOR_VALUE_WEI, gn_data, "WATCHOOR SAY GN", "https://watchoor.robinhood.com", "https://watchoor.robinhood.com/", proxy)
            if classify_result(r) == "success": ok_count += 1
            else: log_warn("Watchoor GN skipped/failed")
            print_result("WATCHOOR GN", r); time.sleep(2)
            # Deploy Counter
            counter_data = "0x" + build_watchoor_simple(WATCHOOR_DEPLOY_COUNTER_SELECTOR).hex()
            r = send_transaction(pk, addr, WATCHOOR_TO, WATCHOOR_VALUE_WEI, counter_data, "WATCHOOR DEPLOY COUNTER", "https://watchoor.robinhood.com", "https://watchoor.robinhood.com/", proxy)
            if classify_result(r) == "success": ok_count += 1
            else: log_warn("Watchoor Counter deploy skipped/failed")
            print_result("WATCHOOR DEPLOY COUNTER", r)
            if ok_count > 0: total_s += 1
            else: total_f += 1
            if idx < len(loaded_accounts): time.sleep(random.randint(5, 10))
        if rnd < repeat: time.sleep(random.randint(10, 20))
    print(f"\n{BOLD_GREEN}{'='*70}\n  WATCHOOR: {BOLD_GREEN}{total_s} OK  {BOLD_RED}{total_f} Fail{RESET}\n{BOLD_GREEN}{'='*70}{RESET}")

# ============================================
# ACTION: ZNS (Znz Connect)
# ============================================
def action_zns():
    print(f"\n{BOLD_CYAN}{'='*70}{RESET}")
    print(f"{BOLD_MAGENTA}  ZNS - ZNZ CONNECT (Robinhood Testnet){RESET}")
    print(f"{BOLD_CYAN}{'='*70}{RESET}")
    print(f"  {BOLD_WHITE}Say GM   : {BOLD_CYAN}{ZNS_SAY_GM_TO}{RESET}")
    print(f"  {BOLD_WHITE}Deploy   : {BOLD_CYAN}{ZNS_DEPLOY_TO}{RESET}")
    print(f"  {BOLD_WHITE}Mint NFT : {BOLD_CYAN}{ZNS_MINT_TO}{RESET}")
    print(f"{BOLD_CYAN}{'='*70}{RESET}")
    if not ensure_accounts_loaded(): return
    repeat = ask_repeat_count("ZNS")
    total_s, total_f, total_sk = 0, 0, 0
    for rnd in range(1, repeat+1):
        print_round_header(rnd, repeat, "ZNS - ZNZ CONNECT")
        for idx, pk in enumerate(loaded_accounts, 1):
            proxy = get_random_proxy(); addr = pk2addr(pk); bal = get_balance(addr, proxy)
            print_account_header(idx, len(loaded_accounts), addr, bal, proxy)
            ok_count = 0
            # Say GM
            gm_data = build_zns_gm()
            r = send_transaction(pk, addr, ZNS_SAY_GM_TO, ZNS_SAY_GM_VALUE, gm_data, "ZNS SAY GM", "https://onchaingm.com", "https://onchaingm.com/", proxy)
            c = classify_result(r)
            if c == "success": ok_count += 1; total_s += 1
            elif c == "skip": total_sk += 1; log_info("ZNS GM already done today")
            else: total_f += 1
            print_result("ZNS SAY GM", r); time.sleep(2)
            # Deploy Smart Contract
            deploy_data = build_zns_deploy()
            r = send_transaction(pk, addr, ZNS_DEPLOY_TO, ZNS_DEPLOY_VALUE, deploy_data, "ZNS DEPLOY CONTRACT", "https://onchaingm.com", "https://onchaingm.com/", proxy)
            c = classify_result(r)
            if c == "success": ok_count += 1; total_s += 1
            elif c == "skip": total_sk += 1; log_info("ZNS Deploy already done today")
            else: total_f += 1
            print_result("ZNS DEPLOY CONTRACT", r); time.sleep(2)
            # Mint NFTs
            mint_data = build_zns_mint()
            r = send_transaction(pk, addr, ZNS_MINT_TO, ZNS_MINT_VALUE, mint_data, "ZNS MINT NFT", "https://onchaingm.com", "https://onchaingm.com/", proxy)
            c = classify_result(r)
            if c == "success": ok_count += 1; total_s += 1
            elif c == "skip": total_sk += 1
            else: total_f += 1
            print_result("ZNS MINT NFT", r)
            if idx < len(loaded_accounts): time.sleep(random.randint(5, 10))
        if rnd < repeat: time.sleep(random.randint(10, 20))
    print(f"\n{BOLD_GREEN}{'='*70}\n  ZNS: {BOLD_GREEN}{total_s} OK  {BOLD_YELLOW}{total_sk} Skip  {BOLD_RED}{total_f} Fail{RESET}\n{BOLD_GREEN}{'='*70}{RESET}")

# ============================================
# OTHER ACTIONS
# ============================================
def run_single(name,contract,value,cdfn,origin="https://onchaingm.com",referer="https://onchaingm.com/",mbe=0.0001):
    if not ensure_accounts_loaded(): return
    repeat=ask_repeat_count(name); ts,tsk,tf=0,0,0
    for rnd in range(1,repeat+1):
        print_round_header(rnd,repeat,name)
        for idx,pk in enumerate(loaded_accounts,1):
            proxy=get_random_proxy(); addr=pk2addr(pk); bal=get_balance(addr,proxy)
            print_account_header(idx,len(loaded_accounts),addr,bal,proxy)
            if bal<(value/10**18)+mbe: log_error("Low balance"); tf+=1; continue
            result=send_transaction(pk,addr,contract,value,cdfn(addr),name,origin,referer,proxy)
            r=classify_result(result)
            if r=="success": ts+=1
            elif r=="skip": tsk+=1
            else: tf+=1
            print_result(name,result)
            if idx<len(loaded_accounts): time.sleep(random.randint(3,8))
        if rnd<repeat: time.sleep(random.randint(5,15))
    print(f"\n{BOLD_GREEN}{'='*70}\n  {name}: {BOLD_GREEN}{ts} OK  {BOLD_YELLOW}{tsk} Skip  {BOLD_RED}{tf} Fail{RESET}\n{BOLD_GREEN}{'='*70}{RESET}")

def action_gm(): run_single("ON CHAIN GM",CONTRACT_GMCARDS,VALUE_GM,lambda a:build_gm())
def action_deploy(): run_single("DEPLOY",CONTRACT_DEPLOY,VALUE_DEPLOY,lambda a:build_deploy())
def action_badge(): run_single("MINT BADGE",CONTRACT_BADGE,VALUE_BADGE,lambda a:build_badge())

def action_domain():
    if not ensure_accounts_loaded(): return
    repeat=ask_repeat_count("Mint Domain"); domains=generate_unique_domains(len(loaded_accounts)*repeat)
    ts,tsk,tf,di=0,0,0,0
    for rnd in range(1,repeat+1):
        print_round_header(rnd,repeat,"MINT DOMAIN")
        for idx,pk in enumerate(loaded_accounts,1):
            proxy=get_random_proxy(); addr=pk2addr(pk); bal=get_balance(addr,proxy)
            dn=domains[di] if di<len(domains) else generate_random_domain(); fd=dn+".hood"; di+=1
            print_account_header(idx,len(loaded_accounts),addr,bal,proxy,{"Domain":fd})
            if bal<(VALUE_MINT_DOMAIN/10**18)+0.0001: log_error("Low"); tf+=1; continue
            result=send_transaction(pk,addr,CONTRACT_INFINITYNAME,VALUE_MINT_DOMAIN,build_domain(dn),f"MINT {fd}","https://infinityname.com","https://infinityname.com/",proxy)
            r=classify_result(result)
            if r=="success": ts+=1; log_to_supabase(dn,addr,result)
            elif r=="skip": tsk+=1
            else: tf+=1
            print_result(f"DOMAIN {fd}",result)
            if idx<len(loaded_accounts): time.sleep(random.randint(3,8))
        if rnd<repeat: time.sleep(random.randint(5,15))
    print(f"\n{BOLD_GREEN}{'='*70}\n  DOMAIN: {BOLD_GREEN}{ts} OK  {BOLD_YELLOW}{tsk} Skip  {BOLD_RED}{tf} Fail{RESET}\n{BOLD_GREEN}{'='*70}{RESET}")

def action_nft():
    print(f"\n  [1] Flamenco  [2] OmniHub  [3] Both")
    nc=input(f"  {BOLD_YELLOW}Select [1-3]: {RESET}").strip()
    if nc not in ["1","2","3"]: return
    if not ensure_accounts_loaded(): return
    repeat=ask_repeat_count("Mint NFT"); fs,fsk,ff,os_,osk,of_=0,0,0,0,0,0
    for rnd in range(1,repeat+1):
        print_round_header(rnd,repeat,"MINT NFT")
        for idx,pk in enumerate(loaded_accounts,1):
            proxy=get_random_proxy(); addr=pk2addr(pk); bal=get_balance(addr,proxy)
            print_account_header(idx,len(loaded_accounts),addr,bal,proxy)
            if nc in ["1","3"]:
                r=send_transaction(pk,addr,CONTRACT_FLAMENCO_MINTER,0,build_flamenco(addr),"FLAMENCO","https://robinhood-flamenco.testnet.nfts2.me","https://robinhood-flamenco.testnet.nfts2.me/",proxy)
                c=classify_result(r)
                if c=="success": fs+=1
                elif c=="skip": fsk+=1
                else: ff+=1
                print_result("FLAMENCO",r); time.sleep(2); bal=get_balance(addr,proxy)
            if nc in ["2","3"]:
                b=omnihub_login(addr,pk,proxy)
                if b: omnihub_verify(b,proxy); time.sleep(1)
                r=send_transaction(pk,addr,CONTRACT_OMNIHUB,VALUE_OMNIHUB,build_omnihub(),"OMNIHUB","https://omnihub.xyz","https://omnihub.xyz/",proxy)
                c=classify_result(r)
                if c=="success": os_+=1
                elif c=="skip": osk+=1
                else: of_+=1
                print_result("OMNIHUB",r)
            if idx<len(loaded_accounts): time.sleep(random.randint(3,8))
        if rnd<repeat: time.sleep(random.randint(5,15))
    print(f"\n{BOLD_GREEN}{'='*70}{RESET}")
    if nc in ["1","3"]: print(f"  FLAMENCO: {BOLD_GREEN}{fs} OK  {BOLD_YELLOW}{fsk} Skip  {BOLD_RED}{ff} Fail{RESET}")
    if nc in ["2","3"]: print(f"  OMNIHUB : {BOLD_GREEN}{os_} OK  {BOLD_YELLOW}{osk} Skip  {BOLD_RED}{of_} Fail{RESET}")
    print(f"{BOLD_GREEN}{'='*70}{RESET}")

def action_faucet():
    if not ensure_accounts_loaded(): return
    tokens=load_faucet_tokens()
    if not tokens: return
    if not captcha_api_key: log_error(f"No captcha key!"); return
    ts,tf,tsk=0,0,0
    hb={"Accept":"*/*","Content-Type":"application/json","Origin":FAUCET_API_BASE,"User-Agent":"Mozilla/5.0"}
    for idx,pk in enumerate(loaded_accounts,1):
        proxy=get_random_proxy(); addr=pk2addr(pk); bal=get_balance(addr,proxy)
        ti=(idx-1)%len(tokens); st=tokens[ti]
        print_account_header(idx,len(loaded_accounts),addr,bal,proxy)
        cookies={"__Secure-authjs.session-token":st}
        headers={**hb,"Referer":f"{FAUCET_API_BASE}/?address={addr}&step=auth"}
        try:
            resp=requests.get(f"{FAUCET_API_BASE}/api/auth/session",headers=headers,cookies=cookies,timeout=15,proxies=proxy)
            if resp.status_code!=200 or not resp.json().get("user",{}).get("name"): tf+=1; continue
        except: tf+=1; continue
        try:
            resp=requests.get(f"{FAUCET_API_BASE}/api/ratelimit",headers=headers,cookies=cookies,timeout=15,proxies=proxy)
            if resp.status_code==200 and not resp.json().get("allowed",False): tsk+=1; continue
        except: pass
        tt=solve_turnstile(proxy)
        if not tt: tf+=1; continue
        try:
            resp=requests.post(f"{FAUCET_API_BASE}/api/distribute",json={"recipientAddress":addr,"turnstileToken":tt},headers=headers,cookies=cookies,timeout=30,proxies=proxy)
            if resp.status_code==200 and resp.json().get("success"): log_success("FAUCET CLAIMED!"); ts+=1
            else: tf+=1
        except: tf+=1
        if idx<len(loaded_accounts): time.sleep(random.randint(5,10))
    print(f"\n{BOLD_GREEN}{'='*70}\n  FAUCET: {BOLD_GREEN}{ts} OK  {BOLD_YELLOW}{tsk} Skip  {BOLD_RED}{tf} Fail{RESET}\n{BOLD_GREEN}{'='*70}{RESET}")

def action_auto():
    if not ensure_accounts_loaded(): return
    repeat=ask_repeat_count("Auto All"); domains=generate_unique_domains(len(loaded_accounts)*repeat)
    R={f"{k}_{s}":0 for k in ["gm","deploy","domain","badge","flamenco","omnihub","watchoor","zns_gm","zns_deploy","zns_mint"] for s in ["success","skip","fail"]}
    di=0
    for rnd in range(1,repeat+1):
        print_round_header(rnd,repeat,"AUTO ALL")
        for idx,pk in enumerate(loaded_accounts,1):
            proxy=get_random_proxy(); addr=pk2addr(pk); bal=get_balance(addr,proxy)
            dn=domains[di] if di<len(domains) else generate_random_domain(); fd=dn+".hood"; di+=1
            print_account_header(idx,len(loaded_accounts),addr,bal,proxy,{"Domain":fd})
            tasks=[("GM",CONTRACT_GMCARDS,VALUE_GM,build_gm(),"https://onchaingm.com","https://onchaingm.com/","gm"),("Deploy",CONTRACT_DEPLOY,VALUE_DEPLOY,build_deploy(),"https://onchaingm.com","https://onchaingm.com/","deploy"),(f"Domain {fd}",CONTRACT_INFINITYNAME,VALUE_MINT_DOMAIN,build_domain(dn),"https://infinityname.com","https://infinityname.com/","domain"),("Badge",CONTRACT_BADGE,VALUE_BADGE,build_badge(),"https://onchaingm.com","https://onchaingm.com/","badge"),("Flamenco",CONTRACT_FLAMENCO_MINTER,0,build_flamenco(addr),"https://robinhood-flamenco.testnet.nfts2.me","https://robinhood-flamenco.testnet.nfts2.me/","flamenco")]
            for tn,(label,contract,value,calldata,origin,referer,key) in enumerate(tasks,1):
                mb=(value/10**18)+0.0001 if value>0 else 0.0005
                if bal<mb: R[f"{key}_fail"]+=1
                else:
                    result=send_transaction(pk,addr,contract,value,calldata,label,origin,referer,proxy)
                    add_result(R,key,result)
                    if key=="domain" and classify_result(result)=="success": log_to_supabase(dn,addr,result)
                    print_result(label,result)
                time.sleep(2); bal=get_balance(addr,proxy)
            if bal<0.0105: R["omnihub_fail"]+=1
            else:
                b=omnihub_login(addr,pk,proxy)
                if b: omnihub_verify(b,proxy); time.sleep(1)
                result=send_transaction(pk,addr,CONTRACT_OMNIHUB,VALUE_OMNIHUB,build_omnihub(),"OmniHub","https://omnihub.xyz","https://omnihub.xyz/",proxy)
                add_result(R,"omnihub",result); print_result("OMNIHUB",result)
                time.sleep(2); bal=get_balance(addr,proxy)
            # Watchoor in Auto All
            wval = WATCHOOR_VALUE_WEI / 10**18
            if bal < wval * 3 + 0.0005: R["watchoor_fail"] += 1
            else:
                wok = 0
                for wdata, wtitle in [
                    ("0x"+build_watchoor_simple(WATCHOOR_GM_SELECTOR).hex(), "Watchoor GM"),
                    ("0x"+build_watchoor_simple(WATCHOOR_GN_SELECTOR).hex(), "Watchoor GN"),
                    ("0x"+build_watchoor_simple(WATCHOOR_DEPLOY_COUNTER_SELECTOR).hex(), "Watchoor Counter"),
                ]:
                    wr = send_transaction(pk, addr, WATCHOOR_TO, WATCHOOR_VALUE_WEI, wdata, wtitle, "https://watchoor.robinhood.com", "https://watchoor.robinhood.com/", proxy)
                    if classify_result(wr) == "success": wok += 1
                    print_result(wtitle, wr); time.sleep(2)
                    bal = get_balance(addr, proxy)
                if wok > 0: R["watchoor_success"] += 1
                else: R["watchoor_fail"] += 1
            # ZNS in Auto All
            for zlabel, zto, zval, zdata, zkey in [
                ("ZNS GM",     ZNS_SAY_GM_TO,  ZNS_SAY_GM_VALUE,  build_zns_gm(),     "zns_gm"),
                ("ZNS Deploy", ZNS_DEPLOY_TO,  ZNS_DEPLOY_VALUE,  build_zns_deploy(), "zns_deploy"),
                ("ZNS Mint",   ZNS_MINT_TO,    ZNS_MINT_VALUE,    build_zns_mint(),   "zns_mint"),
            ]:
                bal = get_balance(addr, proxy)
                zr = send_transaction(pk, addr, zto, zval, zdata, zlabel, "https://onchaingm.com", "https://onchaingm.com/", proxy)
                add_result(R, zkey, zr); print_result(zlabel, zr); time.sleep(2)
            if idx<len(loaded_accounts): time.sleep(random.randint(5,12))
        if rnd<repeat: time.sleep(random.randint(10,20))
    print(f"\n{BOLD_GREEN}{'='*70}\n  AUTO ALL SUMMARY{RESET}")
    for k,n in [("gm","GM"),("deploy","DEPLOY"),("domain","DOMAIN"),("badge","BADGE"),("flamenco","FLAMENCO"),("omnihub","OMNIHUB"),("watchoor","WATCHOOR"),("zns_gm","ZNS GM"),("zns_deploy","ZNS DEPLOY"),("zns_mint","ZNS MINT")]:
        print(f"  {BOLD_WHITE}{n:<12}: {BOLD_GREEN}{R[f'{k}_success']} OK  {BOLD_YELLOW}{R[f'{k}_skip']} Skip  {BOLD_RED}{R[f'{k}_fail']} Fail{RESET}")
    ts=sum(v for k,v in R.items() if "success" in k); tsk=sum(v for k,v in R.items() if "skip" in k); tf=sum(v for k,v in R.items() if "fail" in k)
    print(f"  {BOLD_WHITE}{'TOTAL':<12}: {BOLD_GREEN}{ts} OK  {BOLD_YELLOW}{tsk} Skip  {BOLD_RED}{tf} Fail{RESET}\n{BOLD_GREEN}{'='*70}{RESET}")

# ============================================
# MAIN
# ============================================
def main():
    set_title(); load_proxies(); load_accounts(); load_captcha_key()
    while True:
        banner()
        cb=get_block_number()
        if cb: print(f"  {BOLD_WHITE}Latest Block : {BOLD_GREEN}{cb}{RESET}")
        ac=len(loaded_accounts) if loaded_accounts else "0 (Check pv.txt)"
        pc=len(loaded_proxies) if loaded_proxies else "None (Direct)"
        tc=0
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE) as f: tc=sum(1 for l in f if l.strip() and not l.strip().startswith("#"))
            except: pass
        cs=f"{BOLD_GREEN}Loaded{RESET}" if captcha_api_key else f"{BOLD_RED}Not found{RESET}"
        print(f"  {BOLD_WHITE}Accounts     : {BOLD_CYAN}{ac}{RESET}")
        print(f"  {BOLD_WHITE}Proxies      : {BOLD_YELLOW}{pc}{RESET}")
        print(f"  {BOLD_WHITE}Faucet Tokens: {BOLD_GREEN}{tc}{RESET}")
        print(f"  {BOLD_WHITE}Captcha Key  : {cs}")
        print(f"{BOLD_CYAN}{'='*70}{RESET}")
        display_menu()
        choice=input(f"\n  {BOLD_YELLOW}Select [1-14]: {RESET}").strip()
        actions={
            "1":action_gm,"2":action_deploy,"3":action_domain,"4":action_badge,
            "5":action_nft,"6":action_faucet,"7":action_bridge,
            "8":action_swap,"9":action_add_liquidity,"10":action_lending,
            "11":action_watchoor,"12":action_zns,"13":action_auto,
        }
        if choice in actions:
            actions[choice](); print(); input(f"  {BOLD_YELLOW}Press Enter...{RESET}")
        elif choice=="14":
            print(f"\n{BOLD_GREEN}{'='*70}{RESET}\n{BOLD_RED}  Goodbye! {BOLD_MAGENTA}By KAZUHA VIP{RESET}\n{BOLD_GREEN}{'='*70}{RESET}\n"); sys.exit(0)
        else: log_error("Invalid! Select 1-14"); time.sleep(1)

if __name__=="__main__":
    try: main()
    except KeyboardInterrupt: print(f"\n\n{BOLD_YELLOW}Interrupted{RESET}\n"); sys.exit(0)
