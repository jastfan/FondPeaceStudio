// FondPeace Studio — Interactive Engine v3
let currentRepo = null;
let currentTrendingList = [];
let brandConfig = {
  enabled: true,
  type: 'text',
  text: '@FondPeace',
  imageUrl: '',
  x: 490, // in 720x1280 video space
  y: 1210
};

// DOM Elements
const trendingContainer = document.getElementById('trending-list-container');
const btnRefreshTrending = document.getElementById('btn-refresh-trending');
const customRepoInput = document.getElementById('custom-repo-input');
const btnLoadCustom = document.getElementById('btn-load-custom');

// Preview Elements
const previewTabName = document.getElementById('preview-tab-name');
const previewAddressUrl = document.getElementById('preview-address-url');
const previewRepoTitle = document.getElementById('preview-repo-title');
const previewBrandElement = document.getElementById('preview-brand-element');
const previewBrandText = document.getElementById('preview-brand-text');
const draggableBranding = document.getElementById('draggable-branding');
const posReadout = document.getElementById('pos-readout');
const canvasStage = document.getElementById('canvas-stage');

// Settings Elements
const selectVoice = document.getElementById('select-voice');
const selectEmotion = document.getElementById('select-emotion');
const scrollSlider = document.getElementById('scroll-slider');
const scrollVal = document.getElementById('scroll-val');
const brandEnabledCheck = document.getElementById('brand-enabled-check');
const brandTextInput = document.getElementById('brand-text-input');
const logoFileInput = document.getElementById('logo-file-input');

// Script & Caption
const scriptTextarea = document.getElementById('script-textarea');
const captionTextarea = document.getElementById('caption-textarea');
const scriptWordCount = document.getElementById('script-word-count');
const btnCopyCaption = document.getElementById('btn-copy-caption');

// Render & Progress
const btnRender = document.getElementById('btn-render-reel');
const progressCard = document.getElementById('render-progress-card');
const progressBarFill = document.getElementById('progress-bar-fill');
const progressPctText = document.getElementById('progress-pct-text');
const progressDetailText = document.getElementById('progress-detail-text');
const progressStepText = document.getElementById('progress-step-text');
const videoOutputBox = document.getElementById('video-output-box');
const finalVideoPlayer = document.getElementById('final-video-player');
const btnDownloadVideo = document.getElementById('btn-download-video');

// 1. Initialize
document.addEventListener('DOMContentLoaded', () => {
  initDraggableBranding();
  loadTrendingRepos();
  loadRecentVideos();
  setupEventListeners();
});

function setupEventListeners() {
  btnRefreshTrending.addEventListener('click', loadTrendingRepos);
  
  async function handleLoadCustomRepo() {
    const val = customRepoInput.value.trim();
    if (!val) {
      alert("Please paste a GitHub repository URL or enter owner/repo (e.g. https://github.com/facebook/react)");
      return;
    }

    btnLoadCustom.disabled = true;
    btnLoadCustom.innerText = "⏳ Loading...";

    try {
      const res = await fetch('/api/lookup-repo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url_or_name: val })
      });
      const data = await res.json();
      if (data.success && data.repo) {
        const repo = data.repo;
        repo.rank = "Custom";
        const existingIdx = currentTrendingList.findIndex(r => r.name.toLowerCase() === repo.name.toLowerCase());
        if (existingIdx !== -1) {
          currentTrendingList[existingIdx] = { ...currentTrendingList[existingIdx], ...repo };
        } else {
          currentTrendingList.unshift(repo);
        }
        renderTrendingCards(currentTrendingList);
        const card = document.querySelector(`[data-repo-name="${repo.name}"]`);
        if (card) {
          document.querySelectorAll('.repo-card').forEach(c => c.classList.remove('active'));
          card.classList.add('active');
          card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        selectRepo(repo);
        customRepoInput.value = '';
      } else {
        alert("Failed to find repository. Please check the URL or name.");
      }
    } catch (err) {
      alert("Error loading repo: " + err);
    } finally {
      btnLoadCustom.disabled = false;
      btnLoadCustom.innerText = "✨ Import";
    }
  }

  btnLoadCustom.addEventListener('click', handleLoadCustomRepo);
  customRepoInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleLoadCustomRepo();
  });
  customRepoInput.addEventListener('paste', () => {
    setTimeout(handleLoadCustomRepo, 100);
  });

  scrollSlider.addEventListener('input', (e) => {
    scrollVal.innerText = `${e.target.value} px/s`;
  });

  brandTextInput.addEventListener('input', (e) => {
    brandConfig.text = e.target.value.trim() || '@FondPeace';
    brandConfig.type = 'text';
    previewBrandElement.innerHTML = `
      <span class="branding-dot"></span>
      <span id="preview-brand-text">${brandConfig.text}</span>
    `;
  });

  if (scrollSlider && scrollVal) {
    scrollSlider.addEventListener('input', (e) => {
      scrollVal.innerText = `${e.target.value} px/s (Calm GitTrend)`;
    });
  }

  brandEnabledCheck.addEventListener('change', (e) => {
    brandConfig.enabled = e.target.checked;
    draggableBranding.style.display = e.target.checked ? 'block' : 'none';
  });

  logoFileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async () => {
      const base64Data = reader.result;
      try {
        const res = await fetch('/api/upload-logo', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image_base64: base64Data, filename: file.name })
        });
        const data = await res.json();
        if (data.success) {
          brandConfig.type = 'image';
          brandConfig.imageUrl = data.url;
          previewBrandElement.innerHTML = `<img src="${data.url}" style="height:20px; border-radius:4px; object-fit:contain;">`;
        }
      } catch (err) {
        alert('Failed to upload logo: ' + err);
      }
    };
    reader.readAsDataURL(file);
  });

  btnCopyCaption.addEventListener('click', () => {
    if (!captionTextarea.value) return;
    navigator.clipboard.writeText(captionTextarea.value);
    const orig = btnCopyCaption.innerText;
    btnCopyCaption.innerText = '✅ Copied!';
    setTimeout(() => { btnCopyCaption.innerText = orig; }, 2000);
  });

  scriptTextarea.addEventListener('input', () => {
    const words = scriptTextarea.value.trim().split(/\s+/).filter(Boolean).length;
    scriptWordCount.innerText = `${words} words (~${Math.round(words / 2.5)}s)`;
  });

  btnRender.addEventListener('click', startReelRender);
}

