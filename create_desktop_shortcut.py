import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ICON_PATH = BASE_DIR / "app_icon.ico"
VBS_PATH = BASE_DIR / "FondPeaceStudio.vbs"

desktop_dir = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
if not desktop_dir.exists():
    desktop_dir = Path.home() / "Desktop"

shortcut_path = desktop_dir / "FondPeace Studio.lnk"

# Pure PowerShell shortcut creation (100% reliable on Windows)
ps_script = f"""
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut('{str(shortcut_path)}')
$s.TargetPath = 'wscript.exe'
$s.Arguments = '"{str(VBS_PATH)}"'
$s.WorkingDirectory = '{str(BASE_DIR)}'
$s.IconLocation = '{str(ICON_PATH)},0'
$s.Description = 'FondPeace Studio — Viral Reel Engine Desktop App'
$s.Save()
"""

temp_ps = BASE_DIR / "_temp_create_shortcut.ps1"
with open(temp_ps, "w", encoding="utf-8") as f:
    f.write(ps_script)

res = os.system(f'powershell -ExecutionPolicy Bypass -File "{str(temp_ps)}"')
if temp_ps.exists():
    temp_ps.unlink()

if res == 0 and shortcut_path.exists():
    print("[SUCCESS] FondPeace Studio Desktop App shortcut created successfully at: " + str(shortcut_path))
else:
    print("[ERROR] Failed to create shortcut")
