#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════╗
║       🚀 ZNS.BIO DOMAIN MINTER - Pharos Testnet  🚀               ║
║                Created by KAZUHA | VIP ONLY                    ║
╚═══════════════════════════════════════════════════════════════════╝
"""

from web3 import Web3
import time
from colorama import init, Fore, Back, Style
from datetime import datetime
from decimal import Decimal
import os
import sys
import random
import string
from eth_account import Account

# Initialize colorama for colored output
init(autoreset=True)

# ============================================
# CONFIGURATION
# ============================================

class Config:
    RPC_URL = "https://atlantic.dplabs-internal.com/"
    CONTRACT_ADDRESS = Web3.to_checksum_address("0xf180136ddc9e4f8c9b5a9fe59e2b1f07265c5d4d")
    CHAIN_ID = 688689
    EXPLORER_URL = "https://atlantic.pharosscan.xyz"
    PRIVATE_KEY_FILE = "pv.txt"
    MINT_PRICE = 0.08  # PHRS per domain
    GAS_LIMIT = 527242

# ============================================
# UTILITY FUNCTIONS
# ============================================

def print_banner():
    """Display main banner"""
    print(Fore.CYAN + Style.BRIGHT + "="*70)
    print(Fore.YELLOW + Style.BRIGHT + "          ZNS.BIO DOMAIN MINTER - PHAROS TESTNET")
    print(Fore.GREEN + Style.BRIGHT + "           CREATED BY KAZUHA  | VIP ONLY ")
    print(Fore.CYAN + Style.BRIGHT + "="*70)
    print()

def log_info(msg):
    """Information log"""
    print(Fore.CYAN + Style.BRIGHT + f"[INFO] {msg}")

def log_success(msg):
    """Success log"""
    print(Fore.GREEN + Style.BRIGHT + f"[SUCCESS] {msg}")

def log_error(msg):
    """Error log"""
    print(Fore.RED + Style.BRIGHT + f"[ERROR] {msg}")

def log_warn(msg):
    """Warning log"""
    print(Fore.YELLOW + Style.BRIGHT + f"[WARN] {msg}")

def generate_random_domain(length=6):
    """Generate random domain name"""
    # Mix of different patterns for variety
    patterns = [
        # Pure letters
        lambda: ''.join(random.choices(string.ascii_lowercase, k=length)),
        # Letters with numbers
        lambda: ''.join(random.choices(string.ascii_lowercase + string.digits, k=length)),
        # Word-like patterns
        lambda: random.choice(['meta', 'cyber', 'web', 'zns', 'defi', 'nft']) + ''.join(random.choices(string.digits, k=3)),
        # Name-like patterns
        lambda: random.choice(['john', 'alex', 'max', 'leo', 'kai']) + ''.join(random.choices(string.digits, k=4)),
    ]
    
    pattern = random.choice(patterns)
    return pattern()

# ============================================
# MAIN BOT CLASS
# ============================================

class ZNSBioDomainMinter:
    def __init__(self):
        """Initialize the ZNS Bio Domain Minter"""
        # Initialize Web3 connection
        self.w3 = Web3(Web3.HTTPProvider(Config.RPC_URL))
        
        # Check connection
        if not self.w3.is_connected():
            log_error("Failed to connect to Pharos Atlantic Testnet!")
            sys.exit(1)
        
        log_success(f"Connected to Pharos Atlantic Testnet")
        
        # Display network info
        current_block = self.w3.eth.block_number
        log_info(f"Current Block: {Fore.YELLOW + Style.BRIGHT}{current_block:,}")
        log_info(f"Contract: {Fore.YELLOW + Style.BRIGHT}{Config.CONTRACT_ADDRESS}")
        
        # Load private key
        self.load_private_key()
    
    def load_private_key(self):
        """Load private key from pv.txt file"""
        try:
            if not os.path.exists(Config.PRIVATE_KEY_FILE):
                log_warn(f"Creating {Config.PRIVATE_KEY_FILE} file...")
                with open(Config.PRIVATE_KEY_FILE, 'w') as f:
                    f.write("YOUR_PRIVATE_KEY_HERE")
                log_error(f"Please add your private key to {Config.PRIVATE_KEY_FILE}!")
                sys.exit(1)
            
            with open(Config.PRIVATE_KEY_FILE, 'r') as f:
                private_key = f.read().strip()
            
            if private_key == "YOUR_PRIVATE_KEY_HERE":
                log_error(f"Please add your actual private key to {Config.PRIVATE_KEY_FILE}!")
                sys.exit(1)
            
            if private_key.startswith('0x'):
                private_key = private_key[2:]
            
            if len(private_key) != 64:
                log_error("Invalid private key length!")
                sys.exit(1)
            
            self.private_key = private_key
            self.account = Account.from_key(private_key)
            self.address = Web3.to_checksum_address(self.account.address)
            
            log_success("Wallet loaded successfully")
            log_info(f"Address: {Fore.YELLOW + Style.BRIGHT}{self.address}")
            
            # Show initial balance
            self.check_balance(show_header=False)
            
        except Exception as e:
            log_error(f"Error loading private key: {str(e)}")
            sys.exit(1)
    
    def check_balance(self, show_header=True):
        """Check and display wallet balance"""
        try:
            balance = self.w3.eth.get_balance(self.address)
            balance_phrs = float(self.w3.from_wei(balance, 'ether'))
            
            if show_header:
                print(Fore.CYAN + Style.BRIGHT + "\n" + "="*60)
                print(Fore.YELLOW + Style.BRIGHT + "                 💰 WALLET BALANCE 💰")
                print(Fore.CYAN + Style.BRIGHT + "="*60)
            else:
                print()
                
            print(Fore.CYAN + Style.BRIGHT + f"Address: {Fore.YELLOW + Style.BRIGHT}{self.address}")
            print(Fore.CYAN + Style.BRIGHT + f"Balance: {Fore.GREEN + Style.BRIGHT}{balance_phrs:.6f} PHRS")
            
            # Calculate how many domains can be minted
            estimated_cost = Config.MINT_PRICE + 0.005  # Domain cost + gas
            can_mint = int(balance_phrs / estimated_cost)
            
            print(Fore.CYAN + Style.BRIGHT + f"Can Mint: {Fore.YELLOW + Style.BRIGHT}~{can_mint} domain(s)")
            
            if balance_phrs < 0.085:
                print(Fore.RED + Style.BRIGHT + "\n⚠️  Low balance! Need at least 0.085 PHRS to mint")
            
            if show_header:
                print(Fore.CYAN + Style.BRIGHT + "="*60 + "\n")
            
            return balance_phrs
            
        except Exception as e:
            log_error(f"Error checking balance: {str(e)}")
            return 0
    
    def mint_domain(self, domain_name, auto_confirm=False):
        """Mint a single domain"""
        print(Fore.MAGENTA + Style.BRIGHT + "\n" + "="*60)
        print(Fore.MAGENTA + Style.BRIGHT + "                 🚀 MINTING DOMAIN 🚀")
        print(Fore.MAGENTA + Style.BRIGHT + "="*60)
        
        # Clean domain name
        domain_name = domain_name.strip().lower().replace('.light', '')
        
        print(Fore.CYAN + Style.BRIGHT + f"Domain: {Fore.YELLOW + Style.BRIGHT}{domain_name}.light")
        
        try:
            # Get transaction parameters
            nonce = self.w3.eth.get_transaction_count(self.address)
            gas_price = self.w3.eth.gas_price
            
            # Display transaction details
            print(Fore.WHITE + Style.BRIGHT + "\n" + "-"*50)
            print(Fore.CYAN + Style.BRIGHT + "📋 Transaction Details:")
            print(Fore.WHITE + Style.BRIGHT + "-"*50)
            print(Fore.CYAN + Style.BRIGHT + f"  • Nonce: {Fore.YELLOW + Style.BRIGHT}{nonce}")
            print(Fore.CYAN + Style.BRIGHT + f"  • Gas Price: {Fore.YELLOW + Style.BRIGHT}{float(self.w3.from_wei(gas_price, 'gwei')):.2f} Gwei")
            print(Fore.CYAN + Style.BRIGHT + f"  • Gas Limit: {Fore.YELLOW + Style.BRIGHT}{Config.GAS_LIMIT:,}")
            print(Fore.CYAN + Style.BRIGHT + f"  • Value: {Fore.YELLOW + Style.BRIGHT}{Config.MINT_PRICE} PHRS")
            print(Fore.WHITE + Style.BRIGHT + "-"*50)
            
            # Encode domain name
            encoded_label = domain_name.encode('utf-8').hex()
            padded_label = encoded_label.ljust(64, '0')
            
            # Build transaction data
            method_id = "3a99d4eb"  # registerBatch
            
            input_data = (
                "0x" + method_id +
                "00000000000000000000000000000000000000000000000000000000000000a0" +
                "00000000000000000000000000000000000000000000000000000000000000e0" +
                "0000000000000000000000000000000000000000000000000000000000000160" +
                "0000000000000000000000000000000000000000000000000000000000000000" +
                "0000000000000000000000000000000000000000000000000000000000000000" +
                "0000000000000000000000000000000000000000000000000000000000000001" +
                "000000000000000000000000" + self.address[2:].lower() +
                "0000000000000000000000000000000000000000000000000000000000000001" +
                "0000000000000000000000000000000000000000000000000000000000000020" +
                f"{len(domain_name):064x}" +
                padded_label +
                "0000000000000000000000000000000000000000000000000000000000000001" +
                "0000000000000000000000000000000000000000000000000000000000000001"
            )
            
            # Calculate costs
            total_cost = Config.MINT_PRICE
            max_gas_fee = float(self.w3.from_wei(Config.GAS_LIMIT * gas_price, 'ether'))
            total_max = total_cost + max_gas_fee
            
            # Show cost summary
            print(Fore.YELLOW + Style.BRIGHT + "\n" + "="*60)
            print(Fore.YELLOW + Style.BRIGHT + "              💰 TRANSACTION COST 💰")
            print(Fore.YELLOW + Style.BRIGHT + "="*60)
            print(Fore.CYAN + Style.BRIGHT + "📝 Domain: " + Fore.WHITE + Style.BRIGHT + f"{domain_name}.light")
            print(Fore.CYAN + Style.BRIGHT + "💰 Cost: " + Fore.WHITE + Style.BRIGHT + f"{total_cost} PHRS")
            print(Fore.CYAN + Style.BRIGHT + "⛽ Max Gas: " + Fore.WHITE + Style.BRIGHT + f"{max_gas_fee:.6f} PHRS")
            print(Fore.CYAN + Style.BRIGHT + "💵 Total: " + Fore.YELLOW + Style.BRIGHT + f"{total_max:.6f} PHRS")
            print(Fore.YELLOW + Style.BRIGHT + "="*60)
            
            # Auto confirm for auto-generated domains
            if auto_confirm:
                print(Fore.GREEN + Style.BRIGHT + "\n✓ Auto-confirming transaction...")
                time.sleep(1)
            
            # Build transaction with checksum address
            transaction = {
                'nonce': nonce,
                'to': Config.CONTRACT_ADDRESS,  # Already checksummed in Config
                'value': self.w3.to_wei(Config.MINT_PRICE, 'ether'),
                'gas': Config.GAS_LIMIT,
                'gasPrice': gas_price,
                'data': input_data,
                'chainId': Config.CHAIN_ID
            }
            
            # Sign and send transaction
            log_info("Signing transaction...")
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=self.private_key)
            
            log_info("Sending transaction...")
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            log_success("Transaction sent!")
            log_info(f"TX Hash: {Fore.YELLOW + Style.BRIGHT}{tx_hash_hex}")
            log_info(f"Explorer: {Fore.YELLOW + Style.BRIGHT}{Config.EXPLORER_URL}/tx/{tx_hash_hex}")
            
            # Wait for confirmation
            log_info("Waiting for confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt['status'] == 1:
                # Success!
                print(Fore.GREEN + Style.BRIGHT + "\n" + "="*60)
                print(Fore.GREEN + Style.BRIGHT + "         🎉 SUCCESS! DOMAIN MINTED! 🎉")
                print(Fore.GREEN + Style.BRIGHT + "="*60)
                print(Fore.CYAN + Style.BRIGHT + "✓ Domain: " + Fore.GREEN + Style.BRIGHT + f"{domain_name}.light")
                print(Fore.CYAN + Style.BRIGHT + f"📦 Block: {Fore.YELLOW + Style.BRIGHT}{receipt['blockNumber']:,}")
                print(Fore.CYAN + Style.BRIGHT + f"⛽ Gas Used: {Fore.YELLOW + Style.BRIGHT}{receipt['gasUsed']:,}")
                
                # Calculate actual costs
                actual_gas_cost = float(self.w3.from_wei(receipt['gasUsed'] * receipt['effectiveGasPrice'], 'ether'))
                total_spent = Config.MINT_PRICE + actual_gas_cost
                
                print(Fore.CYAN + Style.BRIGHT + f"💰 Gas Cost: {Fore.YELLOW + Style.BRIGHT}{actual_gas_cost:.6f} PHRS")
                print(Fore.CYAN + Style.BRIGHT + f"💵 Total Spent: {Fore.YELLOW + Style.BRIGHT}{total_spent:.6f} PHRS")
                
                print(Fore.GREEN + Style.BRIGHT + "\n🔗 View Transaction:")
                print(Fore.YELLOW + Style.BRIGHT + f"{Config.EXPLORER_URL}/tx/{tx_hash_hex}")
                print(Fore.GREEN + Style.BRIGHT + "="*60 + "\n")
                
                # Update balance
                new_balance = self.w3.eth.get_balance(self.address)
                new_balance_phrs = float(self.w3.from_wei(new_balance, 'ether'))
                log_info(f"New Balance: {Fore.YELLOW + Style.BRIGHT}{new_balance_phrs:.4f} PHRS")
                
                return True
            else:
                log_error("Transaction Failed!")
                print(Fore.YELLOW + Style.BRIGHT + f"View details: {Config.EXPLORER_URL}/tx/{tx_hash_hex}")
                
                # Try to get revert reason
                try:
                    self.w3.eth.call(transaction, block_identifier=receipt['blockNumber'])
                except Exception as revert_error:
                    error_msg = str(revert_error)
                    log_error(f"Revert Reason: {error_msg}")
                    
                    if "domain unavailable" in error_msg.lower():
                        log_warn("💡 This domain is already taken!")
                    elif "insufficient" in error_msg.lower():
                        log_warn("💡 Insufficient funds!")
                    elif "price" in error_msg.lower():
                        log_warn("💡 Incorrect price sent!")
                
                return False
                
        except Exception as e:
            log_error(f"Transaction error: {str(e)}")
            
            if "insufficient funds" in str(e).lower():
                balance = self.w3.eth.get_balance(self.address)
                balance_phrs = float(self.w3.from_wei(balance, 'ether'))
                log_warn(f"Current balance: {balance_phrs:.6f} PHRS")
                log_warn(f"Required: ~0.085 PHRS (0.08 + gas)")
            elif "nonce" in str(e).lower():
                log_warn("Nonce issue. Please wait and try again.")
            elif "already known" in str(e).lower():
                log_warn("Transaction already in mempool. Please wait.")
                
            return False

    def auto_mint_domains(self):
        """Auto generate and mint multiple domains"""
        print(Fore.CYAN + Style.BRIGHT + "\n" + "="*60)
        print(Fore.YELLOW + Style.BRIGHT + "         🤖 AUTO DOMAIN GENERATOR 🤖")
        print(Fore.CYAN + Style.BRIGHT + "="*60)
        
        # Ask for count
        try:
            count = int(input(Fore.CYAN + Style.BRIGHT + "\n➤ How many domains to mint? " + Fore.WHITE + Style.BRIGHT))
            
            if count <= 0:
                log_error("Invalid count!")
                return
                
            # Check balance
            balance = self.w3.eth.get_balance(self.address)
            balance_phrs = float(self.w3.from_wei(balance, 'ether'))
            required = count * 0.085  # Approximate cost per domain
            
            if balance_phrs < required:
                log_error(f"Insufficient balance for {count} domains!")
                log_warn(f"Current: {balance_phrs:.6f} PHRS")
                log_warn(f"Required: ~{required:.6f} PHRS")
                return
            
            # Ask for delay
            delay = int(input(Fore.CYAN + Style.BRIGHT + "➤ Delay between mints (seconds)? " + Fore.WHITE + Style.BRIGHT))
            
            print(Fore.GREEN + Style.BRIGHT + "\n" + "="*60)
            print(Fore.GREEN + Style.BRIGHT + f"     Starting auto mint for {count} domains")
            print(Fore.GREEN + Style.BRIGHT + "="*60)
            
            success = 0
            failed = 0
            
            for i in range(count):
                print(Fore.YELLOW + Style.BRIGHT + f"\n[{i+1}/{count}] Generating random domain...")
                
                # Generate random domain
                domain = generate_random_domain(random.randint(5, 8))
                
                print(Fore.CYAN + Style.BRIGHT + f"Generated: {Fore.YELLOW + Style.BRIGHT}{domain}.light")
                
                # Try to mint
                result = self.mint_domain(domain, auto_confirm=True)
                
                if result:
                    success += 1
                    log_success(f"Minted successfully! ({success}/{i+1})")
                else:
                    failed += 1
                    log_warn(f"Failed to mint. Trying next... ({failed} failed)")
                
                # Delay before next
                if i < count - 1:
                    print(Fore.CYAN + Style.BRIGHT + f"\n⏳ Waiting {delay} seconds before next mint...")
                    time.sleep(delay)
            
            # Summary
            print(Fore.GREEN + Style.BRIGHT + "\n" + "="*60)
            print(Fore.GREEN + Style.BRIGHT + "         📊 AUTO MINT SUMMARY 📊")
            print(Fore.GREEN + Style.BRIGHT + "="*60)
            print(Fore.CYAN + Style.BRIGHT + f"Total Attempted: {Fore.YELLOW + Style.BRIGHT}{count}")
            print(Fore.CYAN + Style.BRIGHT + f"Successful: {Fore.GREEN + Style.BRIGHT}{success}")
            print(Fore.CYAN + Style.BRIGHT + f"Failed: {Fore.RED + Style.BRIGHT}{failed}")
            print(Fore.GREEN + Style.BRIGHT + "="*60)
            
        except ValueError:
            log_error("Invalid input! Please enter a number.")
        except KeyboardInterrupt:
            print(Fore.YELLOW + Style.BRIGHT + "\n\nAuto mint stopped by user")
        except Exception as e:
            log_error(f"Auto mint error: {str(e)}")

# ============================================
# MAIN EXECUTION
# ============================================

def main():
    """Main function"""
    print_banner()
    
    try:
        # Initialize bot
        minter = ZNSBioDomainMinter()
        
        while True:
            # Display menu
            print(Fore.WHITE + Style.BRIGHT + "\n" + "="*60)
            print(Fore.YELLOW + Style.BRIGHT + "                    MAIN MENU")
            print(Fore.WHITE + Style.BRIGHT + "="*60)
            print(Fore.GREEN + Style.BRIGHT + "1. " + Fore.WHITE + Style.BRIGHT + "Mint Domain (Manual)")
            print(Fore.GREEN + Style.BRIGHT + "2. " + Fore.WHITE + Style.BRIGHT + "Auto Generate & Mint")
            print(Fore.GREEN + Style.BRIGHT + "3. " + Fore.WHITE + Style.BRIGHT + "Check Balance")
            print(Fore.RED + Style.BRIGHT + "4. " + Fore.WHITE + Style.BRIGHT + "Exit")
            print(Fore.WHITE + Style.BRIGHT + "="*60)
            
            choice = input(Fore.CYAN + Style.BRIGHT + "\n➤ Select Option (1-4): " + Fore.WHITE + Style.BRIGHT).strip()
            
            if choice == '1':
                # Manual Mint Domain
                domain = input(Fore.CYAN + Style.BRIGHT + "\n➤ Enter domain name (without .light): " + Fore.WHITE + Style.BRIGHT).strip()
                
                if domain:
                    if len(domain) < 3:
                        log_error("Domain name must be at least 3 characters!")
                    elif not domain.replace('-', '').replace('_', '').isalnum():
                        log_error("Domain name can only contain letters, numbers, hyphens, and underscores!")
                    else:
                        # Check balance before minting
                        balance = minter.w3.eth.get_balance(minter.address)
                        balance_phrs = float(minter.w3.from_wei(balance, 'ether'))
                        
                        if balance_phrs < 0.085:
                            log_error("Insufficient balance!")
                            log_warn(f"Current: {balance_phrs:.6f} PHRS")
                            log_warn("Required: 0.085 PHRS (minimum)")
                        else:
                            minter.mint_domain(domain, auto_confirm=False)
                else:
                    log_error("No domain name entered!")
                    
            elif choice == '2':
                # Auto Generate and Mint
                minter.auto_mint_domains()
                
            elif choice == '3':
                # Check Balance
                minter.check_balance(show_header=True)
                
                # Also show transaction count
                try:
                    nonce = minter.w3.eth.get_transaction_count(minter.address)
                    if nonce > 0:
                        print(Fore.CYAN + Style.BRIGHT + f"\nTotal Transactions: {Fore.YELLOW + Style.BRIGHT}{nonce}")
                        print(Fore.CYAN + Style.BRIGHT + "View all transactions:")
                        print(Fore.YELLOW + Style.BRIGHT + f"{Config.EXPLORER_URL}/address/{minter.address}")
                except:
                    pass
                
                input(Fore.YELLOW + Style.BRIGHT + "\nPress Enter to continue...")
                
            elif choice == '4':
                # Exit
                print(Fore.YELLOW + Style.BRIGHT + "\n" + "="*60)
                print(Fore.GREEN + Style.BRIGHT + "         Thank you for using ZNS.BIO Minter!")
                print(Fore.CYAN + Style.BRIGHT + "              Created by KAZUHA")
                print(Fore.YELLOW + Style.BRIGHT + "="*60)
                print(Fore.WHITE + Style.BRIGHT + "\nGoodbye! 👋\n")
                break
                
            else:
                log_error("Invalid choice! Please select 1-4")
                
    except KeyboardInterrupt:
        print(Fore.YELLOW + Style.BRIGHT + "\n\nStopped by user")
        sys.exit(0)
    except Exception as e:
        log_error(f"Fatal Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
