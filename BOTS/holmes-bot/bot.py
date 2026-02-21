import os
import sys
import time
import random
import requests
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# ==================== CONFIGURATION ====================
API_BASE = "https://api.holmesai.xyz"
AGENT_SERVICE = f"{API_BASE}/agent-service"
INSTANT_GENERATE = f"{API_BASE}/agent-backend/instant_generate"

# Random data
BUSINESSES = ["Digital Assets", "Blockchain", "Cryptocurrency", "Web3", "DeFi"]
NICHES = ["Ethereum", "Bitcoin", "Solana", "Polygon", "Arbitrum"]
TONES = ["Encouraging", "Professional", "Friendly", "Analytical", "Casual"]
LEVELS = ["Entry Level", "Intermediate", "Advanced", "Expert"]
CATEGORIES = ["Social Media", "Content Creation", "Research", "Trading", "Education"]

AGENT_IMAGES = [
    "https://www-s.ucloud.cn/2025/07/7f8c40bb2cbab1afdea5e08cee99c326_1751341269786.png"
]

CHAT_PROMPTS = [
    "Hello, how are you today?",
    "What is blockchain technology?",
    "Explain DeFi in simple terms",
    "What are NFTs?",
    "How does Ethereum work?",
    "Tell me about Web3",
    "What is cryptocurrency mining?",
    "Explain smart contracts",
    "What is a DAO?",
    "How to start investing in crypto?",
    "What is staking in crypto?",
    "Explain layer 2 solutions",
    "What are meme coins?",
    "How do hardware wallets work?",
    "What is yield farming?",
    "Explain liquidity pools",
    "What is a DEX?",
    "How does proof of stake work?",
    "What are gas fees?",
    "Explain tokenomics"
]

# ==================== COLORS ====================
class C:
    R = '\033[1;91m'
    G = '\033[1;92m'
    Y = '\033[1;93m'
    B = '\033[1;94m'
    M = '\033[1;95m'
    C = '\033[1;96m'
    W = '\033[1;97m'
    E = '\033[0m'