// 2. Draggable Branding Engine (translates 360x640 preview to 720x1280 master space)
function initDraggableBranding() {
  let isDragging = false;
  let startX, startY, initialLeft, initialTop;

  draggableBranding.addEventListener('mousedown', (e) => {
    isDragging = true;
    startX = e.clientX;
    startY = e.clientY;
    initialLeft = draggableBranding.offsetLeft;
    initialTop = draggableBranding.offsetTop;
    e.preventDefault();
  });

  document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;

    const canvasRect = canvasStage.getBoundingClientRect();
    const elemRect = draggableBranding.getBoundingClientRect();

    let newLeft = Math.max(0, Math.min(canvasRect.width - elemRect.width, initialLeft + dx));
    let newTop = Math.max(0, Math.min(canvasRect.height - elemRect.height, initialTop + dy));

    draggableBranding.style.left = `${newLeft}px`;
    draggableBranding.style.top = `${newTop}px`;

    // Map 360x640 preview coordinates to 720x1280 video space
    brandConfig.x = Math.round(newLeft * 2);
    brandConfig.y = Math.round(newTop * 2);

    posReadout.innerText = `📍 Branding Position: X: ${brandConfig.x}px | Y: ${brandConfig.y}px (720x1280 Master)`;
  });

  document.addEventListener('mouseup', () => {
    isDragging = false;
  });
}

// 3. Load Trending Repositories
async function loadTrendingRepos() {
  trendingContainer.innerHTML = `
    <div style="text-align:center; padding: 40px; color: var(--text-muted); font-size: 13px;">
      ⏳ Scanning today's breakout repositories from GitHub...
    </div>
  `;

  try {
    const res = await fetch('/api/trending');
    const data = await res.json();
    const reposList = data.repos || data.trending || [];
    if (data.success && reposList.length > 0) {
      currentTrendingList = reposList;
      renderTrendingCards(reposList);
      // Select first repo by default
      selectRepo(reposList[0]);
    } else {
      trendingContainer.innerHTML = `<div style="padding:20px; color:#f85149;">No trending repositories found.</div>`;
    }
  } catch (err) {
    trendingContainer.innerHTML = `<div style="padding:20px; color:#f85149;">Failed to load trending: ${err}</div>`;
  }
}

