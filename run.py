import requests
import re
import urllib3
import time
import threading
import hashlib
import os
from urllib.parse import urlparse, parse_qs, urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- GAME OPTIMIZED CONFIG ---
SECRET_SALT = "ohmygod@123"
PING_THREADS = 3        # ဂိမ်းအတွက် ၃ ခုထိ တိုးထားပေးတယ်
PING_INTERVAL = 0.5     # 0.5 စက္ကန့်ဆိုရင် လိုင်းပိုငြိမ်ပါတယ်
CHECK_INTERVAL = 1      # ၁ စက္ကန့်ခြား တစ်ခါ စစ်မယ် (ပြတ်တာနဲ့ ချက်ချင်းသိဖို့)
TIMEOUT_FAST = 2        # ၂ စက္ကန့်အတွင်း Response မလာရင် ပြန်ချိတ်မယ်

# Global Session for Speed
session = requests.Session()

def get_stable_id():
    try:
        serial = os.popen("getprop ro.serialno").read().strip()
        if not serial: serial = os.popen("getprop ro.build.display.id").read().strip()
    except: serial = "DEFAULT_NODE"
    return f"TRB-{hashlib.md5(serial.encode()).hexdigest()[:10].upper()}"

def check_real_internet():
    try:
        # ဂိမ်းဆော့ရင် latency နည်းအောင် Google 204 ကို သုံးတာ ပိုမြန်တယ်
        return session.get("http://connectivitycheck.gstatic.com/generate_204", timeout=TIMEOUT_FAST).status_code == 204
    except: return False

def high_speed_ping(auth_link, sid):
    while True:
        try:
            # တကယ် Active ဖြစ်မဖြစ် အဆက်မပြတ် စစ်နေမယ်
            session.get(auth_link, timeout=TIMEOUT_FAST)
            print(f"[{time.strftime('%H:%M:%S')}] Active: {sid[:8]}...      ", end='\r')
        except: 
            break
        time.sleep(PING_INTERVAL)

def start_process():
    device_id = get_stable_id()
    print(f"DEVICE ID: {device_id} | Status: Verified ✔")
    print(f"[{time.strftime('%H:%M:%S')}] Turbo Mode: Enabled (Low Latency)")

    while True:
        try:
            # အင်တာနက် ရှိနေရင် ခဏစောင့်မယ်
            if check_real_internet():
                time.sleep(CHECK_INTERVAL)
                continue
            
            # အင်တာနက် မရှိတော့ရင် (Redirect ဖြစ်ရင်) ချက်ချင်း စလုပ်မယ်
            print(f"\n[{time.strftime('%H:%M:%S')}] Connection Dropped! Relogging...")
            
            # ပထမဆုံး Redirect link ကို အမြန်ဖမ်းမယ်
            r = session.get("http://connectivitycheck.gstatic.com/generate_204", allow_redirects=True, timeout=5)
            portal_url = r.url
            
            if portal_url == r.request.url: # တကယ်လို့ Redirect မဖြစ်ရင်
                continue

            parsed_portal = urlparse(portal_url)
            portal_host = f"{parsed_portal.scheme}://{parsed_portal.netloc}"
            
            # Session ID ကို အမြန်ဆုံးနည်းနဲ့ ဆွဲထုတ်မယ်
            r1 = session.get(portal_url, verify=False, timeout=5)
            path_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", r1.text)
            next_url = urljoin(portal_url, path_match.group(1)) if path_match else portal_url
            
            r2 = session.get(next_url, verify=False, timeout=5)
            sid = parse_qs(urlparse(r2.url).query).get('sessionId', [None])[0]
            
            if sid:
                # Login Process
                params = parse_qs(parsed_portal.query)
                gw_addr = params.get('gw_address', ['192.168.60.1'])[0]
                gw_port = params.get('gw_port', ['2060'])[0]
                auth_link = f"http://{gw_addr}:{gw_port}/wifidog/auth?token={sid}&phonenumber=12345"

                # Background Threads စတင်မယ်
                for _ in range(PING_THREADS):
                    threading.Thread(target=high_speed_ping, args=(auth_link, sid), daemon=True).start()

                print(f"[{time.strftime('%H:%M:%S')}] Reconnected! Session: {sid[:10]}")
                
                # အင်တာနက် ပြန်ပြတ်သွားတဲ့အထိ ဒီမှာပဲ စောင့်ကြည့်နေမယ်
                while check_real_internet():
                    time.sleep(CHECK_INTERVAL)

        except Exception:
            time.sleep(1) # Error တက်ရင် ၁ စက္ကန့်ပဲ စောင့်ပြီး ပြန်ကြိုးစားမယ်

if __name__ == "__main__":
    start_process()
