import os
import math
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from config import TEMP_DIR, VIDEO_WIDTH, VIDEO_HEIGHT

async def record_repo_readme_scroll(
    repo_url: str, 
    target_duration: float, 
    video_filename: str = "scroll_recording.webm"
) -> str:
    """
    Automates browsing a GitHub repo, locates where the README starts,
    and smoothly scrolls down to the bottom over the target_duration,
    recording a 9:16 vertical video.
    """
    record_dir = TEMP_DIR / "browser_recordings"
    record_dir.mkdir(parents=True, exist_ok=True)
    
    # Clean previous webm in this temp subfolder to avoid confusion
    for old_file in record_dir.glob("*.webm"):
        try:
            old_file.unlink()
        except Exception:
            pass

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': VIDEO_WIDTH, 'height': VIDEO_HEIGHT},
            device_scale_factor=1,
            color_scheme='dark',
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            record_video_dir=str(record_dir),
            record_video_size={'width': VIDEO_WIDTH, 'height': VIDEO_HEIGHT}
        )
        
        page = await context.new_page()
        
        print(f"[Browser] Navigating to {repo_url}...")
        try:
            await page.goto(repo_url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(2000)
        except Exception as e:
            print(f"[Browser] Warning during goto: {e}, continuing...")

        # Inject styling for cleaner presentation: hide banners & enhance readability
        await page.add_style_tag(content="""
            .js-cookie-consent-banner, 
            #repos-sticky-header, 
            .AppHeader, 
            .signup-prompt-bg,
            div[aria-label="Repository files"] { 
                /* keep page clean */
            }
            .js-cookie-consent-banner, #repos-sticky-header {
                display: none !important;
            }
            html {
                scroll-behavior: smooth !important;
            }
        """)

        # Find the README element start position
        scroll_bounds = await page.evaluate("""() => {
            const readme = document.querySelector('#readme') || 
                           document.querySelector('article.markdown-body') ||
                           document.querySelector('[data-target="readme-toc.content"]');
            
            let startY = 0;
            if (readme) {
                const rect = readme.getBoundingClientRect();
                startY = rect.top + window.scrollY - 30; // slightly above header
            }
            
            const totalHeight = document.documentElement.scrollHeight;
            const maxY = Math.max(0, totalHeight - window.innerHeight);
            return {
                startY: Math.max(0, Math.floor(startY)),
                maxY: Math.floor(maxY),
                totalHeight: totalHeight
            };
        }""")
        
        start_y = scroll_bounds["startY"]
        max_y = scroll_bounds["maxY"]
        
        print(f"[Browser] README Start Position: {start_y}px, Page Bottom: {max_y}px")
        
        # Position viewport right at the start of the README
        await page.evaluate(f"window.scrollTo(0, {start_y})")
        
        # Hold on README title/banner for the opening hook (2.5 seconds)
        initial_hold = 2.5
        await page.wait_for_timeout(int(initial_hold * 1000))
        
        # Calculate remaining scroll duration
        # We reserve 2.0s at the end for the CTA hold
        final_hold = 2.0
        scroll_time = max(5.0, target_duration - initial_hold - final_hold)
        
        # Human-like smooth scrolling simulation
        # Divide into steps with smooth easing
        steps = int(scroll_time * 30) # 30 updates per second
        distance = max(0, max_y - start_y)
        
        print(f"[Browser] Scrolling {distance}px smoothly over {scroll_time:.2f}s...")
        
        step_delay = scroll_time / steps
        for step in range(1, steps + 1):
            # Smooth cosine easing for natural human scroll feel
            progress = step / steps
            # Smooth step: 0.5 * (1 - cos(pi * progress))
            eased_progress = 0.5 * (1 - math.cos(math.pi * progress))
            target_scroll = start_y + (distance * eased_progress)
            
            await page.evaluate(f"window.scrollTo(0, {target_scroll})")
            await asyncio.sleep(step_delay)
            
        # Hold at the bottom
        print("[Browser] Reached bottom. Holding for Call-to-Action...")
        await page.wait_for_timeout(int(final_hold * 1000))
        
        # Get path to recorded video
        video_obj = page.video
        await context.close()
        await browser.close()
        
        if video_obj:
            raw_video_path = await video_obj.path()
            target_path = str(TEMP_DIR / video_filename)
            # Rename/copy to standardized temp path
            if os.path.exists(target_path):
                os.remove(target_path)
            os.rename(raw_video_path, target_path)
            print(f"[Browser] Recording complete: {target_path}")
            return target_path
        else:
            # Fallback to search in record_dir
            files = list(record_dir.glob("*.webm"))
            if files:
                return str(files[0])
            raise RuntimeError("No video file was recorded.")

if __name__ == "__main__":
    test_url = "https://github.com/Panniantong/Agent-Reach"
    path = asyncio.run(record_repo_readme_scroll(test_url, target_duration=12.0))
    print(f"Test recorded video at: {path}")
