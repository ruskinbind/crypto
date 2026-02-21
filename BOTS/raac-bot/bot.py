#!/usr/bin/env python3
"""
========================================
  RAAC AUTO BOT
  CREATED BY KAZUHA
========================================
"""
import os
import sys
import time
from web3 import Web3
from eth_account import Account

BOLD="\033[1m"
RED="\033[1;31m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
CYAN="\033[1;36m"
MAGENTA="\033[1;35m"
WHITE="\033[1;37m"
RESET="\033[0m"

CRVUSD_TOKEN="0x8047a14301583CAaf9e2128D5F88F9f435659d35"
IRAAC_TOKEN="0x1c1789629B2511821aC78618eBd23d41E7b04989"
RCRVUSD_TOKEN="0xc96c34825aa96A77A4AD884e393960a70c5f1186"
DECRVUSD_TOKEN="0x5841dc06d2C9e0D2605392f669be71Bfe6d04cf7"
SWAP_CONTRACT="0x0cAa0daa4f5EC8934428Ae406965B044f42F7D49"
VAULT_CONTRACT="0xefCff23AEed94ae0f23377DFDaB78C3c868eeB33"
STABILITY_CONTRACT="0xd7663c079445A070Ef24405CD5ef1511B9d9E060"

RPC_URL="https://11155111.rpc.thirdweb.com/23bc4c157e11215cab1bfeb978452e4b"
BACKUP_RPC="https://rpc.sepolia.org"
CHAIN_ID=11155111
EXPLORER="https://sepolia.etherscan.io/tx/"