def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""{C.C}
    ============================================================
              HOLMESAI AUTOMATION - BOT
              CREATED BY KAZUHA VIP ONLY 
    ============================================================{C.E}
    """)

def menu():
    print(f"""
    {C.G}[1]{C.W} Daily Check-In
    {C.G}[2]{C.W} Create Persona
    {C.G}[3]{C.W} Create Agent
    {C.G}[4]{C.W} Chat + Publish
    {C.G}[5]{C.W} View Personas
    {C.G}[6]{C.W} View Agents
    {C.G}[7]{C.W} View Published Posts
    {C.G}[8]{C.W} Full Automation
    {C.G}[9]{C.W} Exit
    """)

def ok(m): print(f"    {C.G}[OK]{C.W} {m}")
def err(m): print(f"    {C.R}[ERROR]{C.W} {m}")
def info(m): print(f"    {C.C}[INFO]{C.W} {m}")
def warn(m): print(f"    {C.Y}[WARN]{C.W} {m}")

# ==================== LOAD ACCOUNTS FROM .ENV ====================
def load_accounts():
    accounts = []
    
    # Check if .env exists
    if not os.path.exists(".env"):
        err(".env file not found!")
        print(f"""
    {C.Y}Create .env file with this format:{C.E}

    {C.G}# Account 1{C.E}
    {C.W}WALLET_1=0xYourWalletAddress1{C.E}
    {C.W}SESSION_1=yott_ai_session_value1{C.E}
    {C.W}LOGIN_1=login_yott_ai_value1{C.E}

    {C.G}# Account 2{C.E}
    {C.W}WALLET_2=0xYourWalletAddress2{C.E}
    {C.W}SESSION_2=yott_ai_session_value2{C.E}
    {C.W}LOGIN_2=login_yott_ai_value2{C.E}

    {C.G}# Account 3 (and so on...){C.E}
    {C.W}WALLET_3=0xYourWalletAddress3{C.E}
    {C.W}SESSION_3=yott_ai_session_value3{C.E}
    {C.W}LOGIN_3=login_yott_ai_value3{C.E}

    {C.Y}How to get tokens:{C.E}
    {C.W}1. Open holmesai.xyz in browser{C.E}
    {C.W}2. Login with wallet{C.E}
    {C.W}3. Press F12 (DevTools){C.E}
    {C.W}4. Go to Application > Cookies{C.E}
    {C.W}5. Copy yott_ai_session and login_yott_ai values{C.E}
        """)
        sys.exit(1)
    
    # Load accounts dynamically
    i = 1
    while True:
        wallet = os.getenv(f"WALLET_{i}")
        session = os.getenv(f"SESSION_{i}")
        login = os.getenv(f"LOGIN_{i}")
        
        if wallet and session and login:
            accounts.append({
                "wallet": wallet.strip(),
                "session": session.strip(),
                "login": login.strip(),
                "name": f"Account_{i}"
            })
            i += 1
        else:
            break
    
    if not accounts:
        err("No accounts found in .env")
        print(f"""
    {C.Y}Make sure .env has proper format:{C.E}
    {C.W}WALLET_1=0x...{C.E}
    {C.W}SESSION_1=MTc2NTgx...{C.E}
    {C.W}LOGIN_1=86c5a9f9-...{C.E}
        """)
        sys.exit(1)
    
    return accounts

# ==================== API REQUEST ====================
def get_headers(session_tok, login_tok):
    cookie = f"yott_ai_session={session_tok}; login_yott_ai={login_tok}"
    return {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "connection": "keep-alive",
        "content-type": "application/json",
        "cookie": cookie,
        "host": "api.holmesai.xyz",
        "origin": "https://www.holmesai.xyz",
        "referer": "https://www.holmesai.xyz/",
        "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36"
    }

def api_request(acc, payload):
    try:
        headers = get_headers(acc["session"], acc["login"])
        r = requests.post(AGENT_SERVICE, json=payload, headers=headers, timeout=30)
        return r.json()
    except Exception as e:
        err(f"Request failed: {e}")
        return None

def api_chat(acc, payload):
    try:
        headers = get_headers(acc["session"], acc["login"])
        r = requests.post(INSTANT_GENERATE, json=payload, headers=headers, timeout=60)
        return r.json()
    except Exception as e:
        err(f"Chat failed: {e}")
        return None

# ==================== FUNCTIONS ====================
def checkin(acc):
    info(f"Check-in: {acc['wallet'][:12]}...{acc['wallet'][-6:]}")
    payload = {"Action": "CheckIn", "UserId": acc["wallet"]}
    r = api_request(acc, payload)
    
    if r:
        if r.get("RetCode") == 0:
            ok(f"Check-in done! Streak: {r.get('CurrentStreak', 0)} days")
            return True
        else:
            msg = r.get("Message", "")
            if "already" in msg.lower():
                warn("Already checked in today")
                return True
            err(f"Failed: {msg}")
    return False

def get_personas(acc):
    payload = {
        "Action": "GetUserPersonaListWithAllInfo",
        "UserId": acc["wallet"],
        "Page": 0,
        "Limit": 20
    }
    r = api_request(acc, payload)
    if r and r.get("RetCode") == 0:
        return r.get("Personas", [])
    return []

def create_persona(acc):
    name = f"Persona_{random.randint(1000,9999)}"
    info(f"Creating persona: {name}")
    
    payload = {
        "Action": "CreatePersona",
        "UserId": acc["wallet"],
        "PersonaName": name,
        "Business": random.choice(BUSINESSES),
        "Niche": random.choice(NICHES),
        "Tone": random.choice(TONES),
        "Level": random.choice(LEVELS),
        "KnowledgeBaseId": 0,
        "Prompt": ""
    }
    
    r = api_request(acc, payload)
    if r and r.get("RetCode") == 0:
        pid = r.get("Id", 0)
        ok(f"Persona created! ID: {pid}")
        return pid
    elif r:
        err(f"Failed: {r.get('Message', 'Unknown')}")
    return None

def get_agents(acc):
    payload = {"Action": "GetUserAgentList", "UserId": acc["wallet"]}
    r = api_request(acc, payload)
    if r and r.get("RetCode") == 0:
        return r.get("Agents", [])
    return []

def create_agent(acc, persona_id):
    name = f"Agent_{random.randint(1000,9999)}"
    info(f"Creating agent: {name}")
    
    desc = """You are an X Post Publisher. Your task is to regularly create original posts that reflect the user's typical voice, communication style, and thematic preferences. Posts should feel natural, not overly polished. Your agent will automatically generate new posts based on your persona, with at least [2 hours] between each one, up to [10] posts per day using [english]"""
    
    payload = {
        "Action": "CreateAgent",
        "UserId": acc["wallet"],
        "AgentName": name,
        "ImgUrl": random.choice(AGENT_IMAGES),
        "Category": random.choice(CATEGORIES),
        "Description": desc,
        "PersonaId": persona_id
    }
    
    r = api_request(acc, payload)
    if r and r.get("RetCode") == 0:
        aid = r.get("Id", 0)
        ok(f"Agent created! ID: {aid}")
        return aid
    elif r:
        err(f"Failed: {r.get('Message', 'Unknown')}")
    return None

