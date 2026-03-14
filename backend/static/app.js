/**
 * FocusAI PRO MONITOR - Full Working, Real Data Only
 */
const API_BASE = '';
let ws = null;
let charts = {};
let currentState = null;

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initSidebar();
  initCharts();
  initSettings();
  loadSettings();
  connectWebSocket();
  startSessionTimer();
  addPageHeaders();
});

function addPageHeaders() {
  const pages = ['productivity', 'security', 'reports', 'settings', 'status'];
  const titles = {
    productivity: 'Productivity Analytics',
    security: 'Security Monitor',
    reports: 'Reports & Exports',
    settings: 'Settings',
    status: 'System Status'
  };
  pages.forEach(pageId => {
    const page = document.getElementById(`page-${pageId}`);
    if (!page) return;
    const header = document.createElement('div');
    header.className = 'page-header';
    header.innerHTML = `
      <div>
        <div class="page-title">${titles[pageId]}</div>
        <div class="page-date">${formatDate(new Date())}</div>
      </div>
      <div class="page-status-group">
        <span class="live-badge"><span class="live-dot"></span> LIVE</span>
        <span class="active-pill" id="pageActivePill">ACTIVE</span>
      </div>
    `;
    page.insertBefore(header, page.firstChild);
  });
}

function formatDate(d) {
  return d.toLocaleDateString('en-US', {
    weekday: 'long', year: 'numeric', month: 'short', day: 'numeric'
  });
}

function initNavigation() {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const page = item.dataset.page;
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      item.classList.add('active');
      document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
      document.getElementById(`page-${page}`)?.classList.add('active');
      if (page === 'reports') loadReportsData();
    });
  });
  const hash = window.location.hash.slice(1) || 'dashboard';
  const navItem = document.querySelector(`[data-page="${hash}"]`);
  if (navItem) navItem.click();
}

function initSidebar() {
  const btn = document.getElementById('collapseBtn');
  const sidebar = document.getElementById('sidebar');
  if (btn && sidebar) btn.addEventListener('click', () => sidebar.classList.toggle('collapsed'));
}

function connectWebSocket() {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${protocol}//${location.host}/ws/dashboard`);
  ws.onopen = () => {
    document.getElementById('syncStatus').textContent = 'LIVE';
  };
  ws.onmessage = (e) => {
    try {
      currentState = JSON.parse(e.data);
      updateDashboard(currentState);
    } catch (err) { console.error(err); }
  };
  ws.onclose = () => {
    document.getElementById('syncStatus').textContent = 'Reconnecting...';
    setTimeout(connectWebSocket, 3000);
  };
  ws.onerror = () => {
    setInterval(fetchDashboard, 3000);
    fetchDashboard();
  };
}

async function fetchDashboard() {
  try {
    const res = await fetch(`${API_BASE}/api/dashboard`);
    currentState = await res.json();
    updateDashboard(currentState);
  } catch (err) {
    document.getElementById('syncStatus').textContent = 'Offline';
  }
}

