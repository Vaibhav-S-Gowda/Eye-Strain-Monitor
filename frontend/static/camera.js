const videoElement = document.getElementsByClassName('input_video')[0];
const canvasElement = document.getElementsByClassName('output_canvas')[0];
const canvasCtx = canvasElement.getContext('2d');

// --- Background Heartbeat Worker ---
const workerCode = `
    let interval = null;
    self.onmessage = (e) => {
        if (e.data === 'start') {
            if (!interval) interval = setInterval(() => self.postMessage('tick'), 200);
        } else if (e.data === 'stop') {
            if (interval) { clearInterval(interval); interval = null; }
        }
    };
`;
const blob = new Blob([workerCode], {type: 'application/javascript'});
const heartbeatWorker = new Worker(URL.createObjectURL(blob));
heartbeatWorker.onmessage = () => {
    if (isRunning) {
        recordTelemetry();
        fetchActivity();
        
        // CRITICAL: If tab is hidden, manually trigger a frame capture
        // since requestAnimationFrame will be throttled.
        if (document.visibilityState === 'hidden' && camera) {
            faceMesh.send({image: videoElement}).catch(e => console.warn("Background frame fail:", e));
        }
    }
};

let isRunning = false;
let showMask = true; // New state for mask visibility
let blinkCount = 0;
let blinkEvents = []; // Array of timestamps for moving window blink rate
let lastBlinkTime = 0;
let startTime = Date.now();
let muted = false;

// Config — tuned for browser webcam accuracy
const BLINK_THRESHOLD = 0.24;      // EAR below this = eyes closing (raised for sensitivity)
const BLINK_COOLDOWN_MS = 300;      // Minimum ms between blink counts (debounce)
const MIN_DISTANCE_CM = 50;
const HEAD_TILT_THRESHOLD = 15;
let lastBlinkRegistered = 0;         // Timestamp of last counted blink

const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

function playBeep(frequency, duration) {
    if (muted) return;
    const oscillator = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();
    
    oscillator.type = 'sine';
    oscillator.frequency.value = frequency;
    oscillator.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    
    oscillator.start();
    setTimeout(() => {
        oscillator.stop();
    }, duration);
}

// MediaPipe Helper Functions
function getEar(landmarks, eyeIndices) {
    const points = eyeIndices.map(i => landmarks[i]);
    const v1 = Math.hypot(points[1].x - points[5].x, points[1].y - points[5].y);
    const v2 = Math.hypot(points[2].x - points[4].x, points[2].y - points[4].y);
    const h = Math.hypot(points[0].x - points[3].x, points[0].y - points[3].y);
    return (v1 + v2) / (2.0 * h);
}

function calculateDistance(landmarks, w) {
    const left = landmarks[234];
    const right = landmarks[454];
    const faceWidth = Math.abs(left.x - right.x) * w;
    if (faceWidth === 0) return 50;
    return Math.round((16 * 600) / faceWidth);
}

function headTiltAngle(landmarks, w, h) {
    const left = landmarks[234];
    const right = landmarks[454];
    const angle = Math.atan2((right.y - left.y) * h, (right.x - left.x) * w) * (180 / Math.PI);
    return Math.abs(angle);
}

let consecutiveFramesBelow = 0;

