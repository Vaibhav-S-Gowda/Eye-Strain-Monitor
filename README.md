<<<<<<< HEAD
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
=======
# 👁️ Eye Strain Monitor

A real-time **eye strain detection system** that monitors user eye activity and posture using a webcam.  
This project helps prevent digital eye fatigue by analyzing blink rate and head posture and sending alerts when unhealthy patterns are detected.

With increasing screen usage, people often forget to blink regularly or maintain proper posture, which leads to eye strain and discomfort. This system uses computer vision to monitor these patterns and notify the user.

---

## 🚀 Features

- 👁️ **Blink Detection** using Eye Aspect Ratio (EAR)
- 🧠 **Eye Strain Monitoring**
- 🪑 **Head Posture Detection**
- 🔔 **Real-time Sound Alerts**
- 📊 **Data Logging and Visualization**
- 🎥 **Live Webcam Monitoring**

---

## 🛠 Tech Stack

**Language**

- Python

**Libraries**

- OpenCV
- MediaPipe
- NumPy
- Pandas
- Matplotlib
- Scikit-learn

**Other Tools**

- Webcam
- Winsound (alerts)
- Boto3 (AWS integration)

---

## 🧠 How It Works

1. The webcam captures live video frames.
2. MediaPipe detects facial landmarks.
3. Eye landmarks are used to calculate the **Eye Aspect Ratio (EAR)**.
4. If the EAR drops below a threshold, a blink is detected.
5. Blink rate and head posture are monitored continuously.
6. If abnormal patterns are detected:
   - A sound alert is triggered.
   - Data is logged for analysis.

---

## 📂 Project Structure

```
Eye-Strain-Monitor
│
├── main.py
├── requirements.txt
├── README.md
│
├── data
│   └── logs.csv
│
├── models
│   └── model.pkl
│
└── assets
    └── alert.wav
```

*(Project structure may change as the project evolves.)*

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/Vaibhav-S-Gowda/Eye-Strain-Monitor.git
```

### 2. Go to the project folder

```bash
cd Eye-Strain-Monitor
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Project

```bash
python main.py
```

The webcam will start and the system will begin monitoring your eye activity.

---

## 📈 Future Improvements

- Machine learning based eye fatigue prediction
- Web dashboard for analytics
- Mobile notifications
- Personalized eye health recommendations
- Multi-user support

---

## 🤝 Contributing

Contributions are welcome.

Steps to contribute:

1. Fork the repository  
2. Create a new branch

```bash
git checkout -b feature-name
```

3. Commit changes

```bash
git commit -m "Added new feature"
```

4. Push to branch

```bash
git push origin feature-name
```

5. Open a Pull Request

---

## 👨‍💻 Author

**Hinduja C**
- GitHub: https://github.com/Hinduja30

**Mahima P**
- GitHub: https://github.com/Mahimaa-30

**Vaibhav S Gowda**
- GitHub: https://github.com/Vaibhav-S-Gowda
>>>>>>> 4f6cb9c1f95baf319326b0cce34f6c6e4c40c697
