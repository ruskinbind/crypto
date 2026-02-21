import os
import time
import random
import requests
from colorama import Fore, Style

from .config import QUOTE_API, WUSDC_CONTRACT

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def human_delay(min_sec=1.5, max_sec=3.5):
    """Human-like random delay"""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)

def short_delay(min_sec=0.5, max_sec=1.5):
    """Short random delay"""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)

def typing_effect(text, delay=0.02):
    """Simulate typing effect"""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(random.uniform(delay * 0.5, delay * 1.5))
    print()

def random_wait_message():
    """Random wait messages for human-like behavior"""
    messages = [
        "Processing request...",
        "Please wait...",
        "Working on it...",
        "Almost there...",
        "Executing transaction...",
        "Connecting to network...",
    ]
    return random.choice(messages)

def get_quote(token_in, token_out, amount_in):
    payload = {"tokenIn": token_in, "tokenOut": token_out, "amountIn": str(amount_in), "exactIn": True}
    headers = {"Content-Type": "application/json", "Origin": "https://testnet.axpha.io", "Referer": "https://testnet.axpha.io/"}
    try:
        response = requests.post(QUOTE_API, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def generate_device_fingerprint():
    """Generate random device fingerprint"""
    import hashlib
    random_data = f"{random.random()}{time.time()}{random.randint(1000000, 9999999)}"
    return hashlib.md5(random_data.encode()).hexdigest()

def generate_request_id():
    """Generate random request ID"""
    import string
    chars = string.ascii_letters + string.digits
    part1 = ''.join(random.choices(chars, k=10))
    part2 = ''.join(random.choices(chars, k=20))
    return f"{part1}-{part2}"

def print_header(title):
    print(Fore.CYAN + Style.BRIGHT + "=" * 50)
    print(Fore.YELLOW + Style.BRIGHT + title)
    print(Fore.CYAN + Style.BRIGHT + "=" * 50)

def print_success(msg):
    print(Fore.GREEN + Style.BRIGHT + msg)

def print_error(msg):
    print(Fore.RED + Style.BRIGHT + msg)

def print_info(msg):
    print(Fore.WHITE + Style.BRIGHT + msg)

def print_warning(msg):
    print(Fore.YELLOW + Style.BRIGHT + msg)