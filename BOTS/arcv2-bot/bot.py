import os
import sys
import time
import random
from colorama import init, Fore, Style

init(autoreset=True)

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import CHAIN_ID, EXPLORER_URL, NFT_CONTRACTS, SWAP_TOKENS
from src.utils import clear, human_delay, print_header, print_info, print_success, print_error, print_warning
from src.wallet import load_private_keys, get_web3, get_account, get_all_balances
from src.wrap_unwrap import wrap_usdc, unwrap_wusdc
from src.swap import perform_single_swap, swap_all_tokens
from src.liquidity import add_liquidity, remove_liquidity, get_lp_balance
from src.arcdex import (
    arcdex_swap, swap_arcdex_usdc_to_eurc, swap_arcdex_eurc_to_usdc,
    swap_arcdex_usdc_to_swprc, swap_arcdex_swprc_to_usdc,
    swap_arcdex_eurc_to_swprc, swap_arcdex_swprc_to_eurc,
    swaparc_add_liquidity, swaparc_remove_liquidity,
    get_eurc_balance, get_swprc_balance, get_swaparc_lp_balance
)
from src.nft import mint_nft, mint_all_nfts
from src.arcade import arcade_daily_claim, ArcadeDaily


def display_banner():
    print(Fore.CYAN + Style.BRIGHT + "=" * 55)
    print(Fore.YELLOW + Style.BRIGHT + "           New Arc Auto Bot V2")
    print(Fore.YELLOW + Style.BRIGHT + "       Created by Kazuha VIP ONLY")
    print(Fore.CYAN + Style.BRIGHT + "=" * 55)


def display_balances(w3, account):
    balances = get_all_balances(w3, account)
    
    print(Fore.WHITE + Style.BRIGHT + f"Network: Arc Testnet | Chain: {CHAIN_ID}")
    print(Fore.WHITE + Style.BRIGHT + f"Wallet: {account.address[:10]}...{account.address[-8:]}")
    print(Fore.CYAN + Style.BRIGHT + "-" * 55)
    print(Fore.GREEN + Style.BRIGHT + "BALANCES:")
    print(Fore.WHITE + f"  USDC: {float(w3.from_wei(balances['usdc'], 'ether')):.6f}")
    print(Fore.WHITE + f"  WUSDC: {float(w3.from_wei(balances['wusdc'], 'ether')):.6f}")
    print(Fore.WHITE + f"  USDC.a: {balances['usdc_a'] / 10**6:.6f}")
    print(Fore.WHITE + f"  LP: {balances['lp'] / 10**18:.10f}")
    print(Fore.WHITE + f"  USDC Token: {balances['usdc_token'] / 10**6:.6f}")
    print(Fore.WHITE + f"  EURC: {balances['eurc'] / 10**6:.6f}")
    print(Fore.WHITE + f"  SWPRC: {balances['swprc'] / 10**6:.6f}")
    print(Fore.WHITE + f"  SLP: {balances['slp'] / 10**6:.6f}")