def get_workflow_results(acc, agent_id):
    payload = {
        "Action": "GetWorkflowResults",
        "UserId": acc["wallet"],
        "AgentId": agent_id,
        "Limit": 10,
        "Page": 0
    }
    r = api_request(acc, payload)
    if r and r.get("RetCode") == 0:
        return r.get("Results", []), r.get("Total", 0)
    return [], 0

def publish_content(acc, agent_id, content):
    info("Publishing content...")
    
    payload = {
        "Action": "CreateWorkflowResults",
        "AgentId": agent_id,
        "Title": "Instant Generate",
        "Content": content
    }
    
    r = api_request(acc, payload)
    if r and r.get("RetCode") == 0:
        pid = r.get("Id", 0)
        ok(f"Published! Post ID: {pid}")
        return pid
    elif r:
        err(f"Publish failed: {r.get('Message', 'Unknown')}")
    return None

def chat_and_publish(acc, agent_id, prompt):
    info(f"Chat: {prompt[:35]}...")
    
    payload = {
        "agent_id": agent_id,
        "chat_history": [],
        "prompt": prompt + "\n"
    }
    
    r = api_chat(acc, payload)
    
    if r and r.get("success"):
        content = r.get("output", "")
        print(f"    {C.G}[RESPONSE]{C.W} Received {C.G}{len(content)}{C.W} chars")
        
        time.sleep(1)
        pub_id = publish_content(acc, agent_id, content)
        
        if pub_id:
            return True, content
        return False, content
    elif r:
        err(f"Chat failed: {r.get('error', r.get('message', 'Unknown'))}")
    return False, None

def show_personas(personas):
    if not personas:
        warn("No personas")
        return
    print(f"\n    {C.C}{'='*55}{C.E}")
    print(f"    {C.Y}PERSONAS{C.E}")
    print(f"    {C.C}{'='*55}{C.E}")
    for i, p in enumerate(personas, 1):
        print(f"    {C.G}[{i}] ID:{C.W} {p.get('Id')} | {C.G}Name:{C.W} {p.get('PersonaName')}")
        print(f"        {C.G}Business:{C.W} {p.get('Business')} | {C.G}Niche:{C.W} {p.get('Niche')}")
        print(f"    {C.C}{'-'*55}{C.E}")

