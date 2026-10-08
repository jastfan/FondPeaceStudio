import os
import sys
import time
import subprocess
import urllib.request
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent
SERVER_URL = "http://127.0.0.1:8000"
APP_DATA_DIR = BASE_DIR / ".app_profile"
APP_DATA_DIR.mkdir(exist_ok=True)

def is_server_online():
    try:
        req = urllib.request.Request(f"{SERVER_URL}/api/status", headers={"User-Agent": "FondPeaceApp"})
        with urllib.request.urlopen(req, timeout=1.5) as res:
            if res.status == 200:
                data = json.loads(res.read().decode())
                return data.get("status") == "online"
    except Exception:
        pass
    return False

def ensure_server_running():
    if is_server_online():
        print("✅ FondPeace Studio server is already running on http://127.0.0.1:8000")
        return None

    print("🚀 Starting FondPeace Studio background engine...")
    server_script = BASE_DIR / "server.py"
    log_file = BASE_DIR / "server.log"
    log_fp = open(log_file, "a", encoding="utf-8")

    pythonw = Path(sys.executable).with_name("pythonw.exe")
    exe_to_use = str(pythonw) if pythonw.exists() else sys.executable

    # Launch detached server process with pythonw (official Windows headless python)
    if os.name == 'nt':
        proc = subprocess.Popen(
            [exe_to_use, str(server_script)],
            cwd=str(BASE_DIR),
            stdout=log_fp,
            stderr=log_fp,
            close_fds=True
        )
    else:
        proc = subprocess.Popen(
            [exe_to_use, str(server_script)],
            cwd=str(BASE_DIR),
            stdout=log_fp,
            stderr=log_fp
        )

    # Wait for server to become responsive (Torch/Whisper takes ~8-12s)
    for i in range(60):
        time.sleep(0.5)
        if is_server_online():
            print("✨ FondPeace Studio engine online!")
            return proc

    print("⚠️ Warning: Server startup took longer than expected, opening app window...")
    return proc

def find_app_browser():
    candidates = [
        # Windows Chrome
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        # Windows Edge
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        # Windows Brave
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        # macOS Chrome / Edge / Brave
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        # Linux
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/brave-browser",
        "/usr/bin/microsoft-edge",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def launch_native_app():
    ensure_server_running()

    browser = find_app_browser()
    if not browser:
        print("⚠️ Chromium-based browser not found. Opening in default browser...")
        import webbrowser
        webbrowser.open(SERVER_URL)
        return

    print("🎬 Opening FondPeace Studio in standalone native window (No URL / Frameless)...")
    cmd = [
        browser,
        f"--app={SERVER_URL}",
        "--window-size=1460,940",
        "--window-position=50,30"
    ]
    subprocess.Popen(cmd)
    print("🎉 FondPeace Studio App launched successfully!")

if __name__ == "__main__":
    launch_native_app()
