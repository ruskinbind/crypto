import os
import sys
import json
import time
import random
import string
import re
import requests
import urllib3
from eth_account import Account
from eth_account.messages import encode_defunct

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
Account.enable_unaudited_hdwallet_features()

class Colors:
    BOLD = '\033[1m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

# ==================== TEMP MAIL SERVICES ====================

class TempMailService:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Accept": "application/json"
        })
    
    def random_string(self, length=10):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    # ========== Internxt Mail (Fast) ==========
    def create_internxt(self):
        try:
            resp = self.session.get("https://internxt.com/api/temp-mail", timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "email": data.get('address'),
                    "token": data.get('token'),
                    "service": "internxt"
                }
        except:
            pass
        return None
    
    def check_internxt(self, token):
        try:
            resp = self.session.get(
                f"https://internxt.com/api/temp-mail/messages/{token}",
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        return []
    
    # ========== Tempmail.lol (Fast) ==========
    def create_tempmail_lol(self):
        try:
            resp = self.session.get("https://api.tempmail.lol/generate", timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "email": data.get('address'),
                    "token": data.get('token'),
                    "service": "tempmail_lol"
                }
        except:
            pass
        return None
    
    def check_tempmail_lol(self, token):
        try:
            resp = self.session.get(
                f"https://api.tempmail.lol/auth/{token}",
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get('email', [])
        except:
            pass
        return []
    
    # ========== Mail.gw (Fast) ==========
    def create_mailgw(self):
        try:
            # Get domains
            resp = self.session.get("https://api.mail.gw/domains", timeout=30)
            if resp.status_code != 200:
                return None
            
            domains = resp.json().get('hydra:member', [])
            if not domains:
                return None
            
            domain = domains[0]['domain']
            username = self.random_string(12)
            email = f"{username}@{domain}"
            password = self.random_string(16)
            
            # Create account
            resp = self.session.post(
                "https://api.mail.gw/accounts",
                json={"address": email, "password": password},
                timeout=30
            )
            if resp.status_code not in [200, 201]:
                return None
            
            # Get token
            resp = self.session.post(
                "https://api.mail.gw/token",
                json={"address": email, "password": password},
                timeout=30
            )
            if resp.status_code != 200:
                return None
            
            return {
                "email": email,
                "token": resp.json().get('token'),
                "service": "mailgw"
            }
        except:
            return None
    
    def check_mailgw(self, token):
        try:
            resp = self.session.get(
                "https://api.mail.gw/messages",
                headers={"Authorization": f"Bearer {token}"},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json().get('hydra:member', [])
        except:
            pass
        return []
    
    def read_mailgw(self, token, msg_id):
        try:
            resp = self.session.get(
                f"https://api.mail.gw/messages/{msg_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        return None
    
    # ========== Mail.tm ==========
    def create_mailtm(self):
        try:
            resp = self.session.get("https://api.mail.tm/domains", timeout=30)
            if resp.status_code != 200:
                return None
            
            domains = resp.json().get('hydra:member', [])
            if not domains:
                return None
            
            domain = domains[0]['domain']
            username = self.random_string(12)
            email = f"{username}@{domain}"
            password = self.random_string(16)
            
            resp = self.session.post(
                "https://api.mail.tm/accounts",
                json={"address": email, "password": password},
                timeout=30
            )
            if resp.status_code not in [200, 201]:
                return None
            
            resp = self.session.post(
                "https://api.mail.tm/token",
                json={"address": email, "password": password},
                timeout=30
            )
            if resp.status_code != 200:
                return None
            
            return {
                "email": email,
                "token": resp.json().get('token'),
                "service": "mailtm"
            }
        except:
            return None
    
    def check_mailtm(self, token):
        try:
            resp = self.session.get(
                "https://api.mail.tm/messages",
                headers={"Authorization": f"Bearer {token}"},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json().get('hydra:member', [])
        except:
            pass
        return []
    
    def read_mailtm(self, token, msg_id):
        try:
            resp = self.session.get(
                f"https://api.mail.tm/messages/{msg_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        return None
    
    # ========== Guerrilla Mail ==========
    def create_guerrilla(self):
        try:
            resp = self.session.get(
                "https://api.guerrillamail.com/ajax.php?f=get_email_address&lang=en",
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "email": data.get('email_addr'),
                    "sid_token": data.get('sid_token'),
                    "service": "guerrilla"
                }
        except:
            pass
        return None
    
    def check_guerrilla(self, sid_token):
        try:
            resp = self.session.get(
                f"https://api.guerrillamail.com/ajax.php?f=check_email&seq=0&sid_token={sid_token}",
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json().get('list', [])
        except:
            pass
        return []
    
    def read_guerrilla(self, sid_token, mail_id):
        try:
            resp = self.session.get(
                f"https://api.guerrillamail.com/ajax.php?f=fetch_email&email_id={mail_id}&sid_token={sid_token}",
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        return None
    
    # ========== Dropmail.me ==========
    def create_dropmail(self):
        try:
            query = """
            mutation {
                introduceSession {
                    id
                    expiresAt
                    addresses {
                        address
                        }
                }
            }
            """
            resp = self.session.post(
                "https://dropmail.me/api/graphql/web-test-wgq3v",
                json={"query": query},
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                session = data.get('data', {}).get('introduceSession', {})
                addresses = session.get('addresses', [])
                if addresses:
                    return {
                        "email": addresses[0].get('address'),
                        "session_id": session.get('id'),
                        "service": "dropmail"
                    }
        except:
            pass
        return None
    
    def check_dropmail(self, session_id):
        try:
            query = """
            query ($id: ID!) {
                session(id: $id) {
                    mails {
                        rawSize
                        fromAddr
                        toAddr
                        downloadUrl
                        text
                        headerSubject
                    }
                }
            }
            """
            resp = self.session.post(
                "https://dropmail.me/api/graphql/web-test-wgq3v",
                json={"query": query, "variables": {"id": session_id}},
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get('data', {}).get('session', {}).get('mails', [])
        except:
            pass
        return []
    
    # ========== Main Methods ==========
    def create_temp_email(self):
        services = [
            ("mail.gw", self.create_mailgw),
            ("mail.tm", self.create_mailtm),
            ("dropmail", self.create_dropmail),
            ("guerrilla", self.create_guerrilla),
            ("tempmail.lol", self.create_tempmail_lol),
        ]
        
        for name, func in services:
            try:
                print_status("◆", f"Trying {name}...", Colors.YELLOW)
                result = func()
                if result and result.get('email'):
                    return result
            except:
                continue
        
        return None
    
    def extract_code(self, text):
        if not text:
            return None
        text = str(text)
        codes = re.findall(r'\b(\d{6})\b', text)
        return codes[0] if codes else None
    
    def wait_for_code(self, email_data, timeout=120):
        start = time.time()
        
        while time.time() - start < timeout:
            elapsed = int(time.time() - start)
            print(f"\r    {Colors.YELLOW}{Colors.BOLD}◆ Checking inbox... [{elapsed}s / {timeout}s]{Colors.RESET}    ", end="", flush=True)
            
            try:
                code = self._check_inbox(email_data)
                if code:
                    print()
                    return code
            except:
                pass
            
            time.sleep(3)
        
        print()
        return None
    
    def _check_inbox(self, email_data):
        service = email_data.get('service')
        
        if service == "mailgw":
            messages = self.check_mailgw(email_data['token'])
            for msg in messages:
                full = self.read_mailgw(email_data['token'], msg['id'])
                if full:
                    body = str(full.get('text', '')) + str(full.get('html', ''))
                    code = self.extract_code(body)
                    if code:
                        return code
        
        elif service == "mailtm":
            messages = self.check_mailtm(email_data['token'])
            for msg in messages:
                full = self.read_mailtm(email_data['token'], msg['id'])
                if full:
                    body = str(full.get('text', '')) + str(full.get('html', ''))
                    code = self.extract_code(body)
                    if code:
                        return code
        
        elif service == "guerrilla":
            messages = self.check_guerrilla(email_data['sid_token'])
            for msg in messages:
                full = self.read_guerrilla(email_data['sid_token'], msg.get('mail_id'))
                if full:
                    code = self.extract_code(str(full.get('mail_body', '')))
                    if code:
                        return code
        
        elif service == "dropmail":
            messages = self.check_dropmail(email_data['session_id'])
            for msg in messages:
                code = self.extract_code(str(msg.get('text', '')))
                if code:
                    return code
        
        elif service == "tempmail_lol":
            messages = self.check_tempmail_lol(email_data['token'])
            for msg in messages:
                body = str(msg.get('body', '')) + str(msg.get('html', ''))
                code = self.extract_code(body)
                if code:
                    return code
        
        elif service == "internxt":
            messages = self.check_internxt(email_data['token'])
            for msg in messages:
                body = str(msg.get('body', '')) + str(msg.get('text', ''))
                code = self.extract_code(body)
                if code:
                    return code
        
        return None


# ==================== FAIRSHARES API ====================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    clear_screen()
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}         FAIRSHARES AUTO REFERRAL{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.YELLOW}           Created by Kazuha VIP ONLY{Colors.RESET}\n")

def print_status(icon, message, color):
    print(f"    {color}{Colors.BOLD}{icon} {message}{Colors.RESET}")

def generate_wallet():
    account = Account.create()
    pk = account.key.hex()
    if not pk.startswith('0x'):
        pk = '0x' + pk
    return {"address": account.address, "private_key": pk, "account": account}

def sign_message(account, message):
    encoded = encode_defunct(text=message)
    signed = Account.sign_message(encoded, private_key=account.key)
    sig = signed.signature.hex()
    return sig if sig.startswith('0x') else '0x' + sig

def get_headers(token=None):
    h = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Content-Type": "application/json; charset=utf-8",
        "Origin": "https://app.fairshares.io",
        "Referer": "https://app.fairshares.io/",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }
    if token:
        h["Authorization"] = f"jwt {token}"
    return h

def api_request(method, url, data=None, token=None, retries=3):
    for _ in range(retries):
        try:
            if method == "POST":
                r = requests.post(url, json=data, headers=get_headers(token), timeout=60, verify=False)
            else:
                r = requests.get(url, headers=get_headers(token), timeout=60, verify=False)
            if r.status_code == 200:
                return r.json()
        except:
            time.sleep(2)
    return None

def connect_wallet(address, signature):
    msg = "Welcome to FairShares\n\nSign this message to join the FairShares waitlist.\nThis signature does not trigger any blockchain transaction."
    return api_request("POST", "https://api.fairshares.io/user_public/evm_connect", 
                       {"walletAddress": address, "message": msg, "signature": signature})

def get_user_info(token):
    return api_request("GET", "https://api.fairshares.io/user/user_info", token=token)

def check_invite(token, code):
    return api_request("GET", f"https://api.fairshares.io/user_public/check_invite?inviteCode={code}", token=token)

def bind_invite(token, code):
    return api_request("GET", f"https://api.fairshares.io/user/bind_invite?inviteCode={code}", token=token)

def check_email(token, email):
    return api_request("GET", f"https://api.fairshares.io/email/check_email?email={email}", token=token)

def send_code(token, email):
    return api_request("POST", "https://api.fairshares.io/email/send_code", {"email": email}, token=token)

def bind_email(token, email, code):
    return api_request("POST", "https://api.fairshares.io/email/bind_email", {"email": email, "code": str(code)}, token=token)

def save_json(data, filename="new.json"):
    existing = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                existing = json.loads(f.read().strip() or "[]")
                if not isinstance(existing, list):
                    existing = [existing]
        except:
            existing = []
    existing.append(data)
    with open(filename, 'w') as f:
        json.dump(existing, f, indent=4)


def process_wallet(invite_code, num, total, mail_service):
    print(f"\n{Colors.BOLD}{Colors.BLUE}┌{'─'*48}┐{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}│{Colors.CYAN}  WALLET {num}/{total}{Colors.BLUE}{' '*35}│{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}└{'─'*48}┘{Colors.RESET}")
    
    # 1. Generate Wallet
    print_status("◆", "Generating wallet...", Colors.CYAN)
    wallet = generate_wallet()
    address = wallet['address']
    private_key = wallet['private_key']
    account = wallet['account']
    print_status("✓", f"Address: {address[:18]}...{address[-8:]}", Colors.GREEN)
    
    # 2. Sign Message
    msg = "Welcome to FairShares\n\nSign this message to join the FairShares waitlist.\nThis signature does not trigger any blockchain transaction."
    signature = sign_message(account, msg)
    print_status("✓", "Message signed", Colors.GREEN)
    
    # 3. Connect Wallet
    print_status("◆", "Connecting wallet...", Colors.CYAN)
    time.sleep(1)
    resp = connect_wallet(address, signature)
    if not resp or resp.get('code') != 200:
        print_status("✗", "Failed to connect wallet", Colors.RED)
        return None
    token = resp['data']['token']
    print_status("✓", "Wallet connected!", Colors.GREEN)
    
    # 4. Get User Info
    print_status("◆", "Getting user info...", Colors.CYAN)
    time.sleep(1)
    resp = get_user_info(token)
    if not resp or resp.get('code') != 200:
        print_status("✗", "Failed to get user info", Colors.RED)
        return None
    user_id = resp['data']['userId']
    user_code = resp['data']['inviteCode']
    print_status("✓", f"User ID: {user_id}", Colors.MAGENTA)
    print_status("✓", f"Your Code: {user_code}", Colors.MAGENTA)
    
    # 5. Create Temp Email
    print_status("◆", "Creating temp email...", Colors.CYAN)
    email_data = mail_service.create_temp_email()
    if not email_data:
        print_status("✗", "Failed to create temp email", Colors.RED)
        return None
    temp_email = email_data['email']
    print_status("✓", f"Email: {temp_email}", Colors.GREEN)
    print_status("✓", f"Service: {email_data['service']}", Colors.GREEN)
    
    # 6. Check Email
    print_status("◆", "Checking email availability...", Colors.CYAN)
    time.sleep(1)
    resp = check_email(token, temp_email)
    if not resp or resp.get('code') != 200:
        print_status("✗", "Email not available", Colors.RED)
        return None
    print_status("✓", "Email available!", Colors.GREEN)
    
    # 7. Send Verification Code
    print_status("◆", "Sending verification code...", Colors.CYAN)
    time.sleep(1)
    resp = send_code(token, temp_email)
    if not resp or resp.get('code') != 200:
        print_status("✗", "Failed to send code", Colors.RED)
        return None
    print_status("✓", "Code sent!", Colors.GREEN)
    
    # 8. Wait for Code
    verification_code = mail_service.wait_for_code(email_data, timeout=120)
    if not verification_code:
        print_status("✗", "Code not received", Colors.RED)
        return None
    print_status("✓", f"Code received: {verification_code}", Colors.GREEN)
    
    # 9. Bind Email
    print_status("◆", "Verifying email...", Colors.CYAN)
    time.sleep(1)
    resp = bind_email(token, temp_email, verification_code)
    if not resp or resp.get('code') != 200:
        print_status("✗", "Failed to verify email", Colors.RED)
        return None
    print_status("✓", "Email verified!", Colors.GREEN)
    
    # 10. Check Invite Code
    print_status("◆", f"Checking invite code: {invite_code}", Colors.CYAN)
    time.sleep(1)
    resp = check_invite(token, invite_code)
    if not resp or not resp.get('data'):
        print_status("✗", "Invalid invite code", Colors.RED)
        return None
    print_status("✓", "Invite code valid!", Colors.GREEN)
    
    # 11. Bind Invite Code
    print_status("◆", "Binding invite code...", Colors.CYAN)
    time.sleep(1)
    resp = bind_invite(token, invite_code)
    if not resp or resp.get('code') != 200:
        print_status("✗", "Failed to bind invite", Colors.RED)
        return None
    print_status("✓", "Invite code bound!", Colors.GREEN)
    
    # 12. Save
    save_data = {
        "wallet_number": num,
        "address": address,
        "private_key": private_key,
        "user_id": user_id,
        "user_invite_code": user_code,
        "email": temp_email,
        "email_verified": True,
        "email_service": email_data['service'],
        "bound_to": invite_code,
        "token": token,
        "status": "SUCCESS",
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    save_json(save_data, "new.json")
    print_status("✓", "Saved to new.json", Colors.GREEN)
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}    ═══════ WALLET {num} COMPLETED ═══════{Colors.RESET}")
    return save_data


def main():
    display_banner()
    
    mail_service = TempMailService()
    
    # Test API
    print(f"{Colors.BOLD}{Colors.CYAN}◆ Testing API connection...{Colors.RESET}")
    try:
        r = requests.get("https://api.fairshares.io/user_public/check_invite?inviteCode=x7ufaitf",
                        headers=get_headers(), timeout=30, verify=False)
        if r.status_code == 200:
            print(f"{Colors.BOLD}{Colors.GREEN}✓ API connection successful!{Colors.RESET}\n")
        else:
            print(f"{Colors.BOLD}{Colors.RED}✗ API error{Colors.RESET}\n")
    except Exception as e:
        print(f"{Colors.BOLD}{Colors.RED}✗ Connection error{Colors.RESET}\n")
    
    # Config
    print(f"{Colors.BOLD}{Colors.BLUE}┌{'─'*48}┐{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}│{Colors.WHITE}  CONFIGURATION{Colors.BLUE}{' '*32}│{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}└{'─'*48}┘{Colors.RESET}")
    
    while True:
        try:
            num_wallets = int(input(f"{Colors.BOLD}{Colors.WHITE}  ◆ Number of wallets: {Colors.RESET}"))
            if num_wallets > 0:
                break
        except:
            pass
        print(f"{Colors.BOLD}{Colors.RED}  ✗ Enter valid number{Colors.RESET}")
    
    invite_code = input(f"{Colors.BOLD}{Colors.WHITE}  ◆ Referral code [{Colors.YELLOW}x7ufaitf{Colors.WHITE}]: {Colors.RESET}").strip() or "x7ufaitf"
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}║{Colors.GREEN}      STARTING REFERRAL + EMAIL PROCESS          {Colors.CYAN}║{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}║{Colors.WHITE}  Wallets: {num_wallets}  |  Referral: {invite_code}{' '*(24-len(invite_code))}{Colors.CYAN}║{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}╚══════════════════════════════════════════════════╝{Colors.RESET}")
    
    success = 0
    fail = 0
    
    for i in range(1, num_wallets + 1):
        try:
            result = process_wallet(invite_code, i, num_wallets, mail_service)
            if result:
                success += 1
            else:
                fail += 1
        except Exception as e:
            print(f"{Colors.BOLD}{Colors.RED}    ✗ Error: {e}{Colors.RESET}")
            fail += 1
        
        if i < num_wallets:
            wait = random.randint(3, 7)
            print(f"\n{Colors.BOLD}{Colors.YELLOW}    ◆ Waiting {wait}s...{Colors.RESET}")
            time.sleep(wait)
    
    # Summary
    print(f"\n{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}║{Colors.GREEN}              PROCESS COMPLETED                  {Colors.CYAN}║{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}╠══════════════════════════════════════════════════╣{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}║{Colors.GREEN}  ✓ Successful: {success}{' '*(32-len(str(success)))}{Colors.CYAN}║{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}║{Colors.RED}  ✗ Failed: {fail}{' '*(36-len(str(fail)))}{Colors.CYAN}║{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}║{Colors.YELLOW}  ◆ Saved to: new.json{' '*25}{Colors.CYAN}║{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}╚══════════════════════════════════════════════════╝{Colors.RESET}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.BOLD}{Colors.RED}✗ Interrupted{Colors.RESET}")
        sys.exit(0)