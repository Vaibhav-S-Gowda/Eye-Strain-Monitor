<div align="center">

# Neural Nexus

### AI-Powered Eye Health & Productivity Guardian

*Combat digital eye strain with real-time AI monitoring, intelligent interventions, and predictive health analytics.*

</div>

---

## Overview

Neural Nexus is a full-stack health monitoring application that uses your webcam and AI to actively prevent Computer Vision Syndrome (CVS). Unlike passive dashboards that just display data, Neural Nexus acts as a **real-time health guardian** — detecting unsafe eye conditions, triggering interventions, and forecasting fatigue before it happens.

### Key Capabilities

| Feature | Description |
|---|---|
| **Real-Time Guardian** | Unified Eye Risk Score combining fatigue, blink rate, and screen distance into a single actionable metric with live alerts |
| **Blink Detection** | EAR-based blink tracking with debounce logic for accuracy, alerting when blink rate drops below healthy range |
| **Distance Monitoring** | Sub-centimeter screen distance estimation using MediaPipe FaceMesh interpupillary mapping |
| **Fatigue Prediction** | Slope-based fatigue forecasting that recommends breaks before strain occurs |
| **Productivity Timeline** | City-skyline visualization showing focus intensity, session segmentation, and work pattern analysis |
| **AI Assistant** | Context-aware GPT-powered wellness advisor with local intelligence fallback |
| **Automated Interventions** | Break enforcement, posture alerts, and mode-based responses (Silent / Strict) |
| **Interactive Visualizations** | 2D line, bar, and 3D Plotly charts with smart hover insights |

---

## Architecture

```
Neural Nexus
├── backend/
│   ├── server.py                 # Flask API, auth, AI orchestration, REST endpoints
│   └── monitor/
│       └── activity_tracker.py   # MediaPipe inference, activity classification
├── frontend/
│   ├── templates/
│   │   ├── dashboard.html        # Main dashboard with metrics, charts, AI chat
│   │   ├── real_time.html        # Real-Time Guardian with risk scoring & alerts
│   │   ├── timeline.html         # Productivity Timeline with city-skyline view
│   │   ├── camera.html           # Camera diagnostic with face mesh overlay
│   │   ├── analytics.html        # Historical analytics and trends
│   │   ├── profile.html          # User profile and preferences
│   │   └── login.html            # Authentication page
│   └── static/
│       ├── style.css             # Design system (cream theme, CSS variables)
│       ├── dashboard.js          # Chart init, telemetry sync, polling loop
│       └── camera.js             # MediaPipe FaceMesh, blink/distance/fatigue engine
├── run.py                        # Application entry point (multi-threaded launcher)
├── requirements.txt              # Python dependencies
└── .env                          # API keys (OpenRouter)
```

---

## Pages

### Dashboard
The central hub displaying real-time eye health metrics, focus score, session timer, Eye Strain Index gauge, and the Visual Dynamics chart with line/bar/3D toggle.

### Real-Time Guardian
An intelligent intervention system featuring:
- **Eye Risk Score** (0–100) combining fatigue + blink rate + distance
- **Live alert feed** with contextual explanations
- **Intervention panel** that appears only when action is needed
- **Session tracker** monitoring work duration and break compliance
- **Gamification** with compliance scores and safe streaks
- **Break enforcement overlay** in Strict mode

### Productivity Timeline
A multi-layer analytical view with:
- **City-skyline visualization** where bar height reflects focus intensity
- **Session segmentation** grouping continuous work periods
- **Canvas overlays** for fatigue and blink rate trend lines
- **Smart insights** detecting peak productivity, distractions, and anomalies

### Camera Diagnostic
Full-screen camera view with face mesh overlay, real-time blink counter, distance measurement, head tilt tracking, and background (PiP) mode.

### Analytics
Historical trend analysis with weekly breakdowns.

---

## Getting Started

### Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.9+ |
| MongoDB | 6.0+ ([Download](https://www.mongodb.com/try/download/community)) |
| Webcam | Any standard HD webcam |

### Installation

```bash
# Clone the repository
git clone https://github.com/Vaibhav-S-Gowda/Eye-Strain-Monitor.git
cd Eye-Strain-Monitor

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root for AI assistant capabilities (optional):

```env
OPENROUTER_API_KEY=your_key_here
```

> The application works fully without an API key. The AI assistant falls back to local intelligence mode.

### Running

```bash
# Ensure MongoDB is running on localhost:27017
python run.py
```

Open **http://127.0.0.1:5000** in your browser.

---

## Technical Stack

| Layer | Technology |
|---|---|
| **Computer Vision** | MediaPipe FaceMesh, OpenCV, TensorFlow Lite |
| **Backend** | Flask, multi-threaded activity monitoring |
| **Database** | MongoDB (document store for telemetry & user data) |
| **Frontend** | Vanilla HTML/CSS/JS, Chart.js, Plotly.js |
| **AI** | OpenRouter API (GPT) with local fallback |
| **Design** | Custom design system — warm cream aesthetic, Inter typography |

---

## License

This project is licensed under the Apache License 2.0 — see the [LICENSE](LICENSE) file for details.