def swap_arcdex_menu(w3, account):
    from src.config import USDC_CONTRACT, ERC20_ABI
    from web3 import Web3
    
    while True:
        clear()
        print(Fore.CYAN + Style.BRIGHT + "=" * 50)
        print(Fore.YELLOW + Style.BRIGHT + "SWAPARCDEX")
        print(Fore.CYAN + Style.BRIGHT + "=" * 50)
        
        usdc_contract = w3.eth.contract(address=Web3.to_checksum_address(USDC_CONTRACT), abi=ERC20_ABI)
        usdc_balance = usdc_contract.functions.balanceOf(account.address).call()
        eurc_balance = get_eurc_balance(w3, account)
        swprc_balance = get_swprc_balance(w3, account)
        slp_balance = get_swaparc_lp_balance(w3, account)
        
        print(Fore.WHITE + Style.BRIGHT + f"USDC: {usdc_balance / 10**6:.6f} | EURC: {eurc_balance / 10**6:.6f}")
        print(Fore.WHITE + Style.BRIGHT + f"SWPRC: {swprc_balance / 10**6:.6f} | SLP: {slp_balance / 10**6:.6f}")
        print(Fore.CYAN + Style.BRIGHT + "=" * 50)
        print(Fore.GREEN + Style.BRIGHT + "=== SWAP ===")
        print(Fore.GREEN + Style.BRIGHT + "1. USDC -> EURC")
        print(Fore.GREEN + Style.BRIGHT + "2. EURC -> USDC")
        print(Fore.GREEN + Style.BRIGHT + "3. USDC -> SWPRC")
        print(Fore.GREEN + Style.BRIGHT + "4. SWPRC -> USDC")
        print(Fore.GREEN + Style.BRIGHT + "5. EURC -> SWPRC")
        print(Fore.GREEN + Style.BRIGHT + "6. SWPRC -> EURC")
        print(Fore.MAGENTA + Style.BRIGHT + "7. Swap All")
        print(Fore.CYAN + Style.BRIGHT + "=== LIQUIDITY ===")
        print(Fore.YELLOW + Style.BRIGHT + "8. Add Liquidity")
        print(Fore.YELLOW + Style.BRIGHT + "9. Remove Liquidity")
        print(Fore.RED + Style.BRIGHT + "0. Back")
        print(Fore.CYAN + Style.BRIGHT + "=" * 50)
        
        choice = input(Fore.YELLOW + Style.BRIGHT + "Choice: " + Fore.WHITE).strip()
        
        if choice == "1":
            amt = input(Fore.YELLOW + "USDC amount: " + Fore.WHITE).strip()
            try:
                amt = float(amt)
                if amt > 0:
                    print()
                    swap_arcdex_usdc_to_eurc(w3, account, amt)
            except:
                pass
            input(Fore.YELLOW + "Press Enter...")
            
        elif choice == "2":
            amt = input(Fore.YELLOW + "EURC amount: " + Fore.WHITE).strip()
            try:
                amt = float(amt)
                if amt > 0:
                    print()
                    swap_arcdex_eurc_to_usdc(w3, account, amt)
            except:
                pass
            input(Fore.YELLOW + "Press Enter...")
            
        elif choice == "3":
            amt = input(Fore.YELLOW + "USDC amount: " + Fore.WHITE).strip()
            try:
                amt = float(amt)
                if amt > 0:
                    print()
                    swap_arcdex_usdc_to_swprc(w3, account, amt)
            except:
                pass
            input(Fore.YELLOW + "Press Enter...")
            
        elif choice == "4":
            amt = input(Fore.YELLOW + "SWPRC amount: " + Fore.WHITE).strip()
            try:
                amt = float(amt)
                if amt > 0:
                    print()
                    swap_arcdex_swprc_to_usdc(w3, account, amt)
            except:
                pass
            input(Fore.YELLOW + "Press Enter...")
            
        elif choice == "5":
            amt = input(Fore.YELLOW + "EURC amount: " + Fore.WHITE).strip()
            try:
                amt = float(amt)
                if amt > 0:
                    print()
                    swap_arcdex_eurc_to_swprc(w3, account, amt)
            except:
                pass
            input(Fore.YELLOW + "Press Enter...")
            
        elif choice == "6":
            amt = input(Fore.YELLOW + "SWPRC amount: " + Fore.WHITE).strip()
            try:
                amt = float(amt)
                if amt > 0:
                    print()
                    swap_arcdex_swprc_to_eurc(w3, account, amt)
            except:
                pass
            input(Fore.YELLOW + "Press Enter...")
            
        elif choice == "7":
            amt = input(Fore.YELLOW + "USDC amount: " + Fore.WHITE).strip()
            try:
                amt = float(amt)
                if amt > 0:
                    print()
                    print(Fore.MAGENTA + "[1/3] USDC -> EURC")
                    r1 = swap_arcdex_usdc_to_eurc(w3, account, amt)
                    if r1:
                        time.sleep(random.uniform(5, 10))
                        eurc = get_eurc_balance(w3, account) / 10**6
                        print()
                        print(Fore.MAGENTA + "[2/3] EURC -> SWPRC")
                        r2 = swap_arcdex_eurc_to_swprc(w3, account, eurc)
                        if r2:
                            time.sleep(random.uniform(5, 10))
                            swprc = get_swprc_balance(w3, account) / 10**6
                            print()
                            print(Fore.MAGENTA + "[3/3] SWPRC -> USDC")
                            swap_arcdex_swprc_to_usdc(w3, account, swprc)
            except:
                pass
            input(Fore.YELLOW + "Press Enter...")
            
        elif choice == "8":
            print(Fore.YELLOW + "\nAdd Liquidity (USDC + EURC):")
            try:
                usdc_amt = float(input(Fore.YELLOW + "USDC: " + Fore.WHITE).strip())
                eurc_amt = float(input(Fore.YELLOW + "EURC: " + Fore.WHITE).strip())
                if usdc_amt > 0 and eurc_amt > 0:
                    print()
                    swaparc_add_liquidity(w3, account, usdc_amt, eurc_amt)
            except:
                pass
            input(Fore.YELLOW + "Press Enter...")
            
        elif choice == "9":
            print(Fore.YELLOW + "\nRemove Liquidity:")
            slp_cur = get_swaparc_lp_balance(w3, account)
            if slp_cur > 0:
                print(Fore.GREEN + f"SLP: {slp_cur / 10**6:.6f}")
                amt = input(Fore.YELLOW + "Amount (or 'all'): " + Fore.WHITE).strip()
                if amt.lower() == 'all':
                    lp_amt = None
                else:
                    try:
                        lp_amt = float(amt)
                    except:
                        lp_amt = None
                print()
                swaparc_remove_liquidity(w3, account, lp_amt)
            else:
                print(Fore.RED + "No SLP tokens!")
            input(Fore.YELLOW + "Press Enter...")
            
        elif choice == "0":
            break


