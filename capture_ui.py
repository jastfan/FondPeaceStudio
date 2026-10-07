import asyncio
import os
import sys
from playwright.async_api import async_playwright

async def capture(target_url: str = "https://fondpeace.com", out_path: str = "assets/fondpeace_ui.png"):
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print(f"Navigating to {target_url}...")
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Navigation warning ({target_url}): {e}")

        # Wait for fonts, layout, and animations to settle
        await page.wait_for_timeout(2000)
        
        await page.screenshot(path=out_path, full_page=False)
        print(f"Screenshot successfully captured and saved to: {out_path}!")
        await browser.close()

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "https://fondpeace.com"
    destination = sys.argv[2] if len(sys.argv) > 2 else "assets/fondpeace_ui.png"
    asyncio.run(capture(target, destination))
