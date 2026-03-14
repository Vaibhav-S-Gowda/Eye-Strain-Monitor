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
