import os
import sys
import json
import re
import requests
from typing import Dict, Tuple

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from config import GEMINI_KEYS

CANDIDATE_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-flash-latest",
    "gemini-3.1-flash-lite"
]

def clean_gemini_markdown(text: str) -> str:
    if not text:
        return ""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json|markdown)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()

def clean_social_media_caption(text: str) -> str:
    """
    Sanitizes AI-generated captions for Instagram, YouTube Shorts, Facebook Reels, and Threads.
    Completely removes markdown asterisks (**bold**, *italic*), backtick code blocks (```bash),
    and markdown headers, while preserving emojis, clean unicode bullets (•), and hashtags (#viral).
    """
    if not text:
        return ""
    
    # 1. Strip code fence blocks while preserving the command inside
    # e.g. ```bash\ngit clone ...\n``` -> git clone ...
    text = re.sub(r"```(?:bash|sh|zsh|python|javascript|json)?\s*\n?([\s\S]*?)```", r"\1", text)
    # Inline code ticks `foo` -> foo
    text = re.sub(r"`([^`]+)`", r"\1", text)
    
    # 2. Strip bold/italic markdown (**text**, *text*, __text__)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    
    # 3. Clean line by line
    lines = []
    for line in text.split("\n"):
        # Convert markdown headers ("### Header", "## Header") that are NOT hashtags
        # Note: A markdown header has space after hash, e.g. "### Title", while hashtags are "#trending"
        line_clean = re.sub(r"^#{1,6}\s+", "", line)
        
        # Convert bullet points: "* " or "- " -> "• "
        if re.match(r"^\s*[\*\-]\s+", line_clean):
            line_clean = re.sub(r"^\s*[\*\-]\s+", "• ", line_clean)
            
        # Clean any remaining rogue asterisks or underscores used for emphasis
        line_clean = re.sub(r"(?<=\s)\*([^*\n]+)\*(?=\s|$)", r"\1", line_clean)
        line_clean = line_clean.replace("**", "").replace("*", "")
        
        lines.append(line_clean)
        
    cleaned_caption = "\n".join(lines)
    # Collapse 3+ consecutive newlines to 2
    cleaned_caption = re.sub(r"\n{3,}", "\n\n", cleaned_caption)
    return cleaned_caption.strip()

