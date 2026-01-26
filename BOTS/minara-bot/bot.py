import requests
import random
import time
import uuid
import sys
import os

BASE_URL = "https://api.minara.ai"

# Check if terminal supports colors
def supports_color():
    """Check if the terminal supports ANSI colors"""
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except:
            return os.environ.get('TERM') is not None or 'WT_SESSION' in os.environ
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

# Color class with fallback
class Colors:
    def __init__(self):
        if supports_color():
            self.RED = '\033[91m'
            self.GREEN = '\033[92m'
            self.YELLOW = '\033[93m'
            self.BLUE = '\033[94m'
            self.MAGENTA = '\033[95m'
            self.CYAN = '\033[96m'
            self.WHITE = '\033[97m'
            self.BOLD = '\033[1m'
            self.RESET = '\033[0m'
        else:
            self.RED = ''
            self.GREEN = ''
            self.YELLOW = ''
            self.BLUE = ''
            self.MAGENTA = ''
            self.CYAN = ''
            self.WHITE = ''
            self.BOLD = ''
            self.RESET = ''

# Initialize colors
C = Colors()

RANDOM_PROMPTS = [
    "Explain Bitcoin using game theory and incentive design",
    "Why does Bitcoin have value without physical backing? Compare with gold",
    "Explain blockchain security by analyzing real attack vectors",
    "Explain Ethereum from a computer science perspective, not history",
    "Break down how the Ethereum Virtual Machine (EVM) works internally",
    "What happens step-by-step when an Ethereum transaction is sent?",
    "Compare Ethereum and Solana at the protocol and consensus level",
    "Explain gas fees using network congestion and bidding mechanics",
    "Explain DeFi from a protocol builder's perspective",
    "How do Automated Market Makers work? Explain x*y=k with examples",
    "Explain impermanent loss with real numerical calculations",
    "What hidden risks exist in yield farming that most users ignore?",
    "Explain crypto market cycles using investor psychology",
    "Why do most crypto traders lose money? Be brutally honest",
    "Explain support and resistance using liquidity zones, not lines",
    "How do whales manipulate markets without illegal activity?",
    "Analyze tokenomics like a venture capitalist",
    "What makes token inflation healthy versus destructive?",
    "Explain vesting schedules and their impact on retail investors",
    "How to identify bad tokenomics before a project launches",
    "Explain common crypto scams with real attack flows",
    "How do smart contract exploits actually happen step-by-step?",
    "Explain hot wallets vs cold wallets using threat modeling",
    "Design a personal crypto security system from scratch",
    "Explain Web3 without buzzwords or marketing hype",
    "What problems does Web3 fail to solve?",
    "Is decentralization always beneficial? Give counter-examples",
    "Why will most crypto projects fail in the next market cycle",
    "What are the strongest arguments against cryptocurrency?",
    "If crypto disappeared tomorrow, what technologies would survive?"
]


def print_line(char="=", length=50):
    """Print a decorative line"""
    print(f"{C.CYAN}{C.BOLD}{char * length}{C.RESET}")

def print_header(text):
    """Print centered header text"""
    padding = (50 - len(text)) // 2
    print(f"{C.CYAN}{C.BOLD}{' ' * padding}{text}{C.RESET}")

def print_success(message):
    """Print success message"""
    print(f"{C.GREEN}{C.BOLD}[SUCCESS]{C.RESET} {message}")

def print_error(message):
    """Print error message"""
    print(f"{C.RED}{C.BOLD}[ERROR]{C.RESET} {message}")

def print_info(message):
    """Print info message"""
    print(f"{C.YELLOW}{C.BOLD}[INFO]{C.RESET} {message}")

def print_waiting(message):
    """Print waiting message"""
    print(f"{C.BLUE}{C.BOLD}[WAITING]{C.RESET} {message}")

def print_account(index, message):
    """Print account specific message"""
    print(f"{C.MAGENTA}{C.BOLD}[ACCOUNT {index}]{C.RESET} {message}")