function renderTrendingCards(repos) {
  trendingContainer.innerHTML = '';
  repos.forEach((repo, idx) => {
    const card = document.createElement('div');
    card.className = `repo-card ${idx === 0 ? 'active' : ''}`;
    card.dataset.repoName = repo.name;

    const parts = repo.name.split('/');
    const owner = parts.length > 1 ? parts[0] : '';
    const repoTitle = parts.length > 1 ? parts[1] : repo.name;

    card.innerHTML = `
      <div class="repo-card-top">
        <span class="repo-rank-pill">#${repo.rank || idx + 1} Trending</span>
        <span class="repo-stars-today">📈 ${repo.stars_today}</span>
      </div>
      <div class="repo-name" title="${repo.name}">
        ${owner ? `<span style="color:#94a3b8; font-weight:600; font-size:12.5px;">${owner} / </span>` : ''}
        <span style="color:#ffffff; font-weight:800;">${repoTitle}</span>
      </div>
      <div class="repo-desc">${repo.description || 'Breakout open-source project trending today on GitHub.'}</div>
      <div class="repo-meta">
        <span style="color:#fbbf24; font-weight:700;">★ ${repo.total_stars}</span>
        <span class="repo-lang-pill">${repo.language || 'Code'}</span>
      </div>
    `;

    card.addEventListener('click', () => {
      document.querySelectorAll('.repo-card').forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      selectRepo(repo);
    });

    trendingContainer.appendChild(card);
  });
}

// 4. Select Repository & Auto-Generate AI Script
async function selectRepo(repo) {
  currentRepo = repo;
  
  // 1. Update Selected Repository Full Details Card in Right Panel
  const selRank = document.getElementById('selected-repo-rank');
  const selLang = document.getElementById('selected-repo-lang');
  const selLink = document.getElementById('selected-repo-link');
  const selName = document.getElementById('selected-repo-name');
  const selDesc = document.getElementById('selected-repo-desc');
  const selToday = document.getElementById('selected-repo-today');
  const selStars = document.getElementById('selected-repo-stars');
  const btnCopyClone = document.getElementById('btn-copy-clone-cmd');

  const repoUrl = repo.url || `https://github.com/${repo.name}`;
  const repoShort = repo.name.split('/').pop();

  if (selRank) selRank.innerText = `#${repo.rank || 1} Trending`;
  if (selLang) selLang.innerText = `💻 ${repo.language || 'Code'}`;
  if (selLink) {
    selLink.href = repoUrl;
    selLink.innerText = `🔗 Open GitHub ↗`;
  }
  if (selName) selName.innerText = repo.name;
  if (selDesc) selDesc.innerText = repo.description || 'Trending open source project.';
  if (selToday) selToday.innerText = `📈 ${repo.stars_today || 'Trending'}`;
  if (selStars) selStars.innerText = `★ ${repo.total_stars || 'Active'}`;

  if (btnCopyClone) {
    btnCopyClone.onclick = () => {
      const cloneCmd = `git clone ${repoUrl}.git`;
      navigator.clipboard.writeText(cloneCmd);
      const orig = btnCopyClone.innerText;
      btnCopyClone.innerText = '✅ Copied!';
      setTimeout(() => { btnCopyClone.innerText = orig; }, 2000);
    };
  }

  // 2. Update 9:16 Center Phone Canvas Preview Mockup
  previewTabName.innerText = `GitHub - ${repo.name}`;
  previewAddressUrl.innerText = `github.com/${repo.name}#readme`;
  previewRepoTitle.innerText = repoShort;

  const previewTagline = document.getElementById('preview-repo-tagline');
  const previewStars = document.getElementById('preview-stars-badge');
  const previewToday = document.getElementById('preview-today-badge');
  const previewLang = document.getElementById('preview-lang-badge');
  const previewDesc = document.getElementById('preview-repo-desc');
  const previewCmd = document.getElementById('preview-cmd-badge');

  if (previewTagline) previewTagline.innerText = repo.description || 'High-retention open-source project.';
  if (previewStars) previewStars.innerText = `★ ${repo.total_stars || '10,000+'}`;
  if (previewToday) previewToday.innerText = `${repo.stars_today || 'Trending'} today`;
  if (previewLang) previewLang.innerText = repo.language || 'Code';
  if (previewDesc) previewDesc.innerText = repo.description || 'Breakout developer tool trending on GitHub.';
  if (previewCmd) previewCmd.innerText = `$ git clone ${repoUrl}.git`;

  // 3. Fetch AI Script & Clean Social Caption
  scriptTextarea.value = "⏳ Generating viral spoken script with Gemini 3.6 AI...";
  captionTextarea.value = "⏳ Generating clean social media caption (no markdown) & 25+ hashtags...";

  try {
    const res = await fetch('/api/script', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_name: repo.name })
    });
    const data = await res.json();
    if (data.success) {
      scriptTextarea.value = data.voiceover_script;
      captionTextarea.value = data.post_caption;
      const words = data.voiceover_script.trim().split(/\s+/).filter(Boolean).length;
      scriptWordCount.innerText = `${words} words (~${Math.round(words / 2.5)}s)`;
    }
  } catch (err) {
    scriptTextarea.value = "Error generating script. You can write your script manually here.";
  }
}

