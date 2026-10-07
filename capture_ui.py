import asyncio
from playwright.async_api import async_playwright

async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page = await context.new_page()
        
        print("Navigating to http://127.0.0.1:8000...")
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        
        await page.wait_for_selector(".repo-card", timeout=15000)
        
        # Wait for script generation to complete or up to 8 seconds
        for _ in range(16):
            await page.wait_for_timeout(500)
            val = await page.input_value("#script-textarea")
            if val and "Generating" not in val and len(val) > 20:
                print("Script loaded:", val[:50])
                break
                
        await page.wait_for_timeout(1000)
        out_path = "assets/studio_ui.png"
        await page.screenshot(path=out_path)
        print(f"Screenshot successfully updated at {out_path}!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture())
