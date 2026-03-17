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

# --- CONFIGURATION (ပိုမိုတည်ငြိမ်အောင် ပြင်ဆင်ထားသည်) ---
SECRET_SALT = "ohmygod@123"
PING_THREADS = 3       # Thread အရေအတွက် လျှော့ချခြင်းဖြင့် ပိုငြိမ်စေသည်
PING_INTERVAL = 1.0    # ၁ စက္ကန့်လျှင် ၁ ကြိမ်နှုန်း (Router Spam မဖြစ်စေရန်)
RETRY_DELAY = 5        # Connection ပြတ်ပါက ၅ စက္ကန့်ခြားပြီး ပြန်စစ်ရန်

def get_stable_id():
    """Device တစ်ခုအတွက် ပုံသေဖြစ်နေမည့် ID ကို ထုတ်ပေးခြင်း"""
    try:
        serial = os.popen("getprop ro.serialno").read().strip()
        if not serial:
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
    """အမှန်တကယ် အင်တာနက် ရှိမရှိကို ၃ ကြိမ်စစ်ဆေးခြင်း (Stability Check)"""
    for _ in range(3):
        try:
            # Timeout ကို ၅ စက္ကန့်အထိ တိုးမြှင့်ထားသည်
            response = requests.get("http://www.google.com", timeout=5)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(2) # တစ်ခါမရရင် ၂ စက္ကန့်စောင့်ပြီး ပြန်စမ်းမယ်
    return False

def high_speed_ping(auth_link, session, sid):
    """Background မှာ Session ကို အသက်ဆက်ပေးမည့် Thread"""
    while True:
        try:
            session.get(auth_link, timeout=5)
            # အောက်ပါစာကြောင်းသည် Terminal တွင် ID ပြောင်းလဲမှုကို စောင့်ကြည့်ရန်ဖြစ်သည်
            print(f"[{time.strftime('%H:%M:%S')}] Pinging SID: {sid} (Active)   ", end='\r')
        except:
            break # Connection ပြတ်သွားလျှင် Thread ကို ရပ်မည်
        time.sleep(PING_INTERVAL)

def start_process():
    if not verify_activation():
        return

    print(f"[{time.strftime('%H:%M:%S')}] Turbo Script Initializing...")
    
    while True:
        # ၁။ လက်ရှိ အင်တာနက် အခြေအနေကို အရင်စစ်ဆေးမည်
        if check_real_internet():
            print(f"[{time.strftime('%H:%M:%S')}] Connection Stable. Monitoring... ", end='\r')
            time.sleep(10) # ၁၀ စက္ကန့်တစ်ခါပဲ အေးဆေးစစ်မည်
            continue

        # ၂။ အင်တာနက် တကယ်ပြတ်သွားမှသာ Login အသစ်ပြန်ဝင်မည်
        print(f"\n[{time.strftime('%H:%M:%S')}] Connection Lost. Re-authenticating...")
        session = requests.Session()
        test_url = "http://connectivitycheck.gstatic.com/generate_204"
        
        try:
            r = requests.get(test_url, allow_redirects=True, timeout=10)
            portal_url = r.url
            
            # Google ကို တန်းရောက်မသွားဘဲ Portal Page မှာပဲ ရှိနေမှ ဆက်လုပ်မည်
            if portal_url != test_url:
                parsed_portal = urlparse(portal_url)
                portal_host = f"{parsed_portal.scheme}://{parsed_portal.netloc}"
                
                # Portal Link မှ Redirect Link ကို ရှာဖွေခြင်း
                r1 = session.get(portal_url, verify=False, timeout=10)
                path_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", r1.text)
                next_url = urljoin(portal_url, path_match.group(1)) if path_match else portal_url
                
                r2 = session.get(next_url, verify=False, timeout=15)
                
                # Session ID (SID) ကို ထုတ်ယူခြင်း
                sid = parse_qs(urlparse(r2.url).query).get('sessionId', [None])[0]
                if not sid:
                    sid_match = re.search(r'sessionId=([a-zA-Z0-9]+)', r2.text)
                    sid = sid_match.group(1) if sid_match else None
                
                if sid:
                    # Voucher Activation (Bypass လုပ်ရန် ကြိုးစားခြင်း)
                    voucher_api = f"{portal_host}/api/auth/voucher/"
                    try:
                        session.post(voucher_api, json={'accessCode': '123456', 'sessionId': sid, 'apiVersion': 1}, timeout=5)
                    except: pass

                    # Auth Ping Link တည်ဆောက်ခြင်း
                    params = parse_qs(parsed_portal.query)
                    gw_addr = params.get('gw_address', ['192.168.60.1'])[0]
                    gw_port = params.get('gw_port', ['2060'])[0]
                    auth_link = f"http://{gw_addr}:{gw_port}/wifidog/auth?token={sid}&phonenumber=12345"

                    print(f"[*] New SID Found: {sid}")
                    
                    # Background Threads စတင်ခြင်း
                    for _ in range(PING_THREADS):
                        t = threading.Thread(target=high_speed_ping, args=(auth_link, session, sid), daemon=True)
                        t.start()

                    # အင်တာနက် ပြန်ရသွားပြီလားဆိုတာကို ခဏစောင့်စစ်မည်
                    time.sleep(5)
            
        except Exception as e:
            # Error တက်ပါက ခဏနားပြီးမှ ပြန်စမည်
            time.sleep(RETRY_DELAY)

if __name__ == "__main__":
    try:
        start_process()
    except KeyboardInterrupt:
        print("\nScript Stopped by User.")
