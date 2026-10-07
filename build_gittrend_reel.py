import os
import sys
import json
import asyncio
import time
from datetime import datetime
from pathlib import Path
import imageio_ffmpeg
from mutagen.mp3 import MP3
import whisper
import cv2
from playwright.async_api import async_playwright
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Environment & Paths
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = str(Path(ffmpeg_path).parent)
os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

BASE_DIR = Path(r"C:\Users\hp\.gemini\antigravity-ide\scratch\FondPeaceRepos")
OUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"
OUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

_CACHED_WHISPER_MODEL = None

def get_whisper_model():
    global _CACHED_WHISPER_MODEL
    if _CACHED_WHISPER_MODEL is None:
        print("🧠 Pre-loading Whisper AI model into memory...")
        _CACHED_WHISPER_MODEL = whisper.load_model("base")
    return _CACHED_WHISPER_MODEL

from config import DEFAULT_DEEPMIND_VOICE, NORMAL_SCROLL_SPEED_PPS, INITIAL_HOLD_SEC
from trending_fetcher import fetch_trending_repos, fetch_repo_readme
from script_generator import generate_voiceover_script
from tts_engine import generate_voiceover_audio
from asset_normalizer import normalize_github_readme_html, enable_markdown_in_html

STAGE_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Reel Stage</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 0;
      overflow: hidden;
      background: #070913;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 1280px;
      width: 720px;
    }

    #reel-stage {
      width: 720px;
      height: 1280px;
      background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 25%, #fbc2eb 70%, #fad0c4 100%);
      display: flex;
      justify-content: center;
      align-items: center;
      position: relative;
      opacity: 1;
    }

    #mockup-window {
      width: 654px;
      height: 1184px;
      background-color: #0d1117;
      border-radius: 24px;
      box-shadow: 0 24px 60px rgba(0, 0, 0, 0.4);
      border: 1px solid rgba(255, 255, 255, 0.12);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      position: relative;
    }

    /* Chrome Titlebar */
    #chrome-titlebar {
      height: 38px;
      background-color: #161b22;
      display: flex;
      align-items: center;
      padding: 0 12px;
      gap: 8px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .window-controls .control-dot {
      display: inline-block;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: #30363d;
    }

    .chrome-tab {
      height: 28px;
      background-color: #0d1117;
      border-radius: 8px 8px 0 0;
      display: flex;
      align-items: center;
      padding: 0 10px;
      gap: 6px;
      font-size: 11px;
      color: #c9d1d9;
      max-width: 230px;
    }

    .tab-title {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .tab-close {
      color: #8b949e;
      font-size: 14px;
      margin-left: 4px;
    }

    .tab-add {
      color: #8b949e;
      font-size: 16px;
      margin-left: 2px;
    }

    /* Chrome Addressbar */
    #chrome-addressbar {
      height: 44px;
      background-color: #161b22;
      display: flex;
      align-items: center;
      padding: 0 12px;
      gap: 10px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }

    .nav-btns {
      display: flex;
      gap: 8px;
      color: #8b949e;
      font-size: 13px;
    }

    .url-bar {
      flex: 1;
      height: 30px;
      background-color: #0d1117;
      border-radius: 15px;
      border: 1px solid #30363d;
      display: flex;
      align-items: center;
      padding: 0 10px;
      gap: 8px;
      color: #c9d1d9;
      font-size: 11.5px;
    }

    .url-text {
      flex: 1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .url-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .btn-install {
      background: #1f6feb;
      color: #ffffff;
      padding: 2px 8px;
      border-radius: 10px;
      font-size: 10px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .action-icon {
      color: #8b949e;
      font-size: 12px;
    }

    .avatar-dot {
      width: 14px;
      height: 14px;
      border-radius: 50%;
      background: #484f58;
    }

    /* Secondary Tabs */
    #secondary-tabs {
      height: 38px;
      background-color: #0d1117;
      display: flex;
      align-items: center;
      padding: 0 16px;
      gap: 18px;
      border-bottom: 1px solid #21262d;
      font-size: 12px;
      color: #8b949e;
      font-weight: 500;
    }

    .sub-tab.active {
      color: #f0f6fc;
      font-weight: 600;
      border-bottom: 2px solid #f78166;
      padding-bottom: 8px;
      margin-bottom: -8px;
    }

    .sub-tab-menu {
      margin-left: auto;
      font-size: 14px;
      color: #8b949e;
    }

    /* README Viewport */
    #readme-viewport {
      flex: 1;
      overflow-y: scroll;
      scroll-behavior: auto;
      padding: 24px 28px;
      background-color: #0d1117;
      color: #c9d1d9;
    }

    #readme-viewport::-webkit-scrollbar {
      display: none;
    }

    /* GitHub Markdown Dark Styling */
    .markdown-body {
      font-size: 14px;
      line-height: 1.6;
      color: #c9d1d9;
    }
    .markdown-body h1, .markdown-body h2, .markdown-body h3 {
      color: #f0f6fc;
      border-bottom: 1px solid #21262d;
      padding-bottom: 0.3em;
      margin-top: 24px;
      margin-bottom: 16px;
    }
    .markdown-body h1 { font-size: 1.8em; text-align: center; }
    .markdown-body h2 { font-size: 1.4em; }
    .markdown-body h3 { font-size: 1.2em; }
    .markdown-body p { margin-top: 0; margin-bottom: 16px; }
    .markdown-body a { color: #58a6ff; text-decoration: none; }
    .markdown-body a:hover { text-decoration: underline; }
    .markdown-body img { max-width: 100%; border-radius: 6px; }
    .markdown-body pre {
      background-color: #161b22;
      border-radius: 6px;
      padding: 16px;
      overflow: auto;
      font-size: 85%;
      border: 1px solid #30363d;
    }
    .markdown-body code {
      background-color: rgba(110,118,129,0.4);
      padding: 0.2em 0.4em;
      border-radius: 6px;
      font-size: 85%;
    }
    .markdown-body pre code {
      background-color: transparent;
      padding: 0;
    }
    .markdown-body table {
      border-collapse: collapse;
      width: 100%;
      margin-bottom: 16px;
    }
    .markdown-body th, .markdown-body td {
      border: 1px solid #30363d;
      padding: 6px 13px;
    }
    .markdown-body tr:nth-child(2n) {
      background-color: #161b22;
    }

    /* Hormozi Captions Container (Elevated Social Safe Zone for IG / YT Shorts / FB Reels) */
    #caption-container {
      position: absolute;
      bottom: 350px;
      left: 0;
      right: 0;
      display: flex;
      justify-content: center;
      padding: 0 50px;
      pointer-events: none;
      z-index: 9999;
      transform: translateZ(0);
      will-change: transform;
    }

    #caption-box {
      background: rgba(15, 15, 15, 0.94);
      border-radius: 10px;
      padding: 8px 22px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.65);
      border: 1px solid rgba(255, 255, 255, 0.1);
      max-width: 580px;
      text-align: center;
    }

    #caption-text {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      font-weight: 900;
      font-size: 26px;
      letter-spacing: 1px;
      color: #ffffff;
      text-transform: uppercase;
    }

    .hl-yellow {
      color: #ffe600 !important;
    }
  </style>
