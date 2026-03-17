import requests
import re
import urllib3
import time
import threading
import hashlib
import os
from urllib.parse import urlparse, parse_qs, urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- ULTIMATE CONFIGURATION ---
SECRET_SALT = "ohmygod@123"
PING_THREADS = 15      # (အချက် ၃) Ping ငြိမ်ဖို့ Thread ၁၅ ခု (Optimal)
PING_INTERVAL = 0.1    # (အချက် ၁) တုံ့ပြန်မှုနှုန်း အမြန်ဆုံးဖြစ်စေရန်
CHECK_DELAY = 1        # အင်တာနက် စစ်ဆေးသည့် အချိန်ခြားနားမှု

# (အချက် ၂) Data Speed တိုးစေရန် Router ကို လှည့်စားမယ့် Header များ
SPOOF_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "X-Requested-With": "com.facebook.orca", # Facebook App လိုမျိုး ဟန်ဆောင်ခြင်း
}

def get_stable_id():
    try:
        serial = os.popen("getprop ro.serialno").read().strip()
        if not serial: serial = os.popen("getprop ro.build.display.id").read().strip()
    except: serial = "DEFAULT_NODE"
    return f"TRB-{hashlib.md5(serial.encode()).hexdigest()[:10].upper()}"

def verify_activation():
    device_id = get_stable_id()
    key_file = os.path.join(os.path.expanduser("~"), ".turbo_license")
    correct_key = hashlib.sha256(f"{device_id}{SECRET_SALT}".encode()).hexdigest()[:12].upper()
    if os.path.exists(key_file) and open(key_file).read().strip() == correct_key: return True
    print(f"DEVICE ID: {device_id}")
    input_key = input("Enter Activation Key: ").strip().upper()
    if input_key == correct_key:
        with open(key_file, "w") as f: f.write(input_key)
        return True
    return False

def check_real_internet():
    try:
        # (အချက် ၁) Timeout ကို ၂ စက္ကန့်ပဲထားပြီး အမြန်ဆုံး စစ်ဆေးမယ်
        return requests.get("http://www.google.com", timeout=2, headers=SPOOF_HEADERS).status_code == 200
    except: return False

def high_speed_keep_alive(auth_link, session, sid):
    """ (အချက် ၃) Session ကို အမြဲနိုးကြားစေပြီး Ping ငြိမ်စေခြင်း """
    while True:
        try:
            # (အချက် ၂) Speed ပိုရစေရန် Spoof Headers များ သုံးထားသည်
            session.get(auth_link, timeout=3, headers=SPOOF_HEADERS)
            print(f"[{time.strftime('%H:%M:%S')}] [LOCKED] SID: {sid} | Speed: MAX      ", end='\r')
        except: break
        time.sleep(PING_INTERVAL)

def start_process():
    if not verify_activation(): return
    print(f"[{time.strftime('%H:%M:%S')}] Turbo V3 Ultimate Initializing...")
    
    while True:
        if check_real_internet():
            print(f"[{time.strftime('%H:%M:%S')}] Internet OK. Fast Monitoring...   ", end='\r')
            time.sleep(CHECK_DELAY)
            continue
            
        print(f"\n[{time.strftime('%H:%M:%S')}] Connection Lost! Relaunching Turbo...")
        session = requests.Session()
        session.headers.update(SPOOF_HEADERS) # Session တစ်ခုလုံးကို Header အသစ်ပြောင်းခြင်း

        try:
            # Captive Portal ကို အမြန်ဆုံး ဖမ်းယူခြင်း
            r = requests.get("http://connectivitycheck.gstatic.com/generate_204", allow_redirects=True, timeout=5)
            portal_url = r.url
            
            if portal_url != "http://connectivitycheck.gstatic.com/generate_204":
                parsed_portal = urlparse(portal_url)
                portal_host = f"{parsed_portal.scheme}://{parsed_portal.netloc}"
                
                r1 = session.get(portal_url, verify=False, timeout=5)
                path_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", r1.text)
                next_url = urljoin(portal_url, path_match.group(1)) if path_match else portal_url
                
                r2 = session.get(next_url, verify=False, timeout=5)
                sid = parse_qs(urlparse(r2.url).query).get('sessionId', [None])[0]
                
                if sid:
                    # Voucher Activation (Bypass Speed)
                    session.post(f"{portal_host}/api/auth/voucher/", 
                                 json={'accessCode': '123456', 'sessionId': sid, 'apiVersion': 1}, timeout=5)

                    # Auth Link တည်ဆောက်ခြင်း
                    params = parse_qs(parsed_portal.query)
                    gw_addr = params.get('gw_address', ['192.168.60.1'])[0]
                    gw_port = params.get('gw_port', ['2060'])[0]
                    auth_link = f"http://{gw_addr}:{gw_port}/wifidog/auth?token={sid}"

                    print(f"[*] Turbo Boost Active! New SID: {sid}")
                    
                    # (အချက် ၃) Threads များဖြင့် Session ကို အတင်းဆွဲထားခြင်း
                    for _ in range(PING_THREADS):
                        threading.Thread(target=high_speed_keep_alive, args=(auth_link, session, sid), daemon=True).start()
                    
                    time.sleep(2) # အမြန်ဆုံး ပြန်သုံးနိုင်ရန်
        except:
            time.sleep(1)

if __name__ == "__main__":
    try: start_process()
    except KeyboardInterrupt: print("\nTurbo Stopped.")