// 5. Start Reel Render with Live Progress Polling
async function startReelRender() {
  if (!currentRepo) {
    alert("Please select a trending repository first.");
    return;
  }

  btnRender.disabled = true;
  btnRender.innerText = "⏳ Rendering Reel in Progress...";
  progressCard.style.display = "block";
  videoOutputBox.style.display = "none";
  progressBarFill.style.width = "5%";
  progressPctText.innerText = "5%";
  progressStepText.innerText = "Initiating Production Pipeline...";

  const payload = {
    repo_name: currentRepo.name,
    voice_name: selectVoice.value,
    emotion_style: selectEmotion.value,
    scroll_speed: parseFloat(scrollSlider.value),
    brand_enabled: brandConfig.enabled,
    brand_type: brandConfig.type,
    brand_text: brandConfig.text,
    brand_image_url: brandConfig.imageUrl,
    brand_x: brandConfig.x,
    brand_y: brandConfig.y,
    custom_script: scriptTextarea.value,
    custom_caption: captionTextarea.value
  };

  try {
    const res = await fetch('/api/render', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (!data.success) {
      alert(data.message);
      btnRender.disabled = false;
      btnRender.innerText = "🚀 Render Viral Reel (9:16 MP4)";
      return;
    }

    // Start progress polling
    pollRenderProgress();
  } catch (err) {
    alert("Render failed: " + err);
    btnRender.disabled = false;
    btnRender.innerText = "🚀 Render Viral Reel (9:16 MP4)";
  }
}

function pollRenderProgress() {
  const interval = setInterval(async () => {
    try {
      const res = await fetch('/api/progress');
      const data = await res.json();

      const pct = data.percentage || 0;
      progressBarFill.style.width = `${pct}%`;
      progressPctText.innerText = `${pct}%`;
      progressDetailText.innerText = data.message || "Working...";

      if (data.status === 'completed') {
        clearInterval(interval);
        btnRender.disabled = false;
        btnRender.innerText = "🚀 Render Viral Reel (9:16 MP4)";
        progressStepText.innerText = "🎉 Complete!";
        
        // Show video player
        if (data.result && data.result.video_filename) {
          const videoUrl = `/output/${data.result.video_filename}`;
          finalVideoPlayer.src = videoUrl;
          btnDownloadVideo.href = videoUrl;
          btnDownloadVideo.setAttribute('download', data.result.video_filename);
          videoOutputBox.style.display = "flex";
          finalVideoPlayer.play();
          if (centerVideoPlayer && btnToggleCenterVideo) {
            centerVideoPlayer.src = videoUrl;
            centerVideoPlayer.style.display = 'block';
            centerVideoPlayer.play();
            btnToggleCenterVideo.style.display = 'inline-block';
            btnToggleCenterVideo.innerText = '📱 Edit Template';
          }
          loadRecentVideos();
        }
      } else if (data.status === 'failed') {
        clearInterval(interval);
        btnRender.disabled = false;
        btnRender.innerText = "🚀 Render Viral Reel (9:16 MP4)";
        alert("Render error: " + data.error);
      }
    } catch (err) {
      console.error("Progress poll error:", err);
    }
  }, 1200);
}

// 6. Recent Videos Gallery
const recentVideosList = document.getElementById('recent-videos-list');
const btnRefreshVideos = document.getElementById('btn-refresh-videos');

if (btnRefreshVideos) {
  btnRefreshVideos.addEventListener('click', loadRecentVideos);
}

async function loadRecentVideos() {
  if (!recentVideosList) return;
  try {
    const res = await fetch('/api/videos');
    const data = await res.json();
    if (!data.videos || data.videos.length === 0) {
      recentVideosList.innerHTML = '<div style="font-size:11px; color:var(--text-muted); padding:6px 0;">No exported reels yet.</div>';
      return;
    }
    recentVideosList.innerHTML = '';
    data.videos.forEach(v => {
      const item = document.createElement('div');
      item.style.cssText = 'display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.03); border:1px solid var(--border-color); border-radius:8px; padding:8px 12px; font-size:12px; gap:8px;';
      item.innerHTML = `
        <div style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1; font-weight:600; color:var(--text-main);" title="${v.filename}">
          📹 ${v.filename}
        </div>
        <div style="display:flex; gap:6px; align-items:center; flex-shrink:0;">
          <span style="font-size:10px; color:var(--text-muted); font-family:monospace;">${v.size_mb}MB</span>
          <button class="btn-secondary" style="padding:3px 8px; font-size:11px;" onclick="playRecentVideo('${v.url}', '${v.filename}')">▶️ Play</button>
          <a href="${v.url}" download="${v.filename}" class="btn-primary" style="padding:3px 8px; font-size:11px; text-decoration:none;">⬇️ Save</a>
        </div>
      `;
      recentVideosList.appendChild(item);
    });
  } catch (err) {
    console.error("Failed to load recent videos:", err);
  }
}

const centerVideoPlayer = document.getElementById('center-video-player');
const btnToggleCenterVideo = document.getElementById('btn-toggle-center-video');

if (btnToggleCenterVideo && centerVideoPlayer) {
  btnToggleCenterVideo.addEventListener('click', () => {
    if (centerVideoPlayer.style.display === 'none') {
      centerVideoPlayer.style.display = 'block';
      centerVideoPlayer.play();
      btnToggleCenterVideo.innerText = '📱 Edit Template';
    } else {
      centerVideoPlayer.style.display = 'none';
      centerVideoPlayer.pause();
      btnToggleCenterVideo.innerText = '▶️ Watch Video';
    }
  });
}

window.playRecentVideo = function(url, filename) {
  finalVideoPlayer.src = url;
  btnDownloadVideo.href = url;
  btnDownloadVideo.setAttribute('download', filename);
  videoOutputBox.style.display = "flex";
  finalVideoPlayer.play();

  // Also setup center phone canvas video player
  if (centerVideoPlayer && btnToggleCenterVideo) {
    centerVideoPlayer.src = url;
    centerVideoPlayer.style.display = 'block';
    centerVideoPlayer.play();
    btnToggleCenterVideo.style.display = 'inline-block';
    btnToggleCenterVideo.innerText = '📱 Edit Template';
  }
};

// ==========================================================================
// PWA INSTALLATION & MOBILE APP NAVIGATION
// ==========================================================================
let deferredInstallPrompt = null;
const btnInstallPwa = document.getElementById('btn-install-pwa');

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredInstallPrompt = e;
  if (btnInstallPwa) {
    btnInstallPwa.style.display = 'inline-flex';
  }
});

