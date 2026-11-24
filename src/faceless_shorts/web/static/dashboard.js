let currentTab = 'pipeline';
let pipelineRenderKey = '';
let refreshInFlight = false;
let statusData = null;
let queueData = null;
let projectFilterChannel = 'all';
let projectStatusFilter = 'all';
let projectSearchQuery = '';
let currentTrendChannel = 'en';
let currentTrendCategory = 'all';
let selectedStyleFilter = 'all';
let trendsLoading = false;
let trendsData = [];
let currentLogChannel = 'all';

async function api(path, options = {}) {
  try {
    const res = await fetch(path, options);
    const data = await res.json();
    if (!res.ok && !data.error) data.error = `Request failed (${res.status})`;
    return data;
  } catch (err) {
    console.error('API Error:', err);
    return { error: String(err) };
  }
}

function updateEngineControls() {
  const engine = document.getElementById('engine-select')?.value || '3d';
  const style = document.getElementById('style-select');
  if (style) {
    style.disabled = engine === 'mpt';
    style.title = engine === 'mpt' ? 'Visual styles apply to the Three.js engine; MPT uses stock footage.' : 'Visual style for the selected channel';
  }
  updateRunSettingsSummary();
}

function updateRunSettingsSummary() {
  const engine = document.getElementById('engine-select')?.value || '3d';
  const style = document.getElementById('style-select')?.value || 'auto';
  const dryRun = document.getElementById('dry-run-check')?.checked;
  const engineName = engine === 'mpt' ? 'MPT' : '3D Cinema';
  const styleName = style === 'auto' ? 'Auto style' : style.replaceAll('-', ' ');
  const summary = document.getElementById('run-settings-summary');
  if (summary) summary.textContent = `${engineName} · ${styleName} · ${dryRun ? 'Dry run' : 'Upload enabled'}`;
}