def show_banner():
    """Display the main menu"""
    print()
    print_line("=")
    print(f"{C.MAGENTA}{C.BOLD}        MINARA AI CHAT BOT{C.RESET}")
    print(f"{C.YELLOW}{C.BOLD}        Created by Kazuha  VIP Only{C.RESET}")
    print_line("=")
    print()

def load_tokens():
    """Load multiple tokens from file - one token per line"""
    tokens = []
    try:
        with open("token.txt", "r") as f:
            lines = f.readlines()
            for line in lines:
                token = line.strip()
                if token:
                    if token.startswith("Bearer "):
                        tokens.append(token)
                    else:
                        tokens.append(f"Bearer {token}")
        
        if tokens:
            print_success(f"Loaded {len(tokens)} token(s) from token.txt")
            return tokens
        else:
            print_error("No tokens found in token.txt")
            return None
    except FileNotFoundError:
        print_error("token.txt not found")
        return None

def get_headers(token):
    """Get request headers"""
    return {
        "accept": "application/json",
        "authorization": token,
        "content-type": "application/json",
        "origin": "https://minara.ai",
        "referer": "https://minara.ai/",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36"
    }

def get_user_info(token):
    """Get user information from API"""
    headers = get_headers(token)
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        if response.status_code in [200, 304]:
            return response.json()
        else:
            return None
    except Exception as e:
        return None

def validate_accounts(tokens):
    """Validate all tokens and return account info list"""
    accounts = []
    print()
    print_line("=")
    print(f"{C.CYAN}{C.BOLD}       VALIDATING ACCOUNTS{C.RESET}")
    print_line("=")
    print()
    
    for i, token in enumerate(tokens, 1):
        print_info(f"Validating account {i}/{len(tokens)}...")
        user_info = get_user_info(token)
        
        if user_info:
            user_id = user_info.get("_id") or user_info.get("id")
            display_name = user_info.get("displayName", "Unknown")
            username = user_info.get("username", "Unknown")
            credit = user_info.get("creditBalance", {})
            remaining = credit.get("remaining", "0")
            
            accounts.append({
                "index": i,
                "token": token,
                "user_info": user_info,
                "user_id": user_id,
                "display_name": display_name,
                "username": username,
                "remaining": remaining,
                "valid": True
            })
            print_success(f"Account {i}: {display_name} (@{username}) - Credits: {remaining}")
        else:
            accounts.append({
                "index": i,
                "token": token,
                "valid": False
            })
            print_error(f"Account {i}: Invalid token or connection failed")
    
    valid_count = sum(1 for acc in accounts if acc["valid"])
    print()
    print_line("-")
    print(f"{C.GREEN}{C.BOLD}Valid Accounts: {valid_count}/{len(tokens)}{C.RESET}")
    print_line("-")
    
    return accounts

