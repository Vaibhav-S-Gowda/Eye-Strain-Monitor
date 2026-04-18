// ============================================================
// Neural Nexus Dashboard — Main JavaScript
// ============================================================

let blinkChart;
let blinkChartMode = 'line'; // 'line' or 'bar'
let fatigueChart;
let distanceChart;
let weeklyChart;
let map;

// Session Timer Tracking
let sessionUptimeSeconds = 0;
setInterval(() => {
    const statusEl = document.getElementById('system-status');
    if (statusEl && statusEl.textContent === 'Monitoring') {
        sessionUptimeSeconds++;
        const el = document.getElementById('session-timer-val');
        if (el) {
            const h = Math.floor(sessionUptimeSeconds / 3600).toString().padStart(2, '0');
            const m = Math.floor((sessionUptimeSeconds % 3600) / 60).toString().padStart(2, '0');
            const s = (sessionUptimeSeconds % 60).toString().padStart(2, '0');
            el.innerHTML = `${h}:${m}:${s}`;
        }
    }
}, 1000);

// Global Personalization Settings
let fatigueThresholdTarget = 65; // Default normal
const sensitivityDict = { 'strict': 50, 'normal': 65, 'relaxed': 80 };

function applyAmbientGlow(fatigue) {
    let shadow = 'none';
    if (fatigue > fatigueThresholdTarget) {
        shadow = 'inset 0 0 120px rgba(239, 68, 68, 0.25)'; // Red glow
    } else if (fatigue > fatigueThresholdTarget - 20) {
        shadow = 'inset 0 0 80px rgba(232, 200, 74, 0.15)'; // Yellow glow
    }
    document.body.style.boxShadow = shadow;
    document.body.style.transition = 'box-shadow 2s ease-in-out';
}

function calculatePredictiveFatigue(historyData, threshold) {
    if(!historyData || historyData.length < 5) return 'Prediction calculating...';
    
    const recent = historyData.slice(-5);
    const first = recent[0];
    const last = recent[recent.length - 1];

    const fatigueDiff = last.fatigue - first.fatigue; // Positive if gaining fatigue
    const timeDiffMs = last.timestamp - first.timestamp;
    
    if (fatigueDiff <= 0) return 'Fatigue stable. Keep it up!';

    const fatiguePerMinute = (fatigueDiff / (timeDiffMs / 60000));
    if (fatiguePerMinute < 1) return 'Fatigue stable. Keep it up!';

    // Time remaining until threshold
    const fatigueRemaining = Math.max(0, threshold - last.fatigue);
    const minutesRemaining = fatigueRemaining / fatiguePerMinute;

    if (minutesRemaining < 1) return '⚠️ Fatigue threshold imminent!';
    if (minutesRemaining > 60) return 'Fatigue stable. Keep it up!';

    return `⚠️ Fatigue likely in ~${Math.round(minutesRemaining)} min`;
}

function createGradient(ctx, colorStart, colorEnd) {
    const g = ctx.createLinearGradient(0, 0, 0, 400);
    g.addColorStop(0, colorStart);
    g.addColorStop(1, colorEnd);
    return g;
}

const horizontalLinePlugin = {
    id: 'horizontalLine',
    beforeDraw: (chart) => {
        if(chart.config.options.plugins.horizontalLine) {
            const yValue = chart.config.options.plugins.horizontalLine.y;
            const yAxis = chart.scales.y;
            const yPixel = yAxis.getPixelForValue(yValue);
            const ctx = chart.ctx;
            ctx.save();
            ctx.beginPath();
            ctx.moveTo(chart.chartArea.left, yPixel);
            ctx.lineTo(chart.chartArea.right, yPixel);
            ctx.lineWidth = 1;
            ctx.strokeStyle = 'rgba(239, 68, 68, 0.5)';
            ctx.setLineDash([5, 5]);
            ctx.stroke();
            ctx.restore();
        }
    }
};
Chart.register(horizontalLinePlugin);