function updateDashboard(state) {
  if (!state) return;

  const systemState = document.getElementById('systemState');
  const systemStateText = document.getElementById('systemStateText');
  if (systemState) systemState.className = 'status-dot' + (state.system_state === 'idle' ? ' idle' : '');
  if (systemStateText) systemStateText.textContent = state.system_state === 'idle' ? 'IDLE' : 'ACTIVE';

  document.querySelectorAll('.active-pill').forEach(el => {
    if (el) el.textContent = state.system_state === 'idle' ? 'IDLE' : 'ACTIVE';
  });

  const aiEl = document.getElementById('aiEngineStatus');
  if (aiEl) aiEl.textContent = state.ai_engine_status === 'running' ? 'Running' : 'Idle';

  const threatEl = document.getElementById('threatLevel');
  if (threatEl) {
    threatEl.textContent = (state.threat_level || 'low').toUpperCase();
    threatEl.className = 'badge-' + (state.threat_level || 'low');
  }

  const sessionEl = document.getElementById('sessionTime');
  if (sessionEl) sessionEl.textContent = formatSessionTime(state.session_time_sec);

  const syncEl = document.getElementById('syncStatus');
  if (syncEl) syncEl.textContent = state.sync_status === 'synced' ? 'LIVE' : state.sync_status;

  const focusEl = document.getElementById('focusScore');
  if (focusEl) {
    const prev = parseInt(focusEl.textContent, 10);
    animateValue('focusScore', state.focus_score, (isNaN(prev) ? 0 : prev), 400);
  }

  const gradeEl = document.getElementById('gradeBadge');
  if (gradeEl) gradeEl.textContent = `Grade ${state.productivity_grade || '-'}`;

  const insightEl = document.getElementById('aiSuggestion');
  if (insightEl) insightEl.textContent = state.ai_suggestion || 'Initializing...';

  const cpuEl = document.getElementById('cpuUsage');
  if (cpuEl) cpuEl.textContent = `${state.cpu_usage || 0}%`;

  const ramEl = document.getElementById('ramUsage');
  if (ramEl) ramEl.textContent = `${state.ram_usage || 0}%`;

  const netUp = document.getElementById('networkUpload');
  if (netUp) netUp.textContent = formatBytes(state.network_upload || 0);

  const netDown = document.getElementById('networkDownload');
  if (netDown) netDown.textContent = formatBytes(state.network_download || 0);

  const procEl = document.getElementById('processCount');
  if (procEl) procEl.textContent = state.active_processes || 0;

  renderAlerts(state.alerts || []);
  updateTopAppsChart(state.top_apps || []);
  updateProductivityChart(state.productivity_split || {});
  updateFocusTrendChart(state.focus_trend || []);
  updateNetworkChart(state);
  renderProcessTable(state.top_processes || []);
  renderAppRanking(state.top_apps || []);

  const deepWorkEl = document.getElementById('deepWorkDuration');
  if (deepWorkEl) {
    const sec = state.productive_sec || 0;
    if (sec >= 3600) deepWorkEl.textContent = `${Math.floor(sec / 3600)}h ${Math.floor((sec % 3600) / 60)}m`;
    else if (sec >= 60) deepWorkEl.textContent = `${Math.floor(sec / 60)}m`;
    else deepWorkEl.textContent = `${sec}s`;
  }

  const switchEl = document.getElementById('switchFrequency');
  if (switchEl) switchEl.textContent = `${state.switch_count || 0}x`;

  const idleEl = document.getElementById('idleRatio');
  if (idleEl) idleEl.textContent = `${state.idle_ratio || 0}%`;

  const riskEl = document.getElementById('riskScore');
  if (riskEl) {
    riskEl.textContent = state.risk_score ?? 100;
    riskEl.className = 'risk-value ' + (state.risk_score >= 80 ? 'low' : state.risk_score >= 50 ? 'medium' : 'high');
  }

  updateReports(state);
  updateSystemStatus(state);
}

function renderProcessTable(processes) {
  const tbody = document.getElementById('processTableBody');
  if (!tbody) return;
  const data = (processes || []).slice(0, 5);
  const barColor = r => r === 'high' ? '#f85149' : r === 'medium' ? '#d29922' : '#3fb950';
  tbody.innerHTML = data.map(p => {
    const pc = Math.min(p.cpu_percent || 0, 100);
    return `<tr>
      <td>${(p.name || 'unknown').replace('.exe', '')}</td>
      <td><span class="cpu-bar" style="--w:${pc}%;--c:${barColor(p.risk)}"></span> ${pc}%</td>
      <td><span class="risk-badge ${p.risk || 'low'}">${(p.risk || 'low').toUpperCase()}</span></td>
    </tr>`;
  }).join('') || '<tr><td colspan="3">No processes</td></tr>';
}

function renderAppRanking(topApps) {
  const tbody = document.getElementById('appRankingBody');
  if (!tbody) return;
  const data = (topApps || []).slice(0, 5);
  const getScore = (cat) => cat === 'productive' ? 85 : cat === 'distracting' ? 25 : 55;
  tbody.innerHTML = data.map((a, i) => {
    const cat = a.category || 'neutral';
    return `<tr>
      <td>${String(i + 1).padStart(2, '0')}</td>
      <td>${(a.name || 'Unknown').replace('.exe', '')}</td>
      <td>${Math.floor((a.duration || 0) / 60)}m</td>
      <td><span class="category-pill ${cat}">${cat.charAt(0).toUpperCase() + cat.slice(1)}</span></td>
      <td>${getScore(cat)}</td>
    </tr>`;
  }).join('') || '<tr><td colspan="5">No data yet</td></tr>';
}