def generate_voiceover_script(repo: Dict[str, str], readme_excerpt: str = "") -> Tuple[str, str]:
    """
    Generates a crystal-clear, high-retention voiceover script (easy for anyone to understand)
    and a comprehensive, full-detail social media caption with features, quickstart, and viral hashtags.
    Uses multi-key Gemini AI (gemini-3.6-flash / 3.5-flash pool) with a smart fallback.
    Returns: (voiceover_script, post_caption)
    """
    name = repo.get("name", "Trending Project")
    short_name = name.split("/")[-1]
    desc = repo.get("description", "")
    stars_today = repo.get("stars_today", "")
    total_stars = repo.get("total_stars", "")
    lang = repo.get("language", "Code")
    url = repo.get("url", f"https://github.com/{name}")
    cta_keyword = short_name.replace("-", "").replace("_", "").lower()[:8]

    prompt = f"""
You are a world-class viral developer content creator producing an Instagram Reel / TikTok / YouTube Short about a trending open-source GitHub repository.

Repository Details:
- Name: {name} (Short: {short_name})
- Primary Language: {lang}
- Tagline: {desc}
- Momentum: {stars_today} gained today
- Total Stars: {total_stars}

README Excerpt:
{readme_excerpt[:2500]}

INSTRUCTIONS:
1. VOICEOVER SCRIPT (26 to 32 seconds, around 65 to 75 spoken words):
   - Hook in the first 3 seconds: address a common developer struggle or exciting breakthrough.
   - Explain what this project does in plain, simple English that even a beginner can easily understand.
   - Mention 2 specific powerful features visible in the documentation on screen.
   - Mention that it's going viral right now with {stars_today} on GitHub.
   - End with a clear call to action: "Comment '{cta_keyword.upper()}', and I'll send you the direct repo link!"
   - NO markdown asterisks, no sound effects, no emojis in the voiceover script. ONLY plain spoken words.

2. POST CAPTION & HASHTAGS (FOR INSTAGRAM / YOUTUBE SHORTS / THREADS / FACEBOOK REELS):
   CRITICAL FORMATTING REQUIREMENT:
   DO NOT USE ANY MARKDOWN SYNTAX IN THE CAPTION! Instagram, YouTube, Facebook, and Threads do NOT parse markdown!
   - NEVER use markdown bold/italic asterisks (NO `**`, NO `*`).
   - NEVER use markdown code blocks (NO ```bash or ``` fences). Write commands on a clean line (e.g. git clone {url}.git).
   - Use clean unicode bullet points (• ) for lists, NEVER markdown `* ` or `- `.
   - Use emoji accents for section titles (e.g. 💡 What is it:, 🚀 Why it's blowing up today:, ⚡ Key Features:).
   
   Structure:
   - Catchy title with fire/rocket emojis
   - 💡 What is it: (Simple plain English explanation)
   - 🚀 Why it's blowing up today: (+{stars_today}, total stars)
   - ⚡ Key Features: (3-4 bullet points starting with • and emojis)
   - 🛠️ Quickstart command: (Plain single line command)
   - 💻 Language & Tech stack:
   - 🔗 How to get the link:
   - 🌐 Website CTA: "Discuss this tool & discover more daily dev reels on fondpeace.com"
   - 👇 Call to Action: "Comment '{cta_keyword.upper()}' below and I'll DM you the link!"
   - 🏷️ 25+ viral hashtags for GitHub, coding, developer reels, and AI.

OUTPUT FORMAT EXACTLY:
---VOICEOVER---
<spoken script text here>
---CAPTION---
<full plain social caption here>
"""

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048
        }
    }

    # Try multi-key Gemini pool across candidate models
    for key_idx, key in enumerate(GEMINI_KEYS):
        for model in CANDIDATE_MODELS:
            url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            try:
                res = requests.post(url_gemini, headers=headers, json=payload, timeout=25)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            raw_out = clean_gemini_markdown(parts[0]["text"])
                            if "---VOICEOVER---" in raw_out and "---CAPTION---" in raw_out:
                                split_parts = raw_out.split("---CAPTION---")
                                vo = split_parts[0].replace("---VOICEOVER---", "").strip()
                                raw_caption = split_parts[1].strip()
                                # Clean vo of any stray asterisks
                                vo = re.sub(r'[*_#`]', '', vo).strip()
                                # Sanitize caption to 100% clean social media format (no markdown asterisks or code fences)
                                caption = clean_social_media_caption(raw_caption)
                                print(f"✅ Generated high-retention script & clean social caption via Gemini AI ({model}, Key #{key_idx+1})!")
                                return vo, caption
                elif res.status_code == 429:
                    print(f"[Gemini Script] Rate limit on Key #{key_idx+1}. Failing over...")
                    break
            except Exception as e:
                continue

    # Fallback High-Retention Script & Full-Detail Clean Social Caption
    print("[Notice] Using built-in high-retention script template.")
    clean_desc = desc if desc else f"A powerful new open-source developer tool for {lang}."
    vo_script = (
        f"If you are still building everything from scratch, stop. "
        f"This new breakout GitHub repository called {short_name} is blowing up right now. "
        f"{clean_desc} "
        f"It is completely open source, super lightweight, and already gained {stars_today} on GitHub. "
        f"You can set it up in seconds and supercharge your entire workflow. "
        f"Comment '{cta_keyword}', and I will send you the direct repo link right now!"
    )

    caption = (
        f"🚀 NEW TRENDING GITHUB REPO: {name}\n\n"
        f"💡 What is it?\n"
        f"{clean_desc}\n\n"
        f"🔥 Why It's Blowing Up Today:\n"
        f"• 📈 Gained {stars_today} in the last 24 hours alone!\n"
        f"• 🏆 Total Stars: ★ {total_stars}\n"
        f"• 💻 Language: {lang}\n"
        f"• ⚡ Instant setup with zero friction\n"
        f"• 🔒 100% Free & Open Source\n\n"
        f"🛠️ Quickstart:\n"
        f"git clone {url}.git\n\n"
        f"🔗 Repository Link:\n"
        f"{url}\n\n"
        f"🌐 Discuss this tool & discover more daily dev reels on:\n"
        f"👉 fondpeace.com\n\n"
        f"👇 Comment '{cta_keyword.upper()}' below and I'll DM you the link directly!\n"
        f"💾 Save this reel so you don't lose it for your next project 🚀\n\n"
        f"#github #trending #opensource #coding #programming #developer #{lang.lower()} "
        f"#softwareengineer #webdev #techreels #pythoncode #aitools #agenticai #devlife "
        f"#learntocode #coder #techtrends #githubtrending #codinglife #automation #buildinpublic "
        f"#softwaredeveloper #fullstack #techcommunity #programmer #techtok"
    )

    return vo_script, clean_social_media_caption(caption)

if __name__ == "__main__":
    dummy_repo = {
        "name": "Panniantong/Agent-Reach",
        "description": "Give your AI agent eyes to see the entire internet. Read & search Twitter, Reddit, YouTube, GitHub — one CLI, zero API fees.",
        "stars_today": "+1,696 stars",
        "total_stars": "90,018",
        "language": "Python",
        "url": "https://github.com/Panniantong/Agent-Reach"
    }
    v, c = generate_voiceover_script(dummy_repo)
    print("VOICEOVER SCRIPT:")
    print(v)
    print("\nFULL POST CAPTION:")
    print(c)