function initCharts() {
    Chart.defaults.color = '#888';
    Chart.defaults.font.family = "'Inter', sans-serif";

    // 1. Blink vs Fatigue Dual-Line Chart (Dashboard)
    const elBlink = document.getElementById("blinkChart");
    if (elBlink) {
        const ctx = elBlink.getContext("2d");
        blinkChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: "Blink Rate (per min)",
                        data: [],
                        borderColor: '#e8c84a',
                        backgroundColor: 'rgba(232, 200, 74, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        yAxisID: 'y'
                    },
                    {
                        label: "Fatigue Index (%)",
                        data: [],
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        tension: 0.4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: { 
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(15, 15, 15, 0.9)',
                        titleColor: '#e8c84a',
                        bodyColor: '#fff',
                        borderColor: 'rgba(255,255,255,0.1)',
                        borderWidth: 1,
                        padding: 10,
                        callbacks: {
                            afterBody: function(context) {
                                const blinks = context[0]?.raw || 0;
                                const fatigue = context[1]?.raw || 0;
                                if (fatigue > 65 && blinks < 12) return '\n⚠️ Low blinks driving fatigue up. Take a break!';
                                return null;
                            }
                        }
                    }
                },
                scales: {
                    y: { 
                        type: 'linear', display: true, position: 'left',
                        grid: { color: 'rgba(255,255,255,0.05)' }, 
                        ticks: { color: '#888' }, beginAtZero: true 
                    },
                    y1: {
                        type: 'linear', display: true, position: 'right',
                        grid: { display: false },
                        ticks: { color: '#ef4444' }, min: 0, max: 100
                    },
                    x: { grid: { display: false }, ticks: { color: '#888', maxRotation: 0, maxTicksLimit: 6 } }
                }
            }
        });

        // ── Chart Mode Toggle (Line / Bar / 3D) ──
        const MODES = ['line', 'bar', '3d'];
        const MODE_LABELS = { line: 'Bar View', bar: '3D View', '3d': 'Line View' };
        const modeBtn = document.getElementById('chartModeToggle');
        const chart3DEl = document.getElementById('blinkChart3D');
        if (modeBtn) {
            modeBtn.addEventListener('click', () => {
                const curIdx = MODES.indexOf(blinkChartMode);
                blinkChartMode = MODES[(curIdx + 1) % MODES.length];
                modeBtn.textContent = MODE_LABELS[blinkChartMode];
                if (blinkChartMode === '3d') {
                    // ── 3D Mode: Plotly scatter3d ──
                    elBlink.style.display = 'none';
                    if (chart3DEl) chart3DEl.style.display = 'block';
                    const labels3d = blinkChart.data.labels || [];
                    const bData = blinkChart.data.datasets[0]?.data || [];
                    const fData = blinkChart.data.datasets.length > 1 ? blinkChart.data.datasets[1]?.data || [] : [];
                    const xV = labels3d.map((_, i) => i);
                    const trace = {
                        x: xV, y: bData, z: fData,
                        mode: 'markers+lines', type: 'scatter3d',
                        marker: { size: 4, color: bData, colorscale: [[0,'#ef4444'],[0.5,'#e8c84a'],[1,'#22c55e']], opacity: 0.85 },
                        line: { color: '#e8c84a', width: 2 },
                        name: 'Blink vs Fatigue',
                        hovertemplate: 'Time: %{x}<br>Blink Rate: %{y}/min<br>Fatigue: %{z}%<extra></extra>'
                    };
                    const layout3d = {
                        margin: { l: 0, r: 0, t: 0, b: 0 },
                        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
                        scene: {
                            xaxis: { title: 'Time', showgrid: true, gridcolor: 'rgba(0,0,0,0.06)' },
                            yaxis: { title: 'Blinks/min', showgrid: true, gridcolor: 'rgba(0,0,0,0.06)' },
                            zaxis: { title: 'Fatigue %', showgrid: true, gridcolor: 'rgba(0,0,0,0.06)', range: [0, 100] },
                            bgcolor: 'rgba(0,0,0,0)',
                            camera: { eye: { x: 1.6, y: 1.6, z: 0.8 } }
                        },
                        font: { family: 'Inter', size: 10, color: '#888' },
                    };
                    if (chart3DEl) Plotly.newPlot(chart3DEl, [trace], layout3d, { responsive: true, displayModeBar: false });
                } else {
                    // ── 2D Mode: Chart.js line or bar ──
                    elBlink.style.display = 'block';
                    if (chart3DEl) { chart3DEl.style.display = 'none'; if (typeof Plotly !== 'undefined') Plotly.purge(chart3DEl); }
                    const savedLabels = [...blinkChart.data.labels];
                    const savedBlink = [...blinkChart.data.datasets[0].data];
                    const savedFatigue = blinkChart.data.datasets.length > 1 ? [...blinkChart.data.datasets[1].data] : [];
                    blinkChart.destroy();
                    const isBar = blinkChartMode === 'bar';
                    blinkChart = new Chart(ctx, {
                        type: isBar ? 'bar' : 'line',
                        data: {
                            labels: savedLabels,
                            datasets: [
                                { label: 'Blink Rate', data: savedBlink, borderColor: '#e8c84a', backgroundColor: isBar ? 'rgba(232,200,74,0.7)' : 'rgba(232,200,74,0.1)', borderWidth: isBar ? 0 : 2, tension: 0.4, yAxisID: 'y', borderRadius: isBar ? 4 : 0 },
                                { label: 'Fatigue %', data: savedFatigue, borderColor: '#ef4444', backgroundColor: isBar ? 'rgba(239,68,68,0.6)' : 'rgba(239,68,68,0.1)', borderWidth: isBar ? 0 : 2, borderDash: isBar ? [] : [5,5], tension: 0.4, yAxisID: 'y1', borderRadius: isBar ? 4 : 0 }
                            ]
                        },
                        options: {
                            responsive: true, maintainAspectRatio: false,
                            interaction: { mode: 'index', intersect: false },
                            plugins: { legend: { display: false }, tooltip: {
                                backgroundColor: 'rgba(15,15,15,0.9)', titleColor: '#e8c84a', bodyColor: '#fff', padding: 12,
                                callbacks: { afterBody: function(c) {
                                    const b = c[0]?.raw||0, f = c[1]?.raw||0;
                                    if (f > 65 && b < 12) return '\n⚠️ Low blinks + high fatigue = staring too long!';
                                    if (b >= 15 && f < 30) return '\n✅ Healthy blink rate, low fatigue.';
                                    if (b < 10) return '\n👁️ Very low blink rate — dry eye risk.';
                                    if (f > 50) return '\n🧠 Fatigue building — consider a break.';
                                    return null;
                                }}
                            }},
                            scales: {
                                y: { type: 'linear', display: true, position: 'left', grid: { color: 'rgba(0,0,0,0.04)' }, beginAtZero: true },
                                y1: { type: 'linear', display: true, position: 'right', grid: { display: false }, ticks: { color: '#ef4444' }, min: 0, max: 100 },
                                x: { grid: { display: false }, ticks: { maxRotation: 0, maxTicksLimit: 6 } }
                            }
                        }
                    });
                }
            });
        }

        // ── Info Tooltip hover ──
        const infoBtn = document.getElementById('chartInfoBtn');
        const infoTip = document.getElementById('chartInfoTooltip');
        if (infoBtn && infoTip) {
            infoBtn.addEventListener('mouseenter', () => { infoTip.style.display = 'block'; infoBtn.style.opacity = '1'; });
            infoBtn.addEventListener('mouseleave', () => { infoTip.style.display = 'none'; infoBtn.style.opacity = '0.5'; });
        }
    }

    // 2. Fatigue Chart (Real-Time)
    const elFatigue = document.getElementById("fatigueChart");
    if (elFatigue) {
        const ctx = elFatigue.getContext("2d");
        fatigueChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: "Fatigue %",
                    data: [],
                    borderColor: '#ef4444',
                    backgroundColor: createGradient(ctx, 'rgba(239,68,68,0.3)', 'rgba(239,68,68,0)'),
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { max: 100, min: 0, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#888' } },
                    x: { grid: { display: false }, ticks: { display: false } }
                }
            }
        });
    }

    // 3. Distance Chart (Real-Time)
    const elDistance = document.getElementById("distanceChart");
    if (elDistance) {
        const ctx = elDistance.getContext("2d");
        distanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: "Distance (cm)",
                    data: [],
                    borderColor: '#00d2ff',
                    backgroundColor: createGradient(ctx, 'rgba(0,210,255,0.3)', 'rgba(0,210,255,0)'),
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { min: 20, max: 120, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#888' } },
                    x: { grid: { display: false }, ticks: { display: false } }
                }
            }
        });
    }

    // 4. Weekly Progress (Analytics)
    const elWeekly = document.getElementById("weeklyChart");
    if (elWeekly) {
        const ctx = elWeekly.getContext("2d");
        weeklyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Health Score',
                    data: [85, 82, 90, 78, 88, 92, 85],
                    borderColor: '#e8c84a',
                    backgroundColor: createGradient(ctx, 'rgba(232,200,74,0.2)', 'rgba(232,200,74,0)'),
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: '#e8c84a'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: { display: true, text: 'Weekly Health Index', color: '#fff', font: { size: 16 } }
                },
                scales: {
                    y: { max: 100, min: 0, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#888' } },
                    x: { grid: { display: false }, ticks: { color: '#888' } }
                }
            }
        });
    }
}