async function loadReportsData() {
  try {
    const [weeklyRes, monthlyRes] = await Promise.all([
      fetch(`${API_BASE}/api/reports/weekly`),
      fetch(`${API_BASE}/api/reports/monthly`)
    ]);
    const weekly = await weeklyRes.json();
    const monthly = await monthlyRes.json();
    updateWeeklyReport(weekly);
    updateMonthChart(monthly);
  } catch (err) { console.error(err); }
}

function updateReports(state) {
  const dailyList = document.getElementById('dailyReportList');
  if (dailyList) {
    const topApp = state.top_apps?.[0]?.name || '--';
    const distCount = (state.alerts || []).filter(a => ['focus', 'switching'].includes(a.type)).length;
    const threatCount = (state.alerts || []).filter(a => a.severity === 'critical').length;
    dailyList.innerHTML = `
      <li>Focus Score: ${state.focus_score || 0}% → Grade ${state.productivity_grade || '-'}</li>
      <li>Deep Work: ${state.productive_sec ? Math.floor(state.productive_sec / 60) + 'm' : '--'}</li>
      <li>Top App: ${topApp}</li>
      <li>Distractions: ${distCount} flagged</li>
      <li>Threats Detected: ${threatCount}</li>
    `;
  }
  const weeklyList = document.getElementById('weeklyReportList');
  if (weeklyList && state) {
    weeklyList.innerHTML = `
      <li>Avg Focus: ${state.focus_score || 0}%</li>
      <li>Best Day: Loading...</li>
      <li>Context Switching: ${state.switch_count || 0}x</li>
      <li>Recommendation: ${state.ai_suggestion || '--'}</li>
    `;
  }
}

function updateWeeklyReport(weekly) {
  const list = document.getElementById('weeklyReportList');
  if (!list) return;
  list.innerHTML = `
    <li>Avg Focus: ${weekly.avg_focus || 0}%</li>
    <li>Best Day: ${weekly.best_day || '-'}</li>
    <li>Context Switching: ${currentState?.switch_count || 0}x</li>
    <li>Recommendation: ${weekly.recommendation || currentState?.ai_suggestion || '-'}</li>
  `;
}

function updateMonthChart(monthly) {
  if (!charts.monthFocus) return;
  const data = monthly || [];
  charts.monthFocus.data.labels = data.map(d => d.date?.slice(-2) || '');
  charts.monthFocus.data.datasets[0].data = data.map(d => d.score || 0);
  charts.monthFocus.update('none');
}

async function updateSystemStatus(state) {
  const modules = document.querySelectorAll('.module-uptime');
  const sessionStr = formatSessionTime(state.session_time_sec || 0);
  modules.forEach((el, i) => {
    if (i < 5) el.textContent = sessionStr;
    else el.textContent = '--';
  });

  try {
    const res = await fetch(`${API_BASE}/api/log`);
    const logs = await res.json();
    const logEl = document.getElementById('systemLog');
    if (logEl) {
      const levels = { INFO: 'log-info', WARN: 'log-warn', ALERT: 'log-alert', SYNC: 'log-sync', INIT: 'log-info' };
      logEl.innerHTML = logs.map(e =>
        `<div class="log-entry"><span class="log-time">${e.time}</span> <span class="${levels[e.level] || 'log-info'}">[${e.level}]</span> ${e.msg}</div>`
      ).join('') || '<div class="log-entry"><span class="log-info">[INIT]</span> Waiting for data...</div>';
    }
  } catch (err) {}
}