def nft_menu(w3, account):
    while True:
        clear()
        print(Fore.CYAN + Style.BRIGHT + "=" * 50)
        print(Fore.YELLOW + Style.BRIGHT + "MINT NFT")
        print(Fore.CYAN + Style.BRIGHT + "=" * 50)
        
        balance = w3.eth.get_balance(account.address)
        balance_formatted = float(w3.from_wei(balance, 'ether'))
        print(Fore.WHITE + Style.BRIGHT + f"USDC Balance: {balance_formatted:.6f}")
        print(Fore.CYAN + Style.BRIGHT + "=" * 50)
        
        print(Fore.GREEN + Style.BRIGHT + "Available NFTs:")
        for idx, (key, nft) in enumerate(NFT_CONTRACTS.items(), 1):
            price_str = f"{nft['price']} USDC" if nft['price'] > 0 else "FREE"
            print(Fore.WHITE + Style.BRIGHT + f"{idx}. {nft['name']} - {price_str}")
        
        print(Fore.CYAN + Style.BRIGHT + "=" * 50)
        print(Fore.MAGENTA + Style.BRIGHT + "4. Mint All NFTs")
        print(Fore.RED + Style.BRIGHT + "0. Back")
        print(Fore.CYAN + Style.BRIGHT + "=" * 50)
        
        choice = input(Fore.YELLOW + Style.BRIGHT + "Choice: " + Fore.WHITE).strip()
        
        if choice == "1":
            print()
            mint_nft(w3, account, "KIKO")
            input(Fore.YELLOW + "Press Enter...")
            
        elif choice == "2":
            print()
            mint_nft(w3, account, "FLORA")
            input(Fore.YELLOW + "Press Enter...")
            
        elif choice == "3":
            print()
            mint_nft(w3, account, "CANVAS")
            input(Fore.YELLOW + "Press Enter...")
            
        elif choice == "4":
            print()
            mint_all_nfts(w3, account)
            input(Fore.YELLOW + "Press Enter...")
            
        elif choice == "0":
            break


