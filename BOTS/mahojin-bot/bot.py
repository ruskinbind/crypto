import requests
import json
import time
import random
import os
import sys

RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
CYAN = "\033[1;36m"
MAGENTA = "\033[1;35m"
WHITE = "\033[1;37m"
RESET = "\033[0m"

BASE_URL = "https://app.mahojin.ai"
TEMPLATE_ID = "NnzSzjCPR8KJgj5e96_5SQ"

EXISTING_IMAGES = [
    "https://d1kfhpz1mqv5dj.cloudfront.net/uploaded/templates/a1bd3e00-fa53-467e-8b93-d3b8d8c26485.jpeg",
    "https://assets-production.mahojin-infra.net/generation-workflow-requests/users/e4ebd46c-b3d6-469b-bd63-3e1a9832375d/228c9966-ea22-4434-8b8d-d465daeec6de/watermarked_ef1b7a62-6bfb-4824-931c-8f65b7af1783.png",
    "https://assets-production.mahojin-infra.net/generation-workflow-requests/users/c0b28a03-1229-4eb3-990c-38595a175806/059464b3-7830-476b-b58a-b059a8afa2a3/watermarked_02bc4a1f-fe40-4376-83e3-d2ff290b69ea.png",
    "https://assets-production.mahojin-infra.net/generation-workflow-requests/users/c0b28a03-1229-4eb3-990c-38595a175806/134a9190-30b3-4cc5-953f-6fe7c7d37497/watermarked_af591c18-1494-435e-aa6b-0cefcca9f0b0.png",
    "https://assets-production.mahojin-infra.net/generation-workflow-requests/users/c0b28a03-1229-4eb3-990c-38595a175806/4810a3f5-5102-470f-b4ce-140fc2004300/watermarked_69736b97-f588-4e88-bba2-4ba230ffa8dc.png",
]


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def banner():
    clear_screen()
    print(f"{CYAN}{'=' * 55}{RESET}")
    print(f"{MAGENTA}       MAHOJIN AUTO BOT - CREATED BY KAZUHA VIP ONLY{RESET}")
    print(f"{CYAN}{'=' * 55}{RESET}")
    print()


def load_tokens():
    if not os.path.exists("token.txt"):
        print(f"{RED}token.txt file not found!{RESET}")
        sys.exit(1)
    with open("token.txt", "r") as f:
        tokens = [l.strip() for l in f if l.strip()]
    if not tokens:
        print(f"{RED}No tokens in token.txt!{RESET}")
        sys.exit(1)
    return tokens


def create_session(token):
    s = requests.Session()
    s.headers.update({
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": BASE_URL,
        "referer": f"{BASE_URL}/maho-point",
        "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
    })
    s.cookies.set("__Secure-next-auth.session-token", token, domain="app.mahojin.ai", path="/")
    s.cookies.set("__Secure-next-auth.callback-url", "https://app.mahojin.ai/", domain="app.mahojin.ai", path="/")
    s.cookies.set("perf_dv6Tr4n", "1", domain="app.mahojin.ai", path="/")
    return s


def get_csrf(s):
    try:
        r = s.get(f"{BASE_URL}/api/auth/csrf", timeout=30)
        if r.status_code == 200:
            csrf = r.json().get("csrfToken", "")
            if csrf:
                s.cookies.set("__Secure-next-auth.csrf-token", csrf + "%7C" + "a" * 64, domain="app.mahojin.ai", path="/")
            return csrf
    except Exception as e:
        print(f"{RED}CSRF error: {e}{RESET}")
    return None


def get_session_info(s, csrf=None):
    try:
        if csrf:
            r = s.post(f"{BASE_URL}/api/auth/session", json={"csrfToken": csrf}, timeout=30)
            if r.status_code == 200:
                for c in r.cookies:
                    if c.name == "__Secure-next-auth.session-token":
                        s.cookies.set("__Secure-next-auth.session-token", c.value, domain="app.mahojin.ai", path="/")
                d = r.json()
                if d and "user" in d:
                    return d
    except:
        pass
    try:
        r = s.get(f"{BASE_URL}/api/auth/session", timeout=30)
        if r.status_code == 200:
            for c in r.cookies:
                if c.name == "__Secure-next-auth.session-token":
                    s.cookies.set("__Secure-next-auth.session-token", c.value, domain="app.mahojin.ai", path="/")
            d = r.json()
            if d and "user" in d:
                return d
    except:
        pass
    return None


