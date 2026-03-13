# 👁️ AI Digital Eye Strain Monitor

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-orange)](https://opencv.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Latest-green)](https://mediapipe.dev/)

## ⚠️ The Problem
In the era of remote work and digital learning, heavy screen usage leads to **Computer Vision Syndrome (CVS)**. This manifests as:
* **Reduced Blink Rate:** Leading to dry and irritated eyes.
* **Poor Posture:** Causing neck and back pain.
* **Fatigue:** Resulting from ignoring the 20-20-20 rule.

## ✅ The Solution
This AI-powered monitor uses computer vision to analyze your behavior in real-time. It acts as a digital health assistant that tracks your eye health and posture without requiring extra hardware.

---

## 🚀 Features
* **Blink Detection:** Uses Eye Aspect Ratio (EAR) to track blink frequency and prevent dry eyes.
* **20-20-20 Rule Reminders:** Automatic alerts every 20 minutes to look at something 20 feet away for 20 seconds.
* **Distance Estimation:** Detects if you are sitting too close to the screen.
* **Posture Tracking:** Monitors head tilt and alignment to prevent "tech neck."
* **Live UI:** Real-time feedback overlay on the camera feed.

---

## 🛠️ Tech Stack
| Component | Technology |
| :--- | :--- |
| **Language** | Python 3.x |
| **Vision Engine** | MediaPipe (Face Mesh) |
| **Image Processing** | OpenCV |
| **Math Operations** | NumPy |

---