if (btnInstallPwa) {
  btnInstallPwa.addEventListener('click', async () => {
    if (deferredInstallPrompt) {
      deferredInstallPrompt.prompt();
      const { outcome } = await deferredInstallPrompt.userChoice;
      console.log('PWA install outcome:', outcome);
      deferredInstallPrompt = null;
      btnInstallPwa.style.display = 'none';
    } else {
      alert("To install FondPeace Studio as a standalone desktop/phone app, tap your browser's menu (⋮ or ⋯) and select 'Install FondPeace Studio' or 'Add to Home Screen'!");
    }
  });
}

// Mobile Bottom Navigation Tabs (Responsive Device Navigation)
const navTabs = document.querySelectorAll('.mobile-bottom-nav .nav-tab');
const panels = {
  'panel-trending': document.getElementById('panel-trending'),
  'panel-preview': document.getElementById('panel-preview'),
  'panel-studio': document.getElementById('panel-studio'),
  'recent-videos-section': document.getElementById('recent-videos-section')
};

// Default active tab on mobile/tablet
if (panels['panel-trending']) {
  panels['panel-trending'].classList.add('tab-active');
}

navTabs.forEach(tab => {
  tab.addEventListener('click', () => {
    const targetId = tab.getAttribute('data-target');
    
    // Update active tab highlight
    navTabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');

    if (targetId === 'recent-videos-section') {
      // Switch to studio tab and scroll down to recent videos
      Object.values(panels).forEach(p => p && p.classList.remove('tab-active'));
      if (panels['panel-studio']) {
        panels['panel-studio'].classList.add('tab-active');
        const rvs = document.getElementById('recent-videos-section');
        if (rvs) rvs.scrollIntoView({ behavior: 'smooth' });
      }
      return;
    }

    // Switch visible panel on mobile/tablet
    Object.values(panels).forEach(p => p && p.classList.remove('tab-active'));
    if (panels[targetId]) {
      panels[targetId].classList.add('tab-active');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  });
});

// Service Worker Registration for Offline App Mode
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js').catch(err => {
      console.log('SW registration error:', err);
    });
  });
}