def display_profile(user_info, account_index=None):
    """Display user profile information"""
    print()
    print_line("=")
    if account_index:
        print(f"{C.MAGENTA}{C.BOLD}       ACCOUNT {account_index} - PROFILE{C.RESET}")
    else:
        print(f"{C.MAGENTA}{C.BOLD}           PROFILE INFORMATION{C.RESET}")
    print_line("=")
    print()
    
    display_name = user_info.get("displayName", "Unknown")
    username = user_info.get("username", "Unknown")
    email = user_info.get("email", "Unknown")
    uid = user_info.get("UID", "N/A")
    country = user_info.get("country", "N/A")
    
    print(f"  {C.YELLOW}{C.BOLD}Name:{C.RESET}     {C.WHITE}{display_name}{C.RESET}")
    print(f"  {C.YELLOW}{C.BOLD}Username:{C.RESET} {C.WHITE}@{username}{C.RESET}")
    print(f"  {C.YELLOW}{C.BOLD}Email:{C.RESET}    {C.WHITE}{email}{C.RESET}")
    print(f"  {C.YELLOW}{C.BOLD}UID:{C.RESET}      {C.WHITE}{uid}{C.RESET}")
    print(f"  {C.YELLOW}{C.BOLD}Country:{C.RESET}  {C.WHITE}{country}{C.RESET}")
    
    print()
    print_line("-")
    print(f"{C.GREEN}{C.BOLD}           CREDIT BALANCE{C.RESET}")
    print_line("-")
    print()
    
    credit = user_info.get("creditBalance", {})
    total = credit.get("total", "0")
    remaining = credit.get("remaining", "0")
    package_credit = credit.get("package", "0")
    reward = credit.get("reward", "0")
    
    try:
        total_num = float(total)
        remaining_num = float(remaining)
        if total_num > 0:
            usage_percent = ((total_num - remaining_num) / total_num) * 100
        else:
            usage_percent = 0
    except:
        usage_percent = 0
    
    try:
        remaining_display = f"{float(remaining):.2f}"
        total_display = f"{float(total):.2f}"
    except:
        remaining_display = remaining
        total_display = total
    
    print(f"  {C.GREEN}{C.BOLD}Total:{C.RESET}     {C.WHITE}{total_display}{C.RESET}")
    print(f"  {C.GREEN}{C.BOLD}Remaining:{C.RESET} {C.WHITE}{remaining_display}{C.RESET}")
    print(f"  {C.GREEN}{C.BOLD}Package:{C.RESET}   {C.WHITE}{package_credit}{C.RESET}")
    print(f"  {C.GREEN}{C.BOLD}Reward:{C.RESET}    {C.WHITE}{reward}{C.RESET}")
    print(f"  {C.GREEN}{C.BOLD}Used:{C.RESET}      {C.WHITE}{usage_percent:.1f}%{C.RESET}")
    
    print()
    print_line("-")
    print(f"{C.BLUE}{C.BOLD}           SUBSCRIPTION{C.RESET}")
    print_line("-")
    print()
    
    sub = user_info.get("subscription", {})
    plan_name = sub.get("planName", "Free")
    plan_interval = sub.get("planInterval", "N/A")
    start_time = sub.get("subStartTime", "N/A")
    end_time = sub.get("subEndTime", "N/A")
    
    if start_time != "N/A" and len(start_time) >= 10:
        start_time = start_time[:10]
    if end_time != "N/A" and len(end_time) >= 10:
        end_time = end_time[:10]
    
    print(f"  {C.BLUE}{C.BOLD}Plan:{C.RESET}      {C.WHITE}{plan_name}{C.RESET}")
    print(f"  {C.BLUE}{C.BOLD}Interval:{C.RESET}  {C.WHITE}{plan_interval}{C.RESET}")
    print(f"  {C.BLUE}{C.BOLD}Start:{C.RESET}     {C.WHITE}{start_time}{C.RESET}")
    print(f"  {C.BLUE}{C.BOLD}End:{C.RESET}       {C.WHITE}{end_time}{C.RESET}")
    
    print()
    print_line("-")
    print(f"{C.MAGENTA}{C.BOLD}           INVITE CODE{C.RESET}")
    print_line("-")
    print()
    
    invite = user_info.get("inviteCode", {})
    if invite:
        code = invite.get("code", "N/A")
        invite_count = invite.get("inviteCount", 0)
        print(f"  {C.MAGENTA}{C.BOLD}Code:{C.RESET}      {C.WHITE}{code}{C.RESET}")
        print(f"  {C.MAGENTA}{C.BOLD}Invites:{C.RESET}   {C.WHITE}{invite_count}{C.RESET}")
    else:
        print(f"  {C.WHITE}No invite code available{C.RESET}")
    
    print()
    print_line("=")
    print()

def display_all_profiles(accounts):
    """Display all account profiles"""
    valid_accounts = [acc for acc in accounts if acc["valid"]]
    
    if not valid_accounts:
        print_error("No valid accounts to display")
        return
    
    for acc in valid_accounts:
        user_info = get_user_info(acc["token"])
        if user_info:
            display_profile(user_info, acc["index"])