def get_points(s):
    try:
        r = s.get(f"{BASE_URL}/api/point", timeout=30)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None


def daily_checkin(s):
    try:
        r = s.post(f"{BASE_URL}/api/user/check-in", json={"timezoneOffset": -330}, timeout=30)
        if r.status_code == 200:
            return r.json()
        print(f"{RED}Check-in: {r.status_code} | {r.text[:200]}{RESET}")
    except Exception as e:
        print(f"{RED}Check-in error: {e}{RESET}")
    return None


def generate_workflow(s, user_id, img_url):
    s.headers["referer"] = f"{BASE_URL}/workflows/{TEMPLATE_ID}"
    ts = int(time.time() * 1000)
    payload = {
        "userId": user_id,
        "steps": [
            {"id": "step-1", "stepNumber": 1, "nodeId": "1770788945177", "nodeType": "userInput",
             "data": {"prompt": "user input", "endpoint": "userInput", "uploadedFile": {"url": img_url, "name": "uploaded-file"}, "elements": [], "referenceImages": []},
             "dependencies": [], "outputs": ["step-8"]},
            {"id": "step-2", "stepNumber": 2, "nodeId": "1770789162951", "nodeType": "userInput",
             "data": {"prompt": "user input", "endpoint": "userInput", "uploadedFile": {"url": "https://d1kfhpz1mqv5dj.cloudfront.net/uploaded/images/6f4aeb79-3849-468b-b797-810473a33dbf.png", "type": "imageGeneration"}, "elements": [], "referenceImages": []},
             "dependencies": [], "outputs": []},
            {"id": "step-3", "stepNumber": 3, "nodeId": "1770789325344", "nodeType": "imageGeneration",
             "data": {"prompt": "", "endpoint": "fal-ai/nano-banana/edit", "prompts": [{"type": "textfield", "id": f"textfield-{ts}", "prompt": "Use the provided image as the fixed base image.\nApply face swap using the input face reference.\nFace swap must be identity-locked and structure-accurate.\nPreserve original facial proportions and bone structure.\nMaintain the original single directional light.\ncinematic natural light\nanalog portrait\nsubtle film grain\nmoody classic portrait\nraw texture", "orderIndex": 0}], "params": {}, "elements": [], "referenceImages": []},
             "dependencies": [], "outputs": []},
            {"id": "step-4", "stepNumber": 4, "nodeId": "1770789503583", "nodeType": "imageGeneration",
             "data": {"prompt": "", "endpoint": "fal-ai/nano-banana/edit", "prompts": [{"type": "textfield", "id": f"textfield-{ts}", "prompt": "Base image locked.\nPerform identity-locked face swap.\nAnalog cinematic.\n35mm film grain.\nCFG 6\nDenoise 0.4", "orderIndex": 0}], "params": {}, "elements": [], "referenceImages": []},
             "dependencies": [], "outputs": []},
            {"id": "step-5", "stepNumber": 5, "nodeId": "1770789871201", "nodeType": "imageGeneration",
             "data": {"prompt": "", "endpoint": "fal-ai/nano-banana/edit", "prompts": [{"type": "textfield", "id": f"textfield-{ts}", "prompt": "Strict structural reference.\nDramatic natural light.\nFace swap only.\nCFG 6\nDenoise 0.4", "orderIndex": 0}], "params": {}, "elements": [], "referenceImages": []},
             "dependencies": [], "outputs": []},
            {"id": "step-6", "stepNumber": 6, "nodeId": "1770789950558", "nodeType": "imageGeneration",
             "data": {"prompt": "", "endpoint": "fal-ai/nano-banana/edit", "prompts": [{"type": "textfield", "id": f"textfield-{ts}", "prompt": "Head turned 45 degrees.\nMoody analog cinematic.\n35mm film look.\nFace swap only.\nCFG 6\nDenoise 0.4", "orderIndex": 0}], "params": {}, "elements": [], "referenceImages": []},
             "dependencies": [], "outputs": []},
            {"id": "step-7", "stepNumber": 7, "nodeId": "1770790051202", "nodeType": "imageGeneration",
             "data": {"prompt": "", "endpoint": "fal-ai/nano-banana/edit", "prompts": [{"type": "textfield", "id": f"textfield-{ts}", "prompt": "Head 45 degrees to left.\nMoody analog cinematic.\nFace swap only.\nCFG 6\nDenoise 0.4", "orderIndex": 0}], "params": {}, "elements": [], "referenceImages": []},
             "dependencies": [], "outputs": []},
            {"id": "step-8", "stepNumber": 8, "nodeId": "1770788950569", "nodeType": "imageGeneration",
             "data": {"prompt": "", "endpoint": "fal-ai/nano-banana/edit", "prompts": [{"type": "textfield", "id": f"textfield-{ts+1}", "prompt": "Strict structural reference.\nHead 45 degrees left.\nDramatic light from camera-left.\nMoody analog cinematic.\n35mm film look.\nFace swap only.\nCFG 6\nDenoise 0.4", "orderIndex": 0}], "params": {}, "elements": [], "referenceImages": []},
             "dependencies": ["step-1"], "outputs": ["step-9"]},
            {"id": "step-9", "stepNumber": 9, "nodeId": "1770788947604", "nodeType": "userOutput",
             "data": {"prompt": "user output", "endpoint": "userOutput", "elements": [], "referenceImages": []},
             "dependencies": ["step-8"], "outputs": []}
        ],
        "templateId": TEMPLATE_ID, "costMana": 50, "scope": "public",
        "seedImageUrls": [img_url, "https://d1kfhpz1mqv5dj.cloudfront.net/uploaded/images/6f4aeb79-3849-468b-b797-810473a33dbf.png"]
    }
    try:
        r = s.post(f"{BASE_URL}/api/generate-workflow-request/generate", json=payload, timeout=60)
        if r.status_code == 200:
            return r.json()
        print(f"{RED}Generate: {r.status_code} | {r.text[:300]}{RESET}")
    except Exception as e:
        print(f"{RED}Generate error: {e}{RESET}")
    return None


