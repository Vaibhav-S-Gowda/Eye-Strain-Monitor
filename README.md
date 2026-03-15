# Neural Nexus: Eye Health AI 

Neural Nexus is a premium, AI-powered health monitoring ecosystem designed to combat digital eye strain (Computer Vision Syndrome). It transforms your computer into a sentient wellness companion that monitors posture, blinks, and screen distance in real-time.

---

## Premium Features

### Neural Nexus AI Assistant
- **Context-Aware Feedback**: An intelligent GPT-powered assistant that interprets your live telemetry (fatigue, distance, posture) to give witty, personalized wellness advice.
- **Smart Fallback**: Features a "Local Intelligence" mode that continues to monitor and assist even without an internet connection.

### Precision Biometric Tracking
- **Neural Distance Calc**: Uses MediaPipe FaceMesh for sub-centimeter screen distance estimation via interpupillary mapping.
- **Blink Velocity Monitoring**: Tracks Eye Aspect Ratio (EAR) to ensure healthy lubrication and micro-rest intervals.
- **Postural Correction**: Detects "The Slouch" instantly and provides subtle visual cues to realign your spine.

### State-of-the-Art Aesthetic
- **Glassmorphism UI**: A high-contrast, premium interface featuring frosted glass cards, neo-glow icons, and shimmering gradients.
- **Interactive Dashboards**: Real-time telemetry syncing with Chart.js for beautiful historical health analytics.
- **Micro-Animations**: Dynamic "Neural Bubbles" and morphing shapes provide a fluid, premium UX.

---

## Project Structure

```text
eye_health_ai/
├── backend/
│   ├── server.py             # Flask API, Authentication, and AI Orchestration
│   ├── monitor/
│   │   └── activity_tracker.py # Computer Vision & MediaPipe Inference Engine
│   └── database/             # MongoDB Connection Logic
├── frontend/
│   ├── templates/            # HTML5 Dashboards (Dashboard, Profile, Analytics)
│   └── static/
│       ├── style.css         # Global Glassmorphism Design System
│       └── camera.js         # Real-time WebCam & Telemetry Sync
├── run.py                    # Unified System Loader (Launches Multi-Threads)
├── requirements.txt          # Neural Nexus Dependencies
└── .env                      # Intelligence API Keys (OpenRouter)
```

---

## Quick Start

### 1. Hardware & Environment
- **Camera**: Standard HD Webcam.
- **Python**: v3.9 or higher.
- **Database**: MongoDB v6.0+.

### 2. Database Setup
Install and start **MongoDB Community Server** ([Download here](https://www.mongodb.com/try/download/community)). Ensure it is running on `localhost:27017`.

### 3. Installation
Clone the repository and install the Neural Core:
```bash
pip install -r requirements.txt
```

### 4. API Configuration (Optional)
To enable full AI capabilities, add your OpenRouter API key to the `.env` file:
```text
OPENROUTER_API_KEY=your_key_here
```

### 5. Launch the Nexus
Run the unified startup script:
```bash
python run.py
```
Visit **`http://127.0.0.1:5000`** in your browser.

---

## Technical Architecture
- **Inference Layer**: MediaPipe FaceMesh + OpenCV.
- **Logic Tier**: Multi-threaded Flask + Activity Monitoring.
- **Persistence**: MongoDB Document Store.
- **Visuals Tier**: Vanilla JS + CSS3 (Variables & Backdrop Filters).

*Created with ❤️ for Eye Health and Neural Excellence.*