ERC20_ABI=[{"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
MINT_ABI=[{"inputs":[{"name":"_account","type":"address"},{"name":"_amount","type":"uint256"}],"name":"mint","outputs":[],"stateMutability":"nonpayable","type":"function"}]
SWAP_ABI=[{"inputs":[{"name":"i","type":"uint256"},{"name":"j","type":"uint256"},{"name":"in_amount","type":"uint256"},{"name":"min_amount","type":"uint256"},{"name":"_for","type":"address"}],"name":"exchange","outputs":[],"stateMutability":"nonpayable","type":"function"}]
VAULT_ABI=[{"inputs":[{"name":"amount","type":"uint256"}],"name":"deposit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"name":"amount","type":"uint256"}],"name":"withdraw","outputs":[],"stateMutability":"nonpayable","type":"function"}]
STABILITY_ABI=[{"inputs":[{"name":"amount","type":"uint256"}],"name":"deposit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"name":"_total","type":"uint256"}],"name":"requestWithdraw","outputs":[],"stateMutability":"nonpayable","type":"function"}]

MAX_UINT256=2**256-1
MINT_AMOUNT=Web3.to_wei(200000,'ether')
task_count=0

def clear():
    os.system('cls' if os.name=='nt' else 'clear')

def banner():
    clear()
    print(f"{CYAN}{BOLD}{'='*55}{RESET}")
    print(f"{GREEN}{BOLD}              RAAC AUTO BOT{RESET}")
    print(f"{YELLOW}{BOLD}          CREATED BY KAZUHA VIP ONLY{RESET}")
    print(f"{CYAN}{BOLD}{'='*55}{RESET}\n")

def show_balance(w3,acc):
    global task_count
    try:
        eth=w3.eth.get_balance(acc.address)
        crvusd=bal(w3,acc,CRVUSD_TOKEN)
        iraac=bal(w3,acc,IRAAC_TOKEN)
        rcrvusd=bal(w3,acc,RCRVUSD_TOKEN)
        decrvusd=bal(w3,acc,DECRVUSD_TOKEN)
    except:
        eth=crvusd=iraac=rcrvusd=decrvusd=0
    print(f"{WHITE}{BOLD}WALLET: {acc.address}{RESET}")
    print(f"{CYAN}{BOLD}{'─'*55}{RESET}")
    print(f"{GREEN}{BOLD}ETH:{RESET}      {WHITE}{BOLD}{Web3.from_wei(eth,'ether'):.6f}{RESET}")
    print(f"{GREEN}{BOLD}crvUSD:{RESET}   {WHITE}{BOLD}{Web3.from_wei(crvusd,'ether'):.4f}{RESET}")
    print(f"{GREEN}{BOLD}iRAAC:{RESET}    {WHITE}{BOLD}{Web3.from_wei(iraac,'ether'):.4f}{RESET}")
    print(f"{GREEN}{BOLD}RcrvUSD:{RESET}  {WHITE}{BOLD}{Web3.from_wei(rcrvusd,'ether'):.4f}{RESET}")
    print(f"{GREEN}{BOLD}DEcrvUSD:{RESET} {WHITE}{BOLD}{Web3.from_wei(decrvusd,'ether'):.4f}{RESET}")
    print(f"{CYAN}{BOLD}{'─'*55}{RESET}")
    print(f"{YELLOW}{BOLD}TASKS COMPLETED: {task_count}{RESET}\n")

def menu():
    print(f"{WHITE}{BOLD}SELECT OPTION:{RESET}")
    print(f"{GREEN}{BOLD}[1]{RESET} {WHITE}{BOLD}MINT TOKEN{RESET}")
    print(f"{GREEN}{BOLD}[2]{RESET} {WHITE}{BOLD}SWAP crvUSD -> iRAAC -> crvUSD{RESET}")
    print(f"{GREEN}{BOLD}[3]{RESET} {WHITE}{BOLD}LEND DEPOSIT{RESET}")
    print(f"{GREEN}{BOLD}[4]{RESET} {WHITE}{BOLD}LEND WITHDRAW{RESET}")
    print(f"{GREEN}{BOLD}[5]{RESET} {WHITE}{BOLD}STABILITY DEPOSIT{RESET}")
    print(f"{GREEN}{BOLD}[6]{RESET} {WHITE}{BOLD}STABILITY WITHDRAW{RESET}")
    print(f"{MAGENTA}{BOLD}[7]{RESET} {WHITE}{BOLD}AUTO ALL TASKS{RESET}")
    print(f"{RED}{BOLD}[8]{RESET} {WHITE}{BOLD}EXIT{RESET}\n")

def load_pk():
    try:
        with open("pv.txt","r") as f:
            pk=f.read().strip()
            return pk if pk.startswith("0x") else "0x"+pk
    except:
        print(f"{RED}{BOLD}ERROR: pv.txt NOT FOUND{RESET}")
        sys.exit(1)

def get_w3():
    try:
        w3=Web3(Web3.HTTPProvider(RPC_URL,request_kwargs={'timeout':60}))
        if w3.is_connected():
            return w3
    except:pass
    try:
        w3=Web3(Web3.HTTPProvider(BACKUP_RPC,request_kwargs={'timeout':60}))
        if w3.is_connected():
            return w3
    except:pass
    print(f"{RED}{BOLD}ERROR: RPC CONNECTION FAILED{RESET}")
    sys.exit(1)

def gas_params(w3):
    try:
        base=w3.eth.get_block('latest')['baseFeePerGas']
        priority=Web3.to_wei(1.1,'gwei')
        return base+priority,priority
    except:
        return Web3.to_wei(5,'gwei'),Web3.to_wei(1.1,'gwei')

def send(w3,acc,tx):
    try:
        tx['nonce']=w3.eth.get_transaction_count(acc.address,'pending')
        tx['chainId']=CHAIN_ID
        if 'gas' not in tx:tx['gas']=500000
        mf,mp=gas_params(w3)
        tx['maxFeePerGas']=mf
        tx['maxPriorityFeePerGas']=mp
        signed=acc.sign_transaction(tx)
        h=w3.eth.send_raw_transaction(signed.raw_transaction)
        return h.hex()
    except Exception as e:
        print(f"{RED}{BOLD}TX ERROR: {e}{RESET}")
        return None

def wait(w3,h,t=180):
    print(f"{YELLOW}{BOLD}WAITING FOR CONFIRMATION...{RESET}")
    start=time.time()
    while time.time()-start<t:
        try:
            r=w3.eth.get_transaction_receipt(h)
            if r:
                block=r['blockNumber']
                if r['status']==1:
                    print(f"{GREEN}{BOLD}STATUS: SUCCESS{RESET}")
                    print(f"{WHITE}{BOLD}BLOCK: {block}{RESET}")
                    print(f"{GREEN}{BOLD}TX: {h}{RESET}")
                    print(f"{GREEN}{BOLD}URL: {EXPLORER}{h}{RESET}")
                    return True
                else:
                    print(f"{RED}{BOLD}STATUS: FAILED{RESET}")
                    print(f"{WHITE}{BOLD}BLOCK: {block}{RESET}")
                    print(f"{GREEN}{BOLD}TX: {h}{RESET}")
                    print(f"{GREEN}{BOLD}URL: {EXPLORER}{h}{RESET}")
                    return False
        except:pass
        time.sleep(2)
    print(f"{RED}{BOLD}TIMEOUT{RESET}")
    return False

def bal(w3,acc,addr):
    try:
        c=w3.eth.contract(address=Web3.to_checksum_address(addr),abi=ERC20_ABI)
        return c.functions.balanceOf(acc.address).call()
    except:
        return 0

def approve(w3,acc,token,spender,amt):
    print(f"{CYAN}{BOLD}APPROVING TOKEN...{RESET}")
    c=w3.eth.contract(address=Web3.to_checksum_address(token),abi=ERC20_ABI)
    tx=c.functions.approve(Web3.to_checksum_address(spender),amt).build_transaction({'from':acc.address,'value':0,'gas':80000})
    h=send(w3,acc,tx)
    if not h:return False
    return wait(w3,h)

def mint(w3,acc):
    global task_count
    print(f"{CYAN}{BOLD}MINTING 200,000 crvUSD...{RESET}")
    c=w3.eth.contract(address=Web3.to_checksum_address(CRVUSD_TOKEN),abi=MINT_ABI)
    tx=c.functions.mint(acc.address,MINT_AMOUNT).build_transaction({'from':acc.address,'value':0,'gas':100000})
    h=send(w3,acc,tx)
    if not h:return False
    if wait(w3,h):
        task_count+=1
        print(f"{GREEN}{BOLD}MINTED 200,000 crvUSD{RESET}")
        return True
    return False

def swap_func(w3,acc,i,j,amt):
    c=w3.eth.contract(address=Web3.to_checksum_address(SWAP_CONTRACT),abi=SWAP_ABI)
    tx=c.functions.exchange(i,j,amt,int(amt*98//100),acc.address).build_transaction({'from':acc.address,'value':0,'gas':200000})
    h=send(w3,acc,tx)
    if not h:return False
    return wait(w3,h)

def full_swap(w3,acc):
    global task_count
    b=bal(w3,acc,CRVUSD_TOKEN)
    if b==0:
        print(f"{RED}{BOLD}NO crvUSD BALANCE{RESET}")
        return False
    amt=Web3.to_wei(10,'ether')
    if b<amt:amt=b
    print(f"{WHITE}{BOLD}SWAP AMOUNT: {Web3.from_wei(amt,'ether')} crvUSD{RESET}\n")
    print(f"{YELLOW}{BOLD}[1/4] APPROVING crvUSD...{RESET}")
    if not approve(w3,acc,CRVUSD_TOKEN,SWAP_CONTRACT,amt):return False
    time.sleep(3)
    print(f"\n{YELLOW}{BOLD}[2/4] SWAPPING crvUSD -> iRAAC...{RESET}")
    if not swap_func(w3,acc,0,1,amt):return False
    task_count+=1
    time.sleep(3)
    b2=bal(w3,acc,IRAAC_TOKEN)
    if b2==0:
        print(f"{RED}{BOLD}NO iRAAC{RESET}")
        return False
    amt2=Web3.to_wei(10,'ether')
    if b2<amt2:amt2=b2
    print(f"\n{YELLOW}{BOLD}[3/4] APPROVING iRAAC...{RESET}")
    if not approve(w3,acc,IRAAC_TOKEN,SWAP_CONTRACT,amt2):return False
    time.sleep(3)
    print(f"\n{YELLOW}{BOLD}[4/4] SWAPPING iRAAC -> crvUSD...{RESET}")
    if not swap_func(w3,acc,1,0,amt2):return False
    task_count+=1
    print(f"\n{GREEN}{BOLD}SWAPPED {Web3.from_wei(amt,'ether')} crvUSD <-> iRAAC{RESET}")
    return True

def lend_deposit(w3,acc):
    global task_count
    b=bal(w3,acc,CRVUSD_TOKEN)
    if b==0:
        print(f"{RED}{BOLD}NO crvUSD BALANCE{RESET}")
        return False
    amt=Web3.to_wei(50,'ether')
    if b<amt:amt=b
    print(f"{WHITE}{BOLD}LEND DEPOSIT: {Web3.from_wei(amt,'ether')} crvUSD{RESET}\n")
    print(f"{YELLOW}{BOLD}[1/2] APPROVING crvUSD...{RESET}")
    if not approve(w3,acc,CRVUSD_TOKEN,VAULT_CONTRACT,amt):return False
    time.sleep(3)
    print(f"\n{YELLOW}{BOLD}[2/2] DEPOSITING TO LEND...{RESET}")
    c=w3.eth.contract(address=Web3.to_checksum_address(VAULT_CONTRACT),abi=VAULT_ABI)
    tx=c.functions.deposit(amt).build_transaction({'from':acc.address,'value':0,'gas':600000})
    h=send(w3,acc,tx)
    if not h:return False
    if wait(w3,h):
        task_count+=1
        print(f"{GREEN}{BOLD}DEPOSITED {Web3.from_wei(amt,'ether')} crvUSD{RESET}")
        return True
    return False

def lend_withdraw(w3,acc):
    global task_count
    b=bal(w3,acc,RCRVUSD_TOKEN)
    if b==0:
        print(f"{RED}{BOLD}NO RcrvUSD BALANCE{RESET}")
        return False
    amt=Web3.to_wei(5,'ether')
    if b<amt:amt=b
    print(f"{WHITE}{BOLD}LEND WITHDRAW: {Web3.from_wei(amt,'ether')} RcrvUSD{RESET}\n")
    print(f"{YELLOW}{BOLD}WITHDRAWING FROM LEND...{RESET}")
    c=w3.eth.contract(address=Web3.to_checksum_address(VAULT_CONTRACT),abi=VAULT_ABI)
    tx=c.functions.withdraw(amt).build_transaction({'from':acc.address,'value':0,'gas':400000})
    h=send(w3,acc,tx)
    if not h:return False
    if wait(w3,h):
        task_count+=1
        print(f"{GREEN}{BOLD}WITHDRAWN {Web3.from_wei(amt,'ether')} crvUSD{RESET}")
        return True
    return False

def stability_deposit(w3,acc):
    global task_count
    b=bal(w3,acc,RCRVUSD_TOKEN)
    if b==0:
        print(f"{RED}{BOLD}NO RcrvUSD BALANCE{RESET}")
        return False
    amt=Web3.to_wei(1,'ether')
    if b<amt:amt=b
    print(f"{WHITE}{BOLD}STABILITY DEPOSIT: {Web3.from_wei(amt,'ether')} RcrvUSD{RESET}\n")
    print(f"{YELLOW}{BOLD}[1/2] APPROVING RcrvUSD...{RESET}")
    if not approve(w3,acc,RCRVUSD_TOKEN,STABILITY_CONTRACT,MAX_UINT256):return False
    time.sleep(3)
    print(f"\n{YELLOW}{BOLD}[2/2] DEPOSITING TO STABILITY...{RESET}")
    c=w3.eth.contract(address=Web3.to_checksum_address(STABILITY_CONTRACT),abi=STABILITY_ABI)
    tx=c.functions.deposit(amt).build_transaction({'from':acc.address,'value':0,'gas':450000})
    h=send(w3,acc,tx)
    if not h:return False
    if wait(w3,h):
        task_count+=1
        print(f"{GREEN}{BOLD}DEPOSITED {Web3.from_wei(amt,'ether')} TO STABILITY{RESET}")
        return True
    return False

def stability_withdraw(w3,acc):
    global task_count
    b=bal(w3,acc,DECRVUSD_TOKEN)
    if b==0:
        print(f"{RED}{BOLD}NO DEcrvUSD BALANCE{RESET}")
        return False
    amt=Web3.to_wei(1,'ether')
    if b<amt:amt=b
    print(f"{WHITE}{BOLD}STABILITY WITHDRAW: {Web3.from_wei(amt,'ether')} DEcrvUSD{RESET}\n")
    print(f"{YELLOW}{BOLD}[1/2] APPROVING DEcrvUSD...{RESET}")
    if not approve(w3,acc,DECRVUSD_TOKEN,STABILITY_CONTRACT,MAX_UINT256):return False
    time.sleep(3)
    print(f"\n{YELLOW}{BOLD}[2/2] REQUESTING WITHDRAW...{RESET}")
    c=w3.eth.contract(address=Web3.to_checksum_address(STABILITY_CONTRACT),abi=STABILITY_ABI)
    tx=c.functions.requestWithdraw(amt).build_transaction({'from':acc.address,'value':0,'gas':350000})
    h=send(w3,acc,tx)
    if not h:return False
    if wait(w3,h):
        task_count+=1
        print(f"{GREEN}{BOLD}WITHDRAW REQUESTED {Web3.from_wei(amt,'ether')}{RESET}")
        return True
    return False

def auto_all(w3,acc):
    print(f"{MAGENTA}{BOLD}{'='*55}{RESET}")
    print(f"{MAGENTA}{BOLD}         STARTING AUTO ALL TASKS{RESET}")
    print(f"{MAGENTA}{BOLD}{'='*55}{RESET}\n")
    print(f"{YELLOW}{BOLD}[TASK 1/6] MINT TOKEN{RESET}")
    print(f"{CYAN}{BOLD}{'─'*55}{RESET}")
    mint(w3,acc)
    time.sleep(5)
    print(f"\n{YELLOW}{BOLD}[TASK 2/6] SWAP{RESET}")
    print(f"{CYAN}{BOLD}{'─'*55}{RESET}")
    full_swap(w3,acc)
    time.sleep(5)
    print(f"\n{YELLOW}{BOLD}[TASK 3/6] LEND DEPOSIT{RESET}")
    print(f"{CYAN}{BOLD}{'─'*55}{RESET}")
    lend_deposit(w3,acc)
    time.sleep(5)
    print(f"\n{YELLOW}{BOLD}[TASK 4/6] LEND WITHDRAW{RESET}")
    print(f"{CYAN}{BOLD}{'─'*55}{RESET}")
    lend_withdraw(w3,acc)
    time.sleep(5)
    print(f"\n{YELLOW}{BOLD}[TASK 5/6] STABILITY DEPOSIT{RESET}")
    print(f"{CYAN}{BOLD}{'─'*55}{RESET}")
    stability_deposit(w3,acc)
    time.sleep(5)
    print(f"\n{YELLOW}{BOLD}[TASK 6/6] STABILITY WITHDRAW{RESET}")
    print(f"{CYAN}{BOLD}{'─'*55}{RESET}")
    stability_withdraw(w3,acc)
    print(f"\n{GREEN}{BOLD}{'='*55}{RESET}")
    print(f"{GREEN}{BOLD}         ALL TASKS COMPLETED!{RESET}")
    print(f"{GREEN}{BOLD}{'='*55}{RESET}")

def main():
    banner()
    pk=load_pk()
    w3=get_w3()
    acc=Account.from_key(pk)
    show_balance(w3,acc)
    while True:
        menu()
        c=input(f"{CYAN}{BOLD}CHOICE: {RESET}").strip()
        if c=="1":
            print()
            mint(w3,acc)
            print()
            input(f"{YELLOW}{BOLD}PRESS ENTER TO CONTINUE...{RESET}")
            banner()
            show_balance(w3,acc)
        elif c=="2":
            print()
            full_swap(w3,acc)
            print()
            input(f"{YELLOW}{BOLD}PRESS ENTER TO CONTINUE...{RESET}")
            banner()
            show_balance(w3,acc)
        elif c=="3":
            print()
            lend_deposit(w3,acc)
            print()
            input(f"{YELLOW}{BOLD}PRESS ENTER TO CONTINUE...{RESET}")
            banner()
            show_balance(w3,acc)
        elif c=="4":
            print()
            lend_withdraw(w3,acc)
            print()
            input(f"{YELLOW}{BOLD}PRESS ENTER TO CONTINUE...{RESET}")
            banner()
            show_balance(w3,acc)
        elif c=="5":
            print()
            stability_deposit(w3,acc)
            print()
            input(f"{YELLOW}{BOLD}PRESS ENTER TO CONTINUE...{RESET}")
            banner()
            show_balance(w3,acc)
        elif c=="6":
            print()
            stability_withdraw(w3,acc)
            print()
            input(f"{YELLOW}{BOLD}PRESS ENTER TO CONTINUE...{RESET}")
            banner()
            show_balance(w3,acc)
        elif c=="7":
            print()
            auto_all(w3,acc)
            print()
            input(f"{YELLOW}{BOLD}PRESS ENTER TO CONTINUE...{RESET}")
            banner()
            show_balance(w3,acc)
        elif c=="8":
            print(f"{RED}{BOLD}EXITING...{RESET}")
            sys.exit(0)
        else:
            print(f"{RED}{BOLD}INVALID CHOICE{RESET}")
            time.sleep(1)
            banner()
            show_balance(w3,acc)

if __name__=="__main__":
    main()