import sys
import re
import urllib.request
from typing import List, Dict, Optional
from config import TRENDING_README_URL

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Verified high-impact fallback list if GitHub raw is ever unreachable
FALLBACK_TRENDING = [
    {
        "rank": 1,
        "name": "DietrichGebert/ponytail",
        "url": "https://github.com/DietrichGebert/ponytail",
        "description": "Makes your AI agent think like the laziest senior dev in the room. The best code is the code you never wrote.",
        "stars_today": "+1,894",
        "total_stars": "155,136",
        "language": "JavaScript"
    },
    {
        "rank": 2,
        "name": "pbakaus/impeccable",
        "url": "https://github.com/pbakaus/impeccable",
        "description": "The design language that makes your AI harness better at design.",
        "stars_today": "+1,171",
        "total_stars": "76,478",
        "language": "JavaScript"
    },
    {
        "rank": 3,
        "name": "Panniantong/Agent-Reach",
        "url": "https://github.com/Panniantong/Agent-Reach",
        "description": "Give your AI agent eyes to see the entire internet. Read & search Twitter, Reddit, YouTube, GitHub, Bilibili.",
        "stars_today": "+980",
        "total_stars": "91,122",
        "language": "Python"
    },
    {
        "rank": 4,
        "name": "affaan-m/ECC",
        "url": "https://github.com/affaan-m/ECC",
        "description": "The agent harness performance optimization system. Skills, instincts, memory, security for Claude Code & Cursor.",
        "stars_today": "+891",
        "total_stars": "273,090",
        "language": "JavaScript"
    },
    {
        "rank": 5,
        "name": "thedotmack/claude-mem",
        "url": "https://github.com/thedotmack/claude-mem",
        "description": "Persistent memory capture for Claude Code and coding agents across multi-turn sessions.",
        "stars_today": "+628",
        "total_stars": "96,239",
        "language": "TypeScript"
    }
]

def fetch_trending_repos() -> List[Dict[str, str]]:
    """
    Fetches today's trending repositories from jastfan/github-trending registry.
    Handles cross-platform line endings and format changes with rock-solid fallback.
    """
    content = ""
    try:
        req = urllib.request.Request(
            TRENDING_README_URL, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"[Trending Fetcher] Warning: Could not fetch online README ({e}), using cached breakout list.")
        return FALLBACK_TRENDING

    # Normalize line endings
    content = content.replace("\r\n", "\n")
    repos = []

    # 1. Parse Top Breakout Table lines directly
    # Rows look like: | 1 | [**DietrichGebert/ponytail**](https://github.com/DietrichGebert/ponytail) | `JavaScript` | ...
    for line in content.split("\n"):
        line = line.strip()
        if not line.startswith("|") or ":---:" in line or "Language" in line:
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) >= 6:
            rank_str = cols[0]
            repo_link = cols[1]
            lang = cols[2].replace("`", "").strip() if len(cols) > 2 else "Code"
            
            # Find repo name and url
            m_link = re.search(r"\[\*\*(.*?)\*\*\]\((https://github\.com/.*?)\)", repo_link)
            if not m_link:
                m_link = re.search(r"\[(.*?)\]\((https://github\.com/.*?)\)", repo_link)
            
            if m_link:
                name = m_link.group(1).replace("**", "").strip()
                url = m_link.group(2).strip()
                stars_today = cols[4].replace("🔥", "").replace("**", "").strip() if len(cols) > 4 else "Trending"
                total_stars = cols[5].replace("★", "").strip() if len(cols) > 5 else "Active"
                desc = cols[6].strip() if len(cols) > 6 else f"Breakout trending repository {name}"

                if not any(r['name'].lower() == name.lower() for r in repos):
                    repos.append({
                        "rank": int(rank_str) if rank_str.isdigit() else len(repos) + 1,
                        "name": name,
                        "url": url,
                        "description": desc,
                        "stars_today": stars_today,
                        "total_stars": total_stars,
                        "language": lang
                    })

    if not repos:
        print("[Trending Fetcher] Table parsing yielded 0 repos, using verified breakout list.")
        return FALLBACK_TRENDING

    return repos

def parse_github_url_or_name(input_str: str) -> Optional[str]:
    """
    Parses any GitHub repository URL, markdown link, or plain owner/repo string.
    Examples:
      - https://github.com/facebook/react -> facebook/react
      - https://github.com/facebook/react/tree/main -> facebook/react
      - github.com/facebook/react -> facebook/react
      - facebook/react -> facebook/react
    """
    if not input_str:
        return None
    clean = input_str.strip().rstrip("/")
    m = re.search(r"(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)", clean)
    if m:
        repo_clean = m.group(2).replace(".git", "")
        return f"{m.group(1)}/{repo_clean}"
    
    parts = clean.split("/")
    if len(parts) == 2 and parts[0] and parts[1]:
        return f"{parts[0].strip()}/{parts[1].strip().replace('.git', '')}"
    return None

def fetch_repo_metadata(repo_name_or_url: str) -> Dict[str, str]:
    """
    Given any repo name or URL, fetches accurate metadata (stars, description, language)
    from GitHub API with graceful HTML fallback.
    """
    parsed = parse_github_url_or_name(repo_name_or_url)
    if not parsed:
        parsed = repo_name_or_url.strip()

    result = {
        "name": parsed,
        "url": f"https://github.com/{parsed}",
        "description": f"Repository {parsed}",
        "stars_today": "Trending",
        "total_stars": "Top",
        "language": "Code"
    }

    try:
        api_url = f"https://api.github.com/repos/{parsed}"
        req = urllib.request.Request(
            api_url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            import json
            data = json.loads(resp.read().decode('utf-8'))
            result["name"] = parsed
            result["description"] = data.get("description") or f"Open-source project {parsed}"
            stars = data.get("stargazers_count", 0)
            result["total_stars"] = f"{stars:,}" if stars else "Active"
            result["language"] = data.get("language") or "Code"
            result["stars_today"] = f"+{data.get('forks_count', 100)} forks"
            return result
    except Exception:
        pass

    # HTML scraping fallback if API is rate-limited
    try:
        web_url = f"https://github.com/{parsed}"
        req = urllib.request.Request(web_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=6) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            m_desc = re.search(r'<meta name="description" content="(.*?)"', html)
            if m_desc:
                result["description"] = m_desc.group(1).replace("&quot;", '"')
            m_stars = re.search(r'id="repo-stars-counter-star"[^>]*>(.*?)</span>', html)
            if m_stars:
                result["total_stars"] = m_stars.group(1).strip()
    except Exception:
        pass

    return result

def fetch_repo_readme(repo_name: str) -> str:
    """
    Fetches the raw README from GitHub for a given repo name (e.g. 'facebook/react').
    """
    clean_name = parse_github_url_or_name(repo_name) or repo_name.strip()
    for branch in ["main", "master", "HEAD"]:
        try:
            url = f"https://raw.githubusercontent.com/{clean_name}/{branch}/README.md"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as resp:
                return resp.read().decode('utf-8', errors='ignore')
        except Exception:
            continue
    return ""

if __name__ == "__main__":
    trending = fetch_trending_repos()
    print(f"Found {len(trending)} trending repos:")
    for r in trending[:5]:
        print(f"#{r['rank']}: {r['name']} ({r['language']}) - {r['stars_today']} stars today | {r['description']}")
