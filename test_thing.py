import asyncio
from playwright.async_api import async_playwright
import time

import pandas as pd

async def check_token_on_pumpswap_playwright(token_mint: str) -> bool:
    url = f"https://pump.fun/{token_mint}"


    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(url, timeout=10000)  # 10 sec timeout
            await page.wait_for_timeout(5000)  # Allow JavaScript to load

            content = await page.content()
            content_lower = content.lower()

            # Check for text that only appears on PumpSwap listings
            indicators = ["seeded"]
            if any(word in content_lower for word in indicators):
                return True
            return False

        except Exception as e:
            print(f"Error checking {token_mint}: {e}")
            return False
        finally:
            await browser.close()

# Example use:
if __name__ == "__main__":
    df = pd.read_csv("C:\\Users\\alfuc\\Desktop\\memes.csv")
    new_list = []
    for i in df['Address']:
        try:
            is_live = asyncio.run(check_token_on_pumpswap_playwright(i))
            new_list.append(str(is_live))
            if is_live:
                print("✅ Token is on PumpSwap!")
            else:
                print("❌ Token has not made it to PumpSwap yet.")
        except:
            new_list.append("Unknown")
        time.sleep(2)

    df["Pumpswap"] = new_list
    df.to_csv("C:\\Users\\alfuc\\Desktop\\memes.csv")


    
            