def join_waitlist(token, account_index=None):
    """Join the waitlist"""
    headers = get_headers(token)
    payload = {"type": "copilot"}
    try:
        response = requests.post(f"{BASE_URL}/waitlist/add-to-waitlist", headers=headers, json=payload)
        if response.status_code == 201:
            data = response.json()
            if account_index:
                print_account(account_index, f"{C.GREEN}Waitlist joined: {data.get('message', 'Success')}{C.RESET}")
            else:
                print_success(data.get('message', 'Waitlist joined successfully'))
            return True
        else:
            if account_index:
                print_account(account_index, f"{C.RED}Failed: Status {response.status_code}{C.RESET}")
            else:
                print_error(f"Status: {response.status_code}")
            try:
                error_data = response.json()
                print_info(str(error_data))
            except:
                pass
            return False
    except Exception as e:
        print_error(str(e))
        return False

def join_waitlist_all(accounts):
    """Join waitlist for all valid accounts"""
    valid_accounts = [acc for acc in accounts if acc["valid"]]
    
    if not valid_accounts:
        print_error("No valid accounts")
        return
    
    print()
    print_line("=")
    print(f"{C.CYAN}{C.BOLD}    JOINING WAITLIST - ALL ACCOUNTS{C.RESET}")
    print_line("=")
    print()
    
    success = 0
    failed = 0
    
    for acc in valid_accounts:
        if join_waitlist(acc["token"], acc["index"]):
            success += 1
        else:
            failed += 1
        time.sleep(1)
    
    print()
    print_line("-")
    print(f"{C.GREEN}{C.BOLD}Success: {success}{C.RESET} | {C.RED}{C.BOLD}Failed: {failed}{C.RESET}")
    print_line("-")

def chat_with_ai(token, user_id, account_index=None, show_response=True):
    """Send a chat message to AI"""
    headers = get_headers(token)
    headers["accept"] = "text/event-stream"
    headers["cache-control"] = "no-cache"
    
    prompt = random.choice(RANDOM_PROMPTS)
    chat_id = str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    timestamp = int(time.time() * 1000)
    nonce = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
    
    payload = {
        "chatId": chat_id,
        "userId": user_id,
        "thinking": True,
        "mode": "fast",
        "deepresearch": False,
        "parentMessageId": None,
        "message": {
            "id": message_id,
            "content": prompt,
            "role": "user"
        },
        "userTimezone": "Asia/Calcutta"
    }
    
    if show_response:
        print()
        print_line("-")
        if account_index:
            print(f"{C.MAGENTA}{C.BOLD}[ACCOUNT {account_index}]{C.RESET}")
        print(f"{C.YELLOW}{C.BOLD}[PROMPT]{C.RESET} {C.WHITE}{prompt[:60]}...{C.RESET}")
        print_waiting("Getting AI response...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat?_t={timestamp}&_nonce={nonce}",
            headers=headers,
            json=payload,
            stream=True,
            timeout=120
        )
        
        if response.status_code == 201:
            full_response = ""
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith('0:"'):
                        text = decoded[3:-1]
                        text = text.replace('\\n', '\n')
                        full_response += text
            
            if show_response:
                if full_response:
                    clean_response = full_response.replace("<!-- FINAL_REPORT_START -->", "").strip()
                    print(f"{C.GREEN}{C.BOLD}[RESPONSE]{C.RESET} {C.WHITE}{clean_response[:200]}...{C.RESET}")
                print_success("Chat completed")
            return True
        else:
            if show_response:
                print_error(f"Chat failed: {response.status_code}")
            return False
    except Exception as e:
        if show_response:
            print_error(str(e))
        return False

def auto_chat_single(account, chat_count):
    """Auto chat for a single account"""
    successful = 0
    failed = 0
    
    for i in range(1, chat_count + 1):
        print()
        print(f"{C.MAGENTA}{C.BOLD}[ACCOUNT {account['index']}]{C.RESET} Chat {i}/{chat_count}")
        
        if chat_with_ai(account["token"], account["user_id"], account["index"]):
            successful += 1
        else:
            failed += 1
        
        if i < chat_count:
            delay = random.uniform(2, 4)
            time.sleep(delay)
    
    return successful, failed