def show_agents(agents):
    if not agents:
        warn("No agents")
        return
    print(f"\n    {C.C}{'='*55}{C.E}")
    print(f"    {C.Y}AGENTS{C.E}")
    print(f"    {C.C}{'='*55}{C.E}")
    for i, a in enumerate(agents, 1):
        print(f"    {C.G}[{i}] ID:{C.W} {a.get('Id')} | {C.G}Name:{C.W} {a.get('AgentName')}")
        print(f"        {C.G}Category:{C.W} {a.get('Category')} | {C.G}PersonaID:{C.W} {a.get('PersonaId')}")
        print(f"    {C.C}{'-'*55}{C.E}")

def show_published_posts(acc):
    agents = get_agents(acc)
    if not agents:
        warn("No agents found")
        return
    
    print(f"\n    {C.C}{'='*55}{C.E}")
    print(f"    {C.Y}SELECT AGENT TO VIEW POSTS{C.E}")
    print(f"    {C.C}{'='*55}{C.E}")
    
    for i, a in enumerate(agents, 1):
        print(f"    {C.G}[{i}]{C.W} {a.get('AgentName')} (ID: {a.get('Id')})")
    
    try:
        sel = input(f"\n    {C.Y}Select [1-{len(agents)}]:{C.E} ").strip()
        idx = int(sel) - 1
        if idx < 0 or idx >= len(agents):
            err("Invalid")
            return
    except:
        err("Invalid")
        return
    
    agent = agents[idx]
    agent_id = agent.get("Id")
    
    results, total = get_workflow_results(acc, agent_id)
    
    print(f"\n    {C.C}{'='*55}{C.E}")
    print(f"    {C.Y}PUBLISHED POSTS - Total: {total}{C.E}")
    print(f"    {C.C}{'='*55}{C.E}")
    
    if not results:
        warn("No posts found")
        return
    
    for r in results:
        status = "Published" if r.get("BlockChainUploaded") > 0 else "Pending"
        content = r.get("Content", "")[:80]
        print(f"    {C.G}ID:{C.W} {r.get('Id')}")
        print(f"    {C.G}Status:{C.W} {status}")
        print(f"    {C.G}Content:{C.W} {content}...")
        print(f"    {C.G}Created:{C.W} {r.get('CreateTime', '')[:19]}")
        if r.get("BlockChainTxHash"):
            print(f"    {C.G}TxHash:{C.W} {r.get('BlockChainTxHash')[:20]}...")
        print(f"    {C.C}{'-'*55}{C.E}")

def display_account_info(acc, personas, agents):
    print(f"\n    {C.C}{'='*55}{C.E}")
    print(f"    {C.Y}ACCOUNT INFO{C.E}")
    print(f"    {C.C}{'='*55}{C.E}")
    print(f"    {C.G}Wallet:{C.W} {acc['wallet'][:15]}...{acc['wallet'][-8:]}")
    print(f"    {C.G}Total Personas:{C.W} {len(personas)}")
    print(f"    {C.G}Total Agents:{C.W} {len(agents)}")
    
    total_posts = 0
    for a in agents:
        _, count = get_workflow_results(acc, a.get("Id"))
        total_posts += count
    
    print(f"    {C.G}Total Published:{C.W} {total_posts} posts")
    print(f"    {C.C}{'='*55}{C.E}")

def select_persona(acc, personas):
    print(f"\n    {C.C}{'='*55}{C.E}")
    print(f"    {C.Y}STEP 1: SELECT PERSONA{C.E}")
    print(f"    {C.C}{'='*55}{C.E}")
    
    for i, p in enumerate(personas, 1):
        print(f"    {C.G}[{i}]{C.W} {p.get('PersonaName')} (ID: {p.get('Id')})")
        print(f"        {C.M}Business:{C.W} {p.get('Business')} | {C.M}Niche:{C.W} {p.get('Niche')}")
    
    print(f"    {C.C}{'-'*55}{C.E}")
    
    try:
        sel = input(f"    {C.Y}Select persona [1-{len(personas)}]:{C.E} ").strip()
        idx = int(sel) - 1
        if idx < 0 or idx >= len(personas):
            err("Invalid selection")
            return None
    except:
        err("Invalid input")
        return None
    
    selected = personas[idx]
    ok(f"Selected Persona: {selected.get('PersonaName')} (ID: {selected.get('Id')})")
    return selected

