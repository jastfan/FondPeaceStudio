import os
import json
from pathlib import Path
import imageio_ffmpeg

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"

OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

# Trending Registry URL
TRENDING_README_URL = "https://raw.githubusercontent.com/jastfan/github-trending/main/README.md"

# Read keys from capcut-video-studio config if available
CAPCUT_CONFIG_PATH = Path(r"C:\Users\hp\.gemini\antigravity\scratch\capcut-video-studio\config.json")
GEMINI_KEYS = []

if CAPCUT_CONFIG_PATH.exists():
    try:
        with open(CAPCUT_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            for k in ["gemini_api_key", "gemini_api_key_2", "gemini_api_key_3"]:
                val = cfg.get(k, "").strip()
                if val and val not in GEMINI_KEYS:
                    GEMINI_KEYS.append(val)
    except Exception as e:
        print(f"[Warning] Could not load capcut config: {e}")

# Also check environment variables
for env_k in ["GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"]:
    val = os.getenv(env_k, "").strip()
    if val and val not in GEMINI_KEYS:
        GEMINI_KEYS.append(val)

# Default Voice settings
DEFAULT_DEEPMIND_VOICE = "Puck"  # High-retention, expressive energetic voice
FALLBACK_EDGE_VOICE = "en-US-ChristopherNeural"

# Video dimensions (9:16 vertical Reel standard)
VIDEO_WIDTH = 720
VIDEO_HEIGHT = 1280

# Comfortable human reading scroll speed (pixels per second)
NORMAL_SCROLL_SPEED_PPS = 28.0
INITIAL_HOLD_SEC = 2.8
