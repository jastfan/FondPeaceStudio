# 🚀 FondPeaceRepos — Automated GitHub Trending Video Reel Pipeline

Fully automated pipeline to create daily viral 9:16 vertical videos (Instagram Reels, Facebook Reels, TikTok, YouTube Shorts) of trending GitHub repositories.

Zero manual video editing required: the system scans today's breakout repositories, loads the repository in dark mode, locates the exact start of the README, smoothly scrolls down to the bottom, generates a neural AI voiceover, overlays stats & branding, and outputs a ready-to-post `.mp4` video with hashtags!

---

## 📁 Project Architecture

```
FondPeaceRepos/
│
├── config.py             # Global settings, resolutions, paths, FFmpeg binary
├── trending_fetcher.py   # Scrapes today's top breakout repos from jastfan/github-trending
├── script_generator.py   # Gemini AI & high-retention scriptwriter + caption generator
├── tts_engine.py         # Studio-grade neural text-to-speech engine (edge-tts)
├── browser_recorder.py   # Playwright headless browser recording (README scroll from start to bottom)
├── video_composer.py     # FFmpeg video muxing, glassmorphic header card & 9:16 export
├── main.py               # Master CLI orchestrator
│
├── output/               # Ready-to-post MP4 videos and social media captions (.txt)
│   ├── 20261004_Panniantong_Agent-Reach_trending_reel.mp4
│   └── 20261004_Panniantong_Agent-Reach_caption.txt
│
└── temp/                 # Temporary voiceover audio, browser webm, and overlay PNGs
```

---

## ⚡ How It Works

1. **Finds Today's Trending Repositories**:
   Fetches the daily updated leaderboard from `jastfan/github-trending` (tracking star velocity, total stars, and description).
2. **Generates Voiceover Script**:
   Extracts repo metadata & README contents. Uses **Gemini AI** (or built-in viral templates) to generate a punchy 25–40s script and Instagram post caption with hashtags.
3. **Synthesizes Neural Audio**:
   Generates crystal-clear spoken audio using neural voice models (default: `en-US-ChristopherNeural`).
4. **Automated Scrolling Video Capture**:
   - Opens the GitHub repo in a 9:16 vertical resolution (1080x1920) in dark mode.
   - Automatically finds `#readme` / `article.markdown-body`.
   - Starts recording right at the top of the README.
   - Smoothly scrolls all the way to the bottom of the page, timed to the exact duration of the voiceover.
   - Holds on the call-to-action at the end.
5. **Composes Final Reel**:
   Overlays a modern glassmorphic header card with:
   - 🔥 *TODAY'S GITHUB BREAKOUT*
   - Repository Name
   - ⭐ Stars Gained Today & Total Stars
   - Language Badge
   Muxes audio and outputs a production-ready `.mp4` file.

---

## 💻 How to Run

### 1. Generate Video for Today's #1 Trending Repo
```bash
python main.py
```

### 2. Generate Video for #2 or #3 Trending Repo
```bash
python main.py --rank 2
python main.py --rank 3
```

### 3. Generate Video for Any Custom GitHub Repository
```bash
python main.py --repo owner/repository-name
```
*Example:* `python main.py --repo facebook/react`

---

## 🔑 Adding Your Gemini API Key (Optional)

You can pass your Gemini API key in an `.env` file or environment variable:
```env
GEMINI_API_KEY=your_gemini_api_key_here
DEFAULT_VOICE=en-US-ChristopherNeural
```
When provided, Gemini will analyze the full README and tailor a unique viral script for every single video. If no API key is present, the built-in smart template works automatically.