def auto_all(w3, account, wrap_amount, swap_amount, liquidity_amount, arcdex_amount, nft_mint, arcade_claim, cycles=1):
    print(Fore.CYAN + Style.BRIGHT + "=" * 60)
    print(Fore.YELLOW + Style.BRIGHT + "AUTO ALL - FULL AUTOMATION")
    print(Fore.CYAN + Style.BRIGHT + "=" * 60)
    print(Fore.WHITE + Style.BRIGHT + f"Cycles: {cycles}")
    print(Fore.WHITE + Style.BRIGHT + f"Wrap Amount: {wrap_amount} USDC")
    print(Fore.WHITE + Style.BRIGHT + f"Swap Amount: {swap_amount} USDC per token")
    print(Fore.WHITE + Style.BRIGHT + f"Liquidity Amount: {liquidity_amount} USDC.a")
    print(Fore.WHITE + Style.BRIGHT + f"ArcDex Amount: {arcdex_amount} USDC")
    print(Fore.WHITE + Style.BRIGHT + f"Mint NFTs: {'Yes' if nft_mint else 'No'}")
    print(Fore.WHITE + Style.BRIGHT + f"Arcade Daily: {'Yes' if arcade_claim else 'No'}")
    print(Fore.CYAN + Style.BRIGHT + "=" * 60)
    print()
    
    for cycle in range(1, cycles + 1):
        print(Fore.MAGENTA + Style.BRIGHT + f"\n{'='*60}")
        print(Fore.MAGENTA + Style.BRIGHT + f"CYCLE {cycle}/{cycles}")
        print(Fore.MAGENTA + Style.BRIGHT + f"{'='*60}\n")
        
        # Step 0: Arcade Daily (only once per day)
        if arcade_claim and cycle == 1:
            print(Fore.CYAN + Style.BRIGHT + "\n[STEP 0/8] ARCADE DAILY CLAIM")
            human_delay(2, 4)
            arcade_daily_claim(account)
            time.sleep(random.uniform(3, 6))
        
        # Step 1: Wrap
        print(Fore.CYAN + Style.BRIGHT + "\n[STEP 1/8] WRAP USDC -> WUSDC")
        human_delay(2, 4)
        wrap_result = wrap_usdc(w3, account, wrap_amount)
        print(Fore.GREEN if wrap_result else Fore.RED, end="")
        print(Style.BRIGHT + f"Result: {'SUCCESS' if wrap_result else 'FAILED'}")
        
        time.sleep(random.uniform(5, 10))
        
        # Step 2: Unwrap
        print(Fore.CYAN + Style.BRIGHT + "\n[STEP 2/8] UNWRAP WUSDC -> USDC")
        human_delay(2, 4)
        unwrap_result = unwrap_wusdc(w3, account, wrap_amount)
        print(Fore.GREEN if unwrap_result else Fore.RED, end="")
        print(Style.BRIGHT + f"Result: {'SUCCESS' if unwrap_result else 'FAILED'}")
        
        time.sleep(random.uniform(5, 10))
        
        # Step 3: Swap all tokens
        print(Fore.CYAN + Style.BRIGHT + "\n[STEP 3/8] SWAP TO ALL TOKENS")
        human_delay(2, 4)
        swap_all_tokens(w3, account, swap_amount)
        
        time.sleep(random.uniform(5, 10))
        
        # Step 4: ArcDex Swaps
        print(Fore.CYAN + Style.BRIGHT + "\n[STEP 4/8] SWAPARCDEX OPERATIONS")
        human_delay(2, 4)
        
        print(Fore.WHITE + Style.BRIGHT + "  [4.1] USDC -> EURC")
        r1 = swap_arcdex_usdc_to_eurc(w3, account, arcdex_amount)
        time.sleep(random.uniform(3, 6))
        
        if r1:
            eurc_bal = get_eurc_balance(w3, account) / 10**6
            print(Fore.WHITE + Style.BRIGHT + "  [4.2] EURC -> SWPRC")
            r2 = swap_arcdex_eurc_to_swprc(w3, account, eurc_bal)
            time.sleep(random.uniform(3, 6))
            
            if r2:
                swprc_bal = get_swprc_balance(w3, account) / 10**6
                print(Fore.WHITE + Style.BRIGHT + "  [4.3] SWPRC -> USDC")
                swap_arcdex_swprc_to_usdc(w3, account, swprc_bal)
        
        time.sleep(random.uniform(5, 10))
        
        # Step 5: Mint NFTs
        if nft_mint:
            print(Fore.CYAN + Style.BRIGHT + "\n[STEP 5/8] MINT NFTs")
            human_delay(2, 4)
            mint_all_nfts(w3, account)
            time.sleep(random.uniform(5, 10))
        else:
            print(Fore.CYAN + Style.BRIGHT + "\n[STEP 5/8] MINT NFTs - SKIPPED")
        
        # Step 6: Add Liquidity
        print(Fore.CYAN + Style.BRIGHT + "\n[STEP 6/8] ADD LIQUIDITY")
        human_delay(2, 4)
        add_result = add_liquidity(w3, account, liquidity_amount)
        print(Fore.GREEN if add_result else Fore.RED, end="")
        print(Style.BRIGHT + f"Result: {'SUCCESS' if add_result else 'FAILED'}")
        
        if add_result:
            # Wait for cooldown
            print(Fore.YELLOW + Style.BRIGHT + "\n[STEP 7/8] WAITING 20 MINUTES FOR COOLDOWN...")
            for remaining in range(1200, 0, -1):
                mins = remaining // 60
                secs = remaining % 60
                print(Fore.CYAN + Style.BRIGHT + f"    Cooldown: {mins:02d}:{secs:02d}    ", end='\r')
                time.sleep(1)
            print(Fore.GREEN + Style.BRIGHT + "\n    Cooldown complete!                    ")
            
            # Step 8: Remove Liquidity
            print(Fore.CYAN + Style.BRIGHT + "\n[STEP 8/8] REMOVE LIQUIDITY")
            human_delay(2, 4)
            remove_result = remove_liquidity(w3, account, wait_for_cooldown=False)
            print(Fore.GREEN if remove_result else Fore.RED, end="")
            print(Style.BRIGHT + f"Result: {'SUCCESS' if remove_result else 'FAILED'}")
        else:
            print(Fore.CYAN + Style.BRIGHT + "\n[STEP 7/8] COOLDOWN - SKIPPED")
            print(Fore.CYAN + Style.BRIGHT + "\n[STEP 8/8] REMOVE LIQUIDITY - SKIPPED")
        
        if cycle < cycles:
            wait_time = random.uniform(10, 20)
            print(Fore.YELLOW + Style.BRIGHT + f"\nWaiting {wait_time:.1f}s before next cycle...")
            time.sleep(wait_time)
    
    print(Fore.CYAN + Style.BRIGHT + "\n" + "=" * 60)
    print(Fore.GREEN + Style.BRIGHT + f"AUTO ALL COMPLETED FOR {account.address[:10]}...!")
    print(Fore.CYAN + Style.BRIGHT + "=" * 60)