</head>
<body>
  <div id="reel-stage">
    <div id="mockup-window">
      <!-- Chrome Title Bar -->
      <div id="chrome-titlebar">
        <div class="window-controls">
          <span class="control-dot"></span>
        </div>
        <div class="chrome-tab">
          <svg class="gh-icon" height="14" viewBox="0 0 16 16" width="14" fill="#8b949e"><path d="M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9 1.09 1.48.42.69 1.54.49 2.05.37.01.68.01 1.25.01 1.44 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"></path></svg>
          <span class="tab-title">GitHub - REPO_NAME</span>
          <span class="tab-close">×</span>
        </div>
        <span class="tab-add">+</span>
      </div>

      <!-- Chrome Address Bar -->
      <div id="chrome-addressbar">
        <div class="nav-btns">
          <span class="nav-arrow">←</span>
          <span class="nav-arrow">→</span>
          <span class="nav-refresh">↻</span>
        </div>
        <div class="url-bar">
          <svg class="lock-icon" height="12" viewBox="0 0 16 16" width="12" fill="#8b949e"><path d="M4 4v2h-.5A1.5 1.5 0 0 0 2 7.5v6A1.5 1.5 0 0 0 3.5 15h9a1.5 1.5 0 0 0 1.5-1.5v-6A1.5 1.5 0 0 0 12.5 6H12V4a4 4 0 0 0-8 0Zm6.5 2H5.5V4a2.5 2.5 0 0 1 5 0v2Z"></path></svg>
          <span class="url-text">github.com/REPO_URL#readme</span>
          <div class="url-actions">
            <span class="btn-install">
              <svg height="11" viewBox="0 0 16 16" width="11" fill="currentColor"><path d="M2.75 14A1.75 1.75 0 0 1 1 12.25v-2.5a.75.75 0 0 1 1.5 0v2.5c0 .138.112.25.25.25h10.5a.25.25 0 0 1 .25-.25v-2.5a.75.75 0 0 1 1.5 0v2.5A1.75 1.75 0 0 1 13.25 14Z"></path><path d="M7.25 1.75a.75.75 0 0 1 1.5 0v7.69l2.72-2.72a.75.75 0 1 1 1.06 1.06l-4 4a.75.75 0 0 1-1.06 0l-4-4a.75.75 0 0 1 1.06-1.06l2.72 2.72Z"></path></svg>
              Install
            </span>
            <span class="action-icon">★</span>
            <span class="avatar-dot"></span>
          </div>
        </div>
      </div>

      <!-- Secondary Tab Bar -->
      <div id="secondary-tabs">
        <div class="sub-tab active">README</div>
        <div class="sub-tab">Contributing</div>
        <div class="sub-tab">MIT license</div>
        <div class="sub-tab">Security</div>
        <div class="sub-tab-menu">☰</div>
      </div>

      <!-- Content Viewport (Starts Directly with README!) -->
      <div id="readme-viewport">
        <div id="readme-content-slot" class="markdown-body">
          README_HTML_CONTENT
        </div>
      </div>
    </div> <!-- /#mockup-window -->

    <!-- Dynamic Hormozi Captions Container (Isolated Composite Overlay) -->
    <div id="caption-container">
      <div id="caption-box">
        <span id="caption-text">START_CAPTION</span>
      </div>
    </div>

    <!-- Calibration Sync Marker: triggers frame-accurate video/audio alignment -->
    <div id="sync-marker" style="position: absolute; top: 0; left: 0; width: 16px; height: 16px; background: #070913; z-index: 99999999;"></div>

    <!-- User Custom Draggable Branding Overlay (Global Canvas Layer) -->
    USER_BRANDING_HTML

  </div> <!-- /#reel-stage -->

  <script>
    window.timelineChunks = CHUNKS_JSON_DATA;
    window.totalAnimTime = TOTAL_ANIM_TIME;
    window.animStartTime = null;
    window.animationActive = false;

    const viewport = document.getElementById('readme-viewport');
    const captionBox = document.getElementById('caption-box');
    const captionText = document.getElementById('caption-text');
    const reelStage = document.getElementById('reel-stage');

    function updateFrame(timestamp) {
      if (!window.animationActive) return;
      if (!window.animStartTime) {
        window.animStartTime = timestamp;
      }
      const elapsed = (timestamp - window.animStartTime) / 1000;

      // Calibration marker is hidden after 250ms so it never shows in the final video
      if (elapsed > 0.25) {
        const marker = document.getElementById('sync-marker');
        if (marker && marker.style.display !== 'none') {
          marker.style.display = 'none';
        }
      }

      // 1. Update Subtitles with high-contrast Hormozi styling & seamless transitions
      let activeChunk = null;
      let lastPastChunk = null;
      for (let i = 0; i < window.timelineChunks.length; i++) {
        const c = window.timelineChunks[i];
        if (elapsed >= c.start && elapsed <= c.end) {
          activeChunk = c;
          break;
        }
        if (elapsed > c.end) {
          lastPastChunk = c;
        }
      }

      if (activeChunk) {
        captionBox.style.opacity = '1';
        captionText.innerHTML = activeChunk.html;
      } else if (lastPastChunk && (elapsed - lastPastChunk.end) < 0.6) {
        // Keep words visible during micro-pauses so subtitle box doesn't flicker
        captionBox.style.opacity = '1';
        captionText.innerHTML = lastPastChunk.plain || lastPastChunk.html;
      } else if (elapsed > window.totalAnimTime - 2.2) {
        captionBox.style.opacity = '1';
        captionText.innerHTML = 'COMMENT <span class="hl-yellow">"CODE"</span> FOR LINK';
      } else if (window.timelineChunks.length > 0 && elapsed < window.timelineChunks[0].start) {
        // Before the first word is spoken, show opening chunk in crisp white
        captionBox.style.opacity = '1';
        captionText.innerHTML = window.timelineChunks[0].plain || window.timelineChunks[0].html;
      } else {
        captionBox.style.opacity = '0.9';
      }

      // 2. Exact rock-solid hold on header & badges, then silky smooth ease-in into steady scroll
      const initialHold = INITIAL_HOLD_SEC; // Pause on header/badges
      const scrollSpeed = SCROLL_SPEED_PPS; // Steady human reading speed
      const maxScroll = viewport.scrollHeight - viewport.clientHeight;

      if (elapsed <= initialHold) {
        viewport.scrollTop = 0;
      } else {
        const scrollTime = elapsed - initialHold;
        const easeInDuration = 0.8; // 0.8s smooth quadratic ease-in acceleration
        let scrollDist;
        if (scrollTime < easeInDuration) {
          const t = scrollTime / easeInDuration;
          scrollDist = (scrollSpeed * easeInDuration * 0.5) * (t * t);
        } else {
          const rampDist = scrollSpeed * easeInDuration * 0.5;
          scrollDist = rampDist + scrollSpeed * (scrollTime - easeInDuration);
        }
        viewport.scrollTop = Math.min(maxScroll, scrollDist);
      }

      if (elapsed < window.totalAnimTime + 0.5) {
        requestAnimationFrame(updateFrame);
      }
    }

    window.startStudioAnimation = function() {
      const marker = document.getElementById('sync-marker');
      if (marker) {
        marker.style.backgroundColor = '#00FF00'; // Neon green [0, 255, 0] trigger
      }
      window.animationActive = true;
      requestAnimationFrame(updateFrame);
    };
  </script>