function onResults(results) {
    if (!isRunning) return;

    // Draw video to canvas
    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    // Flip horizontally for mirror effect
    canvasCtx.translate(canvasElement.width, 0);
    canvasCtx.scale(-1, 1);
    canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);
    
    let distanceCm = 0;
    let tiltAngle = 0;
    let ear = 0;

    if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
        const landmarks = results.multiFaceLandmarks[0];
        
        // Draw Mesh (Only if showMask is true)
        if (showMask) {
            drawConnectors(canvasCtx, landmarks, FACEMESH_TESSELATION, {color: '#C0C0C070', lineWidth: 1});
        }
        
        const w = canvasElement.width;
        const h = canvasElement.height;
        
        const LEFT_EYE = [362, 385, 387, 263, 373, 380];
        const RIGHT_EYE = [33, 160, 158, 133, 153, 144];
        
        const lEar = getEar(landmarks, LEFT_EYE);
        const rEar = getEar(landmarks, RIGHT_EYE);
        ear = (lEar + rEar) / 2.0;

        if (ear < BLINK_THRESHOLD) {
            consecutiveFramesBelow++;
        } else {
            // A blink = eyes were closed for 2+ frames, then opened
            // Plus a cooldown to prevent double-counting one blink
            if (consecutiveFramesBelow >= 2 && (Date.now() - lastBlinkRegistered) > BLINK_COOLDOWN_MS) {
                blinkCount++;
                blinkEvents.push(Date.now());
                lastBlinkRegistered = Date.now();
                const elMblinks = document.getElementById('m-blinks');
                if (elMblinks) elMblinks.innerText = blinkCount;
            }
            consecutiveFramesBelow = 0;
        }

        distanceCm = calculateDistance(landmarks, w);
        tiltAngle = headTiltAngle(landmarks, w, h);
    }
    
    canvasCtx.restore();

    // --- Improved Fatigue Model (Responsive) ---
    const now = Date.now();
    const elapsedSecs = (now - startTime) / 1000;
    
    // 1. Moving Window Blink Rate (Last 60s)
    blinkEvents = blinkEvents.filter(t => now - t < 60000);
    
    // Calculate current blink rate
    // During 15s warm-up, assume ideal rate (15/min) to prevent initial spike
    let currentBlinkRate = blinkEvents.length;
    if (elapsedSecs < 15) {
        currentBlinkRate = Math.max(currentBlinkRate, 15 * (elapsedSecs / 60));
    }
    
    // Effective blink rate (extrapolated if less than 60s of monitoring)
    const activeWindowSecs = Math.min(elapsedSecs, 60);
    const extrapolatedRate = activeWindowSecs > 5 ? (blinkEvents.length * (60 / activeWindowSecs)) : 15;
    
    // 2. Multi-Metric Scoring (Scale 0-100)
    // Blink Score: 18+ bpm = 0 fatigue, 0 bpm = 100 fatigue
    const blinkScore = Math.min(100, Math.max(0, (18 - extrapolatedRate) * 5.5));
    
    // Distance Score: 50cm+ = 0 fatigue, 30cm = 100 fatigue
    const distScore = distanceCm > 0 ? Math.min(100, Math.max(0, (50 - distanceCm) * 5)) : 0;
    
    // Tilt Score: 15° = 0 fatigue, 45° = 100 fatigue
    const tiltScore = Math.min(100, Math.max(0, (tiltAngle - HEAD_TILT_THRESHOLD) * 3.3));

    // 3. Weighted Result (Balanced for 0-100% range)
    let fatigueScore = Math.round(blinkScore * 0.45 + distScore * 0.35 + tiltScore * 0.2);
    
    // Cap at 100
    fatigueScore = Math.min(100, fatigueScore);

    // Distance Check & Head Tilt Alerting
    if (!muted && distanceCm > 0 && distanceCm < MIN_DISTANCE_CM && (now - lastBlinkTime > 1500)) {
        playBeep(900, 150);
        lastBlinkTime = now;
    }
    if (!muted && tiltAngle > HEAD_TILT_THRESHOLD && (now - lastBlinkTime > 1500)) {
        playBeep(1000, 150);
        lastBlinkTime = now;
    }

    // Update overlay UI Labels (CRITICAL: Fixes the 0-value display issue)
    // Update overlay UI Labels
    const elRate = document.getElementById('m-rate'); if (elRate) elRate.innerText = extrapolatedRate.toFixed(1);
    const elDist = document.getElementById('m-dist'); if (elDist) elDist.innerText = distanceCm;
    const elTilt = document.getElementById('m-tilt'); if (elTilt) elTilt.innerText = tiltAngle.toFixed(1);
    const elFatigue = document.getElementById('m-fatigue'); if (elFatigue) elFatigue.innerText = fatigueScore;
    
    // Store globally for the sync loop
    window.latestTelemetry = {
        blink_rate: parseFloat(extrapolatedRate.toFixed(2)),
        distance: distanceCm,
        tilt: parseFloat(tiltAngle.toFixed(2)),
        fatigue: fatigueScore,
        is_slouching: (distanceCm > 0 && distanceCm < 45)
    };

    const elAiF = document.getElementById('m-ai-fatigued');
    if (elAiF) {
        elAiF.style.display = (fatigueScore > 40) ? 'block' : 'none';
    }
    
    // Dashboard Specific sync (Instant feedback)
    const elDashBlink = document.getElementById('blink-card-val');
    if (elDashBlink) elDashBlink.innerHTML = Math.round(extrapolatedRate) + ' <small>/ min</small>';
    
    const elDashDist = document.getElementById('dist-card-val');
    if (elDashDist) elDashDist.innerHTML = Math.round(distanceCm) + ' <small>cm</small>';

    const elStatBlink = document.getElementById('blinkText');
    if (elStatBlink) elStatBlink.innerText = Math.round(extrapolatedRate);

    const elStatFatigue = document.getElementById('fatigue-stat');
    if (elStatFatigue) elStatFatigue.innerText = Math.round(fatigueScore) + '%';

    if (typeof setStrainRing === 'function') {
        setStrainRing(fatigueScore);
    }
}