function escapeHtml(s) {
  return (s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function openModal(html) {
  document.getElementById('modal-body').innerHTML = html;
  document.getElementById('modal').classList.add('active');
}
function closeModal() {
  document.getElementById('modal').classList.remove('active');
}

const TAB_META = {
  pipeline: ['Overview', 'Monitor production, review staged videos, and see what needs attention.'],
  projects: ['Projects & media', 'Find generated videos, inspect files, and manage publishing.'],
  trends: ['Topic research', 'Review researched ideas and choose what to produce next.'],
  performance: ['Performance', 'Review channel metrics imported from YouTube Analytics.'],
  ledger: ['Topic ledger', 'See and edit topics already used by either channel.'],
  crafts: ['Production guide', 'Understand the quality standards and what each run produces.'],
  logs: ['Live logs', 'Follow pipeline output and diagnose the current or latest run.'],
};

function setCurrentTab(tab) {
  currentTab = tab;
  document.querySelectorAll('nav button').forEach(btn => btn.classList.toggle('active', btn.dataset.tab === tab));
  const [title, description] = TAB_META[tab] || TAB_META.pipeline;
  const titleNode = document.getElementById('page-title');
  const descriptionNode = document.getElementById('page-description');
  if (titleNode) titleNode.textContent = title;
  if (descriptionNode) descriptionNode.textContent = description;
  renderTab();
}

document.querySelectorAll('nav button[data-tab]').forEach(btn => {
  btn.onclick = () => setCurrentTab(btn.dataset.tab);
});

async function refreshStatus() {
  if (refreshInFlight) return;
  refreshInFlight = true;
  try {
  statusData = await api('/api/status');
  if (statusData.error) {
    const pill = document.getElementById('state-pill');
    if (pill) { pill.textContent = 'CONNECTION ISSUE'; pill.className = 'pill err'; }
    const slot = document.getElementById('active-slot');
    if (slot) slot.textContent = 'Status could not be loaded. Retrying automatically…';
    return;
  }
  queueData = await api('/api/queue');
  const pill = document.getElementById('state-pill');
  if (statusData.running_en && statusData.running_te) {
    pill.textContent = 'BOTH RUNNING';
    pill.className = 'pill run';
  } else if (statusData.running_en) {
    pill.textContent = 'ENGLISH RUNNING';
    pill.className = 'pill run';
  } else if (statusData.running_te) {
    pill.textContent = 'TELUGU RUNNING';
    pill.className = 'pill run';
  } else if (statusData.broadcasting) {
    pill.textContent = 'BROADCASTING';
    pill.className = 'pill run';
  } else if (statusData.te?.last_failure) {
    pill.textContent = 'TELUGU RUN FAILED';
    pill.className = 'pill err';
  } else if (statusData.en?.last_failure) {
    pill.textContent = 'ENGLISH RUN FAILED';
    pill.className = 'pill err';
  } else {
    pill.textContent = 'IDLE';
    pill.className = 'pill idle';
  }
  const nextPublish = queueData?.slot?.next_slot;
  const refreshedAt = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  document.getElementById('active-slot').textContent = `${statusData.date} · Updated ${refreshedAt}${nextPublish ? ` · Next publish ${nextPublish}` : ''}`;
  const stopButton = document.getElementById('stop-btn');
  ['run-en-btn', 'run-te-btn', 'run-all-btn'].forEach(id => {
    const button = document.getElementById(id);
    if (button) button.disabled = !!statusData.running;
  });
  if (stopButton) {
    stopButton.disabled = !(statusData.running || statusData.broadcasting);
    stopButton.title = stopButton.disabled ? 'No pipeline or broadcast is active' : 'Stop active generation and upload workers';
  }

  if (currentTab === 'pipeline') {
    renderPipelineTab();
  }
  } finally {
    refreshInFlight = false;
  }
}

function renderTab() {
  if (currentTab === 'pipeline') { pipelineRenderKey = ''; renderPipelineTab(); }
  else if (currentTab === 'crafts') renderCraftsTab();
  else if (currentTab === 'projects') renderProjectsTab();
  else if (currentTab === 'trends') renderTrendsTab();
  else if (currentTab === 'performance') renderPerformanceTab();
  else if (currentTab === 'ledger') renderLedgerTab();
  else if (currentTab === 'logs') renderLogsTab();
}

function renderCraftsTab() {
  document.getElementById('app-content').innerHTML = `
    <div class="card">
      <div class="card-header">
        <div>
          <h2 style="margin:0 0 4px;">🎬 Production Playbook</h2>
          <div style="font-size:12px; color:var(--text-dim);">A quick guide to what each run creates and what to review before release.</div>
        </div>
        <span class="pill idle">English + Telugu</span>
      </div>
      <div class="playbook-grid">
        <article class="card playbook-card"><div class="playbook-icon">✍️</div><h3>Story & facts</h3><p>Keep the channels in their own language and topic lane. Start with one clear question, explain the answer in connected spoken sentences, and keep on-screen text short.</p></article>
        <article class="card playbook-card"><div class="playbook-icon">🎥</div><h3>Visual direction</h3><p>For a 60–90 second video, aim for 18–24 purposeful shots across 3–5 topic-specific sets. Mix wide views, action, close detail, and changed camera angles.</p></article>
        <article class="card playbook-card"><div class="playbook-icon">🎙️</div><h3>Voice & sound</h3><p>Use one natural native-language narrator. Keep music low under speech, preserve pauses, and use only a few soft effects when an action needs emphasis.</p></article>
        <article class="card playbook-card"><div class="playbook-icon">🔎</div><h3>Review & release</h3><p>Check the contact sheet, captions, key scenes, and ending. Preview the mix and export before using the upload or broadcast controls.</p></article>
      </div>
      <div class="playbook-note"><b>Run controls:</b> choose a production engine and style above, then start one channel or both. DRY-RUN keeps the run from uploading. The Stop button is available only while work is active.</div>
    </div>
  `;
}

function renderPipelineTab() {
  if (!statusData) return;
  const en = statusData.en || {};
  const te = statusData.te || {};
  const renderKey = JSON.stringify({
    running: [en.running, te.running, statusData.broadcasting],
    channels: [en, te].map(ch => ({ project: ch.project, style: ch.style, status: ch.status, current: ch.current, last_failure: ch.last_failure,
      stages: (ch.stages || []).map(stage => [stage.id, stage.done]),
      media: [ch.has_render, ch.has_cover, ch.has_sheet, ch.has_audio, ch.video_id] })),
    slot: queueData?.slot?.next_slot,
    queue: (queueData?.queued || []).map(item => [item.project, item.video_id, item.has_cover]),
  });
  if (renderKey === pipelineRenderKey) return;
  pipelineRenderKey = renderKey;

  const makeStepper = (ch) => {
    if (!ch.stages) return '<div style="color:var(--text-dim); padding:10px;">No stages loaded</div>';
    return ch.stages.map(s => {
      // Strictly require that THIS specific channel is running before showing current movement
      const isCur = ch.running && ch.current === s.id;
      const cls = isCur ? 'current' : (s.done ? 'done' : 'pending');
      return `<div class="step ${cls}">
        <span class="dot"></span>
        <span class="step-title">${escapeHtml(s.name)}</span>
        <span class="step-detail">${escapeHtml(s.detail || '')}</span>
      </div>`;
    }).join('');
  };

  const channelState = (ch) => {
    if (ch.running) return ['RUNNING', 'run'];
    if (ch.last_failure) return ['FAILED', 'err'];
    if (ch.video_id) return ['PUBLISHED', 'ready'];
    if (ch.has_render) return ['RENDER READY', 'ready'];
    if (ch.project) return ['INCOMPLETE', 'waiting'];
    return ['WAITING', 'waiting'];
  };

  const makeProgress = (ch) => {
    const stages = ch.stages || [];
    const complete = stages.filter(s => s.done).length;
    const percent = stages.length ? Math.round(complete / stages.length * 100) : 0;
    return `<div class="channel-progress" aria-label="${complete} of ${stages.length} production steps complete"><div class="progress-track"><div class="progress-fill" style="width:${percent}%"></div></div><span class="progress-count">${complete} / ${stages.length} steps</span></div>`;
  };

  const makeFailureNotice = (ch) => ch.last_failure ? `<div class="run-failure" role="status"><b>Last run failed</b><span>${escapeHtml(ch.last_failure.message)}</span><button class="btn" onclick="document.querySelector('[data-tab=logs]').click()">Open logs</button></div>` : '';

  const makePreviewBox = (ch) => {
    if (!ch.project) return '<div style="color:var(--text-dim); padding:12px;">No active project generated yet today.</div>';
    return `<div class="media-preview-box">
      <div>
        ${ch.has_render ? `
          <video class="preview-vid" controls preload="metadata" src="/api/vid?project=${ch.project}"></video>
        ` : (ch.has_cover ? `<img class="preview-cover" src="/api/thumb?project=${ch.project}" onclick="openImage('/api/thumb?project=${ch.project}')">` : '<div style="aspect-ratio:9/16; background:#000; border-radius:8px; display:flex; align-items:center; justify-content:center; color:var(--text-dim);">No render yet</div>')}
      </div>
      <div>
        <div style="font-weight:700; font-size:15px; margin-bottom:4px;">${escapeHtml(ch.project)}</div>
        <div style="color:var(--text-dim); font-size:12px; margin-bottom:10px;">
          Style: <b style="color:var(--text);">${escapeHtml(ch.style || 'auto')}</b> · Status: <span style="color:var(--ok); font-weight:600;">${escapeHtml(ch.status || 'READY')}</span>
        </div>
        ${ch.video_id ? `<div style="margin-bottom:8px;">🔗 <a href="https://youtu.be/${ch.video_id}" target="_blank" style="color:var(--en-accent); font-weight:700;">youtu.be/${ch.video_id}</a> <span style="color:var(--ok); font-size:11px; margin-left:6px;">✓ Uploaded</span></div>` : (ch.has_render ? '<div style="margin-bottom:8px;"><span style="color:#f59e0b; font-size:12px; font-weight:700;">⚡ Unuploaded (Render Ready)</span></div>' : '')}
        ${ch.has_audio ? `
          <label style="font-size:11px; color:var(--text-dim);">Sound & Music Mix (mix.wav):</label>
          <audio controls src="/api/audio?project=${ch.project}&type=mix"></audio>
        ` : ''}
        <div class="toolbar">
          ${ch.has_sheet ? `<button class="btn" onclick="openImage('/api/sheet?project=${ch.project}')">🔍 QA Sheet</button>` : ''}
          ${ch.has_render && !ch.video_id ? `<button class="btn primary" style="background:linear-gradient(135deg, #dc2626, #b91c1c); color:#fff; font-weight:700;" onclick="uploadProject('${ch.project}', true)">🚀 Upload to YouTube</button>` : (ch.video_id ? `<a class="btn" href="https://youtu.be/${ch.video_id}" target="_blank" style="background:#059669; color:#fff; text-decoration:none; font-weight:600;">▶ Watch on YouTube</a>` : '')}
          <button class="btn" onclick="inspectProject('${ch.project}')">Inspect Project</button>
        </div>
      </div>
    </div>`;
  };

  const makeQueueBanner = () => {
    const queueSlot = queueData?.slot || {};
    const queuedItems = queueData?.queued || [];
    const enQueued = queuedItems.find(q => q.channel === 'en');
    const teQueued = queuedItems.find(q => q.channel === 'te');

    return `
      <div class="card" style="margin-bottom: 20px; border-left: 4px solid #f59e0b; background: linear-gradient(180deg, rgba(245, 158, 11, 0.05) 0%, var(--panel) 100%);">
        <div class="card-header" style="border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 14px;">
          <div>
            <h2 style="display:flex; align-items:center; gap:8px; font-size:16px;">
              <span>📡 Broadcast Staging Queue</span>
              <span class="pill" style="background:#f59e0b20; color:#f59e0b; border:1px solid #f59e0b60;">Next publish: ${escapeHtml(queueSlot.next_slot || 'not scheduled')}</span>
              ${statusData.broadcasting ? `
                <span class="pill" style="background:#10b98125; color:#10b981; border:1px solid #10b981; animation: pulse 1.5s infinite; cursor:pointer;" onclick="openBroadcastModal()">
                  📡 Broadcasting Live (PID: ${statusData.broadcast_pid}) — Click to Observe
                </span>
              ` : ''}
            </h2>
            <div style="font-size:12px; color:var(--text-dim); margin-top:4px;">
              A queued video is published at the next configured slot. After publishing, the pipeline prepares the next video. The operating system scheduler controls automatic run times.
            </div>
          </div>
          <div class="queue-actions">
            <button class="btn" onclick="refreshStatus()" title="Refresh queue">🔄 Refresh</button>
            ${statusData.broadcasting ? `
              <button class="btn primary" style="background:linear-gradient(135deg, #2563eb, #1d4ed8); font-weight:700;" onclick="openBroadcastModal()">📡 View Live Broadcast</button>
              <button class="btn" style="background:#dc2626; color:#fff; font-weight:700;" onclick="stopBroadcast()">🛑 Stop Broadcast</button>
            ` : `
              <button class="btn primary" style="background:linear-gradient(135deg, #10b981, #059669); font-weight:700;" onclick="triggerBroadcast('all')">⚡ Broadcast Now (All)</button>
            `}
          </div>
        </div>
        ${queueData?.error ? `<div class="run-failure" role="status"><b>Queue status unavailable</b><span>${escapeHtml(queueData.error)}</span><button class="btn" onclick="refreshStatus()">Retry</button></div>` : ''}
        <div class="queue-grid">
          <!-- English Queue Box -->
          <div style="background:var(--bg); border:1px solid var(--border); border-radius:8px; padding:12px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
              <span class="channel-tag en">🇬🇧 Curiography (English)</span>
              ${enQueued ? `<span style="font-size:11px; color:#10b981; font-weight:700;">✓ Ready for Next Slot</span>` : `<span style="font-size:11px; color:var(--text-dim);">⏳ No Staged Video</span>`}
            </div>
            ${enQueued ? `
              <div style="font-weight:700; font-size:13px; margin-bottom:4px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escapeHtml(enQueued.title)}</div>
              <div style="font-size:11.5px; color:var(--text-dim); margin-bottom:8px;">
                Project: <code>${escapeHtml(enQueued.project)}</code> · ${(enQueued.video_size_mb || enQueued.size_mb || 0).toFixed(1)} MB · ${enQueued.has_cover ? '✓ Cover OK' : '⚠ Missing Cover'}
              </div>
              <button class="btn" style="width:100%; font-size:11.5px;" onclick="triggerBroadcast('en')">🚀 Broadcast English Now</button>
            ` : `
              <div style="font-size:12px; color:var(--text-dim); padding:8px 0;">No video is eligible for publishing yet. The queue requires a render, cover, and passing quality review.</div>
              <button class="btn" style="width:100%; font-size:11.5px;" onclick="triggerRun('en')">▶ Pre-produce English Video</button>
            `}
          </div>

          <!-- Telugu Queue Box -->
          <div style="background:var(--bg); border:1px solid var(--border); border-radius:8px; padding:12px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
              <span class="channel-tag te">🇮🇳 Asakthi (Telugu)</span>
              ${teQueued ? `<span style="font-size:11px; color:#10b981; font-weight:700;">✓ Ready for Next Slot</span>` : `<span style="font-size:11px; color:var(--text-dim);">⏳ No Staged Video</span>`}
            </div>
            ${teQueued ? `
              <div style="font-weight:700; font-size:13px; margin-bottom:4px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escapeHtml(teQueued.title)}</div>
              <div style="font-size:11.5px; color:var(--text-dim); margin-bottom:8px;">
                Project: <code>${escapeHtml(teQueued.project)}</code> · ${(teQueued.video_size_mb || teQueued.size_mb || 0).toFixed(1)} MB · ${teQueued.has_cover ? '✓ Cover OK' : '⚠ Missing Cover'}
              </div>
              <button class="btn" style="width:100%; font-size:11.5px;" onclick="triggerBroadcast('te')">🚀 Broadcast Telugu Now</button>
            ` : `
              <div style="font-size:12px; color:var(--text-dim); padding:8px 0;">No video is eligible for publishing yet. The queue requires a render, cover, and passing quality review.</div>
              <button class="btn" style="width:100%; font-size:11.5px;" onclick="triggerRun('te')">▶ Pre-produce Telugu Video</button>
            `}
          </div>
        </div>
      </div>
    `;
  };

  document.getElementById('app-content').innerHTML = `
    ${makeQueueBanner()}
    <div class="grid-2">
      <div class="card">
        ${(() => { const [label, cls] = channelState(en); return `
        <div class="card-header">
          <h2>
            🇬🇧 Curiography <span class="channel-tag en">English</span>
            <span class="pill ${cls}" style="margin-left:6px;">${label}</span>
          </h2>
          <span style="font-size:12px; color:var(--text-dim);">${en.project || 'Pending today'}</span>
        </div>
        ${makeProgress(en)}`; })()}
        ${makeFailureNotice(en)}
        <div class="stepper">${makeStepper(en)}</div>
        ${makePreviewBox(en)}
      </div>

      <div class="card">
        ${(() => { const [label, cls] = channelState(te); return `
        <div class="card-header">
          <h2>
            🇮🇳 Asakthi <span class="channel-tag te">Telugu</span>
            <span class="pill ${cls}" style="margin-left:6px;">${label}</span>
          </h2>
          <span style="font-size:12px; color:var(--text-dim);">${te.project || 'Pending today'}</span>
        </div>
        ${makeProgress(te)}`; })()}
        ${makeFailureNotice(te)}
        <div class="stepper">${makeStepper(te)}</div>
        ${makePreviewBox(te)}
      </div>
    </div>
  `;
}

async function renderProjectsTab() {
  const data = await api('/api/projects');
  const allProjects = data.projects || [];
  const enProjects = allProjects.filter(p => p.channel === 'curiography');
  const teProjects = allProjects.filter(p => p.channel === 'asakthi');

  const renderProjectCard = (p) => {
    const projectArg = encodeURIComponent(p.name);
    const projectState = p.is_uploaded ? 'uploaded' : (p.has_render ? 'ready' : 'draft');
    return `
    <div class="card project-card" data-project-card data-project-name="${escapeHtml((p.name + ' ' + (p.title || '')).toLowerCase())}" data-project-channel="${p.channel === 'asakthi' ? 'te' : 'en'}" data-project-state="${projectState}" role="button" tabindex="0" style="padding:14px; background:var(--bg); border-color:var(--border); cursor:pointer;" onclick="inspectProject(decodeURIComponent('${projectArg}'))" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();inspectProject(decodeURIComponent('${projectArg}'))}">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span class="channel-tag ${p.channel === 'asakthi' ? 'te' : 'en'}">${p.channel === 'asakthi' ? '🇮🇳 Telugu' : '🇬🇧 English'}</span>
        <span style="font-size:11px; color:var(--text-dim);">${(p.mp4_size / 1024 / 1024).toFixed(1)} MB</span>
      </div>
      <div style="font-weight:700; font-size:14px; margin-bottom:2px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${escapeHtml(p.title || p.name)}">${escapeHtml(p.title || p.name)}</div>
      <div style="font-size:11px; color:var(--text-dim); margin-bottom:6px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escapeHtml(p.name)}</div>
      <div style="font-size:11.5px; margin-bottom:8px;">
        ${p.is_uploaded ? `<span style="color:#10b981; font-weight:700;">✓ Uploaded</span> <a href="${p.youtube_url || ('https://youtu.be/' + p.video_id)}" target="_blank" onclick="event.stopPropagation();" style="color:var(--en-accent); font-size:11px; margin-left:4px;">${p.video_id}</a>` : (p.has_render ? '<span style="color:#f59e0b; font-weight:700;">⚡ Unuploaded (Ready)</span>' : '<span style="color:var(--text-dim);">⏳ No render</span>')}
      </div>
      ${p.has_cover ? `<img src="/api/thumb?project=${projectArg}" style="width:100%; height:190px; object-fit:contain; background:#000; border-radius:6px; margin-bottom:8px;">` : '<div style="height:190px; background:#000; border-radius:6px; display:flex; align-items:center; justify-content:center; color:var(--text-dim); margin-bottom:8px;">No cover</div>'}
      <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--text-dim); margin-bottom:8px;">
        <span>${p.has_render ? '🎬 Rendered' : '⏳ No render'}</span>
        <span>${p.has_audio ? '🎵 Audio' : 'No mix'}</span>
      </div>
      ${p.has_render && !p.is_uploaded ? `
        <button class="btn primary" style="width:100%; padding:6px 10px; font-size:12px; background:linear-gradient(135deg, #dc2626, #b91c1c); color:#fff; font-weight:700;" onclick="event.stopPropagation(); uploadProject(decodeURIComponent('${projectArg}'), true)">🚀 Upload to YouTube</button>
      ` : (p.is_uploaded ? `
        <a class="btn" style="width:100%; padding:6px 10px; font-size:12px; display:block; text-align:center; box-sizing:border-box; background:#059669; color:#fff; text-decoration:none; font-weight:600;" href="${p.youtube_url || ('https://youtu.be/' + p.video_id)}" target="_blank" onclick="event.stopPropagation();">▶ Watch on YouTube</a>
      ` : '')}
    </div>
  `;
  };

  document.getElementById('app-content').innerHTML = `
    <div class="card">
      <div class="card-header">
        <div>
          <h2 style="margin:0 0 4px 0;">📁 Projects & Media Archive</h2>
          <div style="font-size:12px; color:var(--text-dim);">
            Isolated channels · English (Curiography) and Telugu (Asakthi)
          </div>
        </div>
        <div style="font-size:12px; color:var(--text-dim);">
          Total: <b>${allProjects.length}</b> (🇬🇧 ${enProjects.length} · 🇮🇳 ${teProjects.length})
        </div>
      </div>

      <div class="project-controls">
        <input id="project-search" type="search" placeholder="Search project or title…" aria-label="Search projects" value="${escapeHtml(projectSearchQuery)}" oninput="projectSearchQuery=this.value;filterProjectCards()">
        <select id="project-state-filter" onchange="projectStatusFilter=this.value;filterProjectCards()" aria-label="Filter project status">
          <option value="all">All statuses</option><option value="ready">Ready to upload</option><option value="uploaded">Uploaded</option><option value="draft">In progress / no render</option>
        </select>
        <span id="project-visible-count" class="count-note">${allProjects.length} projects</span>
      </div>
      <div class="sub-nav">
        <button class="${projectFilterChannel === 'all' ? 'active' : ''}" onclick="setProjectChannelFilter('all')">
          📂 All Projects (${allProjects.length})
        </button>
        <button class="en ${projectFilterChannel === 'en' ? 'active en' : ''}" onclick="setProjectChannelFilter('en')">
          🇬🇧 English Archive (Curiography) · ${enProjects.length}
        </button>
        <button class="te ${projectFilterChannel === 'te' ? 'active te' : ''}" onclick="setProjectChannelFilter('te')">
          🇮🇳 Telugu Archive (Asakthi) · ${teProjects.length}
        </button>
      </div>

      ${(projectFilterChannel === 'all' || projectFilterChannel === 'en') ? `
        <div class="channel-section-header en" data-project-section="en">
          <h3>🇬🇧 Curiography Video Archive (English Sci/Tech Procedurals)</h3>
          <span style="font-size:12px; font-weight:700; color:var(--en-accent);">${enProjects.length} videos</span>
        </div>
        <div class="project-grid" data-project-grid="en">
          ${enProjects.length > 0 ? enProjects.map(renderProjectCard).join('') : '<div style="color:var(--text-dim); padding:20px;">No English projects found.</div>'}
        </div>
      ` : ''}

      ${(projectFilterChannel === 'all' || projectFilterChannel === 'te') ? `
        <div class="channel-section-header te" data-project-section="te">
          <h3>🇮🇳 Asakthi Video Archive (Telugu Mythology, Lore & Traditions)</h3>
          <span style="font-size:12px; font-weight:700; color:var(--te-accent);">${teProjects.length} videos</span>
        </div>
        <div class="project-grid" data-project-grid="te">
          ${teProjects.length > 0 ? teProjects.map(renderProjectCard).join('') : '<div style="color:var(--text-dim); padding:20px;">No Telugu projects found.</div>'}
        </div>
      ` : ''}
    </div>
  `;
  filterProjectCards();
}

function setProjectChannelFilter(filter) {
  projectFilterChannel = filter;
  renderProjectsTab();
}

function filterProjectCards() {
  const query = projectSearchQuery.trim().toLowerCase();
  let visible = 0;
  document.querySelectorAll('[data-project-card]').forEach(card => {
    const channelOk = projectFilterChannel === 'all' || card.dataset.projectChannel === projectFilterChannel;
    const queryOk = !query || card.dataset.projectName.includes(query);
    const statusOk = projectStatusFilter === 'all' || card.dataset.projectState === projectStatusFilter;
    const show = channelOk && queryOk && statusOk;
    card.hidden = !show;
    if (show) visible++;
  });
  document.querySelectorAll('[data-project-section]').forEach(section => {
    const channel = section.dataset.projectSection;
    const grid = document.querySelector(`[data-project-grid="${channel}"]`);
    const sectionVisible = !!grid && [...grid.querySelectorAll('[data-project-card]')].some(card => !card.hidden);
    section.hidden = !sectionVisible;
    if (grid) grid.hidden = !sectionVisible;
  });
  const count = document.getElementById('project-visible-count');
  if (count) count.textContent = `${visible} project${visible === 1 ? '' : 's'}`;
}

async function renderTrendsTab() {
  const container = document.getElementById('app-content');
  const isTe = currentTrendChannel === 'te';

  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <div>
          <h2 style="margin:0 0 4px 0;">
            🔥 ${isTe ? '🇮🇳 Telugu Lore, Temple Mysteries & Traditions (Asakthi)' : '🇬🇧 Viral Science & Curiosity Trend Hunter (Curiography)'}
          </h2>
          <div style="font-size:12px; color:var(--text-dim);">
            ${isTe ? 'Sanatana Dharma temple mysteries, epic Puranic feats, Telugu cultural heritage & tradition science' : 'Real-time breaking science from Google Trends US, ScienceDaily & Phys.org · Curiosity ranked'}
          </div>
        </div>
        <div class="trend-controls">
          ${!isTe ? `
            <select id="trend-style-select" class="btn" onchange="changeTrendStyle(this.value)">
              <option value="all" ${selectedStyleFilter === 'all' ? 'selected' : ''}>All Styles</option>
              <option value="engineering-explainer" ${selectedStyleFilter === 'engineering-explainer' ? 'selected' : ''}>Engineering Explainer (3D)</option>
              <option value="tall-tale" ${selectedStyleFilter === 'tall-tale' ? 'selected' : ''}>Tall Tale (3D storybook)</option>
              <option value="cinematic-what-if" ${selectedStyleFilter === 'cinematic-what-if' ? 'selected' : ''}>Cinematic What If (2D Ink Vector)</option>
            </select>
          ` : `
            <select id="trend-category-select" class="btn te" onchange="changeTrendCategory(this.value)">
              <option value="all" ${currentTrendCategory === 'all' ? 'selected' : ''}>అన్ని విభాగాలు (All Categories)</option>
              <option value="storybooks" ${currentTrendCategory === 'storybooks' ? 'selected' : ''}>చందమామ & తెలుగు కథల పుస్తకాలు (Storybooks & Chandamama)</option>
              <option value="epics" ${currentTrendCategory === 'epics' ? 'selected' : ''}>హిందూ పురాణ గాథలు (Hindu Epics & Mythology)</option>
              <option value="temples" ${currentTrendCategory === 'temples' ? 'selected' : ''}>దేవాలయ అద్భుతాలు (Temple Marvels)</option>
              <option value="science_tradition" ${currentTrendCategory === 'science_tradition' ? 'selected' : ''}>సంప్రదాయ విజ్ఞానం (Tradition Science)</option>
              <option value="legends" ${currentTrendCategory === 'legends' ? 'selected' : ''}>చారిత్రక చమత్కారాలు (Historical Legends)</option>
            </select>
            <select id="trend-style-select" class="btn te" onchange="changeTrendStyle(this.value)">
              <option value="all" ${selectedStyleFilter === 'all' ? 'selected' : ''}>అన్ని శైలులు (All Styles)</option>
              <option value="tall-tale" ${selectedStyleFilter === 'tall-tale' ? 'selected' : ''}>Tall Tale (పురాణ గాథలు)</option>
            </select>
          `}
          <button class="btn primary" onclick="fetchAndRenderTrends(true)" id="trends-refresh-btn">
            🔄 ${isTe ? 'Refresh Topics' : 'Scan Breaking Feeds'}
          </button>
        </div>
      </div>

      <div class="sub-nav">
        <button class="en ${currentTrendChannel === 'en' ? 'active en' : ''}" onclick="setTrendChannel('en')">
          🇬🇧 English Viral Science (Curiography)
        </button>
        <button class="te ${currentTrendChannel === 'te' ? 'active te' : ''}" onclick="setTrendChannel('te')">
          🇮🇳 Telugu Lore & Traditions (Asakthi)
        </button>
      </div>

      <div id="trends-list">
        ${trendsLoading ? '<div style="padding:40px; text-align:center; color:var(--text-dim);">📡 Scanning topics and filtering against ledger...</div>' : ''}
      </div>
    </div>
  `;

  if (!trendsLoading && trendsData.length === 0) {
    await fetchAndRenderTrends(false);
  } else if (!trendsLoading) {
    renderTrendsList();
  }
}

async function setTrendChannel(ch) {
  if (currentTrendChannel === ch) return;
  currentTrendChannel = ch;
  selectedStyleFilter = 'all';
  currentTrendCategory = 'all';
  trendsData = [];
  await fetchAndRenderTrends(true);
}

async function changeTrendCategory(cat) {
  currentTrendCategory = cat;
  await fetchAndRenderTrends(true);
}

async function changeTrendStyle(val) {
  selectedStyleFilter = val;
  await fetchAndRenderTrends(true);
}

async function fetchAndRenderTrends(force = false) {
  trendsLoading = true;
  const listEl = document.getElementById('trends-list');
  if (listEl) {
    listEl.innerHTML = '<div style="padding:40px; text-align:center; color:var(--text-dim);">📡 Loading channel topics...</div>';
  }

  let query = `?channel=${currentTrendChannel}&count=9`;
  if (selectedStyleFilter !== 'all') {
    query += `&style=${selectedStyleFilter}`;
  }
  if (currentTrendChannel === 'te' && currentTrendCategory !== 'all') {
    query += `&category=${currentTrendCategory}`;
  }

  const data = await api('/api/trends' + query);
  trendsData = data.trends || [];
  trendsLoading = false;
  renderTrendsList();
}

function renderTrendsList() {
  const listEl = document.getElementById('trends-list');
  if (!listEl) return;

  if (trendsData.length === 0) {
    listEl.innerHTML = `
      <div style="padding:40px; text-align:center; color:var(--text-dim);">
        No topics found matching this criteria, or candidates are already covered in ledger.
        <br><br>
        <button class="btn" onclick="fetchAndRenderTrends(true)">Force Re-scan</button>
      </div>
    `;
    return;
  }

  const isTe = currentTrendChannel === 'te';

  listEl.innerHTML = `
    <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(min(340px, 100%), 1fr)); gap:18px; margin-top:10px;">
      ${trendsData.map((t) => `
        <div class="card" style="background:var(--bg); border:1px solid var(--border); display:flex; flex-direction:column; justify-content:space-between; padding:16px;">
          <div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
              <span class="channel-tag ${isTe ? 'te' : 'en'}" style="background:${isTe ? 'rgba(251,191,36,0.15)' : 'rgba(56,189,248,0.15)'};">
                🔥 ${t.curiosity_score || 9}/10 Curiosity
              </span>
              <span style="font-size:11px; color:var(--text-dim); text-transform:uppercase;">
                ${escapeHtml(t.source || (isTe ? 'Telugu Heritage' : 'Breaking News'))}
              </span>
            </div>

            <h3 style="margin:0 0 4px 0; font-size:15px; line-height:1.4;">
              ${escapeHtml(t.title)}
            </h3>

            ${t.english_title ? `
              <div style="font-size:11.5px; color:var(--text-dim); margin-bottom:8px; font-style:italic;">
                ${escapeHtml(t.english_title)}
              </div>
            ` : ''}

            <div style="font-size:11px; margin-bottom:12px; display:flex; gap:6px; flex-wrap:wrap;">
              <span class="channel-tag ${isTe ? 'te' : 'en'}" style="font-size:10px;">
                🎯 Style: ${escapeHtml(t.assigned_style || 'auto')}
              </span>
              ${t.deity ? `<span class="channel-tag te" style="font-size:10px;">🛕 ${escapeHtml(t.deity)}</span>` : ''}
              ${t.location ? `<span class="channel-tag" style="background:rgba(59,130,246,0.12); color:#60a5fa; font-size:10px;">📍 ${escapeHtml(t.location)}</span>` : ''}
              ${t.map_region ? `<span class="channel-tag" style="background:rgba(234,179,8,0.12); color:#facc15; font-size:10px;">🗺️ ${escapeHtml(t.map_region)}</span>` : ''}
              ${t.category ? `<span class="channel-tag" style="background:rgba(255,255,255,0.06); color:var(--text-dim); font-size:10px;">${escapeHtml(t.category)}</span>` : ''}
            </div>

            <details class="topic-details">
              <summary>Research notes, structure and hook ideas</summary>
              <p style="font-size:12px; color:var(--text-dim); line-height:1.5; margin:10px 0 14px;">
                ${escapeHtml(t.summary || '')}
              </p>

            ${(t.engineering_steps && t.engineering_steps.breakthrough) ? `
              <div style="font-size:11px; color:#10b981; background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.2); border-radius:6px; padding:6px 8px; margin-bottom:12px; line-height:1.4;">
                <strong style="color:#34d399;">⚙️ Structural Breakthrough:</strong> ${escapeHtml(t.engineering_steps.breakthrough)}
              </div>
            ` : ''}

            ${(t.hook_angles && t.hook_angles.length > 0) ? `
              <div style="background:var(--surface); border:1px solid var(--border); border-radius:6px; padding:10px; margin-bottom:14px;">
                <div style="font-size:11px; font-weight:700; color:var(--text-dim); margin-bottom:6px;">VIRAL HOOK ANGLES:</div>
                ${t.hook_angles.map(h => `
                  <div style="font-size:11px; color:var(--text); padding:4px 0; border-bottom:1px dashed rgba(255,255,255,0.05); cursor:pointer;" onclick="promptCreateShortWithTopic('${escapeHtml(h).replace(/'/g, "\\'")}', '${t.assigned_style}', '${isTe ? 'te' : 'en'}')" title="Click to create video with this hook">
                    ⚡ "${escapeHtml(h)}"
                  </div>
                `).join('')}
              </div>
            ` : ''}
            </details>
          </div>

          <div style="padding-top:10px; border-top:1px solid var(--border);">
            <button class="btn ${isTe ? 'te' : 'primary'}" style="width:100%; font-size:12px;" onclick="promptCreateShortWithTopic('${escapeHtml(t.title).replace(/'/g, "\\'")}', '${t.assigned_style}', '${isTe ? 'te' : 'en'}')">
              🎬 Create Short For ${isTe ? 'Asakthi (Telugu)' : 'Curiography (English)'}
            </button>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

function promptCreateShortWithTopic(topic, style, targetChannel = 'en') {
  const globalStyle = document.getElementById('style-select')?.value || 'auto';
  const recommendedStyle = (style && style !== 'auto') ? style : (globalStyle !== 'auto' ? globalStyle : (targetChannel === 'en' ? 'engineering-explainer' : 'tall-tale'));
  const preferredEngine = document.getElementById('engine-select')?.value || '3d';
  openModal(`
    <div style="max-width:460px;">
      <h3 style="margin-top:0;">Launch Short Creation</h3>
      <p style="font-size:13px; color:var(--text-dim); line-height:1.4;">
        Start automated short-form generation for this topic:
      </p>
      <div style="background:var(--bg); border:1px solid var(--border); padding:10px; border-radius:6px; font-weight:600; font-size:13px; margin-bottom:14px;">
        ${escapeHtml(topic)}
      </div>
      <div style="font-size:12px; margin-bottom:14px; background:#0b1320; border:1px solid #1e293b; padding:10px; border-radius:6px;">
        <label style="font-weight:600; display:block; margin-bottom:6px; color:#f3f4f6;">Production Engine:</label>
        <label style="display:flex; align-items:center; gap:6px; margin-bottom:6px; font-size:12px; cursor:pointer;">
          <input type="radio" name="engine-mode" value="3d" ${preferredEngine === '3d' ? 'checked' : ''} onchange="document.getElementById('modal-style-select').disabled=false"> 🚀 <b>Three.js 3D WebGL Cinema</b> (Procedural 3D + Neural Voice + Foley)
        </label>
        <label style="display:flex; align-items:center; gap:6px; margin-bottom:10px; font-size:12px; cursor:pointer;">
          <input type="radio" name="engine-mode" value="mpt" ${preferredEngine === 'mpt' ? 'checked' : ''} onchange="document.getElementById('modal-style-select').disabled=true"> 🎥 <b>MoneyPrinterTurbo Engine</b> (stock B-roll draft; simpler visuals)
        </label>
        <label style="font-weight:600; display:block; margin-bottom:6px; color:#f3f4f6;">Visual Style:</label>
        <select id="modal-style-select" ${preferredEngine === 'mpt' ? 'disabled' : ''} style="width:100%; background:var(--surface); border:1px solid var(--border); color:var(--text); font-size:12px; padding:6px; border-radius:6px;">
          <option value="${recommendedStyle}">🎯 Recommended: ${escapeHtml(recommendedStyle)}</option>
          <option value="engineering-explainer">🏗️ 3D Engineering Explainer (maps, cutaways, construction steps)</option>
          <option value="tall-tale">🛕 Tall Tale (3D storybook renderer)</option>
          <option value="cinematic-what-if">🎭 Cinematic What If (2D ink-vector; English only)</option>
        </select>
      </div>
      <div style="display:flex; flex-direction:column; gap:10px;">
        ${targetChannel === 'en' ? `
          <button class="btn en" onclick="startGenerationForTopic('${encodeURIComponent(topic)}', 'en')">▶ Generate for English (Curiography)</button>
        ` : `
          <button class="btn te" onclick="startGenerationForTopic('${encodeURIComponent(topic)}', 'te')">▶ Generate for Telugu (Asakthi)</button>
        `}
        <button class="btn" onclick="startGenerationForTopic('${encodeURIComponent(topic)}', '${targetChannel === 'te' ? 'en' : 'te'}')">▶ Generate for Other Channel</button>
      </div>
    </div>
  `);
}

async function startGenerationForTopic(encodedTopic, channel) {
  const topic = decodeURIComponent(encodedTopic);
  const dry = document.getElementById('dry-run-check')?.checked || false;
  const engine = document.querySelector('input[name="engine-mode"]:checked')?.value || '3d';
  const style = document.getElementById('modal-style-select')?.value || 'auto';
  closeModal();

  const res = await api('/api/run', {
    method: 'POST',
    body: JSON.stringify({ channel, dry, topic, engine, style, format: 'short' })
  });

  if (res.ok) {
    alert(`Pipeline (${engine.toUpperCase()}) triggered for "${topic}" (${channel.toUpperCase()})`);
    setCurrentTab('pipeline');
    refreshStatus();
  } else {
    alert('Failed to start run: ' + res.error);
  }
}

async function inspectProject(projName) {
  const data = await api('/api/project_details?project=' + projName);
  const script = data.script || {};
  const lines = script.lines || [];
  const cast = script.cast || {};

  openModal(`
    <div class="inspect-layout">
      <div class="inspect-sidebar">
        ${data.has_render ? `
          <video class="preview-vid" controls src="/api/vid?project=${projName}"></video>
        ` : (data.has_cover ? `<img class="preview-cover" src="/api/thumb?project=${projName}">` : '')}
        ${data.has_mix ? `
          <div style="margin-top:10px;">
            <label style="font-size:11px; color:var(--text-dim);">Audio Mix:</label>
            <audio controls src="/api/audio?project=${projName}&type=mix"></audio>
          </div>
        ` : ''}
        ${data.has_sheet ? `
          <button class="btn" style="width:100%; margin-top:10px;" onclick="openImage('/api/sheet?project=${projName}')">🔍 View QA Contact Sheet</button>
        ` : ''}
      </div>
      <div class="inspect-main">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
          <h2 style="margin:0; font-size:18px;">${escapeHtml(projName)}</h2>
          <span class="channel-tag ${data.channel === 'asakthi' ? 'te' : 'en'}">${data.channel}</span>
          ${data.is_uploaded ? `
            <span class="pill ok" style="margin-left:4px;">✓ UPLOADED</span>
          ` : (data.has_render ? `
            <span class="pill run" style="margin-left:4px; background:rgba(245,158,11,0.15); color:#f59e0b; border-color:rgba(245,158,11,0.3);">⚡ UNUPLOADED (READY)</span>
          ` : '')}
        </div>
        <div style="background:var(--bg); padding:12px; border-radius:8px; border:1px solid var(--border); margin-bottom:16px;">
          <div style="font-size:15px; font-weight:700; color:#fff; margin-bottom:6px;">${escapeHtml(script.title || 'Untitled')}</div>
          <div style="font-size:12px; color:var(--text-dim);">
            Voice: ${escapeHtml(script.voice || '—')} · Speed: ${script.speed || 1.0} · Music: ${escapeHtml(script.music || 'bed')}
          </div>
          ${Object.keys(cast).length > 0 ? `
            <div style="margin-top:10px; padding:8px 10px; background:rgba(168,85,247,0.08); border:1px solid rgba(168,85,247,0.25); border-radius:6px; font-size:11.5px;">
              <div style="font-weight:700; color:var(--purple); margin-bottom:6px;">👥 Cast Ensemble (${Object.keys(cast).length} Roles)</div>
              <div style="display:flex; flex-wrap:wrap; gap:8px;">
                ${Object.entries(cast).map(([id, c]) => {
                  const ccol = c.color || '#a855f7';
                  return `
                    <span style="background:var(--surface); border:1px solid var(--border); padding:3px 8px; border-radius:4px; font-size:11px;">
                      <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:${ccol}; margin-right:4px;"></span>
                      <b>${escapeHtml(c.name || id)}</b>: ${escapeHtml(c.voice || 'default')} (${c.pitch || '0Hz'})
                    </span>
                  `;
                }).join('')}
              </div>
            </div>
          ` : ''}
        </div>
        <div style="max-height:240px; overflow:auto; border:1px solid var(--border); border-radius:8px; padding:10px; background:var(--bg);">
          <div style="font-size:12px; font-weight:700; color:var(--text-dim); margin-bottom:8px;">SCENE BREAKDOWN (${lines.length} cuts)</div>
          ${lines.map((l, i) => {
            const spkKey = l.speaker || '';
            const spkObj = cast[spkKey] || {};
            const spkName = l.speaker_name || spkObj.name || spkKey;
            const spkCol = l.speaker_color || spkObj.color || '#38bdf8';
            return `
              <div style="padding:6px 0; border-bottom:1px dashed var(--border); font-size:12px;">
                <div style="display:flex; align-items:center; gap:6px; margin-bottom:3px;">
                  <b>#${i+1}</b>
                  ${spkName ? `<span style="font-size:10.5px; font-weight:700; padding:1px 6px; border-radius:4px; background:${spkCol}22; color:${spkCol}; border:1px solid ${spkCol}55;">🎭 ${escapeHtml(spkName)}</span>` : ''}
                </div>
                <div>${escapeHtml(l.text)}</div>
                <div style="color:var(--text-dim); font-size:11px; font-family:monospace; margin-top:2px;">${escapeHtml(l.caps || '')}</div>
              </div>
            `;
          }).join('')}
        </div>
        ${(() => {
          const charList = Array.isArray(data.characters?.characters) ? data.characters.characters : (Array.isArray(data.characters) ? data.characters : Object.values(data.characters || {}));
          if (!charList || charList.length === 0) return '';
          return `
            <div style="margin-top:12px; background:var(--bg); border:1px solid var(--border); border-radius:8px; padding:10px;">
              <div style="font-size:11.5px; font-weight:700; color:var(--text-dim); margin-bottom:6px;">🎭 CHARACTER SPRITES & CARDS (${charList.length})</div>
              <div style="display:flex; gap:10px; overflow-x:auto; padding-bottom:4px;">
                ${charList.map(c => {
                  const cid = c.id || 'char';
                  const cname = c.name || c.canonical || cid;
                  const csprite = c.sprite || ('assets/characters/' + cid + '.png');
                  const ccard = c.card || ('assets/characters/card_' + cid + '.jpg');
                  const cols = Array.isArray(c.palette) ? c.palette : Object.values(c.colors || {});
                  return `
                    <div style="width:110px; flex-shrink:0; background:var(--surface); border:1px solid var(--border); border-radius:6px; padding:6px; text-align:center;">
                      <img src="/api/asset?project=${projName}&path=${csprite}" style="width:56px; height:56px; object-fit:contain; border-radius:50%; background:rgba(255,255,255,0.06); margin:0 auto 4px auto; display:block; cursor:pointer;" onclick="openImage('/api/asset?project=${projName}&path=${ccard}')" title="Click to view reference card">
                      <div style="font-size:11px; font-weight:700; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escapeHtml(cname)}</div>
                      <div style="display:flex; justify-content:center; gap:2px; margin-top:3px;">
                        ${cols.slice(0, 4).map(col => `<span style="width:8px; height:8px; border-radius:2px; background:${col}; display:inline-block; border:1px solid rgba(255,255,255,0.2);" title="${col}"></span>`).join('')}
                      </div>
                    </div>
                  `;
                }).join('')}
              </div>
            </div>
          `;
        })()}
        ${(() => {
          const bgList = Array.isArray(data.backgrounds?.backgrounds) ? data.backgrounds.backgrounds : (Array.isArray(data.backgrounds) ? data.backgrounds : []);
          if (!bgList || bgList.length === 0) return '';
          return `
            <div style="margin-top:12px; background:var(--bg); border:1px solid var(--border); border-radius:8px; padding:10px;">
              <div style="font-size:11.5px; font-weight:700; color:var(--text-dim); margin-bottom:6px;">🌄 ATMOSPHERIC BACKGROUNDS (${bgList.length})</div>
              <div style="display:flex; gap:10px; overflow-x:auto; padding-bottom:4px;">
                ${bgList.map(bg => {
                  const bgPath = bg.file || ('assets/backgrounds/bg_' + bg.id + '.jpg');
                  const bgLabel = bg.setting || bg.id;
                  const bgAtm = bg.atmosphere || '';
                  return `
                    <div style="width:130px; flex-shrink:0; background:var(--surface); border:1px solid var(--border); border-radius:6px; padding:6px; text-align:center;">
                      <img src="/api/asset?project=${projName}&path=${bgPath}" style="width:100%; aspect-ratio:9/16; object-fit:cover; border-radius:4px; margin-bottom:4px; cursor:pointer;" onclick="openImage('/api/asset?project=${projName}&path=${bgPath}')" title="Click to view full background">
                      <div style="font-size:11px; font-weight:700; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escapeHtml(bgLabel)}</div>
                      <div style="font-size:10px; color:var(--text-dim); overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escapeHtml(bgAtm)}</div>
                    </div>
                  `;
                }).join('')}
              </div>
            </div>
          `;
        })()}
        <div class="toolbar" style="margin-top:16px;">
          <button class="btn primary" onclick="runAction('${projName}', 'build')">🔄 Run Build Pipeline</button>
          <button class="btn" onclick="runAction('${projName}', 'render')">🎬 Re-render MP4</button>
          ${data.has_render && !data.is_uploaded ? `
            <button class="btn primary" style="background:linear-gradient(135deg, #dc2626, #b91c1c); color:#fff; font-weight:700;" onclick="uploadProject('${projName}', true)">🚀 Upload to YouTube (${data.channel === 'asakthi' ? '🇮🇳 Asakthi' : '🇬🇧 Curiography'})</button>
          ` : (data.is_uploaded ? `
            <a class="btn" href="${data.youtube_url || ('https://youtu.be/' + data.video_id)}" target="_blank" style="background:#059669; color:#fff; text-decoration:none; font-weight:600;">▶ Watch on YouTube</a>
            <button class="btn" onclick="uploadProject('${projName}', true)">🔄 Re-Upload</button>
          ` : '')}
        </div>
      </div>
    </div>
  `);
}

function openImage(url) {
  openModal(`<img src="${url}" style="max-width:88vw; max-height:85vh; object-fit:contain; border-radius:8px;">`);
}

async function renderPerformanceTab() {
  const data = await api('/api/perf');
  const records = (data.records || []).slice().sort((a, b) => (b.date || '').localeCompare(a.date || ''));

  document.getElementById('app-content').innerHTML = `
    <div class="card">
      <div class="card-header">
        <h2>📊 YouTube Performance Hub (${records.length} videos logged)</h2>
        <button class="btn" onclick="syncYouTubeAnalytics(this)">↻ Sync YouTube Analytics</button>
      </div>
      <div class="table-wrap"><table class="performance-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Channel</th>
            <th>Title</th>
            <th>Views</th>
            <th>CTR</th>
            <th>Retention</th>
            <th>Likes</th>
            <th>Comments</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          ${records.length ? '' : '<tr><td colspan="9" style="text-align:center; color:var(--text-dim); padding:24px;">No performance records yet. Uploaded videos will appear here; use Edit to add YouTube Studio metrics.</td></tr>'}
          ${records.map((r, idx) => `
            <tr>
              <td>${escapeHtml(r.date)}</td>
              <td><span class="channel-tag ${r.channel === 'asakthi' ? 'te' : 'en'}">${r.channel === 'asakthi' ? 'TELUGU' : (r.channel === 'curiography' ? 'ENGLISH' : (r.channel || 'ENGLISH'))}</span></td>
              <td><b>${escapeHtml((r.title || '').slice(0, 45))}</b></td>
              <td>${r.views != null ? r.views.toLocaleString() : '—'}</td>
              <td>${r.ctr != null ? r.ctr + '%' : '—'}</td>
              <td>${r.retention != null ? r.retention + '%' : '—'}</td>
              <td>${r.likes != null ? r.likes : '—'}</td>
              <td>${r.comments != null ? r.comments : '—'}</td>
              <td><button class="btn" style="padding:4px 8px; font-size:11px;" onclick="editPerfRecord(${idx})">Edit</button></td>
            </tr>
          `).join('')}
        </tbody>
      </table></div>
    </div>
  `;
  window._perfRecords = records;
}

async function syncYouTubeAnalytics(button) {
  const old = button.textContent;
  button.disabled = true;
  button.textContent = 'Syncing…';
  try {
    const result = await api('/api/perf/sync', { method: 'POST', body: '{}' });
    if (!result.ok) throw new Error(result.output || 'Sync failed');
    alert(result.output || 'Analytics synced.');
    renderPerformanceTab();
  } catch (error) {
    alert(error.message || 'Analytics sync failed.');
  } finally {
    button.disabled = false;
    button.textContent = old;
  }
}

function editPerfRecord(idx) {
  const r = window._perfRecords[idx];
  openModal(`
    <div style="max-width:400px;">
      <h3 style="margin-top:0;">Log Performance for "${escapeHtml(r.title || r.video_id)}"</h3>
      <div style="display:flex; flex-direction:column; gap:10px; margin-top:14px;">
        <label>Views: <input id="inp-views" type="number" class="btn" style="width:100%;" value="${r.views || ''}"></label>
        <label>CTR (%): <input id="inp-ctr" type="number" step="0.1" class="btn" style="width:100%;" value="${r.ctr || ''}"></label>
        <label>Retention (%): <input id="inp-ret" type="number" step="0.1" class="btn" style="width:100%;" value="${r.retention || ''}"></label>
        <label>Likes: <input id="inp-likes" type="number" class="btn" style="width:100%;" value="${r.likes || ''}"></label>
        <label>Comments: <input id="inp-comments" type="number" class="btn" style="width:100%;" value="${r.comments || ''}"></label>
        <button class="btn primary" style="margin-top:10px;" onclick="savePerfRecord('${r.video_id}')">💾 Save Metrics</button>
      </div>
    </div>
  `);
}

async function savePerfRecord(videoId) {
  const rec = {
    video_id: videoId,
    views: parseFloat(document.getElementById('inp-views').value) || null,
    ctr: parseFloat(document.getElementById('inp-ctr').value) || null,
    retention: parseFloat(document.getElementById('inp-ret').value) || null,
    likes: parseInt(document.getElementById('inp-likes').value) || null,
    comments: parseInt(document.getElementById('inp-comments').value) || null,
  };
  await api('/api/perf', { method: 'POST', body: JSON.stringify({ record: rec }) });
  closeModal();
  renderPerformanceTab();
}

async function renderLedgerTab() {
  const data = await api('/api/file?path=daily/topics-done.md');
  document.getElementById('app-content').innerHTML = `
    <div class="card">
      <div class="card-header">
        <div><h2>📖 Topic Ledger</h2><div class="subtle">Topics already used by either channel. Keep one entry per completed or staged video.</div></div>
        <div class="ledger-actions"><span id="ledger-state" class="subtle">Saved · backup created on save</span><button id="ledger-save" class="btn primary" onclick="saveLedger()">💾 Save ledger</button></div>
      </div>
      <textarea id="ledger-text" class="code-editor" aria-label="Topic ledger" spellcheck="false">${escapeHtml(data.content || '')}</textarea>
    </div>
  `;
  const editor = document.getElementById('ledger-text');
  editor.addEventListener('input', () => {
    const state = document.getElementById('ledger-state');
    state.textContent = 'Unsaved changes'; state.style.color = 'var(--warning, #fbbf24)';
  });
}

async function saveLedger() {
  const content = document.getElementById('ledger-text').value;
  const button = document.getElementById('ledger-save');
  const state = document.getElementById('ledger-state');
  button.disabled = true; button.textContent = 'Saving…';
  const res = await api('/api/file', {
    method: 'POST',
    body: JSON.stringify({ path: 'daily/topics-done.md', content })
  });
  button.disabled = false; button.textContent = '💾 Save ledger';
  if (res.ok) { state.textContent = 'Saved · backup created'; state.style.color = 'var(--success, #34d399)'; }
  else { state.textContent = 'Save failed: ' + (res.error || 'unknown error'); state.style.color = 'var(--danger, #fb7185)'; }
}

async function renderLogsTab() {
  const logsList = await api('/api/logs');
  const logs = logsList.logs || [];

  document.getElementById('app-content').innerHTML = `
    <div class="card">
      <div class="card-header">
        <div>
          <h2 style="margin:0 0 4px 0;">📜 Live Execution Logs</h2>
          <div style="font-size:12px; color:var(--text-dim);">
            Real-time stdout/stderr stream from run-daily.sh, build pipeline, and rendering
          </div>
        </div>
        <div style="display:flex; gap:10px; align-items:center;">
          <select id="log-select" class="btn" onchange="loadLogContent()">
            ${logs.map(l => `<option value="${l}">${l}.log</option>`).join('')}
          </select>
          <label style="font-size:12px; color:var(--text-dim); display:flex; align-items:center; gap:6px;">
            <input type="checkbox" id="auto-tail" checked> Auto-tail (5s poll)
          </label>
        </div>
      </div>

      <div class="sub-nav">
        <button class="${currentLogChannel === 'all' ? 'active' : ''}" onclick="setLogChannel('all')">
          All Logs
        </button>
        <button class="en ${currentLogChannel === 'en' ? 'active en' : ''}" onclick="setLogChannel('en')">
          🇬🇧 English Stream
        </button>
        <button class="te ${currentLogChannel === 'te' ? 'active te' : ''}" onclick="setLogChannel('te')">
          🇮🇳 Telugu Stream
        </button>
        <button class="${currentLogChannel === 'broadcast' ? 'active' : ''}" style="color:#10b981; font-weight:700;" onclick="setLogChannel('broadcast')">
          📡 Broadcast Stream
        </button>
        <button class="btn" style="margin-left:auto; padding:4px 10px; font-size:11px;" onclick="loadLogContent()">
          🔄 Refresh Log Now
        </button>
      </div>

      <div id="log-terminal">Loading live log stream...</div>
    </div>
  `;
  loadLogContent();
}

function setLogChannel(ch) {
  currentLogChannel = ch;
  renderLogsTab();
}

async function loadLogContent() {
  const date = document.getElementById('log-select')?.value;
  if (!date) return;
  const data = await api(`/api/log?date=${date}&tail=800&channel=${currentLogChannel}`);
  const term = document.getElementById('log-terminal');
  if (term) {
    term.textContent = (data.lines && data.lines.length > 0) ? data.lines.join('\n') : '(No log entries for this channel filter yet)';
    if (document.getElementById('auto-tail')?.checked) {
      term.scrollTop = term.scrollHeight;
    }
  }
}

async function triggerRun(channel) {
  const dry = document.getElementById('dry-run-check').checked;
  const engine = document.getElementById('engine-select')?.value || '3d';
  const style = document.getElementById('style-select')?.value || 'auto';
  const chName = channel === 'en' ? 'English (Curiography)' : (channel === 'te' ? 'Telugu (Asakthi)' : 'Both Channels');
  const engineLabel = engine === 'mpt' ? 'MoneyPrinterTurbo (Real B-Roll + Pop Captions)' : 'Three.js 3D Cinema';
  if (!confirm(`Trigger ${engineLabel} Pipeline run for ${chName}? (DRY_RUN=${dry ? '1' : '0'})`)) return;

  const res = await api('/api/run', {
    method: 'POST',
    body: JSON.stringify({ channel, dry, engine, style, format: 'short' })
  });
  if (res.ok) {
    alert(`Pipeline (${engine.toUpperCase()}) triggered for ${chName}!`);
    setTimeout(refreshStatus, 2000);
  } else {
    alert('Failed to trigger run: ' + res.error);
  }
}

let broadcastPollInterval = null;

async function openBroadcastModal(channel = 'all', pid = null) {
  const chLabel = channel === 'en' ? 'English (Curiography)' : (channel === 'te' ? 'Telugu (Asakthi)' : 'All Channels');

  openModal(`
    <div style="width:min(850px, 82vw); max-width:100%;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; border-bottom:1px solid var(--border); padding-bottom:10px;">
        <div style="display:flex; align-items:center; gap:10px;">
          <span style="font-size:22px;">📡</span>
          <div>
            <h3 style="margin:0; font-size:16px;">Live Broadcast Monitor</h3>
            <div style="font-size:12px; color:var(--text-dim);" id="bc-subtext">Publishing queued video for: <b>${escapeHtml(chLabel)}</b></div>
          </div>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <span id="bc-badge" class="pill" style="background:#10b98125; color:#10b981; border:1px solid #10b981; font-weight:700;">
            ● RUNNING ${pid ? `(PID: ${pid})` : ''}
          </span>
          <button class="btn" style="background:#dc2626; color:#fff; font-size:12px; font-weight:700;" onclick="stopBroadcast()">🛑 Stop Broadcast</button>
          <button class="btn" style="font-size:12px;" onclick="closeBroadcastModal()">✖ Close</button>
        </div>
      </div>

      <div style="margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
        <span style="font-size:12px; color:var(--text-dim);">Live terminal output (updating in real time):</span>
        <label style="font-size:12px; color:var(--text-dim); display:flex; align-items:center; gap:6px;">
          <input type="checkbox" id="bc-autoscroll" checked> Auto-scroll to latest
        </label>
      </div>

      <div id="bc-log-viewer" style="
        background:#070a12;
        border:1px solid var(--border);
        border-radius:8px;
        padding:12px 14px;
        height:340px;
        overflow-y:auto;
        font:11.5px/1.5 ui-monospace, Menlo, monospace;
        color:#34d399;
        white-space:pre-wrap;
        word-break:break-all;
      ">Loading broadcast process output...</div>

      <div style="margin-top:12px; display:flex; justify-content:space-between; align-items:center; font-size:12px; color:var(--text-dim);">
        <div>Tip: Closing this window will NOT stop the upload. It continues safely in the background.</div>
        <button class="btn" style="font-size:11.5px;" onclick="closeBroadcastModal(); currentTab='logs'; renderLogsTab();">📜 Open in Full Live Logs Tab</button>
      </div>
    </div>
  `);

  if (broadcastPollInterval) clearInterval(broadcastPollInterval);

  async function pollBroadcast() {
    try {
      const data = await api('/api/broadcast_status');
      const box = document.getElementById('bc-log-viewer');
      const badge = document.getElementById('bc-badge');
      if (!box) {
        clearInterval(broadcastPollInterval);
        return;
      }
      if (data.lines && data.lines.length > 0) {
        box.textContent = data.lines.join('\n');
        if (document.getElementById('bc-autoscroll')?.checked) {
          box.scrollTop = box.scrollHeight;
        }
      } else {
        box.textContent = 'Waiting for broadcast process to emit log lines...';
      }

      if (data.is_running) {
        if (badge) {
          badge.innerHTML = `● RUNNING (PID: ${data.pid})`;
          badge.style.background = '#10b98125';
          badge.style.color = '#10b981';
          badge.style.borderColor = '#10b981';
        }
      } else {
        if (badge) {
          badge.innerHTML = `✓ IDLE / FINISHED`;
          badge.style.background = '#374151';
          badge.style.color = '#9ca3af';
          badge.style.borderColor = '#4b5563';
        }
      }
    } catch (e) {
      console.error(e);
    }
  }

  pollBroadcast();
  broadcastPollInterval = setInterval(pollBroadcast, 1500);
}

function closeBroadcastModal() {
  if (broadcastPollInterval) clearInterval(broadcastPollInterval);
  closeModal();
}

async function triggerBroadcast(channel = 'all') {
  const chLabel = channel === 'en' ? 'English (Curiography)' : (channel === 'te' ? 'Telugu (Asakthi)' : 'All Channels');
  if (!confirm(`🚀 Manually trigger instant broadcast for ${chLabel}?\n\nThis will publish pre-rendered videos waiting in the queue to YouTube in the background.`)) return;

  const res = await api('/api/broadcast', {
    method: 'POST',
    body: JSON.stringify({ channel })
  });

  if (res.ok) {
    // Immediately open Live Broadcast Monitor!
    openBroadcastModal(channel, res.pid);
    refreshStatus();
  } else {
    alert('Failed to trigger broadcast: ' + (res.error || 'Unknown error'));
  }
}

async function stopBroadcast() {
  if (!confirm('🛑 STOP CURRENT BROADCAST PROCESS?\n\nThis will immediately terminate running upload and broadcast workers.')) return;
  const res = await api('/api/broadcast_stop', { method: 'POST' });
  if (res.ok) {
    alert('🛑 Broadcast stopped!');
    refreshStatus();
  } else {
    alert('Failed to stop broadcast: ' + (res.error || 'Unknown error'));
  }
}

async function stopPipeline() {
  if (!confirm('⚠️ STOP ALL ACTIVE PIPELINES?\n\nThis will immediately kill running generation scripts, terminate upload retry loops, and remove lock files.')) return;
  const res = await api('/api/stop', { method: 'POST' });
  if (res.ok) {
    alert('🛑 Pipeline stopped! All active generation and upload processes have been terminated.');
    await refreshStatus();
    if (typeof renderPipelineTab === 'function') renderPipelineTab();
  } else {
    alert('Failed to stop pipeline: ' + (res.error || 'Unknown error'));
  }
}

async function runAction(project, action) {
  if (!confirm(`Execute action "${action}" on project "${project}"?`)) return;
  const res = await api('/api/action', {
    method: 'POST',
    body: JSON.stringify({ project, action })
  });
  if (res.ok) {
    alert(`Action ${action} initiated (pid: ${res.pid})`);
    closeModal();
    setCurrentTab('logs');
  } else {
    alert('Error: ' + res.error);
  }
}

async function uploadProject(project, force = true) {
  if (!confirm(`🚀 Upload video for project "${project}" to YouTube? This will bypass dry-run mode and publish live.`)) return;
  const res = await api('/api/action', {
    method: 'POST',
    body: JSON.stringify({ project, action: 'upload', force: force })
  });
  if (res.ok) {
    alert(`YouTube upload started for "${project}" (pid: ${res.pid})! Switching to live logs...`);
    if (typeof closeModal === 'function') closeModal();
    setCurrentTab('logs');
  } else {
    alert('Upload initiation failed: ' + res.error);
  }
}

// Refresh dashboard state without interrupting media playback.
setInterval(() => {
  refreshStatus();
  if (currentTab === 'logs' && document.getElementById('auto-tail')?.checked) {
    loadLogContent();
  }
}, 5000);

updateEngineControls();
refreshStatus().then(renderTab);
