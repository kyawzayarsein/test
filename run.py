import requests
import re
import urllib3
import time
import threading
import hashlib
import os
import platform
from urllib.parse import urlparse, parse_qs, urljoin

# Warning ပိတ်ခြင်း
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION (အကောင်းဆုံး ချိန်ညှိချက်များ) ---
SECRET_SALT = "ohmygod@123"
PING_THREADS = 2        # ၂ ခုဆိုလျှင် လုံလောက်ပြီး Battery သက်သာစေသည်
PING_INTERVAL = 1.5     # ၁.၅ စက္ကန့်ခြား တစ်ခါ Ping မည် (Router Block မဖြစ်စေရန်)
CHECK_INTERVAL = 2      # ၂ စက္ကန့်ခြား တစ်ခါ အင်တာနက် ရှိ/မရှိ စစ်မည်
TIMEOUT_SEC = 3         # Connection မရလျှင် ၃ စက္ကန့်အတွင်း လက်လျှော့ပြီး ပြန်ချိတ်မည်

def get_stable_id():
    """Device တစ်ခုအတွက် ပုံသေဖြစ်နေမည့် ID ကို ထုတ်ပေးခြင်း"""
    try:
        serial = os.popen("getprop ro.serialno").read().strip()
        if not serial or serial == "":
            serial = os.popen("getprop ro.build.display.id").read().strip()
    except:
        serial = "DEFAULT_NODE"

    fixed_hash = hashlib.md5(serial.encode()).hexdigest()[:10].upper()
    return f"TRB-{fixed_hash}"

def verify_activation():
    device_id = get_stable_id()
    key_file = os.path.join(os.path.expanduser("~"), ".turbo_license")
    
    print(f"DEVICE ID: {device_id}")
    
    if os.path.exists(key_file):
        with open(key_file, "r") as f:
            saved_key = f.read().strip()
    else:
        saved_key = None

    correct_key = hashlib.sha256(f"{device_id}{SECRET_SALT}".encode()).hexdigest()[:12].upper()

    if saved_key == correct_key:
        print("Status: Verified ✔")
        return True
    else:
        print("\nThis device is not activated.")
        print(f"Please copy and send your ID: {device_id}")
        input_key = input("Enter Activation Key: ").strip().upper()
        
        if input_key == correct_key:
            with open(key_file, "w") as f:
                f.write(input_key)
            print("Activation Successful! Restarting...")
            time.sleep(1)
            return True
        else:
            print("Invalid Key! Access Denied.")
            return False

def check_real_internet():
    """အမှန်တကယ် အင်တာနက်ထွက်မထွက် စစ်ဆေးခြင်း"""
    try:
        # ၃ စက္ကန့်အတွင်း Response မရရင် လိုင်းပြတ်တယ်လို့ သတ်မှတ်မယ်
        return requests.get("http://www.google.com", timeout=TIMEOUT_SEC).status_code == 200
    except: 
        return False

def high_speed_ping(auth_link, session, sid):
    """Background မှာ အမြဲတမ်း Connection ကို Keep-alive လုပ်ပေးမည့် Function"""
    while True:
        try:
            # Heartbeat ပို့ခြင်း
            session.get(auth_link, timeout=TIMEOUT_SEC)
            print(f"[{time.strftime('%H:%M:%S')}] Heartbeat: {sid} (Active)   ", end='\r')
        except: 
            # အမှားတက်ရင် Thread ကို ရပ်ပြီး အပြင် Loop မှာ ပြန်ချိတ်မယ်
            break
        time.sleep(PING_INTERVAL)

def start_process():
    if not verify_activation():
        return

    print(f"[{time.strftime('%H:%M:%S')}] Turbo Script Initializing...")
    
    while True:
        session = requests.Session()
        test_url = "http://connectivitycheck.gstatic.com/generate_204"
        
        try:
            r = requests.get(test_url, allow_redirects=True, timeout=TIMEOUT_SEC)
            
            # အင်တာနက်ရှိနေရင် ခေတ္တစောင့်ပြီး ပြန်စစ်မည်
            if r.url == test_url:
                if check_real_internet():
                    print(f"[{time.strftime('%H:%M:%S')}] Internet OK. Monitoring...        ", end='\r')
                    time.sleep(CHECK_INTERVAL)
                    continue
            
            # Login Page သို့ Redirect ဖြစ်သွားလျှင် (လိုင်းပြတ်သွားလျှင်)
            print(f"\n[{time.strftime('%H:%M:%S')}] Redirect Detected. Re-logging...")
            portal_url = r.url
            parsed_portal = urlparse(portal_url)
            portal_host = f"{parsed_portal.scheme}://{parsed_portal.netloc}"
            
            r1 = session.get(portal_url, verify=False, timeout=10)
            path_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", r1.text)
            next_url = urljoin(portal_url, path_match.group(1)) if path_match else portal_url
            r2 = session.get(next_url, verify=False, timeout=10)
            
            # Session ID ကို ရှာခြင်း
            sid = parse_qs(urlparse(r2.url).query).get('sessionId', [None])[0]
            if not sid:
                sid_match = re.search(r'sessionId=([a-zA-Z0-9]+)', r2.text)
                sid = sid_match.group(1) if sid_match else None
            
            if sid:
                # Voucher Activation (ရှိလျှင်)
                voucher_api = f"{portal_host}/api/auth/voucher/"
                try:
                    session.post(voucher_api, json={'accessCode': '123456', 'sessionId': sid, 'apiVersion': 1}, timeout=5)
                except: pass

                # Auth Link တည်ဆောက်ခြင်း
                params = parse_qs(parsed_portal.query)
                gw_addr = params.get('gw_address', ['192.168.60.1'])[0]
                gw_port = params.get('gw_port', ['2060'])[0]
                auth_link = f"http://{gw_addr}:{gw_port}/wifidog/auth?token={sid}&phonenumber=12345"

                print(f"[*] SID: {sid} | Starting Keep-Alive Threads...")
                # Thread စတင်ခြင်း
                for _ in range(PING_THREADS):
                    t = threading.Thread(target=high_speed_ping, args=(auth_link, session, sid), daemon=True)
                    t.start()

                # အင်တာနက် ပြတ်မပြတ်ကို ၂ စက္ကန့်ခြားတစ်ခါ အမြဲစစ်နေမည်
                while check_real_internet():
                    time.sleep(CHECK_INTERVAL)
                
                print(f"\n[{time.strftime('%H:%M:%S')}] Internet Disconnected! Retrying immediately...")

        except Exception as e:
            # Error တစ်ခုခုတက်ရင် ၂ စက္ကန့်စောင့်ပြီး ပြန်ကြိုးစားမည်
            time.sleep(2)

if __name__ == "__main__":
    try:
        start_process()
    except KeyboardInterrupt:
        print("\n[!] Script Stopped by User.")
