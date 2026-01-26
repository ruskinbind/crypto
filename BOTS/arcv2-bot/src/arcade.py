import time
import random
import requests
import secrets
from datetime import datetime, timezone
from eth_account.messages import encode_defunct
from web3 import Web3
from colorama import Fore, Style

from .config import ARCADE_BASE_URL, DYNAMIC_AUTH_URL, DYNAMIC_ENV_ID
from .utils import (
    human_delay, short_delay,
    print_header, print_info, print_success, print_error, print_warning
)


class ArcadeDaily:
    def __init__(self, account):
        self.account = account
        self.address_checksum = Web3.to_checksum_address(account.address)
        self.wallet = account.address.lower()
        self.session = requests.Session()
        self.jwt = None
        self.nonce = None
        self.issued_at = None
        self.session_public_key = '02' + secrets.token_hex(32)
        self.device_fingerprint = secrets.token_hex(16)
        
        # Setup session
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
        })
    
    def _gen_request_id(self):
        chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        p1 = ''.join(random.choices(chars, k=10))
        p2 = ''.join(random.choices(chars, k=20))
        return f"{p1}-{p2}"
    
    def _dynamic_headers(self, with_session=False):
        h = {
            'Content-Type': 'application/json',
            'Origin': 'https://www.arcadeonarc.fun',
            'Referer': 'https://www.arcadeonarc.fun/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'x-dyn-api-version': 'API/0.0.843',
            'x-dyn-device-fingerprint': self.device_fingerprint,
            'x-dyn-is-global-wallet-popup': 'false',
            'x-dyn-request-id': self._gen_request_id(),
            'x-dyn-version': 'WalletKit/4.52.2',
        }
        if with_session:
            h['x-dyn-session-public-key'] = self.session_public_key
        return h
    
    def step1_connect(self):
        """Connect to Dynamic Auth"""
        print_info("[1] Connecting to Dynamic Auth...")
        
        url = f"{DYNAMIC_AUTH_URL}/{DYNAMIC_ENV_ID}/connect"
        payload = {
            "address": self.address_checksum,
            "chain": "EVM",
            "provider": "browserExtension",
            "walletName": "metamask",
            "authMode": "connect-and-sign"
        }
        
        try:
            resp = self.session.post(url, json=payload, headers=self._dynamic_headers(), timeout=30)
            
            if resp.status_code in [200, 202]:
                # Try to parse JSON, but it might be empty for 202
                try:
                    data = resp.json()
                    # Store nonce and issuedAt if present
                    if data.get('nonce'):
                        self.nonce = data.get('nonce')
                    if data.get('issuedAt'):
                        self.issued_at = data.get('issuedAt')
                except:
                    pass
                print_success("    Connected!")
                return True
            
            print_error(f"    Failed: {resp.status_code}")
            return False
        except Exception as e:
            print_error(f"    Error: {str(e)[:50]}")
            return False
    
    def step2_get_nonce(self):
        """Get nonce from Dynamic Auth"""
        print_info("[2] Getting nonce...")
        
        url = f"{DYNAMIC_AUTH_URL}/{DYNAMIC_ENV_ID}/nonce"
        
        try:
            resp = self.session.get(url, headers=self._dynamic_headers(with_session=True), timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                self.nonce = data.get('nonce')
                # Generate issued_at now
                now = datetime.now(timezone.utc)
                ms = now.microsecond // 1000
                self.issued_at = now.strftime('%Y-%m-%dT%H:%M:%S.') + f'{ms:03d}Z'
                print_success(f"    Nonce: {self.nonce[:20]}...")
                return True
            
            print_error(f"    Failed: {resp.status_code}")
            return False
        except Exception as e:
            print_error(f"    Error: {str(e)[:50]}")
            return False
    
    def step3_sign_siwe(self):
        """Create and sign SIWE message"""
        print_info("[3] Signing SIWE message...")
        
        if not self.nonce:
            print_error("    No nonce!")
            return None, None
        
        # Build exact SIWE message format
        statement = "Welcome to ArcadeonArc. Signing is the only way we can truly know that you are the owner of the wallet you are connecting. Signing is a safe, gas-less transaction that does not in any way give ArcadeonArc permission to perform any transactions with your wallet."
        
        message = f"""www.arcadeonarc.fun wants you to sign in with your Ethereum account:
{self.address_checksum}

{statement}

URI: https://www.arcadeonarc.fun/
Version: 1
Chain ID: 5042002
Nonce: {self.nonce}
Issued At: {self.issued_at}
Request ID: {DYNAMIC_ENV_ID}"""
        
        try:
            msg_encoded = encode_defunct(text=message)
            signed = self.account.sign_message(msg_encoded)
            sig = signed.signature.hex()
            if not sig.startswith('0x'):
                sig = '0x' + sig
            print_success("    SIWE signed!")
            return message, sig
        except Exception as e:
            print_error(f"    Error: {str(e)[:50]}")
            return None, None
    
    def step4_verify_dynamic(self, message, signature):
        """Verify SIWE with Dynamic Auth"""
        print_info("[4] Verifying with Dynamic Auth...")
        
        url = f"{DYNAMIC_AUTH_URL}/{DYNAMIC_ENV_ID}/verify"
        
        # New session key for verify
        verify_session_key = '02' + secrets.token_hex(32)
        
        payload = {
            "signedMessage": signature,
            "messageToSign": message,
            "publicWalletAddress": self.address_checksum,
            "chain": "EVM",
            "walletName": "metamask",
            "walletProvider": "browserExtension",
            "network": "5042002",
            "additionalWalletAddresses": [],
            "sessionPublicKey": verify_session_key
        }
        
        headers = self._dynamic_headers(with_session=True)
        
        try:
            resp = self.session.post(url, json=payload, headers=headers, timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                self.jwt = data.get('jwt')
                if self.jwt:
                    print_success("    Dynamic verified!")
                    return True
            
            print_warning(f"    Dynamic auth: {resp.status_code} (continuing...)")
            return False
        except Exception as e:
            print_warning(f"    Dynamic auth error (continuing...)")
            return False
    
    def step5_get_challenge(self):
        """Get challenge from Arcade"""
        print_info("[5] Getting Arcade challenge...")
        
        url = f"{ARCADE_BASE_URL}/api/auth/challenge"
        
        headers = {
            'Content-Type': 'application/json',
            'Origin': 'https://www.arcadeonarc.fun',
            'Referer': 'https://www.arcadeonarc.fun/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
        }
        
        payload = {"wallet": self.wallet}
        
        try:
            resp = self.session.post(url, json=payload, headers=headers, timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                challenge = data.get('challenge')
                message = data.get('message')
                if message:
                    print_success("    Challenge received!")
                    return message
            
            print_error(f"    Failed: {resp.status_code}")
            try:
                print_error(f"    {resp.text[:100]}")
            except:
                pass
            return None
        except Exception as e:
            print_error(f"    Error: {str(e)[:50]}")
            return None
    
    def step6_verify_arcade(self, challenge_message):
        """Sign challenge and verify with Arcade"""
        print_info("[6] Verifying with Arcade...")
        
        if not challenge_message:
            print_error("    No challenge message!")
            return False
        
        # Sign the arcade challenge
        try:
            msg_encoded = encode_defunct(text=challenge_message)
            signed = self.account.sign_message(msg_encoded)
            sig = signed.signature.hex()
            if not sig.startswith('0x'):
                sig = '0x' + sig
        except Exception as e:
            print_error(f"    Sign error: {str(e)[:50]}")
            return False
        
        url = f"{ARCADE_BASE_URL}/api/auth/verify"
        
        headers = {
            'Content-Type': 'application/json',
            'Origin': 'https://www.arcadeonarc.fun',
            'Referer': 'https://www.arcadeonarc.fun/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
        }
        
        payload = {
            "wallet": self.wallet,
            "signature": sig
        }
        
        try:
            resp = self.session.post(url, json=payload, headers=headers, timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get('success'):
                    print_success("    Arcade verified!")
                    return True
            
            print_error(f"    Failed: {resp.status_code}")
            try:
                err = resp.json()
                print_error(f"    {err.get('error', err.get('message', ''))[:80]}")
            except:
                pass
            return False
        except Exception as e:
            print_error(f"    Error: {str(e)[:50]}")
            return False
    
    def step7_setup_user(self, username=None):
        """Check and create user if needed"""
        print_info("[7] Setting up user...")
        
        # Check if user exists
        try:
            resp = self.session.get(
                f"{ARCADE_BASE_URL}/api/users?wallet={self.wallet}",
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get('user'):
                    uname = data['user'].get('username_display', 'exists')
                    print_success(f"    User exists: {uname}")
                    return True
        except:
            pass
        
        # Create new user
        if not username:
            username = f"User{self.wallet[2:8].upper()}{random.randint(10, 99)}"
        
        print_info(f"    Creating: {username}")
        
        try:
            # Check username availability
            check_resp = self.session.get(
                f"{ARCADE_BASE_URL}/api/users/check?username={username}",
                timeout=30
            )
            if check_resp.status_code == 200:
                if not check_resp.json().get('available'):
                    username = f"{username}{random.randint(100, 999)}"
                    print_info(f"    Trying: {username}")
            
            # Create user
            create_resp = self.session.post(
                f"{ARCADE_BASE_URL}/api/users",
                json={"wallet": self.wallet, "username": username},
                timeout=30
            )
            if create_resp.status_code == 200:
                if create_resp.json().get('success'):
                    print_success(f"    Created: {username}")
                    return True
        except Exception as e:
            print_warning(f"    User setup warning: {str(e)[:30]}")
        
        return True  # Continue anyway
    
    def step8_claim_daily(self):
        """Claim daily bonus"""
        print_info("[8] Claiming daily bonus...")
        
        url = f"{ARCADE_BASE_URL}/api/daily-bonus"
        
        headers = {
            'Content-Type': 'application/json',
            'Origin': 'https://www.arcadeonarc.fun',
            'Referer': 'https://www.arcadeonarc.fun/quests',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
        }
        
        # Add JWT if we have it
        if self.jwt:
            headers['Authorization'] = f'Bearer {self.jwt}'
        
        payload = {"wallet": self.wallet}
        
        try:
            resp = self.session.post(url, json=payload, headers=headers, timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                return True, data
            
            try:
                return False, resp.json()
            except:
                return False, {"error": f"HTTP {resp.status_code}"}
        except Exception as e:
            print_error(f"    Error: {str(e)[:50]}")
            return False, None
    
    def run(self, username=None):
        """Execute full login and claim flow"""
        print_header("ARCADE DAILY LOGIN")
        
        # Step 1: Connect to Dynamic
        short_delay()
        if not self.step1_connect():
            return False
        
        # Step 2: Get Nonce
        short_delay()
        if not self.step2_get_nonce():
            return False
        
        # Step 3: Sign SIWE message
        short_delay()
        siwe_message, siwe_signature = self.step3_sign_siwe()
        if not siwe_signature:
            return False
        
        # Step 4: Verify with Dynamic (optional, continue if fails)
        short_delay()
        self.step4_verify_dynamic(siwe_message, siwe_signature)
        
        # Step 5: Get Arcade Challenge
        short_delay()
        challenge_message = self.step5_get_challenge()
        if not challenge_message:
            return False
        
        # Step 6: Verify with Arcade
        short_delay()
        if not self.step6_verify_arcade(challenge_message):
            return False
        
        # Step 7: Setup User
        short_delay()
        self.step7_setup_user(username)
        
        # Step 8: Claim Daily Bonus
        short_delay()
        success, data = self.step8_claim_daily()
        
        # Print Result
        print_header("ARCADE DAILY RESULT")
        
        if success and data:
            if data.get('claimed'):
                print_success("Status: SUCCESS")
                print_success(f"Wallet: {self.wallet[:10]}...{self.wallet[-8:]}")
                print_success(f"Points: +{data.get('points', 0)}")
                print_success(f"Total Daily Points: {data.get('totalDailyPoints', 0)}")
                print_success(f"Message: {data.get('message', 'Daily bonus claimed!')}")
                return True
            else:
                msg = data.get('message', 'Already claimed today')
                print_warning(f"Status: {msg}")
                return False
        
        print_error("Status: FAILED")
        if data:
            err = data.get('message') or data.get('error') or 'Unknown error'
            print_error(f"Error: {err}")
        return False


def arcade_daily_claim(account, username=None):
    """Convenience function for arcade daily claim"""
    arcade = ArcadeDaily(account)
    return arcade.run(username)