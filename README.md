# Eye Health Monitor AI 👁️⚡

A premium, startup-grade Eye Health Analytics Dashboard powered by Computer Vision and AI. Designed to combat digital eye strain (Computer Vision Syndrome), this app runs in the background to monitor your posture, blink rate, and screen usage—providing real-time health advice and gorgeous statistical tracking.

![Dashboard Preview](https://via.placeholder.com/800x400.png?text=Eye+Health+Monitor+Dashboard)

## 🚀 Key Features
* **Computer Vision Distance Tracking:** Uses MediaPipe FaceMesh to precisely calculate your physical distance from the screen using interpupillary math. No hardware depth-sensors required.
* **Real-time Blink Detection:** Tracks eyelid EAR (Eye Aspect Ratio) to ensure you are blinking frequently enough.
* **Smart Idle Detection:** Automatically pauses camera inference when you step away from the keyboard or mouse for >60 seconds, saving massive CPU and Battery.
* **Live Health Advisor Toasts:** Pushes real-time overlay notifications to the dashboard (e.g., "⚠️ Take a 5 minute break" or "⚠️ Move further from the screen") based on live fatigue scores.
* **Premium Glassmorphism Dashboard:** A stunning, modern UI featuring glowing gradients, dynamic Chart.js canvases, and dark-mode aesthetic.

---

## 🛠️ Prerequisites
This project requires **Python 3.9+** and **MongoDB**.

### 1. Install & Run MongoDB
The application relies on a local MongoDB instance to store the real-time health telemetry.
1. Download MongoDB Community Edition from the [official website](https://www.mongodb.com/try/download/community).
2. Install it with default settings (ensure MongoDB Compass is installed if you want a GUI).
3. Ensure the MongoDB service is running on the default port `27017`.

### 2. Install Python Dependencies
Open your terminal in the project directory and run:
```bash
python -m pip install -r requirements.txt
```

---

## 🏃‍♂️ How to Run

1. Simply run the unified startup script:
   ```bash
   python run.py
   ```
2. The script will automatically launch the **Background AI Camera Thread** and the **Flask API Server**.
3. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```
4. *Sit back, code, and watch your eye health stats populate in real-time!*

---

## 🏗️ Architecture Stack
* **Frontend:** Vanilla JS, HTML5, Modern CSS (Glassmorphism UI), Chart.js
* **Backend:** Python, Flask, PyMongo
* **AI & CV:** OpenCV, MediaPipe (FaceMesh), Pynput (Idle Tracking)
* **Database:** MongoDB
