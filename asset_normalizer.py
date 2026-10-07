import re
from urllib.parse import urljoin

def enable_markdown_in_html(text: str) -> str:
    """
    Ensures that markdown inside HTML tags (like <div align="center"> or <p align="center">)
    is properly recognized and parsed by python-markdown by adding markdown="1".
    """
    if not text:
        return ""
    def add_md_attr(m):
        tag = m.group(0)
        if 'markdown=' in tag.lower():
            return tag
        # Replace the trailing '>' with ' markdown="1">'
        return tag[:-1] + ' markdown="1">'
    
    # Target common container tags used in GitHub READMEs
    return re.sub(r'<(div|p|header|section|table|td|th)\b[^>]*>', add_md_attr, text, flags=re.IGNORECASE)

def normalize_github_readme_html(html: str, repo_name: str) -> str:
    """
    Transforms all relative image and asset URLs in GitHub markdown HTML
    into absolute raw GitHub CDN URLs so that no images are broken on the stage.
    """
    if not html or not repo_name or "/" not in repo_name:
        return html

    owner, repo = repo_name.split("/", 1)
    raw_head_base = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/"

    def resolve_url(src: str) -> str:
        s = src.strip()
        if not s or s.startswith(("http://", "https://", "data:", "#")):
            return s
        if s.startswith("//"):
            return "https:" + s

        clean = s.lstrip("/")
        # Check if URL starts with owner/repo/raw/... or owner/repo/blob/...
        pattern = rf"^{re.escape(owner)}/{re.escape(repo)}/(?:raw|blob)/([^/]+)/(.*)$"
        m = re.match(pattern, clean, re.IGNORECASE)
        if m:
            branch = m.group(1)
            rest = m.group(2)
            return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{rest}"

        # Otherwise relative to repo root HEAD
        clean_rel = clean.lstrip("./")
        return urljoin(raw_head_base, clean_rel)

    # 1. Fix <img ... src="..." >
    def fix_img_src(match):
        full_tag = match.group(0)
        src = match.group(1)
        fixed_src = resolve_url(src)
        return full_tag.replace(f'src="{src}"', f'src="{fixed_src}"').replace(f"src='{src}'", f"src='{fixed_src}'")

    normalized = re.sub(r'<img[^>]+src=["\']([^"\']+)["\']', fix_img_src, html, flags=re.IGNORECASE)

    # 2. Fix <source ... srcset="..." > and <img ... srcset="..." >
    def fix_srcset(match):
        full_tag = match.group(0)
        srcset = match.group(1)
        fixed_srcset = resolve_url(srcset)
        return full_tag.replace(f'srcset="{srcset}"', f'srcset="{fixed_srcset}"').replace(f"srcset='{srcset}'", f"srcset='{fixed_srcset}'")

    normalized = re.sub(r'<source[^>]+srcset=["\']([^"\']+)["\']', fix_srcset, normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'<img[^>]+srcset=["\']([^"\']+)["\']', fix_srcset, normalized, flags=re.IGNORECASE)

    # 3. Add styling & script guard: hides broken images on actual error without blocking loading images
    image_guard = """
    <style>
      img:not([src]), img[src=""] { display: none !important; }
      #readme-viewport img { max-width: 100%; height: auto; }
      #readme-viewport a > img { display: inline-block; vertical-align: middle; margin: 2px; }
    </style>
    <script>
      (function() {
        document.querySelectorAll('#readme-viewport img').forEach(function(img) {
          img.addEventListener('error', function() { this.style.display = 'none'; });
        });
      })();
    </script>
    """
    normalized += image_guard
    return normalized