def auto_chat_all(accounts):
    """Auto chat for all valid accounts"""
    valid_accounts = [acc for acc in accounts if acc["valid"]]
    
    if not valid_accounts:
        print_error("No valid accounts")
        return
    
    print()
    print_line("=")
    print(f"{C.CYAN}{C.BOLD}       AUTO CHAT - ALL ACCOUNTS{C.RESET}")
    print_line("=")
    print()
    
    print(f"{C.WHITE}Valid accounts: {len(valid_accounts)}{C.RESET}")
    print()
    
    while True:
        try:
            count_input = input(f"{C.YELLOW}{C.BOLD}How many chats per account? {C.RESET}").strip()
            chat_count = int(count_input)
            if chat_count <= 0:
                print_error("Please enter a number greater than 0")
                continue
            break
        except ValueError:
            print_error("Please enter a valid number")
            continue
    
    print()
    print_info(f"Starting {chat_count} chats for {len(valid_accounts)} accounts...")
    print_info(f"Total chats: {chat_count * len(valid_accounts)}")
    print_line("=")
    
    total_success = 0
    total_failed = 0
    account_results = []
    
    for acc in valid_accounts:
        print()
        print_line("-")
        print(f"{C.MAGENTA}{C.BOLD}Starting Account {acc['index']}: {acc['display_name']}{C.RESET}")
        print_line("-")
        
        success, failed = auto_chat_single(acc, chat_count)
        total_success += success
        total_failed += failed
        account_results.append({
            "index": acc["index"],
            "name": acc["display_name"],
            "success": success,
            "failed": failed
        })
        
        if acc != valid_accounts[-1]:
            delay = random.uniform(3, 6)
            print()
            print_info(f"Switching to next account in {delay:.1f} seconds...")
            time.sleep(delay)
    
    print()
    print_line("=")
    print(f"{C.GREEN}{C.BOLD}         AUTO CHAT COMPLETED{C.RESET}")
    print_line("=")
    print()
    print(f"{C.CYAN}{C.BOLD}Account-wise Results:{C.RESET}")
    print()
    
    for result in account_results:
        print(f"  {C.MAGENTA}Account {result['index']}{C.RESET} ({result['name']}): {C.GREEN}{result['success']} success{C.RESET}, {C.RED}{result['failed']} failed{C.RESET}")
    
    print()
    print_line("-")
    print(f"  {C.GREEN}{C.BOLD}Total Successful:{C.RESET} {C.WHITE}{total_success}{C.RESET}")
    print(f"  {C.RED}{C.BOLD}Total Failed:{C.RESET}     {C.WHITE}{total_failed}{C.RESET}")
    print(f"  {C.YELLOW}{C.BOLD}Grand Total:{C.RESET}      {C.WHITE}{total_success + total_failed}{C.RESET}")
    print_line("=")