def select_agent_for_persona(acc, agents, persona_id, persona_name):
    persona_agents = [a for a in agents if a.get("PersonaId") == persona_id]
    
    print(f"\n    {C.C}{'='*55}{C.E}")
    print(f"    {C.Y}STEP 2: SELECT AGENT FOR {persona_name}{C.E}")
    print(f"    {C.C}{'='*55}{C.E}")
    
    if not persona_agents:
        warn(f"No agents found for persona: {persona_name}")
        create = input(f"    {C.Y}Create new agent? [y/n]:{C.E} ").strip().lower()
        if create == 'y':
            aid = create_agent(acc, persona_id)
            if aid:
                agents = get_agents(acc)
                persona_agents = [a for a in agents if a.get("PersonaId") == persona_id]
            else:
                return None
        else:
            return None
    
    if not persona_agents:
        return None
    
    for i, a in enumerate(persona_agents, 1):
        _, posts = get_workflow_results(acc, a.get("Id"))
        print(f"    {C.G}[{i}]{C.W} {a.get('AgentName')} (ID: {a.get('Id')}) - {C.M}{posts} posts{C.E}")
    
    print(f"    {C.C}{'-'*55}{C.E}")
    
    try:
        sel = input(f"    {C.Y}Select agent [1-{len(persona_agents)}]:{C.E} ").strip()
        idx = int(sel) - 1
        if idx < 0 or idx >= len(persona_agents):
            err("Invalid selection")
            return None
    except:
        err("Invalid input")
        return None
    
    selected = persona_agents[idx]
    ok(f"Selected Agent: {selected.get('AgentName')} (ID: {selected.get('Id')})")
    return selected