function animateValue(id, target, from, duration) {
  const el = document.getElementById(id);
  if (!el) return;
  const start = performance.now();
  const diff = target - from;
  function step(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 2);
    el.textContent = Math.round(from + diff * eased);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function formatSessionTime(sec) {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  return [h, m, s].map(v => v.toString().padStart(2, '0')).join(':');
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function renderAlerts(alerts) {
  const list = document.getElementById('alertList');
  if (!list) return;
  const icons = { warning: '⚠', critical: '❌', stable: '✅' };
  if (!alerts || alerts.length === 0) {
    list.innerHTML = `<div class="alert-item stable"><span class="alert-icon">✅</span><div><div>All systems stable</div><div class="alert-time">No alerts</div></div></div>`;
    return;
  }
  list.innerHTML = alerts.slice(0, 5).map(a => `
    <div class="alert-item ${a.severity}">
      <span class="alert-icon">${icons[a.severity] || '⚠'}</span>
      <div><div>${a.message}</div><div class="alert-time">Just now</div></div>
    </div>
  `).join('');
}

const chartColors = {
  green: 'rgba(63, 185, 80, 0.8)',
  orange: 'rgba(210, 153, 34, 0.8)',
  purple: 'rgba(163, 113, 247, 0.8)',
  blue: 'rgba(88, 166, 255, 0.8)',
  red: 'rgba(248, 81, 73, 0.8)'
};

function initCharts() {
  const gridColor = 'rgba(255, 255, 255, 0.06)';
  const textColor = 'rgba(139, 148, 158, 0.9)';
  const commonOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: { legend: { labels: { color: textColor } } },
    scales: { x: { grid: { color: gridColor }, ticks: { color: textColor } }, y: { grid: { color: gridColor }, ticks: { color: textColor } } }
  };

  const topAppsCtx = document.getElementById('topAppsChart')?.getContext('2d');
  if (topAppsCtx) {
    charts.topApps = new Chart(topAppsCtx, {
      type: 'bar',
      data: { labels: [], datasets: [{ label: 'Minutes', data: [], backgroundColor: chartColors.purple }] },
      options: { ...commonOptions, indexAxis: 'y', plugins: { legend: { display: false } } }
    });
  }

  const prodCtx = document.getElementById('productivityChart')?.getContext('2d');
  if (prodCtx) {
    charts.productivity = new Chart(prodCtx, {
      type: 'doughnut',
      data: { labels: ['Productive', 'Neutral', 'Distracting'], datasets: [{ data: [0, 100, 0], backgroundColor: [chartColors.green, chartColors.orange, chartColors.red] }] },
      options: { ...commonOptions, cutout: '60%' }
    });
  }

  const netCtx = document.getElementById('networkChart')?.getContext('2d');
  if (netCtx) {
    charts.network = new Chart(netCtx, {
      type: 'line',
      data: {
        labels: Array.from({ length: 20 }, (_, i) => i),
        datasets: [
          { label: 'Upload KB', data: [], borderColor: chartColors.blue, fill: false, tension: 0.3 },
          { label: 'Download KB', data: [], borderColor: chartColors.green, fill: false, tension: 0.3 }
        ]
      },
      options: { ...commonOptions }
    });
  }

  const monthCtx = document.getElementById('monthFocusChart')?.getContext('2d');
  if (monthCtx) {
    charts.monthFocus = new Chart(monthCtx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{ label: 'Focus %', data: [], borderColor: chartColors.blue, fill: true, tension: 0.3 }]
      },
      options: { ...commonOptions }
    });
  }

  const trendCtx = document.getElementById('focusTrendChart')?.getContext('2d');
  if (trendCtx) {
    charts.focusTrend = new Chart(trendCtx, {
      type: 'line',
      data: { labels: [], datasets: [{ label: 'Focus %', data: [], borderColor: chartColors.blue, backgroundColor: 'rgba(88, 166, 255, 0.1)', fill: true, tension: 0.3 }] },
      options: { ...commonOptions, scales: { y: { ...commonOptions.scales.y, min: 0, max: 100 } } }
    });
  }
}

function updateTopAppsChart(topApps) {
  if (!charts.topApps) return;
  const data = (topApps || []).slice(0, 5);
  charts.topApps.data.labels = data.map(a => (a.name || 'Unknown').replace('.exe', ''));
  charts.topApps.data.datasets[0].data = data.map(a => Math.round((a.duration || 0) / 60));
  charts.topApps.update('none');
}

function updateProductivityChart(split) {
  if (!charts.productivity || !split) return;
  charts.productivity.data.datasets[0].data = [
    split.productive || 0,
    split.neutral || 0,
    split.distracting || 0
  ];
  charts.productivity.update('none');
}

