import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"

STATIC_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

from trending_fetcher import fetch_trending_repos, fetch_repo_readme, fetch_repo_metadata, parse_github_url_or_name
from script_generator import generate_voiceover_script
from tts_engine import generate_voiceover_audio
from build_gittrend_reel import build_instant_gittrend_reel
from config import GEMINI_KEYS, DEFAULT_DEEPMIND_VOICE, NORMAL_SCROLL_SPEED_PPS

app = FastAPI(title="FondPeace Studio — GitTrend Reel Engine", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory progress tracking
job_progress = {
    "status": "idle",
    "percentage": 0,
    "message": "Ready to generate.",
    "result": None,
    "error": None
}

class ScriptRequest(BaseModel):
    repo_name: str

class RenderRequest(BaseModel):
    repo_name: str
    voice_name: str = "Puck"
    emotion_style: str = "high-energy viral storytelling"
    scroll_speed: float = NORMAL_SCROLL_SPEED_PPS
    brand_enabled: bool = True
    brand_type: str = "text"
    brand_text: str = "@FondPeace"
    brand_image_url: str = ""
    brand_x: int = 490
    brand_y: int = 1210
    custom_script: Optional[str] = None
    custom_caption: Optional[str] = None

@app.get("/api/status")
async def get_system_status():
    return {
        "status": "online",
        "api_keys_loaded": len(GEMINI_KEYS),
        "default_voice": DEFAULT_DEEPMIND_VOICE,
        "default_scroll_speed": NORMAL_SCROLL_SPEED_PPS,
        "output_count": len(list(OUTPUT_DIR.glob("*.mp4")))
    }

@app.get("/api/trending")
async def get_trending_repos():
    try:
        repos = fetch_trending_repos()
        return {"success": True, "count": len(repos), "repos": repos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class RepoLookupRequest(BaseModel):
    url_or_name: str

@app.post("/api/lookup-repo")
async def lookup_repo(req: RepoLookupRequest):
    try:
        repo_data = fetch_repo_metadata(req.url_or_name)
        if not repo_data or not repo_data.get("name"):
            raise HTTPException(status_code=400, detail="Could not parse GitHub repository")
        return {"success": True, "repo": repo_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/script")
async def get_repo_script(req: ScriptRequest):
    try:
        readme = fetch_repo_readme(req.repo_name)
        repo_info = fetch_repo_metadata(req.repo_name)
        vo, caption = generate_voiceover_script(repo_info, readme)
        return {
            "success": True,
            "repo_name": repo_info.get("name", req.repo_name),
            "voiceover_script": vo,
            "post_caption": caption
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class LogoUpload(BaseModel):
    image_base64: str
    filename: Optional[str] = "custom_logo.png"

@app.post("/api/upload-logo")
async def upload_logo(payload: LogoUpload):
    try:
        import base64
        data = payload.image_base64
        if "," in data:
            data = data.split(",", 1)[1]
        raw_bytes = base64.b64decode(data)
        file_path = STATIC_DIR / payload.filename
        with open(file_path, "wb") as f:
            f.write(raw_bytes)
        return {"success": True, "url": f"/static/{payload.filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_render_task(req: RenderRequest):
    global job_progress
    job_progress["status"] = "rendering"
    job_progress["percentage"] = 5
    job_progress["message"] = "Starting render..."
    job_progress["result"] = None
    job_progress["error"] = None

    def update_cb(pct, msg):
        job_progress["percentage"] = pct
        job_progress["message"] = msg

    try:
        result = asyncio.run(build_instant_gittrend_reel(
            repo_target=req.repo_name,
            voice_name=req.voice_name,
            emotion_style=req.emotion_style,
            scroll_speed=req.scroll_speed,
            brand_enabled=req.brand_enabled,
            brand_type=req.brand_type,
            brand_text=req.brand_text,
            brand_image_url=req.brand_image_url,
            brand_x=req.brand_x,
            brand_y=req.brand_y,
            custom_script=req.custom_script,
            custom_caption=req.custom_caption,
            progress_callback=update_cb
        ))
        job_progress["status"] = "completed"
        job_progress["percentage"] = 100
        job_progress["message"] = "Reel rendered successfully!"
        job_progress["result"] = result
    except Exception as e:
        job_progress["status"] = "failed"
        job_progress["error"] = str(e)
        job_progress["message"] = f"Render failed: {e}"

@app.post("/api/render")
async def start_render(req: RenderRequest, bg_tasks: BackgroundTasks):
    global job_progress
    if job_progress["status"] == "rendering":
        return {"success": False, "message": "A render job is already running."}
    
    bg_tasks.add_task(run_render_task, req)
    return {"success": True, "message": "Render task initiated."}

@app.get("/api/progress")
async def get_progress():
    return job_progress

@app.get("/api/videos")
async def list_videos():
    videos = []
    for f in sorted(OUTPUT_DIR.glob("*.mp4"), key=os.path.getmtime, reverse=True):
        videos.append({
            "filename": f.name,
            "url": f"/output/{f.name}",
            "size_mb": round(f.stat().st_size / (1024*1024), 2),
            "created": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        })
    return {"videos": videos}

# Mount static and output folders
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

@app.get("/", response_class=FileResponse)
async def serve_index():
    return FileResponse(STATIC_DIR / "index.html")

if __name__ == "__main__":
    import uvicorn
    from datetime import datetime
    print("🚀 Starting FondPeace Studio Server on http://127.0.0.1:8000 ...")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)