def chat_with_selection(acc):
    personas = get_personas(acc)
    agents = get_agents(acc)
    
    if not personas:
        warn("No personas found! Create a persona first.")
        return
    
    display_account_info(acc, personas, agents)
    
    selected_persona = select_persona(acc, personas)
    if not selected_persona:
        return
    
    persona_id = selected_persona.get("Id")
    persona_name = selected_persona.get("PersonaName")
    
    selected_agent = select_agent_for_persona(acc, agents, persona_id, persona_name)
    if not selected_agent:
        return
    
    agent_id = selected_agent.get("Id")
    agent_name = selected_agent.get("AgentName")
    
    _, current_posts = get_workflow_results(acc, agent_id)
    
    print(f"\n    {C.C}{'='*55}{C.E}")
    print(f"    {C.Y}STEP 3: HOW MANY CHATS + PUBLISH?{C.E}")
    print(f"    {C.C}{'='*55}{C.E}")
    print(f"    {C.G}Persona:{C.W} {persona_name}")
    print(f"    {C.G}Agent:{C.W} {agent_name}")
    print(f"    {C.G}Current Posts:{C.W} {current_posts}")
    print(f"    {C.W}Each chat will be auto-published{C.E}")
    print(f"    {C.C}{'-'*55}{C.E}")
    
    try:
        num_chats = input(f"    {C.Y}Enter number of chats [1-20]:{C.E} ").strip()
        num_chats = int(num_chats)
        if num_chats < 1: num_chats = 1
        if num_chats > 20: num_chats = 20
    except:
        err("Invalid number")
        return
    
    print(f"\n    {C.C}{'='*55}{C.E}")
    print(f"    {C.Y}CONFIRMATION{C.E}")
    print(f"    {C.C}{'='*55}{C.E}")
    print(f"    {C.G}Persona:{C.W} {persona_name} (ID: {persona_id})")
    print(f"    {C.G}Agent:{C.W} {agent_name} (ID: {agent_id})")
    print(f"    {C.G}Chats:{C.W} {num_chats}")
    print(f"    {C.G}Action:{C.W} Chat + Publish each response")
    print(f"    {C.C}{'='*55}{C.E}")
    
    confirm = input(f"    {C.Y}Start? [y/n]:{C.E} ").strip().lower()
    if confirm != 'y':
        info("Cancelled")
        return
    
    print(f"\n    {C.C}{'='*55}{C.E}")
    print(f"    {C.Y}RUNNING CHAT + PUBLISH{C.E}")
    print(f"    {C.M}Persona: {persona_name} | Agent: {agent_name}{C.E}")
    print(f"    {C.C}{'='*55}{C.E}\n")
    
    success = 0
    failed = 0
    used_prompts = []
    
    for i in range(num_chats):
        print(f"    {C.M}[Chat {i+1}/{num_chats}]{C.E}")
        
        available = [p for p in CHAT_PROMPTS if p not in used_prompts]
        if not available:
            used_prompts = []
            available = CHAT_PROMPTS
        
        prompt = random.choice(available)
        used_prompts.append(prompt)
        
        result, _ = chat_and_publish(acc, agent_id, prompt)
        
        if result:
            success += 1
        else:
            failed += 1
        
        if i < num_chats - 1:
            delay = random.randint(5, 10)
            info(f"Waiting {delay}s...")
            time.sleep(delay)
        
        print()
    
    print(f"    {C.C}{'='*55}{C.E}")
    print(f"    {C.Y}SUMMARY{C.E}")
    print(f"    {C.C}{'='*55}{C.E}")
    print(f"    {C.G}Persona:{C.W} {persona_name}")
    print(f"    {C.G}Agent:{C.W} {agent_name}")
    print(f"    {C.G}Total Chats:{C.W} {num_chats}")
    print(f"    {C.G}Published:{C.W} {success}")
    print(f"    {C.R}Failed:{C.W} {failed}")
    print(f"    {C.C}{'='*55}{C.E}")

def full_auto(acc, chat_count=5):
    print(f"\n    {C.C}{'='*55}{C.E}")
    print(f"    {C.Y}FULL AUTOMATION{C.E}")
    print(f"    {C.W}Wallet: {acc['wallet'][:12]}...{acc['wallet'][-6:]}{C.E}")
    print(f"    {C.C}{'='*55}{C.E}\n")
    
    info("Step 1: Check-in")
    checkin(acc)
    time.sleep(2)
    
    info("Step 2: Persona")
    personas = get_personas(acc)
    if personas:
        pid = personas[0].get("Id")
        pname = personas[0].get("PersonaName")
        info(f"Found persona: {pname} (ID: {pid})")
    else:
        pid = create_persona(acc)
        pname = f"Persona_{pid}"
    time.sleep(2)
    
    if pid:
        info("Step 3: Agent")
        agents = get_agents(acc)
        persona_agents = [a for a in agents if a.get("PersonaId") == pid]
        
        if persona_agents:
            aid = persona_agents[0].get("Id")
            aname = persona_agents[0].get("AgentName")
            info(f"Found agent: {aname} (ID: {aid})")
        else:
            aid = create_agent(acc, pid)
            aname = f"Agent_{aid}"
        time.sleep(2)
        
        if aid:
            info(f"Step 4: Chat + Publish ({chat_count} times)")
            print(f"    {C.M}Persona: {pname} | Agent: {aname}{C.E}\n")
            
            used_prompts = []
            success = 0
            
            for i in range(chat_count):
                print(f"    {C.M}[Chat {i+1}/{chat_count}]{C.E}")
                
                available = [p for p in CHAT_PROMPTS if p not in used_prompts]
                if not available:
                    used_prompts = []
                    available = CHAT_PROMPTS
                
                prompt = random.choice(available)
                used_prompts.append(prompt)
                
                result, _ = chat_and_publish(acc, aid, prompt)
                if result:
                    success += 1
                
                if i < chat_count - 1:
                    delay = random.randint(5, 8)
                    info(f"Waiting {delay}s...")
                    time.sleep(delay)
                
                print()
            
            ok(f"Published {success}/{chat_count} posts")
    
    ok("Automation complete!")

