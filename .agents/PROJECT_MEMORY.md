# 🧠 Project Memory & Master State Registry

> **STRICT DIRECTIVE FOR ALL AGENTS:** 
> Before writing any code, ALWAYS read this file to understand what is ALREADY BUILT.
> NEVER rebuild, rewrite, or overwrite working modules. Only build upon existing verified foundations.

---

## 1. Project Invariants (Do NOT Break)
- **App Engine:** FastAPI backend (`server.py`) with persistent daemon on port 8000.
- **Multi-Device Parity:** Must bind to `0.0.0.0` for LAN/Mobile access (`http://10.231.34.170:8000`).
- **Zero-Route Desktop App Mode:** Chrome/Edge `--app=http://127.0.0.1:8000` standalone window with silent VBS launcher (`FondPeaceStudio.vbs`) and desktop shortcut.
- **Fast Startup (Lazy Loading):** Heavy modules (`whisper`, `torch`, `cv2`) MUST ONLY be imported on-demand inside `run_render_task()`, NEVER at top-level.

---

## 2. Completed & Verified Modules (DO NOT RE-DO)
- [x] **Video Rendering Engine:** 9:16 vertical video reel pipeline with Whisper sync & Gemini 3.6 script (`build_gittrend_reel.py`, `tts_engine.py`).
- [x] **Standalone Desktop Launcher:** `FondPeaceStudio.vbs`, `FondPeaceStudio.bat`, `Launch_FondPeace_Studio.bat`, `Stop_FondPeace_Studio.bat`, desktop shortcut `.lnk`.
- [x] **Multi-Device & PWA Integration:** `manifest.json`, `sw.js` (root scope), touch dragging for watermark, safe-area insets for iPhone & Android navigation.
- [x] **LAN Connect Modal:** Dynamic `/api/network-info` with instant QR code rendering in UI header.
- [x] **Remote macOS Launcher:** `FondPeaceStudio_Mac.command` with Chromium path discovery.

---

## 3. Active Task Queue & Roadmap
- [ ] **State Machine & Task Partitioning:** Autonomous delegation between Planner, Builder, and QA agents.
- [ ] **Cross-Session Memory Graph:** Continuous sync of architectural decisions via Memory MCP.

---

## 4. Architectural Decision Records (ADR)
- **ADR-001 (Process Decoupling):** Launcher must NOT kill `server_proc` upon Chrome CLI exit. Server runs as persistent background daemon.
- **ADR-002 (PWA Root Scope):** Service worker registered at `/sw.js` with `{ scope: '/' }` and served directly from root in FastAPI.
- **ADR-003 (Fluid Canvas):** Preview stage uses aspect-ratio 9:16 with dynamic scaling instead of rigid CSS transforms.
