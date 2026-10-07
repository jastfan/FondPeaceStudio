import os
import sys
import json
import base64
import time
import re
import requests
import subprocess
import asyncio
from pathlib import Path
from typing import List, Tuple, Dict
from mutagen.mp3 import MP3
import edge_tts
import imageio_ffmpeg

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from config import (
    TEMP_DIR, 
    FFMPEG_PATH, 
    GEMINI_KEYS, 
    DEFAULT_DEEPMIND_VOICE, 
    FALLBACK_EDGE_VOICE
)

# Active Google DeepMind Native Studio TTS Models
TTS_MODELS = [
    "gemini-2.5-flash-preview-tts",
    "gemini-3.1-flash-tts-preview",
    "gemini-2.5-pro-preview-tts"
]

def split_text_into_chunks(text: str, max_words: int = 120) -> List[str]:
    """
    Splits text into optimal narrative chunks (~80-120 words) at natural sentence and paragraph boundaries.
    Prevents API duration limits and allows lossless part-by-part saving with multi-key failover.
    """
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    chunks = []
    current_chunk = []
    current_count = 0

    for p in paragraphs:
        words = p.split()
        if len(words) > max_words:
            sentences = re.split(r'([।\.!\?]+[\s\n]*)', p)
            temp_sent = ""
            for s in sentences:
                temp_sent += s
                if len(temp_sent.split()) >= max_words:
                    if current_chunk:
                        chunks.append(" ".join(current_chunk))
                        current_chunk = []
                        current_count = 0
                    chunks.append(temp_sent.strip())
                    temp_sent = ""
            if temp_sent.strip():
                if current_count + len(temp_sent.split()) <= max_words:
                    current_chunk.append(temp_sent.strip())
                    current_count += len(temp_sent.split())
                else:
                    if current_chunk:
                        chunks.append(" ".join(current_chunk))
                    current_chunk = [temp_sent.strip()]
                    current_count = len(temp_sent.split())
        else:
            if current_count + len(words) <= max_words:
                current_chunk.append(p)
                current_count += len(words)
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [p]
                current_count = len(words)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return [c.strip() for c in chunks if c.strip()] or [text]

