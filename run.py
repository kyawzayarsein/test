import asyncio
import run as _turbo_core # .so ဖိုင်ကို load လုပ်ခြင်း

def start_process():
    """ 
    .so ဖိုင်ထဲမှ function များကို စုစည်းပြီး 
    Process တစ်ခုလုံးကို စတင်ပေးမည့် function
    """
    async def main():
        try:
            # ၁။ Activation စစ်ဆေးခြင်း
            if await _turbo_core.verify_activation():
                print("[+] Activation Verified. Starting Engine...")
                # ၂။ Main Engine ကို run ခြင်း
                await _turbo_core.main_engine()
            else:
                print("[!] Activation Failed. Access Denied.")
        except Exception as e:
            print(f"[!] Error inside process: {e}")

    try:
        # Asyncio event loop ကို စတင်ခြင်း
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Stopped by User.")
        
