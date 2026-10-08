---
name: auto-debugger
description: Autonomous system troubleshooter for ports, detached processes, network routes, and media pipelines.
---

# Auto-Debugger Skill Runbook

Use this skill whenever diagnosing server, network, or application issues:

1. **Check Port Availability & Process Conflicts:**
   - Detect what PID is listening on port 8000 using PowerShell or netstat.
   - Cleanly terminate blocking zombie processes before starting servers.

2. **Network & Multi-Device Verification:**
   - Verify server binds to `0.0.0.0` for Wi-Fi / LAN access.
   - Test both `http://127.0.0.1:8000` and LAN IP `http://<IP>:8000`.

3. **Standalone App Window Validation:**
   - Check if Chromium (`chrome.exe`, `msedge.exe`) exists and supports `--app=...` mode.
   - Ensure the server process is not prematurely terminated when the browser CLI launcher returns.

4. **Instant Self-Healing:**
   - Apply fixes directly, re-test endpoints, and report results concisely.
