import asyncio
import aiohttp
import re
import time
import hashlib
import os
from urllib.parse import urlparse, parse_qs, urljoin

# --- CONFIGURATION ---
CONCURRENT_PINGS = 10   
PING_INTERVAL = 0.1     
FAST_TIMEOUT = aiohttp.ClientTimeout(total=2)

async def high_speed_ping(session, auth_link, info_msg):
    """Network connection တည်ငြိမ်အောင် ping ပို့ခြင်း"""
    while True:
        try:
            if session.closed: break
            async with session.get(auth_link, timeout=aiohttp.ClientTimeout(total=1)) as response:
                print(f"[{time.strftime('%H:%M:%S')}] Pinging: {info_msg} (Active)      ", end='\r')
                await asyncio.sleep(PING_INTERVAL)
        except:
            break

async def start_process():
    # User ID Approval ဖြုတ်ထားပါသည်
    print(f"[{time.strftime('%H:%M:%S')}] Turbo Async (No Activation) Start...")
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    # aiodns library မလိုဘဲ အလုပ်လုပ်စေရန်
    resolver = aiohttp.ThreadedResolver()
    
    while True:
        # Session အသစ်ဖြင့် စတင်ခြင်း
        connector = aiohttp.TCPConnector(resolver=resolver, use_dns_cache=True, ttl_dns_cache=300)
        async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
            try:
                while not session.closed:
                    try:
                        # အင်တာနက် အခြေအနေ စစ်ဆေးခြင်း
                        async with session.get("http://connectivitycheck.gstatic.com/generate_204", 
                                               allow_redirects=True, 
                                               timeout=FAST_TIMEOUT) as r:
                            
                            if r.status == 204:
                                print(f"[{time.strftime('%H:%M:%S')}] Internet OK. Monitoring... ", end='\r')
                                await asyncio.sleep(0.5) 
                                continue
                            
                            portal_url = str(r.url)
                            print(f"\n[!] Portal Detected: {portal_url}")
                            
                            parsed_url = urlparse(portal_url)
                            info_msg = parsed_url.netloc
                            
                            # Mikrotik logic အတွက် portal url ကိုပဲ အခြေခံ ping ပါမည်
                            auth_link = portal_url
                            
                            print(f"[*] Starting High Speed Reconnection to: {info_msg}")

                            # Multi-tasking ဖြင့် အပြိုင် ping ပို့ခြင်း
                            tasks = [high_speed_ping(session, auth_link, info_msg) for _ in range(CONCURRENT_PINGS)]
                            await asyncio.gather(*tasks)

                    except (aiohttp.ClientError, asyncio.TimeoutError):
                        # Reconnect အမြန်ဖြစ်စေရန် loop အပြင်သို့ ထွက်ခြင်း
                        break
            except Exception:
                pass
            
            if not session.closed:
                await session.close()
        
        # Connection ပြန်မစခင် ခေတ္တနားခြင်း
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    try:
        asyncio.run(start_process())
    except KeyboardInterrupt:
        print("\n\n[!] Script Stopped.")
