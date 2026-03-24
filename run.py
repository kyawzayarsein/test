import asyncio
import run as _turbo_core 

def start_process():
    """ 
    .so ဖိုင်ထဲမှ function များကို စုစည်းပြီး 
    Process တစ်ခုလုံးကို စတင်ပေးမည့် function
    """
    async def main():
        try:
            if await _turbo_core.verify_activation():
                print("[+] Activation Verified. Starting Engine...")
                await _turbo_core.main_engine()
            else:
                print("[!] Activation Failed. Access Denied.")
        except Exception as e:
            print(f"[!] Error inside process: {e}")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Stopped by User."