// ============================================================
// Toast Notifications
// ============================================================
let lastAdvice = "";

function showToast(message) {
    if (!message || message === "Your eyes are healthy." || message === lastAdvice) return;
    lastAdvice = message;

    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `⚠️ ${message}`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => toast.remove(), 500);
    }, 5000);
}

// ============================================================
// In-App Fatigue Modal Bypass
// ============================================================
let appAlertLastShown = 0;
let appAlertSnoozedUntil = 0;

function showFatigueModal(fatigue, blinkRate, distance) {
    const now = Date.now();
    // Cooldown check (5 minutes base, or custom snooze timer)
    if (now < appAlertSnoozedUntil) return;
    if (now - appAlertLastShown < 300000) return; // 5 min default

    // If modal already exists, remove it or don't create a new one
    if (document.getElementById('fatigue-modal')) return;

    appAlertLastShown = now;

    // Proactive AI Warning Injection
    if(typeof appendChat === 'function') {
        appendChat('bot', "⚠️ **Proactive Alert:** I noticed your fatigue index has surged. Please step away from the screen to rest your eyes.");
    }

    const modal = document.createElement('div');
    modal.id = 'fatigue-modal';
    modal.innerHTML = `
        <div style="
            position: fixed; bottom: 20px; right: 20px; width: 340px;
            background: rgba(40, 40, 45, 0.85); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.1); border-left: 4px solid #ef4444; border-radius: 12px;
            color: #fff; font-family: 'Inter', sans-serif; position: relative; z-index: 99999;
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
            transform: translateY(20px); opacity: 0; transition: all 0.3s ease;
        ">
            <div style="padding: 16px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <span style="font-size: 20px;">⚠️</span>
                    <h3 style="margin: 0; font-size: 16px; font-weight: 600;">High Fatigue Detected</h3>
                </div>
                <p style="margin: 0 0 12px 0; font-size: 13px; color: #aaa;">Your eyes are showing signs of heavy strain. Please take a moment to rest.</p>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 16px;">
                    <div style="background: rgba(255,255,255,0.05); padding: 8px; border-radius: 6px;">
                        <div style="font-size: 11px; color: #888;">Fatigue</div>
                        <div style="font-size: 14px; font-weight: 600; color: #ef4444;">${Math.round(fatigue)}%</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.05); padding: 8px; border-radius: 6px;">
                        <div style="font-size: 11px; color: #888;">Distance</div>
                        <div style="font-size: 14px; font-weight: 600; color: #00d2ff;">${Math.round(distance)} cm</div>
                    </div>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button id="modal-btn-break" style="
                        flex: 1; padding: 8px; border: none; border-radius: 6px; cursor: pointer;
                        background: #ef4444; color: white; font-weight: 500; font-family: 'Inter', sans-serif;
                    ">Take a Break</button>
                    <button id="modal-btn-snooze" style="
                        flex: 1; padding: 8px; border: 1px solid rgba(255,255,255,0.2); border-radius: 6px; cursor: pointer;
                        background: transparent; color: #ccc; font-weight: 500; font-family: 'Inter', sans-serif;
                    ">Snooze 5m</button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    // Entrance Animation
    setTimeout(() => {
        modal.firstElementChild.style.transform = 'translateY(0)';
        modal.firstElementChild.style.opacity = '1';
    }, 50);

    const closeModal = () => {
        modal.firstElementChild.style.transform = 'translateY(20px)';
        modal.firstElementChild.style.opacity = '0';
        setTimeout(() => modal.remove(), 300);
    };

    document.getElementById('modal-btn-break').addEventListener('click', () => {
        appAlertSnoozedUntil = Date.now() + (5 * 60000); 
        closeModal();
    });

    document.getElementById('modal-btn-snooze').addEventListener('click', () => {
        appAlertSnoozedUntil = Date.now() + (5 * 60000); 
        closeModal();
    });

    // Auto dismiss after 10s
    setTimeout(() => {
        if (document.getElementById('fatigue-modal')) closeModal();
    }, 10000);
}


// ============================================================
// Strain Ring
// ============================================================
function setStrainRing(percent) {
    const circle = document.getElementById('strain-circle');
    if (!circle) return;
    const circumference = 2 * Math.PI * 50; // r=50
    const filled = (Math.min(Math.max(percent, 0), 100) / 100) * circumference;
    circle.setAttribute('stroke-dasharray', `${filled.toFixed(1)} ${circumference.toFixed(1)}`);

    const el = document.getElementById('strainPercent');
    if (el) el.textContent = Math.round(percent) + '%';

    const riskLabel = document.getElementById('strainRiskLevel');
    const recLabel = document.getElementById('strainRecommendation');

    // Color & Glow: green < 33, yellow 33-66, red > 66
    if (percent < 33) {
        if (riskLabel) { riskLabel.textContent = "Safe"; riskLabel.style.color = "#888"; }
        if (recLabel) { recLabel.textContent = "Great job, keep it up!"; recLabel.style.color = "#888"; }
        circle.style.stroke = '#22c55e';
        circle.style.filter = 'drop-shadow(0 0 8px rgba(34, 197, 94, 0.4))';
    } else if (percent < 66) {
        if (riskLabel) { riskLabel.textContent = "Moderate"; riskLabel.style.color = "#e8c84a"; }
        if (recLabel) { recLabel.textContent = "Consider a 1-minute stretch."; recLabel.style.color = "#e8c84a"; }
        circle.style.stroke = '#e8c84a';
        circle.style.filter = 'drop-shadow(0 0 12px rgba(232, 200, 74, 0.5))';
    } else {
        if (riskLabel) { riskLabel.textContent = "High Risk"; riskLabel.style.color = "#ef4444"; }
        if (recLabel) { recLabel.textContent = "Time for a 10-minute break."; recLabel.style.color = "#ef4444"; }
        circle.style.stroke = '#ef4444';
        circle.style.filter = 'drop-shadow(0 0 15px rgba(239, 68, 68, 0.6))';
    }
}

// ============================================================
// Progress Bars for metric cards
// ============================================================
function setBar(id, percent) {
    const bar = document.getElementById(id);
    if (bar) bar.style.width = Math.min(Math.max(percent, 0), 100) + '%';
}

// ============================================================
// Live Data Loading
// ============================================================
async function loadData() {
    try {
        const now = Date.now();
        const res = await fetch(`/api/data?t=${now}`);
        const data = await res.json();

        // The backend returns latest data first (descending). Reverse it so data[data.length-1] is the newest.
        if (data) {
            data.reverse();
        }

        const sumRes = await fetch(`/api/summary?t=${now}`);
        const summary = await sumRes.json();

        // Update profile stats (Newest is last)
        const blinkRate = data && data.length > 0 ? (data[data.length - 1].blink_rate || 0) : 0;
        const distance  = data && data.length > 0 ? (data[data.length - 1].distance || 0) : 0;
        const fatigue   = data && data.length > 0 ? (data[data.length - 1].fatigue || 0) : 0;
        const activity  = data && data.length > 0 ? (data[data.length - 1].activity || '--') : '--';

        // Profile stats row
        el('blinkText',   Math.round(blinkRate));
        el('screenText',  summary.screen_time_minutes || 0);
        el('fatigue-stat', Math.round(fatigue) + '%');

        // Metric cards (Dashboard)
        el('blink-card-val',  Math.round(blinkRate) + ' <small>/ min</small>');
        el('screen-card-val', (summary.screen_time_minutes || 0) + ' <small>min</small>');
        el('dist-card-val',   Math.round(distance) + ' <small>cm</small>');

        // Real-Time page specific elements
        el('activity', activity);
        el('distance', Math.round(distance) + ' cm');
        el('blink',    Math.round(blinkRate) + ' / min');

        // Progress bars
        setBar('blink-bar',  (blinkRate / 25) * 100);
        setBar('screen-bar', ((summary.screen_time_minutes || 0) / 480) * 100);
        setBar('dist-bar',   (distance / 120) * 100);

        // Strain ring
        setStrainRing(fatigue);

        // Health badge
        setHealthBadge(fatigue);

        // Predictive Fatigue Extrapolation
        const predLabel = document.getElementById('predictive-fatigue');
        if (predLabel) predLabel.innerText = calculatePredictiveFatigue(data, fatigueThresholdTarget);

        // System status
        const statusEl = document.getElementById('system-status');
        const dotEl = document.querySelector('.status-dot');
        const bgStatus = document.getElementById('bg-status');

        let isTrackingActive = false;
        if (data && data.length > 0) {
            const timeSinceLastRecord = Date.now() - data[data.length - 1].timestamp;
            if (timeSinceLastRecord < 15000) {
                isTrackingActive = true;
            }
        }

        if (isTrackingActive) {
            if (statusEl) statusEl.textContent = 'Monitoring';
            if (bgStatus && bgStatus.textContent.includes('offline')) bgStatus.innerHTML = '<span style="color:#22c55e">✨ Monitoring Active</span>';
            if (dotEl) { dotEl.classList.remove('offline'); dotEl.classList.add('online'); }
            
            // Apply Dynamic Body Subconscious Glow
            applyAmbientGlow(fatigue);
        } else {
            if (statusEl) statusEl.textContent = 'Offline';
            if (bgStatus && !bgStatus.innerHTML.includes('Offline')) bgStatus.textContent = 'Monitoring Offline';
            if (dotEl) { dotEl.classList.remove('online'); dotEl.classList.add('offline'); }
            document.body.style.boxShadow = 'none';
        }

        // --- Update Charts ---
        if (data && data.length > 0) {
            const recent = data.slice(-30);
            const labels = recent.map(r => {
                const d = new Date(r.timestamp);
                return `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}:${d.getSeconds().toString().padStart(2,'0')}`;
            });

            // Update Dual-Line Chart (Dashboard)
            if (blinkChart && blinkChart.data.datasets.length === 2) {
                blinkChart.data.labels = labels;
                blinkChart.data.datasets[0].data = recent.map(r => r.blink_rate || 0);
                blinkChart.data.datasets[1].data = recent.map(r => r.fatigue || 0);
                blinkChart.update('none');
            } else if (blinkChart) { // fallback for Real-Time page if it still uses the bar chart
                blinkChart.data.labels = labels;
                blinkChart.data.datasets[0].data = recent.map(r => r.blink_rate || 0);
                blinkChart.update('none');
            }

            // Update Fatigue Chart (Realtime Page)
            if (fatigueChart) {
                fatigueChart.data.labels = labels;
                fatigueChart.data.datasets[0].data = recent.map(r => r.fatigue || 0);
                fatigueChart.update('none');
            }

            // Update Distance Chart (Realtime Page)
            if (distanceChart) {
                distanceChart.data.labels = labels;
                distanceChart.data.datasets[0].data = recent.map(r => r.distance || 50);
                distanceChart.update('none');
            }

            // --- INSIGHT & ADVISORY UPDATES ---
            
            // 1. Focus Score (0-100)
            // Healthy blinks (15) keep score near 100. High fatigue drops it.
            let focusScore = 100 - (fatigue * 0.7);
            if (blinkRate > 10 && blinkRate < 25) focusScore += 10;
            else if (blinkRate < 10) focusScore -= 10;
            if (distance < 40) focusScore -= 15;
            focusScore = Math.min(Math.max(focusScore, 0), 100).toFixed(0);
            
            el('focus-score-val', focusScore + ' <small>/ 100</small>');
            setBar('focus-bar', focusScore);

            // 2. Active Advisory Panel
            const advText = document.getElementById('advisory-text');
            const advBlink = document.getElementById('advisory-blink-hint');
            const advDist = document.getElementById('advisory-dist-hint');
            
            if (advText) {
                if (distance < 40) {
                    advText.textContent = "You are sitting too close to the screen. Lean back instantly to avoid myopic strain.";
                    advText.style.color = "#ef4444";
                } else if (blinkRate < 10) {
                    advText.textContent = "Your blink rate is critically low. Force a few deep blinks to replenish tear film.";
                    advText.style.color = "#e8c84a";
                } else if (fatigue > 60) {
                    advText.textContent = "Fatigue is compounding. Follow the 20-20-20 rule right now.";
                    advText.style.color = "#e8c84a";
                } else {
                    advText.textContent = "Metrics look healthy. Maintain your current posture and rhythm.";
                    advText.style.color = "var(--db-dark)";
                }
            }
            if (advBlink) advBlink.textContent = `Blinks: ${Math.round(blinkRate)}/15 min`;
            if (advDist) advDist.textContent = `Dist: ${Math.round(distance)}/50+ cm`;

            // 3. Goal Progress & Heatmap Simulation Update
            const goalPercent = Math.min((summary.screen_time_minutes || 0) / 240 * 100, 100);
            el('screen-goal-text', Math.round(goalPercent) + '%');
            const goalBar = document.getElementById('screen-goal-bar');
            if (goalBar) goalBar.style.width = goalPercent + '%';

            // 4. Strict Mode enforcement!
            const strictToggle = document.getElementById('strictModeToggle');
            const strictOverlay = document.getElementById('strictOverlay');
            if (strictToggle && strictToggle.checked && fatigue > 80) {
                // If the user hasn't explicitly postponed the strict mode recently
                if (!window.isStrictModeAlerted && strictOverlay) {
                    strictOverlay.style.display = 'flex';
                    window.isStrictModeAlerted = true; 
                    setTimeout(() => { window.isStrictModeAlerted = false; }, 300000); // Allow next alert in 5 mins
                }
            }
        }

        if (data && data.length > 0 && data[data.length - 1].advice) {
            showToast(data[data.length - 1].advice);
        }

        // In-App Web Modal for High Fatigue Bypass
        if (fatigue >= fatigueThresholdTarget) {
            showFatigueModal(fatigue, blinkRate, distance);
        }

    } catch (e) {
        console.error("Load data error:", e);
    }
}

function el(id, html) {
    const e = document.getElementById(id);
    if (e) e.innerHTML = html;
}

function setHealthBadge(fatigue) {
    const badge = document.getElementById('health-badge');
    if (!badge) return;
    if (fatigue < 30) { badge.textContent = '✓ Good'; badge.style.background = '#22c55e'; badge.style.color = 'white'; }
    else if (fatigue < 60) { badge.textContent = '⚠ Moderate'; badge.style.background = '#e8c84a'; badge.style.color = '#1a1a1a'; }
    else { badge.textContent = '✕ High Risk'; badge.style.background = '#ef4444'; badge.style.color = 'white'; }
}

// ============================================================
// User Profile Name
// ============================================================
async function loadProfile() {
    try {
        const res = await fetch('/api/profile');
        if (!res.ok) return;
        const data = await res.json();
        const full_name = data.full_name || data.username || 'User';
        const first = full_name.split(' ')[0];
        
        // Update name in various places
        ['sidebar-user-name', 'header-user-name', 'profile-display-name'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = id === 'profile-display-name' ? full_name : first;
        });

        // Update avatar in sidebar and profile cards
        const sidebarAvatar = document.getElementById('sidebar-avatar-container');
        const dashboardAvatar = document.getElementById('dashboard-avatar-container');

        if (data.avatar_url) {
            if (sidebarAvatar) {
                sidebarAvatar.innerHTML = `<img src="${data.avatar_url}" alt="Profile">`;
                sidebarAvatar.style.padding = '0';
            }
            if (dashboardAvatar) {
                dashboardAvatar.innerHTML = `<div class="avatar-wow"><img src="${data.avatar_url}" alt="Avatar"></div>`;
            }
        } else {
            // Default Astronaut Icon fallback
            if (dashboardAvatar) {
                dashboardAvatar.innerHTML = `<div class="avatar-wow"><i class="fas fa-user-astronaut"></i></div>`;
            }
        }

        // --- Multi-Account Switcher: Sync to LocalStorage ---
        syncAccount({
            username: data.username,
            avatar_url: data.avatar_url,
            full_name: data.full_name
        });

    } catch (e) { /* silent fail */ }
}

function syncAccount(user) {
    if (!user.username) return;
    try {
        let accounts = JSON.parse(localStorage.getItem('neuralNexusAccounts') || '[]');
        const index = accounts.findIndex(a => a.username === user.username);
        if (index > -1) {
            accounts[index] = { ...accounts[index], ...user };
        } else {
            accounts.push(user);
        }
        // Limit to 5 recent accounts
        if (accounts.length > 5) accounts.shift();
        localStorage.setItem('neuralNexusAccounts', JSON.stringify(accounts));
    } catch(e) { console.error("Sync account error:", e); }
}

// ============================================================
// AI Chat Assistant
// ============================================================
async function loadChatHistory() {
    try {
        const res = await fetch("/api/chat/history");
        if (!res.ok) return;
        const history = await res.json();
        const body = document.getElementById("chatBody");
        if (!body || !history.length) return;
        body.innerHTML = '';
        history.forEach(msg => appendChat(msg.role || msg.sender, msg.text));
    } catch (e) {
        console.error("Chat history error:", e);
    }
}

function appendChat(role, text) {
    const body = document.getElementById('chatBody');
    if (!body) return;
    const div = document.createElement('div');
    // Support both old and new design system classes
    const isNewDesign = body.classList.contains('db-chat-messages');
    if (isNewDesign) {
        div.className = `db-chat-msg ${role === 'user' ? 'db-chat-msg--user' : 'db-chat-msg--bot'}`;
    } else {
        div.className = `chat-msg ${role === 'user' ? 'user' : 'bot'}`;
    }
    // Render basic markdown: bold, line breaks
    div.innerHTML = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
    body.appendChild(div);
    body.scrollTop = body.scrollHeight;
}

async function sendChat() {
    const input = document.getElementById('chatInput');
    if (!input) return;
    const msg = input.value.trim();
    if (!msg) return;

    input.value = '';
    input.disabled = true;
    appendChat('user', msg);

    // Show loading
    const chatBody = document.getElementById('chatBody');
    const loadDiv = document.createElement('div');
    const isNewDesign = chatBody && chatBody.classList.contains('db-chat-messages');
    loadDiv.className = isNewDesign ? 'db-chat-msg db-chat-msg--loading' : 'chat-msg loading';
    loadDiv.id = 'chat-loading';
    loadDiv.innerHTML = '<span style="opacity:0.5">Thinking...</span>';
    if (chatBody) chatBody.appendChild(loadDiv);
    chatBody.scrollTop = chatBody.scrollHeight;

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg })
        });

        document.getElementById('chat-loading')?.remove();

        if (!res.ok) {
            let errText = 'Server error (' + res.status + '). Please try again.';
            try { const e = await res.json(); if (e.error) errText = e.error; } catch(_) {}
            appendChat('bot', errText);
            return;
        }

        const data = await res.json();
        appendChat('bot', data.reply || 'No response received.');
    } catch (e) {
        document.getElementById('chat-loading')?.remove();
        appendChat('bot', '⚠️ Connection error. Is the server running?');
        console.error("Chat error:", e);
    } finally {
        input.disabled = false;
        input.focus();
    }
}

async function clearChat() {
    try {
        await fetch('/api/chat/clear', { method: 'POST' });
        const body = document.getElementById('chatBody');
        if (body) {
            body.innerHTML = '<div class="chat-msg bot">Chat cleared! Ask me about your fatigue, posture, or eye health stats.</div>';
        }
    } catch(e) {
        console.error('Clear chat error:', e);
    }
}

// ============================================================
// Historical Data (Heatmap & Weekly Chart)
// ============================================================
async function initHistoricalData() {
    const container = document.getElementById('heatmap-container');

    try {
        const res = await fetch('/api/history');
        const history = await res.json();

        // Populate Heatmap
        if (container) {
            container.innerHTML = '';
            history.forEach(day => {
                const cell = document.createElement('div');
                cell.className = `heatmap-cell level-${day.level || 1}`;
                cell.title = `${day.date}: Score ${day.score}`;
                container.appendChild(cell);
            });
        }

        // Populate Weekly Progress Chart (last 7 days of history)
        if (typeof weeklyChart !== 'undefined' && weeklyChart !== null) {
            const last7Days = history.slice(-7);
            const labels = last7Days.map(d => {
                const dateObj = new Date(d.date);
                // In JS Date, we must ensure the time parsing is correct or just map 'YYYY-MM-DD' properly
                const parts = d.date.split('-');
                const localDate = new Date(parts[0], parts[1] - 1, parts[2]);
                return localDate.toLocaleDateString('en-US', { weekday: 'short' });
            });
            const data = last7Days.map(d => d.score);
            
            weeklyChart.data.labels = labels;
            weeklyChart.data.datasets[0].data = data;
            weeklyChart.update('none');
        }

    } catch (e) { console.error("Historical data error:", e); }
}

// ============================================================
// Map (Analytics)
// ============================================================
function initMap() {
    const mapEl = document.getElementById('map-container');
    if (!mapEl || typeof L === 'undefined') return;

    map = L.map('map-container').setView([20, 77], 5); // Default India view

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    const locateBtn = document.getElementById('locate-btn');
    if (locateBtn) {
        locateBtn.addEventListener('click', () => {
            if (!navigator.geolocation) {
                alert("Geolocation is not supported by your browser");
                return;
            }

            document.getElementById('map-status').textContent = "Locating...";
            navigator.geolocation.getCurrentPosition((pos) => {
                const { latitude, longitude } = pos.coords;
                map.setView([latitude, longitude], 13);
                L.marker([latitude, longitude]).addTo(map)
                    .bindPopup("You are here")
                    .openPopup();
                
                document.getElementById('map-status').textContent = "Found you! Here are some specialists nearby (simulated).";
                
                // Add some fake clinics nearby
                const offset = 0.01;
                L.marker([latitude + offset, longitude + offset]).addTo(map).bindPopup("Nexus Vision Clinic");
                L.marker([latitude - offset, longitude + offset / 2]).addTo(map).bindPopup("EyeCare Specialists");
            }, (err) => {
                document.getElementById('map-status').textContent = "Error: " + err.message;
            });
        });
    }
}

// ============================================================
// Init on DOM Ready
// ============================================================
// Init on DOM Ready
// ============================================================
let pomodoroInterval;
let pomodoroRemaining = 25 * 60;

function setupDashboardEnhancements() {
    // 1. Pomodoro Timer Setup
    const pomoBtn = document.getElementById('pomodoroBtn');
    if (pomoBtn) {
        pomoBtn.addEventListener('click', () => {
            if (pomodoroInterval) {
                clearInterval(pomodoroInterval);
                pomodoroInterval = null;
                pomoBtn.innerHTML = "🍅 Focus (25m)";
                pomoBtn.style.background = "var(--db-dark)";
                pomodoroRemaining = 25 * 60;
            } else {
                pomoBtn.style.background = "#ef4444";
                pomodoroInterval = setInterval(() => {
                    pomodoroRemaining--;
                    if (pomodoroRemaining <= 0) {
                        clearInterval(pomodoroInterval);
                        pomodoroInterval = null;
                        pomoBtn.innerHTML = "🎉 Focus Done! Break time.";
                        showToast("Pomodoro complete. Take a 5-minute break!");
                    } else {
                        const m = Math.floor(pomodoroRemaining / 60).toString().padStart(2, '0');
                        const s = (pomodoroRemaining % 60).toString().padStart(2, '0');
                        pomoBtn.innerHTML = `🍅 ${m}:${s}`;
                    }
                }, 1000);
            }
        });
    }

    // 2. Micro-Break Trigger
    const breakBtn = document.getElementById('breakBtn');
    if (breakBtn) {
        breakBtn.addEventListener('click', () => {
            const overlay = document.getElementById('strictOverlay');
            if (overlay) overlay.style.display = 'flex';
        });
    }

    // 3. Strict Mode Postpone Button
    const postpone = document.getElementById('postponeStrictBtn');
    if (postpone) {
        postpone.addEventListener('click', () => {
            document.getElementById('strictOverlay').style.display = 'none';
            window.isStrictModeAlerted = true;
            setTimeout(() => { window.isStrictModeAlerted = false; }, 300000); // 5 min snooze
        });
    }

    // 4. Generate Visual Density Heatmap (Simulation from LocalStorage or Random)
    const heatmapEl = document.getElementById('dashboard-heatmap');
    if (heatmapEl) {
        let html = '';
        for (let i = 0; i < 36; i++) {
            // Simulated intensity levels based on time of day
            const isMorning = i < 12;
            const isAfternoon = i >= 12 && i < 24;
            const rng = Math.random();
            let color = '#e2e8f0'; // default empty
            if (isAfternoon && rng > 0.3) color = '#fef08a'; // strain building
            if (isAfternoon && rng > 0.8) color = '#fee2e2'; // high strain
            if (isMorning && rng > 0.5) color = '#22c55e'; // healthy focus
            
            html += `<div style="background:${color}; height:24px; border-radius:3px; opacity:0; animation:db-fade-in 0.4s ease forwards; animation-delay:${i*0.02}s;"></div>`;
        }
        heatmapEl.innerHTML = html;
        heatmapEl.style.gridTemplateColumns = "repeat(12, 1fr)";
    }

    // 5. Proactive AI Push Loop
    setInterval(() => {
        const body = document.getElementById('chatBody');
        const statusEl = document.getElementById('system-status');
        if (!body || !statusEl || statusEl.textContent !== 'Monitoring') return;

        const pFatigue = document.getElementById('fatigue-stat');
        if (!pFatigue) return;
        const currentFatigue = parseInt(pFatigue.textContent);

        // Every ~1 minute, 10% chance to push an alert if fatigue is high but not critical
        if (currentFatigue > 40 && Math.random() < 0.15) {
            appendChat('bot', `I noticed your fatigue index has reached ${currentFatigue}%. Prolonged focus limits tear production. Remember the 20-20-20 rule!`);
        } else if (Math.random() < 0.05) {
            appendChat('bot', "Did you know? An ideal blink rate is around 15 times per minute. You're currently performing well.");
        }
    }, 60000);
}

document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    initHistoricalData();
    initMap();
    setupDashboardEnhancements();
    
    // Load Personalization Options
    const sensSelect = document.getElementById('fatigue-sensitivity');
    if(sensSelect) {
        const saved = localStorage.getItem('nexus_sensitivity') || 'normal';
        sensSelect.value = saved;
        fatigueThresholdTarget = sensitivityDict[saved];

        sensSelect.addEventListener('change', (e) => {
            const val = e.target.value;
            localStorage.setItem('nexus_sensitivity', val);
            fatigueThresholdTarget = sensitivityDict[val];
        });
    }

    loadProfile();
    loadChatHistory();
    loadData();

    setInterval(loadData, 3000);

    // Chat send button
    const sendBtn = document.getElementById('sendChatBtn');
    const chatIn  = document.getElementById('chatInput');

    if (sendBtn) {
        sendBtn.addEventListener('click', sendChat);
    }
    if (chatIn) {
        chatIn.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChat();
            }
        });
    }

    // Clear Chat button
    const clearBtn = document.getElementById('clearChatBtn');
    if (clearBtn) clearBtn.addEventListener('click', clearChat);

    // Global Keydown for Snooze (Ctrl + Shift + S)
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 's') {
            e.preventDefault();
            appAlertSnoozedUntil = Date.now() + (10 * 60000); // 10 min snooze
            showToast("System Snoozed: All fatigue alerts suppressed for 10 minutes.");
            if (document.getElementById('fatigue-modal')) {
                document.getElementById('fatigue-modal').remove();
            }
        }
    });
});
