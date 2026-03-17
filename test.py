import requests
import re
import urllib3
import time
import threading
import hashlib
import os
from urllib.parse import urlparse, parse_qs, urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION (SID တည်ငြိမ်ဖို့ အဓိက အပိုင်း) ---
SECRET_SALT = "ohmygod@123"
PING_THREADS = 2       # Thread များရင် Router က Block တတ်လို့ လျှော့ထားပါတယ်
PING_INTERVAL = 0.5    # ၀.၅ စက္ကန့်တစ်ခါ ပို့ပြီး Session ကို အမြဲ နိုးကြားနေစေမယ်
CHECK_DELAY = 1        # အင်တာနက် စစ်ဆေးတဲ့နှုန်းကို မြှင့်ထားတယ်

def get_stable_id():
    try:
        serial = os.popen("getprop ro.serialno").read().strip()
        if not serial:
            serial = os.popen("getprop ro.build.display.id").read().strip()
    except:
        serial = "DEFAULT_NODE"
    return f"TRB-{hashlib.md5(serial.encode()).hexdigest()[:10].upper()}"

def verify_activation():
    device_id = get_stable_id()
    key_file = os.path.join(os.path.expanduser("~"), ".turbo_license")
    correct_key = hashlib.sha256(f"{device_id}{SECRET_SALT}".encode()).hexdigest()[:12].upper()
    if os.path.exists(key_file) and open(key_file).read().strip() == correct_key:
        return True
    print(f"DEVICE ID: {device_id}")
    input_key = input("Enter Activation Key: ").strip().upper()
    if input_key == correct_key:
        with open(key_file, "w") as f: f.write(input_key)
        return True
    return False

def check_real_internet():
    """အင်တာနက် ရှိမရှိကို အမြန်ဆုံး စစ်ဆေးမယ်"""
    try:
        return requests.get("http://www.google.com", timeout=2).status_code == 200
    except:
        return False

def keep_session_alive(auth_link, session, sid):
    """SID လုံးဝ မပြောင်းသွားအောင် Router ကို အဆက်မပြတ် Signal ပို့တဲ့အပိုင်း"""
    while True:
        try:
            # Router ရဲ့ Auth စာမျက်နှာကို ခဏခဏ ခေါ်ပြီး Session ကို Update လုပ်နေမယ်
            resp = session.get(auth_link, timeout=5)
            if resp.status_code == 200:
                print(f"[{time.strftime('%H:%M:%S')}] SID: {sid} (Holding...)      ", end='\r')
            else:
                # အကယ်၍ 200 မပြန်ရင် Session ပြတ်ဖို့ နီးစပ်နေပြီ
                break
        except:
            break
        time.sleep(PING_INTERVAL)

def start_process():
    if not verify_activation(): return
    print(f"[{time.strftime('%H:%M:%S')}] Turbo Script Running (Anti-Drop Mode)...")
    
    current_sid = None

    while True:
        # အင်တာနက် ရှိနေရင် ဘာမှမလုပ်ဘဲ စောင့်နေမယ်
        if check_real_internet():
            time.sleep(CHECK_DELAY)
            continue
        
        # အင်တာနက် ပြတ်တာနဲ့ Login ချက်ချင်းဝင်မယ်
        session = requests.Session()
        try:
            r = requests.get("http://connectivitycheck.gstatic.com/generate_204", allow_redirects=True, timeout=5)
            if r.url != "http://connectivitycheck.gstatic.com/generate_204":
                portal_url = r.url
                parsed_portal = urlparse(portal_url)
                portal_host = f"{parsed_portal.scheme}://{parsed_portal.netloc}"
                
                r1 = session.get(portal_url, verify=False, timeout=5)
                path_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", r1.text)
                next_url = urljoin(portal_url, path_match.group(1)) if path_match else portal_url
                
                r2 = session.get(next_url, verify=False, timeout=5)
                sid = parse_qs(urlparse(r2.url).query).get('sessionId', [None])[0]
                
                if sid:
                    current_sid = sid
                    # Voucher Activation
                    session.post(f"{portal_host}/api/auth/voucher/", 
                                 json={'accessCode': '123456', 'sessionId': sid, 'apiVersion': 1}, timeout=5)

                    # Auth Link တည်ဆောက်ခြင်း
                    params = parse_qs(parsed_portal.query)
                    gw_addr = params.get('gw_address', ['192.168.60.1'])[0]
                    gw_port = params.get('gw_port', ['2060'])[0]
                    auth_link = f"http://{gw_addr}:{gw_port}/wifidog/auth?token={sid}"

                    print(f"\n[*] Locked SID: {sid}")
                    
                    # Session ကို မပြတ်အောင် ထိန်းထားမယ့် Threads တွေကို စမယ်
                    for _ in range(PING_THREADS):
                        threading.Thread(target=keep_session_alive, args=(auth_link, session, sid), daemon=True).start()
                    
                    time.sleep(3) # အင်တာနက် ပြန်တက်လာဖို့ ခဏစောင့်မယ်
        except:
            time.sleep(2)

if __name__ == "__main__":
    try: start_process()
    except KeyboardInterrupt: print("\nStopped.")