def auto_chat_select(accounts):
    """Auto chat with account selection option"""
    valid_accounts = [acc for acc in accounts if acc["valid"]]
    
    if not valid_accounts:
        print_error("No valid accounts")
        return
    
    print()
    print_line("=")
    print(f"{C.CYAN}{C.BOLD}       SELECT ACCOUNT FOR CHAT{C.RESET}")
    print_line("=")
    print()
    
    print(f"  {C.GREEN}{C.BOLD}[0]{C.RESET} {C.WHITE}All Accounts{C.RESET}")
    for acc in valid_accounts:
        print(f"  {C.GREEN}{C.BOLD}[{acc['index']}]{C.RESET} {C.WHITE}{acc['display_name']} (@{acc['username']}) - Credits: {acc['remaining']}{C.RESET}")
    
    print()
    
    while True:
        try:
            choice = input(f"{C.YELLOW}{C.BOLD}Select account (0 for all): {C.RESET}").strip()
            choice_num = int(choice)
            
            if choice_num == 0:
                auto_chat_all(accounts)
                return
            
            selected = None
            for acc in valid_accounts:
                if acc["index"] == choice_num:
                    selected = acc
                    break
            
            if selected:
                print()
                while True:
                    try:
                        count_input = input(f"{C.YELLOW}{C.BOLD}How many chats? {C.RESET}").strip()
                        chat_count = int(count_input)
                        if chat_count <= 0:
                            print_error("Please enter a number greater than 0")
                            continue
                        break
                    except ValueError:
                        print_error("Please enter a valid number")
                        continue
                
                print()
                print_line("=")
                print(f"{C.CYAN}{C.BOLD}Starting chats for: {selected['display_name']}{C.RESET}")
                print_line("=")
                
                success, failed = auto_chat_single(selected, chat_count)
                
                print()
                print_line("=")
                print(f"{C.GREEN}{C.BOLD}         COMPLETED{C.RESET}")
                print_line("=")
                print(f"  {C.GREEN}{C.BOLD}Successful:{C.RESET} {C.WHITE}{success}{C.RESET}")
                print(f"  {C.RED}{C.BOLD}Failed:{C.RESET}     {C.WHITE}{failed}{C.RESET}")
                print_line("=")
                return
            else:
                print_error("Invalid account number")
        except ValueError:
            print_error("Please enter a valid number")

def show_menu(account_count):
    """Display the main menu"""
    print()
    print_line("=")
    print(f"{C.MAGENTA}{C.BOLD}     MENU ({account_count} Accounts Loaded){C.RESET}")
    print_line("=")
    print()
    print(f"  {C.GREEN}{C.BOLD}[1]{C.RESET} {C.WHITE}Join Waitlist (All Accounts){C.RESET}")
    print(f"  {C.BLUE}{C.BOLD}[2]{C.RESET} {C.WHITE}Chat with AI (Select/All){C.RESET}")
    print(f"  {C.YELLOW}{C.BOLD}[3]{C.RESET} {C.WHITE}View All Profiles{C.RESET}")
    print(f"  {C.RED}{C.BOLD}[4]{C.RESET} {C.WHITE}Exit{C.RESET}")
    print()
    print_line("=")
    print()

def main():
    """Main function"""
    if sys.platform == "win32":
        os.system('cls')
    else:
        os.system('clear')
    
    show_banner()
    
    tokens = load_tokens()
    if not tokens:
        print()
        print_error("Please add your Bearer tokens to token.txt (one per line)")
        print()
        print(f"{C.YELLOW}Example token.txt format:{C.RESET}")
        print(f"{C.WHITE}Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...{C.RESET}")
        print(f"{C.WHITE}Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...{C.RESET}")
        input("\nPress Enter to exit...")
        return
    
    accounts = validate_accounts(tokens)
    
    valid_accounts = [acc for acc in accounts if acc["valid"]]
    if not valid_accounts:
        print_error("No valid accounts found. Please check your tokens.")
        input("\nPress Enter to exit...")
        return
    
    print()
    print_success(f"Ready with {len(valid_accounts)} valid account(s)")
    
    while True:
        show_menu(len(valid_accounts))
        choice = input(f"{C.CYAN}{C.BOLD}Select option: {C.RESET}").strip()
        
        if choice == "1":
            join_waitlist_all(accounts)
        
        elif choice == "2":
            auto_chat_select(accounts)
        
        elif choice == "3":
            display_all_profiles(accounts)
        
        elif choice == "4":
            print()
            print(f"{C.MAGENTA}{C.BOLD}[GOODBYE]{C.RESET} Thanks for using Minara AI Bot!")
            print(f"{C.YELLOW}{C.BOLD}                   Created by Kazuha{C.RESET}")
            print()
            break
        
        else:
            print_error("Invalid option, please try again")
        
        input(f"\n{C.CYAN}Press Enter to continue...{C.RESET}")

if __name__ == "__main__":
    main()