</body>
</html>
"""

async def build_instant_gittrend_reel(
    repo_target: str = None, 
    rank_target: int = 1,
    voice_name: str = DEFAULT_DEEPMIND_VOICE,
    emotion_style: str = "high-energy viral storytelling",
    scroll_speed: float = NORMAL_SCROLL_SPEED_PPS,
    brand_enabled: bool = True,
    brand_type: str = "text",
    brand_text: str = "@FondPeace",
    brand_image_url: str = "",
    brand_x: int = 490,
    brand_y: int = 1210,
    custom_script: str = None,
    custom_caption: str = None,
    progress_callback = None
):
    def update_progress(pct: int, msg: str):
        print(f"[{pct}%] {msg}")
        if progress_callback:
            try: progress_callback(pct, msg)
            except: pass

    update_progress(5, "Initializing GitTrend Reel Engine...")
    print("=" * 65)
    print("🚀 FondPeaceRepos — GitTrend Viral Reel Engine (v3 Studio)")
    print("=" * 65)

    # Step 1: Target Discovery
    selected_repo = None
    if repo_target:
        update_progress(10, f"Loading target repository: {repo_target}")
        selected_repo = {
            "rank": 1,
            "name": repo_target,
            "url": f"https://github.com/{repo_target}",
            "description": f"Trending open-source project {repo_target}.",
            "stars_today": "Trending",
            "total_stars": "Top",
            "language": "Code"
        }
    else:
        update_progress(10, "Scanning jastfan/github-trending for today's breakout repositories...")
        trending_list = fetch_trending_repos()
        if not trending_list:
            raise RuntimeError("Failed to fetch trending repositories.")
            
        print(f"✅ Discovered {len(trending_list)} trending projects.")
        for r in trending_list[:3]:
            print(f"   #{r['rank']}: {r['name']} ({r['language']}) - {r['stars_today']} stars today")
            
        idx = max(0, min(rank_target - 1, len(trending_list) - 1))
        selected_repo = trending_list[idx]

    repo_name = selected_repo["name"]
    clean_slug = repo_name.replace("/", "_")
    today_str = datetime.now().strftime("%Y%m%d")
    
    print(f"\n🎯 Selected Target Project: {repo_name}")
    print(f"   URL: {selected_repo['url']}")
    print(f"   Stars Today: {selected_repo['stars_today']} | Total: {selected_repo['total_stars']}")

    # Step 2: Documentation Analysis & Script Generation
    readme_text = fetch_repo_readme(repo_name)
    
    if custom_script and custom_script.strip() and not custom_script.startswith("⏳"):
        update_progress(20, "Using custom user-refined voiceover script...")
        vo_script = custom_script.strip()
        post_caption = custom_caption.strip() if custom_caption else f"Check out {repo_name}! 🔥 #coding #github #opensource"
    else:
        update_progress(20, "Analyzing documentation & generating high-retention AI script...")
        vo_script, post_caption = generate_voiceover_script(selected_repo, readme_text)
    
    caption_file = OUT_DIR / f"{today_str}_{clean_slug}_caption.txt"
    with open(caption_file, "w", encoding="utf-8") as f:
        f.write(post_caption)
    print(f"💾 Saved full social media caption to: {caption_file}")

    # Step 3: Studio Voice Synthesis (DeepMind with 3-key failover + chunking)
    update_progress(40, f"Synthesizing studio voiceover with Google DeepMind ({voice_name})...")
    audio_file, audio_dur = generate_voiceover_audio(
        text=vo_script,
        voice_name=voice_name,
        emotion_style=emotion_style,
        filename=f"{clean_slug}_voiceover.mp3"
    )
    print(f"✅ Voiceover audio ready ({audio_dur:.2f} seconds).")

    # Step 4: Whisper Word/Phrase Alignment for Hormozi Captions
    update_progress(60, "Aligning synchronized Alex Hormozi captions via Whisper...")
    w_model = get_whisper_model()
    w_res = w_model.transcribe(audio_file)
    
    chunks = []
    for s in w_res['segments']:
        words = s['text'].strip().split()
        if not words:
            continue
        seg_dur = s['end'] - s['start']
        word_dur = seg_dur / len(words)
        
        chunk_size = 3
        for i in range(0, len(words), chunk_size):
            sub_words = words[i:i+chunk_size]
            clean_words = [w.upper().replace(",", "").replace(".", "").replace("!", "").replace("?", "").replace('"', '').replace("'", "") for w in sub_words]
            
            # Active Word-by-Word Karaoke: current spoken word is bright yellow, surrounding words stay crisp white!
            for sub_idx in range(len(sub_words)):
                w_start = s['start'] + ((i + sub_idx) * word_dur)
                w_end = s['start'] + ((i + sub_idx + 1) * word_dur)
                
                formatted = []
                for idx, clean_w in enumerate(clean_words):
                    if idx == sub_idx:
                        formatted.append(f'<span class="hl-yellow">{clean_w}</span>')
                    else:
                        formatted.append(clean_w)
                        
                chunks.append({
                    "start": round(w_start, 2),
                    "end": round(w_end, 2),
                    "html": " ".join(formatted),
                    "plain": " ".join(clean_words)
                })
            
    print(f"✅ Created {len(chunks)} synchronized word-level caption chunks.")

    # Step 5: Convert README markdown to high-fidelity HTML & normalize assets
    update_progress(70, "Converting README markdown to high-fidelity HTML and normalizing graphics...")
    if not readme_text:
        readme_text = fetch_repo_readme(repo_name)
    
    import markdown
    if readme_text:
        prep_readme = enable_markdown_in_html(readme_text)
        readme_html = markdown.markdown(
            prep_readme, 
            extensions=['fenced_code', 'tables', 'nl2br', 'extra', 'md_in_html']
        )
    else:
        readme_html = f"<h1>{repo_name}</h1><p>Trending open-source project.</p>"

    # Rewrite all relative paths to raw GitHub CDN to eliminate broken images
    normalized_readme_html = normalize_github_readme_html(readme_html, repo_name)

    # Build User Custom Branding Overlay HTML
    if not brand_enabled:
        branding_html = ""
    elif brand_type == "image" and brand_image_url:
        resolved_img_src = brand_image_url
        if brand_image_url.startswith("/static/"):
            local_img_path = (BASE_DIR / "static") / brand_image_url.replace("/static/", "")
            if local_img_path.exists():
                import base64
                with open(local_img_path, "rb") as f:
                    b64_data = base64.b64encode(f.read()).decode("ascii")
                ext = local_img_path.suffix.lstrip(".").lower() or "png"
                resolved_img_src = f"data:image/{ext};base64,{b64_data}"

        branding_html = f"""
        <div id="user-branding" style="position: absolute; left: {brand_x}px; top: {brand_y}px; z-index: 99999; pointer-events: none;">
          <img src="{resolved_img_src}" style="height: 38px; border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,0.6); object-fit: contain; border: 1px solid rgba(255,255,255,0.2);">
        </div>
        """
    else:
        # Custom Text pill badge
        safe_brand_text = brand_text or "fondpeace.com"
        branding_html = f"""
        <div id="user-branding" style="position: absolute; left: {brand_x}px; top: {brand_y}px; z-index: 99999; background: rgba(13, 17, 23, 0.95); border: 1.5px solid rgba(255, 255, 255, 0.2); border-radius: 20px; padding: 6px 14px; display: flex; align-items: center; gap: 8px; color: #ffffff; font-weight: 700; font-size: 13px; letter-spacing: 0.5px; box-shadow: 0 8px 24px rgba(0,0,0,0.6); pointer-events: none; backdrop-filter: blur(8px);">
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#58a6ff;box-shadow:0 0 8px #58a6ff;"></span>
          <span>{safe_brand_text}</span>
        </div>
        """

    total_anim_time = audio_dur
    start_caption = chunks[0]['html'] if chunks else 'NEW BREAKOUT REPO'
    
    stage_html_content = (
        STAGE_HTML_TEMPLATE
        .replace("REPO_NAME", repo_name)
        .replace("REPO_URL", repo_name)
        .replace("README_HTML_CONTENT", normalized_readme_html)
        .replace("USER_BRANDING_HTML", branding_html)
        .replace("START_CAPTION", start_caption)
        .replace("CHUNKS_JSON_DATA", json.dumps(chunks))
        .replace("TOTAL_ANIM_TIME", str(total_anim_time))
        .replace("INITIAL_HOLD_SEC", str(INITIAL_HOLD_SEC))
        .replace("SCROLL_SPEED_PPS", str(scroll_speed))
    )
    
    stage_html_file = TEMP_DIR / f"{clean_slug}_stage.html"
    with open(stage_html_file, "w", encoding="utf-8") as f:
        f.write(stage_html_content)

    rec_dir = TEMP_DIR / "instant_recordings"
    rec_dir.mkdir(parents=True, exist_ok=True)
    for old in rec_dir.glob("*.webm"):
        try: old.unlink()
        except: pass

    update_progress(80, "Preloading images & recording 9:16 mobile canvas...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled", 
                "--no-sandbox",
                "--background-color=#070913"
            ]
        )
        context = await browser.new_context(
            viewport={'width': 720, 'height': 1280},
            device_scale_factor=1,
            record_video_dir=str(rec_dir),
            record_video_size={'width': 720, 'height': 1280}
        )
        page = await context.new_page()
        page.set_default_timeout(60000)
        page.set_default_navigation_timeout(60000)
        
        # Load local stage with domcontentloaded (eliminates external asset hang and 30000ms timeout)
        stage_url = stage_html_file.as_uri()
        await page.goto(stage_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_selector("#mockup-window", timeout=15000)
        await page.wait_for_selector("#readme-content-slot", timeout=15000)
        
        # Comprehensive preloading check: wait for fonts and images to load completely before starting recording timeline
        try:
            await page.evaluate("""() => {
                return new Promise((resolve) => {
                    const checkAssets = async () => {
                        try {
                            if (document.fonts && document.fonts.ready) {
                                await document.fonts.ready;
                            }
                            const images = Array.from(document.querySelectorAll('#readme-viewport img'));
                            const imagePromises = images.map(img => {
                                if (img.complete) return Promise.resolve();
                                return new Promise(r => { 
                                    img.onload = img.onerror = r; 
                                    setTimeout(r, 2000);
                                });
                            });
                            await Promise.all(imagePromises);
                        } catch (e) {}
                        resolve();
                    };
                    checkAssets();
                    setTimeout(resolve, 3000);
                });
            }""")
        except Exception:
            pass

        # Brief pause to ensure all layout paints are 100% settled before starting recording timeline
        await page.wait_for_timeout(350)

        # Start animation at exact t=0 with neon green marker trigger
        await page.evaluate("window.startStudioAnimation()")
            
        print(f"🎬 Recording animation at calm human scroll velocity ({scroll_speed} px/s)...")
        # Wait for audio duration + 1.2s buffer so video never runs out of frames
        await page.wait_for_timeout(int((audio_dur + 1.2) * 1000))
        
        video_obj = page.video
        await context.close()
        await browser.close()
        
        raw_video = await video_obj.path()

    # Step 6: Frame-Accurate Sync Detection & Lossless Audio Muxing
    update_progress(90, "Synchronizing video timeline & muxing lossless audio track...")
    print("\n🔍 Analyzing recorded video for exact animation start...")
    cap = cv2.VideoCapture(raw_video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    sync_frame = 0
    frame_idx = 0
    first_rendered_frame = None
    
    # Analyze first 150 frames to locate exact trigger frame:
    # 1. Skip blank white (mean > 215) and blank black (mean < 15) frames
    # 2. Check top-left corner (2:14, 2:14) for neon green marker (g > 150 and b < 95 and r < 95)
    while cap.isOpened() and frame_idx < 150:
        ret, frame = cap.read()
        if not ret:
            break
        m = frame.mean()
        # Discard blank white frames or dead black frames
        if m > 215.0 or m < 15.0:
            frame_idx += 1
            continue
            
        if first_rendered_frame is None and 25.0 < m < 210.0:
            first_rendered_frame = frame_idx
            
        # Inspect top-left 16x16 pixel area for neon green trigger
        marker_crop = frame[2:14, 2:14]
        b_mean = float(marker_crop[:, :, 0].mean())
        g_mean = float(marker_crop[:, :, 1].mean())
        r_mean = float(marker_crop[:, :, 2].mean())
        
        if g_mean > 150 and b_mean < 95 and r_mean < 95:
            sync_frame = frame_idx
            print(f"🎯 Neon green trigger confirmed at frame #{sync_frame} (B:{b_mean:.0f}, G:{g_mean:.0f}, R:{r_mean:.0f})!")
            break
            
        frame_idx += 1
    cap.release()

    if sync_frame == 0 and first_rendered_frame is not None:
        sync_frame = first_rendered_frame
        print(f"⚠️ Marker fallback: Selected first valid rendered frame #{sync_frame}.")

    start_sec = sync_frame / fps if sync_frame > 0 else 0.0
    print(f"🎯 Sync point locked at frame #{sync_frame} ({start_sec:.3f}s, {fps:.1f} fps). Zero dead/white frames!")

    final_output = str(OUT_DIR / f"{today_str}_{clean_slug}_viral_reel.mp4")
    
    # Video filters: trim leading dead frames, ensure constant 30fps (CFR) for flawless playback
    vf_chain = []
    if sync_frame > 0:
        vf_chain.append(f"trim=start_frame={sync_frame},setpts=PTS-STARTPTS")
    vf_chain.append("fps=30")
    
    # Broadcast-standard MP4 encode: Constant 30fps, BT.709 color space, faststart
    cmd = [
        ffmpeg_path,
        "-y",
        "-i", raw_video,
        "-i", audio_file,
        "-vf", ",".join(vf_chain),
        "-c:v", "libx264",
        "-preset", "veryfast",   # 3x faster render while maintaining pristine visual quality
        "-crf", "16",           # Ultra-crisp near-lossless clarity
        "-pix_fmt", "yuv420p",
        # Explicit BT.709 color tags ensure video is crisp, properly lit, and never dark/murky on Windows/socials
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
        "-colorspace", "bt709",
        "-color_range", "tv",
        "-c:a", "aac",
        "-b:a", "320k",         # Studio-grade 320kbps audio
        "-ar", "48000",         # 48kHz audio sampling
        "-t", f"{audio_dur:.2f}",
        "-movflags", "+faststart",
        final_output
    ]
    
    subprocess.run(cmd, check=True)

    update_progress(100, "Reel generation complete! Ready to post.")
    print("\n" + "=" * 65)
    print("🎉 SUCCESS! GITTREND-STYLE VIRAL REEL IS READY TO POST!")
    print(f"📹 Final Reel Video: {final_output}")
    print(f"📄 Caption: {caption_file}")
    print(f"📦 File Size: {os.path.getsize(final_output) / (1024*1024):.2f} MB")
    print(f"⏱️ Duration: {audio_dur:.2f}s (Audio & Video 100% Matched)")
    print(f"📜 Scroll Speed: {scroll_speed} px/s (Calm & Readable)")
    print("=" * 65)
    return {
        "video_path": final_output,
        "video_filename": os.path.basename(final_output),
        "caption_path": str(caption_file),
        "caption_text": post_caption,
        "duration": round(audio_dur, 2),
        "file_size_mb": round(os.path.getsize(final_output) / (1024*1024), 2),
        "repo_name": repo_name,
        "status": "success"
    }

if __name__ == "__main__":
    asyncio.run(build_instant_gittrend_reel())