function updateFocusTrendChart(trend) {
  if (!charts.focusTrend) return;
  const data = trend || [];
  charts.focusTrend.data.labels = data.map((_, i) => `${i * 2}m`);
  charts.focusTrend.data.datasets[0].data = data.map(d => d.score || 0);
  charts.focusTrend.update('none');
}

function updateNetworkChart(state) {
  if (!charts.network || !state) return;
  const hist = state.network_history || [];
  const u = hist.map(h => (h.upload || 0) / 1024);
  const d = hist.map(h => (h.download || 0) / 1024);
  charts.network.data.labels = u.map((_, i) => i);
  charts.network.data.datasets[0].data = u;
  charts.network.data.datasets[1].data = d;
  charts.network.update('none');
}

function startSessionTimer() {
  setInterval(() => {
    if (currentState) {
      currentState.session_time_sec = (currentState.session_time_sec || 0) + 1;
      document.getElementById('sessionTime').textContent = formatSessionTime(currentState.session_time_sec);
    }
  }, 1000);
}

async function loadSettings() {
  try {
    const res = await fetch(`${API_BASE}/api/settings`);
    const s = await res.json();
    const idle = document.getElementById('idleThreshold');
    if (idle) { idle.value = s.idle_threshold_sec || 30; document.getElementById('idleValue').textContent = (s.idle_threshold_sec || 30) + 's'; }
    const focus = document.getElementById('focusSensitivity');
    if (focus) { focus.value = s.focus_sensitivity === 'high' ? 100 : s.focus_sensitivity === 'low' ? 30 : 70; document.getElementById('focusValue').textContent = focus.value + '%'; }
    const alert = document.getElementById('alertSensitivity');
    if (alert) { alert.value = s.alert_sensitivity === 'high' ? 100 : s.alert_sensitivity === 'low' ? 30 : 50; document.getElementById('alertValue').textContent = alert.value + '%'; }
    const refresh = document.getElementById('refreshInterval');
    if (refresh) { refresh.value = s.refresh_interval_sec || 3; document.getElementById('refreshValue').textContent = (s.refresh_interval_sec || 3) + 's'; }
  } catch (err) {}
}

function initSettings() {
  document.getElementById('idleThreshold')?.addEventListener('input', (e) => {
    document.getElementById('idleValue').textContent = e.target.value + 's';
    saveSettings();
  });
  document.getElementById('focusSensitivity')?.addEventListener('input', (e) => {
    document.getElementById('focusValue').textContent = e.target.value + '%';
    saveSettings();
  });
  document.getElementById('alertSensitivity')?.addEventListener('input', (e) => {
    document.getElementById('alertValue').textContent = e.target.value + '%';
    saveSettings();
  });
  document.getElementById('refreshInterval')?.addEventListener('input', (e) => {
    document.getElementById('refreshValue').textContent = e.target.value + 's';
    saveSettings();
  });
  document.querySelectorAll('.theme-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      save_setting('theme', btn.dataset.theme);
    });
  });
}

let saveTimeout;
function saveSettings() {
  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(async () => {
    try {
      const focusVal = document.getElementById('focusSensitivity')?.value || 70;
      const alertVal = document.getElementById('alertSensitivity')?.value || 50;
      await fetch(`${API_BASE}/api/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          idle_threshold_sec: parseInt(document.getElementById('idleThreshold')?.value) || 30,
          focus_sensitivity: focusVal >= 80 ? 'high' : focusVal <= 40 ? 'low' : 'medium',
          alert_sensitivity: alertVal >= 80 ? 'high' : alertVal <= 40 ? 'low' : 'medium',
          refresh_interval_sec: parseInt(document.getElementById('refreshInterval')?.value) || 3
        })
      });
    } catch (err) {}
  }, 500);
}

document.getElementById('exportDailyPdf')?.addEventListener('click', () => {
  window.location.href = `${API_BASE}/api/reports/pdf/daily`;
});
document.getElementById('exportWeeklyPdf')?.addEventListener('click', () => {
  window.location.href = `${API_BASE}/api/reports/pdf/weekly`;
});