def merge_audio_chunks(file_list: List[str], output_path: str) -> str:
    """Merges multiple MP3 audio chunks into one single continuous 320kbps MP3 file seamlessly via FFmpeg."""
    if len(file_list) == 1:
        import shutil
        shutil.copyfile(file_list[0], output_path)
        return output_path

    concat_txt = output_path + ".concat.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for fp in file_list:
            f.write(f"file '{os.path.abspath(fp).replace(os.sep, '/')}'\n")

    cmd = [
        FFMPEG_PATH, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_txt,
        "-c:a", "libmp3lame",
        "-b:a", "320k",
        output_path
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        if os.path.exists(concat_txt):
            os.remove(concat_txt)

    return output_path

def synthesize_deepmind_audio(
    keys: List[str],
    voice_name: str,
    text: str,
    output_path: str,
    emotion_style: str = "engaging storytelling"
) -> str:
    """
    Synthesizes speech using 100% native Google DeepMind audio model (gemini-2.5-flash-preview-tts).
    Supports multi-API-key automatic failover pool to bypass rate limits instantly.
    Converts 24kHz raw PCM to broadcast-grade 320kbps MP3 with natural human inflection and emotional tone.
    """
    if not keys:
        raise ValueError("Google Gemini API Key is required for Google DeepMind Voice synthesis.")

    headers = {"Content-Type": "application/json"}
    prompt = f"Speak with natural human inflection, realistic micro-pauses, and {emotion_style} in English: {text}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": voice_name or "Puck"
                    }
                }
            }
        }
    }

    last_error = "Unknown error"
    valid_keys = [k for k in keys if k]

    for pool_round in range(5):
        for active_key in list(valid_keys):
            for model_name in TTS_MODELS:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={active_key}"
                for attempt in range(2):
                    try:
                        res = requests.post(url, headers=headers, json=payload, timeout=45)
                        if res.status_code == 200:
                            data = res.json()
                            candidates = data.get("candidates", [])
                            if not candidates or "content" not in candidates[0]:
                                raise ValueError("No audio content returned from Google DeepMind Voice API.")

                            parts = candidates[0]["content"].get("parts", [])
                            if not parts or "inlineData" not in parts[0]:
                                raise ValueError("Audio inlineData missing in Google Voice response.")

                            audio_b64 = parts[0]["inlineData"].get("data", "")
                            raw_pcm = base64.b64decode(audio_b64)

                            temp_pcm = output_path + f"_{attempt}.pcm"
                            with open(temp_pcm, "wb") as f:
                                f.write(raw_pcm)

                            # Convert PCM (s16le 24kHz mono) to 320kbps MP3 via FFmpeg
                            conv_cmd = [
                                FFMPEG_PATH, "-y",
                                "-f", "s16le",
                                "-ar", "24000",
                                "-ac", "1",
                                "-i", temp_pcm,
                                "-c:a", "libmp3lame",
                                "-b:a", "320k",
                                output_path
                            ]
                            try:
                                subprocess.run(conv_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            finally:
                                if os.path.exists(temp_pcm):
                                    os.remove(temp_pcm)

                            return output_path

                        elif res.status_code == 429:
                            last_error = f"Rate limit (429) on Key {active_key[:8]}..."
                            print(f"[DeepMind TTS] Rate limit on Key {active_key[:8]}... Failing over to next key...")
                            break
                        elif res.status_code in [401, 403]:
                            last_error = f"Authentication Error ({res.status_code})"
                            if active_key in valid_keys:
                                valid_keys.remove(active_key)
                            break
                        elif res.status_code == 503:
                            time.sleep(1.0)
                            continue
                        else:
                            last_error = f"HTTP {res.status_code}: {res.text[:150]}"
                            time.sleep(1.0)
                    except Exception as e:
                        last_error = str(e)
                        time.sleep(1.0)

        # Quota buffer pause if all keys in pool hit rate limit in this round
        if pool_round < 4:
            pause_sec = 5.0 * (pool_round + 1)
            print(f"[DeepMind TTS] ⏳ Quota buffer pause ({pause_sec:.0f}s) before next retry round...")
            time.sleep(pause_sec)

    raise RuntimeError(f"Google DeepMind Voice Synthesis Error: {last_error}")

async def synthesize_edge_tts_fallback(text: str, voice: str, output_path: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def generate_voiceover_audio(
    text: str, 
    voice_name: str = DEFAULT_DEEPMIND_VOICE, 
    emotion_style: str = "high-energy viral storytelling",
    filename: str = "voiceover.mp3"
) -> Tuple[str, float]:
    """
    Robust multi-tier voiceover generator with chunking & multi-key failover:
    - Splits text into optimal narrative chunks if length is substantial.
    - Synthesizes each chunk with Google DeepMind Studio TTS (Puck), rotating keys round-robin.
    - If a chunk hits an error, preserves completed chunks and merges them cleanly.
    - Tier-2 fallback to Microsoft Neural edge-tts if Google keys are completely exhausted.
    Returns: (output_path, duration_seconds)
    """
    clean_text = text.strip()
    output_path = str(TEMP_DIR / filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    word_count = len(clean_text.split())

    # 1. Tier 1: Google DeepMind Native Studio Voice with 3-key pool & chunking
    if GEMINI_KEYS:
        try:
            print(f"[TTS] Synthesizing with Google DeepMind Native Studio Voice ({voice_name}, {emotion_style})...")
            
            # If text has multiple sentences / paragraphs or > 80 words, chunk it
            chunks = split_text_into_chunks(clean_text, max_words=90)
            
            if len(chunks) == 1:
                # Single chunk synthesis
                synthesize_deepmind_audio(
                    keys=GEMINI_KEYS,
                    voice_name=voice_name,
                    text=chunks[0],
                    output_path=output_path,
                    emotion_style=emotion_style
                )
            else:
                # Multi-chunk synthesis with part saving & rotation
                print(f"[TTS] Processing {len(chunks)} chunks for smooth delivery ({word_count} words)...")
                part_files = []
                base_name, ext = os.path.splitext(output_path)
                
                for idx, chunk in enumerate(chunks):
                    part_file = f"{base_name}_part_{idx+1}{ext}"
                    # Rotate key pool for round-robin load distribution
                    rotated_keys = GEMINI_KEYS[idx % len(GEMINI_KEYS):] + GEMINI_KEYS[:idx % len(GEMINI_KEYS)]
                    try:
                        print(f"[TTS] Synthesizing Part {idx+1}/{len(chunks)}...")
                        synthesize_deepmind_audio(
                            keys=rotated_keys,
                            voice_name=voice_name,
                            text=chunk,
                            output_path=part_file,
                            emotion_style=emotion_style
                        )
                        part_files.append(part_file)
                    except Exception as e:
                        print(f"[Warning] Part {idx+1} hit issue: {e}")
                        if part_files:
                            print(f"[TTS] Preserving {len(part_files)} completed audio parts...")
                            break
                        else:
                            raise
                    
                    if idx < len(chunks) - 1:
                        time.sleep(1.0) # Small breathing gap between API requests
                
                # Merge completed chunks
                if part_files:
                    merge_audio_chunks(part_files, output_path)
                    for pf in part_files:
                        try: os.remove(pf)
                        except: pass

            dur = float(MP3(output_path).info.length)
            print(f"✅ DeepMind Studio voice synthesized successfully! Duration: {dur:.2f}s")
            return output_path, dur

        except Exception as e:
            print(f"[Warning] DeepMind TTS pool error: {e}. Switching to Tier 2 Neural Fallback...")

    # 2. Tier 2: Edge-TTS Fallback
    print(f"[TTS] Using Tier 2 Neural Voice ({FALLBACK_EDGE_VOICE})...")
    asyncio.run(synthesize_edge_tts_fallback(clean_text, FALLBACK_EDGE_VOICE, output_path))
    dur = float(MP3(output_path).info.length)
    print(f"✅ Neural voice synthesized successfully! Duration: {dur:.2f}s")
    return output_path, dur

if __name__ == "__main__":
    sample = "Your AI agent is blind without internet access. Give it full vision with this breakout repo."
    f, d = generate_voiceover_audio(sample, voice_name="Puck", filename="test_deepmind.mp3")
    print(f"Result: {f} ({d:.2f}s)")