// Data Sync & Activity Logic
let syncInterval = null;
let activityInterval = null;

async function recordTelemetry() {
    if (!isRunning || !window.latestTelemetry) return;
    try {
        const actEl = document.getElementById('m-act');
        const activityVal = actEl ? actEl.innerText : "Monitoring";
        
        const response = await fetch('/api/record', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ...window.latestTelemetry,
                activity: activityVal
            })
        });
    } catch (e) {
        console.error("Sync Error:", e);
    }
}

async function fetchActivity() {
    if (!isRunning) return;
    try {
        const res = await fetch('/api/activity');
        const data = await res.json();
        document.getElementById('m-act').innerText = data.activity || "Idle";
    } catch (e) {
        console.error("Activity Fetch Error:", e);
    }
}

const faceMesh = new FaceMesh({locateFile: (file) => {
    return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`;
}});
faceMesh.setOptions({
    maxNumFaces: 1,
    refineLandmarks: true,
    minDetectionConfidence: 0.5,
    minTrackingConfidence: 0.5
});
faceMesh.onResults(onResults);

let camera = null;

    document.getElementById('startBtn')?.addEventListener('click', startMonitor);
    document.getElementById('startBgBtn')?.addEventListener('click', () => {
        startMonitor();
        const statusEl = document.getElementById('bg-status');
        if (statusEl) statusEl.innerHTML = '<span style="color:#22c55e">✨ Monitoring Active</span>';
        
        const startBgBtn = document.getElementById('startBgBtn');
        if (startBgBtn) startBgBtn.style.display = 'none';
        
        const stopBgBtn = document.getElementById('stopBgBtn');
        if (stopBgBtn) stopBgBtn.style.display = 'inline-block';
    });

    async function startMonitor() {
        isRunning = true;
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        if (startBtn) startBtn.style.display = 'none';
        if (stopBtn) stopBtn.style.display = 'inline-block';
        
        // Reset performance tracking
        startTime = Date.now();
        blinkCount = 0;
        blinkEvents = [];
        const elBlinks = document.getElementById('m-blinks');
        if (elBlinks) elBlinks.innerText = '0';

        // Start background loops
        syncInterval = setInterval(recordTelemetry, 5000);
        activityInterval = setInterval(fetchActivity, 2500);
        heartbeatWorker.postMessage('start');
        
        const pipBtn = document.getElementById('pipBtn');
        if (pipBtn) pipBtn.style.display = 'inline-block';
        
        const maskBtn = document.getElementById('maskToggleBtn');
        if (maskBtn) maskBtn.style.display = 'inline-block';

        // Try to start camera setup
        if (!camera) {
            try {
                if (window.AudioContext || window.webkitAudioContext) audioCtx.resume();
                camera = new Camera(videoElement, {
                    onFrame: async () => {
                        if(isRunning) {
                             await faceMesh.send({image: videoElement});
                        }
                    },
                    width: 800,
                    height: 600
                });
                await camera.start();
            } catch (e) {
                console.error(e);
                alert("Camera initialization failed. Please allow permissions.");
            }
        } else {
            camera.start();
        }
    }

    document.getElementById('stopBtn')?.addEventListener('click', stopMonitor);
    document.getElementById('stopBgBtn')?.addEventListener('click', stopMonitor);

    function stopMonitor() {
        isRunning = false;
        if (camera) {
            camera.stop();
        }
        if (syncInterval) clearInterval(syncInterval);
        if (activityInterval) clearInterval(activityInterval);
        heartbeatWorker.postMessage('stop');
        
        const pipBtn = document.getElementById('pipBtn');
        if (pipBtn) pipBtn.style.display = 'none';

        const maskBtn = document.getElementById('maskToggleBtn');
        if (maskBtn) maskBtn.style.display = 'none';

        const statusEl = document.getElementById('bg-status');
        if (statusEl) statusEl.innerHTML = 'Monitoring Offline';

        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        if (startBtn) startBtn.style.display = 'inline-block';
        if (stopBtn) stopBtn.style.display = 'none';

        const startBgBtn = document.getElementById('startBgBtn');
        const stopBgBtn = document.getElementById('stopBgBtn');
        if (startBgBtn) startBgBtn.style.display = 'inline-block';
        if (stopBgBtn) stopBgBtn.style.display = 'none';
    }

    document.getElementById('resetBtn')?.addEventListener('click', () => {
        // Reset all internal counters
        blinkCount = 0;
        blinkEvents = [];
        consecutiveFramesBelow = 0;
        lastBlinkRegistered = 0;
        startTime = Date.now();
        window.latestTelemetry = null;

        // Reset all displayed metrics
        const resets = {
            'm-blinks': '0',
            'm-rate': '0.0',
            'm-dist': '0',
            'm-tilt': '0.0',
            'm-fatigue': '0',
        };
        for (const [id, val] of Object.entries(resets)) {
            const el = document.getElementById(id);
            if (el) el.innerText = val;
        }
        const aiEl = document.getElementById('m-ai-fatigued');
        if (aiEl) aiEl.style.display = 'none';
    });

    document.getElementById('muteBtn')?.addEventListener('click', (e) => {
        muted = !muted;
        const elMute = document.getElementById('m-mute');
        if (elMute) elMute.style.display = muted ? 'block' : 'none';
        if (e.target) e.target.innerText = muted ? 'Unmute Sound' : 'Mute Sound';
    });

    document.getElementById('maskToggleBtn')?.addEventListener('click', (e) => {
        showMask = !showMask;
        e.target.innerText = showMask ? 'Hide Mask' : 'Show Mask';
    });

// --- Background Mode (PiP) Implementation ---
const pipVideo = document.getElementById('pip_video');

let pipStream = null;

document.getElementById('pipBtn')?.addEventListener('click', async () => {
    try {
        if (document.pictureInPictureElement) {
            await document.exitPictureInPicture();
        } else {
            // Ensure we have a valid capture stream from the canvas
            if (!pipStream || pipStream.getTracks().length === 0) {
                pipStream = canvasElement.captureStream(30);
                pipVideo.srcObject = pipStream;
            }
            
            // Critical: Wait for video to be ready before requesting PiP
            await pipVideo.play();
            
            // Use requestAnimationFrame to ensure the video has at least one frame drawn
            requestAnimationFrame(async () => {
                try {
                    await pipVideo.requestPictureInPicture();
                } catch (e) {
                    console.error("PiP Request Failed:", e);
                    // Fallback: Try a direct request if the RAF failed
                    await pipVideo.requestPictureInPicture().catch(_ => {
                        alert("Failed to enter Background Mode. Please ensure the camera is running and you have interacted with the page.");
                    });
                }
            });
        }
    } catch (error) {
        console.error("PiP Error:", error);
    }
});

// Sync the event listeners to the pipVideo instead of videoElement
pipVideo?.addEventListener('enterpictureinpicture', () => {
    const btn = document.getElementById('pipBtn');
    if (btn) btn.innerText = '❌ Exit Background';
    const info = document.getElementById('pip-info');
    if (info) info.style.display = 'block';
});

pipVideo?.addEventListener('leavepictureinpicture', () => {
    const btn = document.getElementById('pipBtn');
    if (btn) btn.innerText = '🖼️ Background Mode';
    const info = document.getElementById('pip-info');
    if (info) info.style.display = 'none';
    
    // Clean up
    if (pipVideo) pipVideo.srcObject = null;
    pipStream = null;
});

// Prevent throttling by detecting visibility
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        // High frequency when visible
    } else {
        // Heartbeat worker takes over full sync responsibility in background
    }
});