def main():
    w3 = get_web3()
    
    if not w3.is_connected():
        print(Fore.RED + Style.BRIGHT + "ERROR: Cannot connect to RPC!")
        return
    
    pks = load_private_keys()
    if not pks:
        return
    
    accounts = [get_account(pk) for pk in pks if get_account(pk)]
    if not accounts:
        print(Fore.RED + Style.BRIGHT + "ERROR: No valid accounts found!")
        return
    
    while True:
        clear()
        display_banner()
        print(Fore.WHITE + Style.BRIGHT + f"Total Accounts Loaded: {len(accounts)}")
        print(Fore.CYAN + Style.BRIGHT + "=" * 55)
        
        print(Fore.GREEN + Style.BRIGHT + "COMMANDS:")
        print(Fore.WHITE + Style.BRIGHT + "  1. Start Operations (All Wallets)")
        print(Fore.RED + Style.BRIGHT + "  0. Exit")
        print(Fore.CYAN + Style.BRIGHT + "=" * 55)
        
        cmd = input(Fore.YELLOW + Style.BRIGHT + "Choice: " + Fore.WHITE).strip()
        
        if cmd == "0":
            print(Fore.GREEN + Style.BRIGHT + "\nGoodbye!")
            break
            
        if cmd != "1":
            continue

        while True:
            clear()
            display_banner()
            # Just display balance for first account as representative or just a generic header
            print(Fore.YELLOW + Style.BRIGHT + f"OPERATING ON {len(accounts)} WALLETS")
            print(Fore.CYAN + Style.BRIGHT + "=" * 55)
            print(Fore.GREEN + Style.BRIGHT + "MENU:")
            print(Fore.WHITE + Style.BRIGHT + "  1. Wrap (USDC -> WUSDC)")
            print(Fore.WHITE + Style.BRIGHT + "  2. Unwrap (WUSDC -> USDC)")
            print(Fore.WHITE + Style.BRIGHT + "  3. Swap (All Tokens)")
            print(Fore.WHITE + Style.BRIGHT + "  4. Add Liquidity (USDC.a)")
            print(Fore.WHITE + Style.BRIGHT + "  5. Remove Liquidity")
            print(Fore.WHITE + Style.BRIGHT + "  6. SwapArcDex (Swap & Liquidity)")
            print(Fore.WHITE + Style.BRIGHT + "  7. Mint NFT")
            print(Fore.CYAN + Style.BRIGHT + "  8. Arcade Daily Claim")
            print(Fore.MAGENTA + Style.BRIGHT + "  9. Auto All (Full Automation)")
            print(Fore.RED + Style.BRIGHT + "  0. Back")
            print(Fore.CYAN + Style.BRIGHT + "=" * 55)
            
            choice = input(Fore.YELLOW + Style.BRIGHT + "Choice: " + Fore.WHITE).strip()
            
            if choice == "0":
                break
            
            # Sub-menu choices that need inputs before the loop
            params = {}
            if choice == "1":
                params['amt'] = input(Fore.YELLOW + "Amount USDC to wrap: " + Fore.WHITE).strip()
            elif choice == "2":
                params['amt'] = input(Fore.YELLOW + "Amount WUSDC to unwrap: " + Fore.WHITE).strip()
            elif choice == "3":
                params['amt'] = input(Fore.YELLOW + "Amount USDC per swap: " + Fore.WHITE).strip()
            elif choice == "4":
                print(Fore.YELLOW + "\nAdd Liquidity:")
                print(Fore.WHITE + "  Fee = 2x amount in USDC")
                params['amt'] = input(Fore.YELLOW + "USDC.a amount: " + Fore.WHITE).strip()
            elif choice == "5":
                print(Fore.YELLOW + "\nRemove Liquidity:")
                params['amt'] = input(Fore.YELLOW + "LP amount (or 'all'): " + Fore.WHITE).strip()
                wait = input(Fore.YELLOW + "Wait for cooldown? (y/n): " + Fore.WHITE).strip().lower()
                params['wait_cooldown'] = wait == 'y'
            elif choice == "8":
                print()
                params['username'] = input(Fore.YELLOW + "Username (or press Enter for auto): " + Fore.WHITE).strip()
            elif choice == "9":
                print(Fore.YELLOW + Style.BRIGHT + "\n" + "=" * 55)
                print(Fore.YELLOW + Style.BRIGHT + "AUTO ALL - CONFIGURATION")
                print(Fore.YELLOW + Style.BRIGHT + "=" * 55)
                try:
                    params['cycles'] = int(input(Fore.YELLOW + "Number of cycles: " + Fore.WHITE).strip())
                    params['wrap_amt'] = float(input(Fore.YELLOW + "Wrap amount (USDC): " + Fore.WHITE).strip())
                    params['swap_amt'] = float(input(Fore.YELLOW + "Swap amount per token (USDC): " + Fore.WHITE).strip())
                    params['liq_amt'] = float(input(Fore.YELLOW + "Liquidity amount (USDC.a): " + Fore.WHITE).strip())
                    params['arcdex_amt'] = float(input(Fore.YELLOW + "ArcDex swap amount (USDC): " + Fore.WHITE).strip())
                    nft_choice = input(Fore.YELLOW + "Mint NFTs? (y/n): " + Fore.WHITE).strip().lower()
                    params['nft_mint'] = nft_choice == 'y'
                    arcade_choice = input(Fore.YELLOW + "Claim Arcade Daily? (y/n): " + Fore.WHITE).strip().lower()
                    params['arcade_claim'] = arcade_choice == 'y'
                    confirm = input(Fore.YELLOW + "Start Auto All for ALL wallets? (y/n): " + Fore.WHITE).strip().lower()
                    if confirm != 'y': continue
                except:
                    print(Fore.RED + "Invalid input!")
                    continue
            
            # Loop through all accounts
            for i, account in enumerate(accounts):
                print(Fore.MAGENTA + Style.BRIGHT + f"\n[Account {i+1}/{len(accounts)}] {account.address[:10]}...{account.address[-8:]}")
                
                if choice == "1":
                    try:
                        amt = float(params['amt'])
                        if amt > 0: wrap_usdc(w3, account, amt)
                    except: print(Fore.RED + "Invalid amount!")
                    
                elif choice == "2":
                    try:
                        amt = float(params['amt'])
                        if amt > 0: unwrap_wusdc(w3, account, amt)
                    except: print(Fore.RED + "Invalid amount!")
                    
                elif choice == "3":
                    try:
                        amt = float(params['amt'])
                        if amt > 0: swap_all_tokens(w3, account, amt)
                    except: print(Fore.RED + "Invalid amount!")
                    
                elif choice == "4":
                    try:
                        amt = float(params['amt'])
                        if amt > 0: add_liquidity(w3, account, amt)
                    except: print(Fore.RED + "Invalid amount!")
                    
                elif choice == "5":
                    lp_cur = get_lp_balance(w3, account)
                    if lp_cur > 0:
                        print(Fore.GREEN + f"LP Balance: {lp_cur / 10**18:.18f}")
                        if params['amt'].lower() == 'all': lp_amt = None
                        else:
                            try: lp_amt = float(params['amt'])
                            except: lp_amt = None
                        remove_liquidity(w3, account, lp_amt, params['wait_cooldown'])
                    else:
                        print(Fore.RED + "No LP to remove.")
                        
                elif choice == "6":
                    swap_arcdex_menu(w3, account) # This is still interactive per wallet, but that's okay for manual menu
                    
                elif choice == "7":
                    nft_menu(w3, account) # This is still interactive per wallet
                    
                elif choice == "8":
                    arcade_daily_claim(account, params['username'] if params['username'] else None)
                    
                elif choice == "9":
                    auto_all(w3, account, params['wrap_amt'], params['swap_amt'], params['liq_amt'], params['arcdex_amt'], params['nft_mint'], params['arcade_claim'], params['cycles'])

            print(Fore.CYAN + Style.BRIGHT + "\n" + "=" * 55)
            print(Fore.GREEN + Style.BRIGHT + "Task completed for all wallets!")
            input(Fore.YELLOW + "Press Enter to return to menu...")
        
        else:
            print(Fore.RED + "Invalid choice!")
            input(Fore.YELLOW + "Press Enter...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.RED + Style.BRIGHT + "\n\nExiting...")