def full_auto_with_input(acc):
    personas = get_personas(acc)
    agents = get_agents(acc)
    display_account_info(acc, personas, agents)
    
    print(f"\n    {C.Y}HOW MANY CHAT + PUBLISH?{C.E}")
    print(f"    {C.W}Each chat will be auto-published{C.E}")
    
    try:
        num = input(f"    {C.Y}Enter count [1-20]:{C.E} ").strip()
        num = int(num)
        if num < 1: num = 1
        if num > 20: num = 20
    except:
        num = 5
        info(f"Using default: {num}")
    
    confirm = input(f"    {C.Y}Run with {num} chats? [y/n]:{C.E} ").strip().lower()
    if confirm != 'y':
        info("Cancelled")
        return
    
    full_auto(acc, num)

def process(acc, ch):
    w = acc['wallet']
    print(f"    {C.W}Wallet: {w[:15]}...{w[-8:]}{C.E}")
    
    if ch == "1":
        checkin(acc)
    elif ch == "2":
        create_persona(acc)
    elif ch == "3":
        personas = get_personas(acc)
        if personas:
            print(f"\n    {C.Y}SELECT PERSONA FOR AGENT{C.E}")
            for i, p in enumerate(personas, 1):
                print(f"    {C.G}[{i}]{C.W} {p.get('PersonaName')} (ID: {p.get('Id')})")
            try:
                sel = input(f"    {C.Y}Select [1-{len(personas)}]:{C.E} ").strip()
                idx = int(sel) - 1
                if 0 <= idx < len(personas):
                    create_agent(acc, personas[idx].get("Id"))
            except:
                err("Invalid")
        else:
            warn("Create persona first!")
    elif ch == "4":
        chat_with_selection(acc)
    elif ch == "5":
        show_personas(get_personas(acc))
    elif ch == "6":
        show_agents(get_agents(acc))
    elif ch == "7":
        show_published_posts(acc)
    elif ch == "8":
        full_auto_with_input(acc)

def show_accounts(accounts):
    print(f"\n    {C.C}{'='*55}{C.E}")
    print(f"    {C.Y}LOADED ACCOUNTS{C.E}")
    print(f"    {C.C}{'='*55}{C.E}")
    for i, acc in enumerate(accounts, 1):
        print(f"    {C.G}[{i}]{C.W} {acc['wallet'][:15]}...{acc['wallet'][-8:]}")
    print(f"    {C.C}{'='*55}{C.E}")

# ==================== MAIN ====================
def main():
    banner()
    
    accounts = load_accounts()
    ok(f"Loaded {len(accounts)} account(s) from .env")
    show_accounts(accounts)
    
    while True:
        menu()
        ch = input(f"    {C.Y}Choice [1-9]:{C.E} ").strip()
        
        if ch == "9":
            info("Bye!")
            break
        
        if ch not in ["1","2","3","4","5","6","7","8"]:
            err("Invalid choice")
            continue
        
        print(f"\n    {C.C}Processing {len(accounts)} account(s)...{C.E}\n")
        
        for i, acc in enumerate(accounts, 1):
            print(f"\n    {C.M}[Account {i}/{len(accounts)}]{C.E}")
            process(acc, ch)
            
            if i < len(accounts):
                d = random.randint(3, 7)
                info(f"Wait {d}s...")
                time.sleep(d)
        
        print(f"\n    {C.G}{'='*55}{C.E}")
        ok("All done!")
        print(f"    {C.G}{'='*55}{C.E}")
        
        input(f"\n    {C.Y}Press Enter...{C.E}")
        banner()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n    {C.Y}Stopped{C.E}")

        sys.exit(0)
