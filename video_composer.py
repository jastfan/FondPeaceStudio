import os
import sys
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from config import FFMPEG_PATH, TEMP_DIR, OUTPUT_DIR, VIDEO_WIDTH

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

def create_header_overlay(
    repo_name: str, 
    stars_today: str, 
    total_stars: str, 
    lang: str,
    output_png: str = "header_overlay.png"
) -> str:
    """
    Generates a sleek, high-retention 1080px header banner with glassmorphism 
    and gradients to overlay at the top of the Reel.
    """
    img_path = str(TEMP_DIR / output_png)
    
    # 1080 x 280 transparent canvas
    w, h = VIDEO_WIDTH, 260
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Rounded Card Background
    card_margin = 30
    card_x0, card_y0 = card_margin, 40
    card_x1, card_y1 = w - card_margin, h - 20
    
    # Semi-transparent dark card with subtle neon border
    # Background
    draw.rounded_rectangle(
        [(card_x0, card_y0), (card_x1, card_y1)],
        radius=24,
        fill=(13, 17, 23, 235), # GitHub dark theme color with high opacity
        outline=(56, 139, 253, 180), # Sleek blue accent border
        width=3
    )
    
    # Load fonts (fallback to default if system font not found)
    try:
        font_sub = ImageFont.truetype("arialbd.ttf", 30)
        font_title = ImageFont.truetype("arialbd.ttf", 46)
        font_badge = ImageFont.truetype("arialbd.ttf", 28)
    except Exception:
        font_sub = ImageFont.load_default()
        font_title = ImageFont.load_default()
        font_badge = ImageFont.load_default()
        
    # Top Tag: "🔥 TODAY'S #1 GITHUB TRENDING"
    tag_text = "🔥 TODAY'S GITHUB BREAKOUT"
    draw.text((card_x0 + 35, card_y0 + 25), tag_text, fill=(255, 122, 0, 255), font=font_sub)
    
    # Repo Name (truncated if too long)
    display_name = repo_name if len(repo_name) < 28 else repo_name[:25] + "..."
    draw.text((card_x0 + 35, card_y0 + 70), display_name, fill=(255, 255, 255, 255), font=font_title)
    
    # Stats Badges: ⭐ Stars Today & Language
    badge_text = f"⭐ {stars_today} Today  •  ★ {total_stars} Total  •  💻 {lang}"
    draw.text((card_x0 + 35, card_y0 + 135), badge_text, fill=(139, 148, 158, 255), font=font_badge)
    
    img.save(img_path, "PNG")
    print(f"Generated header overlay: {img_path}")
    return img_path

def compose_final_video(
    video_path: str,
    audio_path: str,
    overlay_png: str,
    output_filename: str,
    audio_duration: float
) -> str:
    """
    Muxes the recorded webm video, mp3 audio, and overlay banner into a production-ready MP4.
    """
    final_output = str(OUTPUT_DIR / output_filename)
    
    # FFmpeg command:
    # 1. Input 0: video (.webm)
    # 2. Input 1: audio (.mp3)
    # 3. Input 2: header overlay (.png)
    # We overlay the PNG at top (y=20), encode as H.264 / AAC, and sync duration to audio
    
    cmd = [
        FFMPEG_PATH,
        "-y",
        "-i", video_path,
        "-i", audio_path,
        "-i", overlay_png,
        "-filter_complex",
        "[0:v][2:v]overlay=0:0[v_out]",
        "-map", "[v_out]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", f"{audio_duration + 1.0:.2f}",
        "-movflags", "+faststart",
        final_output
    ]
    
    print(f"[FFmpeg] Assembling final video into {final_output}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("[FFmpeg Error]:", res.stderr)
        raise RuntimeError(f"FFmpeg failed with code {res.returncode}")
        
    print(f"🎉 Successfully created final video: {final_output}")
    return final_output

if __name__ == "__main__":
    png = create_header_overlay("Panniantong/Agent-Reach", "+1,696 Stars", "90,018", "Python")
    print("Overlay created:", png)