def wait_done(s, rid, mw=300):
    print(f"{YELLOW}Waiting for result...{RESET}")
    st = time.time()
    while time.time() - st < mw:
        try:
            r = s.get(f"{BASE_URL}/api/templates/status/{rid}?type=generation-workflow-request", timeout=30)
            if r.status_code == 200:
                g = r.json().get("generationRequest", {})
                status = g.get("status", "?")
                if status == "done":
                    print(f"{GREEN}COMPLETED!{RESET}")
                    u = g.get("videoUrl", "")
                    if u:
                        print(f"{CYAN}Result: {u}{RESET}")
                    return True
                elif status in ["failed", "error"]:
                    print(f"{RED}FAILED!{RESET}")
                    return False
                print(f"{YELLOW}Status: {status} | {int(time.time()-st)}s{RESET}")
        except:
            pass
        time.sleep(10)
    print(f"{RED}Timeout!{RESET}")
    return False


def action_checkin(tokens):
    print(f"\n{CYAN}{'=' * 55}{RESET}")
    print(f"{GREEN}         DAILY CHECK-IN FOR ALL ACCOUNTS{RESET}")
    print(f"{CYAN}{'=' * 55}{RESET}\n")
    for i, t in enumerate(tokens, 1):
        print(f"{MAGENTA}--- Account {i}/{len(tokens)} ---{RESET}")
        s = create_session(t)
        csrf = get_csrf(s)
        if not csrf:
            print(f"{RED}CSRF failed!{RESET}\n")
            continue
        sd = get_session_info(s, csrf)
        if not sd or "user" not in sd:
            print(f"{RED}Session failed - token expired!{RESET}\n")
            continue
        u = sd["user"]
        name = u.get("name", "?")
        pts = u.get("mahoPoint", 0)
        print(f"{WHITE}User: {name}{RESET}")
        print(f"{WHITE}Points: {pts}{RESET}")
        r = daily_checkin(s)
        if r:
            a = r.get("amount", 0)
            if a > 0:
                print(f"{GREEN}Check-in SUCCESS! +{a} points{RESET}")
            else:
                print(f"{YELLOW}Response: {json.dumps(r)}{RESET}")
        else:
            print(f"{RED}Check-in FAILED!{RESET}")
        pt = get_points(s)
        if pt:
            print(f"{CYAN}Total: {pt.get('point',0)} | Free: {pt.get('freePoint',0)}{RESET}")
        print()
        time.sleep(2)
    print(f"{GREEN}All accounts done!{RESET}")
    input(f"\n{YELLOW}Press Enter to continue...{RESET}")


def action_upload(tokens):
    print(f"\n{CYAN}{'=' * 55}{RESET}")
    print(f"{GREEN}     UPLOAD IMAGE AND GENERATE FOR ALL ACCOUNTS{RESET}")
    print(f"{CYAN}{'=' * 55}{RESET}\n")
    for i, t in enumerate(tokens, 1):
        print(f"{MAGENTA}--- Account {i}/{len(tokens)} ---{RESET}")
        s = create_session(t)
        csrf = get_csrf(s)
        if not csrf:
            print(f"{RED}CSRF failed!{RESET}\n")
            continue
        sd = get_session_info(s, csrf)
        if not sd or "user" not in sd:
            print(f"{RED}Session failed - token expired!{RESET}\n")
            continue
        u = sd["user"]
        uid = u.get("userId", "")
        name = u.get("name", "?")
        print(f"{WHITE}User: {name}{RESET}")
        pt = get_points(s)
        total = 0
        if pt:
            total = pt.get("point", 0) + pt.get("freePoint", 0)
        print(f"{WHITE}Available Points: {total}{RESET}")
        if total < 50:
            print(f"{RED}Not enough points! Need 50{RESET}\n")
            continue

        img_url = random.choice(EXISTING_IMAGES)
        print(f"{GREEN}Image selected{RESET}")
        print(f"{CYAN}Submitting generation...{RESET}")

        gen = generate_workflow(s, uid, img_url)
        if not gen:
            print(f"{RED}Generation submit failed!{RESET}\n")
            continue

        rid = gen.get("requestId", "")
        msg = gen.get("message", "")

        if rid:
            print(f"{GREEN}Submitted! ID: {rid}{RESET}")
            print(f"{WHITE}Message: {msg}{RESET}")
            wait_done(s, rid)
        else:
            print(f"{RED}No request ID returned{RESET}")
            print(f"{RED}Response: {json.dumps(gen)}{RESET}")

        print()
        time.sleep(3)
    print(f"{GREEN}All accounts done!{RESET}")
    input(f"\n{YELLOW}Press Enter to continue...{RESET}")


def main():
    tokens = load_tokens()
    while True:
        banner()
        print(f"{WHITE}Loaded Accounts: {len(tokens)}{RESET}")
        print()
        print(f"{CYAN}{'=' * 55}{RESET}")
        print(f"{GREEN}  [1] CLAIM DAILY CHECK-IN{RESET}")
        print(f"{GREEN}  [2] UPLOAD IMAGE AND GENERATE{RESET}")
        print(f"{RED}  [3] EXIT{RESET}")
        print(f"{CYAN}{'=' * 55}{RESET}")
        print()
        ch = input(f"{YELLOW}Select option: {RESET}").strip()
        if ch == "1":
            action_checkin(tokens)
        elif ch == "2":
            action_upload(tokens)
        elif ch == "3":
            print(f"\n{MAGENTA}Goodbye! - KAZUHA VIP ONLY{RESET}")
            sys.exit(0)
        else:
            print(f"{RED}Invalid option!{RESET}")
            time.sleep(1)


if __name__ == "__main__":
    main()