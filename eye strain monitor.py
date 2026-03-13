import warnings
warnings.filterwarnings("ignore")
import cv2
import mediapipe as mp
import numpy as np
import time
import math
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
#import simpleaudio as sa
import threading
import winsound
import boto3
import os
import warnings


# ---------------- CONFIG ----------------
BLINK_THRESHOLD = 0.22
MIN_DISTANCE_CM = 50
HEAD_TILT_THRESHOLD = 15
LOW_BLINK_LIMIT = 8

SESSION_LOG = "session_log.csv"
DARK_MODE = True

# AWS CONFIG (Fill your credentials)
UPLOAD_TO_S3 = False
S3_BUCKET = "your-bucket-name"

# ---------------- INITIALIZE ----------------
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

cap = cv2.VideoCapture(0)

blink_count = 0
frame_counter = 0
start_time = time.time()

blink_history = []
fatigue_history = []

# ---------------- ML MODEL ----------------
X_train = [[5, 40, 20], [15, 60, 5], [3, 30, 25], [20, 70, 2]]
y_train = [1, 0, 1, 0]  # 1 = fatigued

model = LogisticRegression()
model.fit(X_train, y_train)

# ---------------- FUNCTIONS ----------------

def beep():
    threading.Thread(target=lambda: playsound("alert.mp3")).start()

def get_ear(landmarks, eye):
    pts = [landmarks[i] for i in eye]
    v1 = np.linalg.norm([pts[1].x - pts[5].x, pts[1].y - pts[5].y])
    v2 = np.linalg.norm([pts[2].x - pts[4].x, pts[2].y - pts[4].y])
    h = np.linalg.norm([pts[0].x - pts[3].x, pts[0].y - pts[3].y])
    return (v1 + v2) / (2.0 * h)

def calculate_distance(landmarks, w):
    left = landmarks[234]
    right = landmarks[454]
    face_width = abs(left.x - right.x) * w
    return round((16 * 600) / face_width, 1)

def head_tilt(landmarks, w, h):
    l = landmarks[234]
    r = landmarks[454]
    angle = math.degrees(math.atan2((r.y - l.y)*h, (r.x - l.x)*w))
    return abs(angle)

def fatigue_score(blink_rate, distance, tilt):
    blink_score = max(0, (LOW_BLINK_LIMIT - blink_rate) * 5)
    dist_score = max(0, (MIN_DISTANCE_CM - distance))
    tilt_score = max(0, tilt - HEAD_TILT_THRESHOLD)
    score = blink_score*0.4 + dist_score*0.3 + tilt_score*0.3
    return min(100, round(score,2))

def save_to_csv(data):
    df = pd.DataFrame([data])
    if not os.path.isfile(SESSION_LOG):
        df.to_csv(SESSION_LOG, index=False)
    else:
        df.to_csv(SESSION_LOG, mode='a', header=False, index=False)

def upload_to_s3():
    s3 = boto3.client('s3')
    s3.upload_file(SESSION_LOG, S3_BUCKET, SESSION_LOG)

# ---------------- DARK MODE ----------------
if DARK_MODE:
    bg_color = (30,30,30)
    text_color = (0,255,0)
else:
    bg_color = (255,255,255)
    text_color = (0,0,0)

print("AI Eye Strain Monitor PRO Running...")

# ---------------- MAIN LOOP ----------------
while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    h,w,_ = frame.shape
    frame = cv2.flip(frame,1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark

        l_ear = get_ear(landmarks, LEFT_EYE)
        r_ear = get_ear(landmarks, RIGHT_EYE)
        ear = (l_ear + r_ear)/2

        if ear < BLINK_THRESHOLD:
            frame_counter += 1
        else:
            if frame_counter >= 3:
                blink_count += 1
            frame_counter = 0

        elapsed = (time.time() - start_time)/60
        blink_rate = blink_count/elapsed if elapsed>0 else 0

        distance = calculate_distance(landmarks, w)
        tilt = head_tilt(landmarks,w,h)

        fatigue = fatigue_score(blink_rate, distance, tilt)

        blink_history.append(blink_rate)
        fatigue_history.append(fatigue)

        # ML Prediction
        prediction = model.predict([[blink_rate, distance, tilt]])[0]

        # ALERTS
        if distance < MIN_DISTANCE_CM:
            winsound.Beep(1000, 500)  # frequency, duration
        if tilt > HEAD_TILT_THRESHOLD:
            winsound.Beep(1000, 500)  # frequency, duration

        # DISPLAY
        cv2.putText(frame,f"Blink Rate: {round(blink_rate,2)}",(20,40),
                    cv2.FONT_HERSHEY_SIMPLEX,0.7,text_color,2)

        cv2.putText(frame,f"Distance: {distance}cm",(20,70),
                    cv2.FONT_HERSHEY_SIMPLEX,0.7,text_color,2)

        cv2.putText(frame,f"Tilt: {round(tilt,2)}",(20,100),
                    cv2.FONT_HERSHEY_SIMPLEX,0.7,text_color,2)

        cv2.putText(frame,f"Fatigue Score: {fatigue}",(20,130),
                    cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)

        if prediction == 1:
            cv2.putText(frame,"AI: FATIGUED",(200,200),
                        cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),3)

        save_to_csv({
            "BlinkRate":blink_rate,
            "Distance":distance,
            "Tilt":tilt,
            "FatigueScore":fatigue
        })

    cv2.imshow("AI Eye Monitor PRO",frame)

    if cv2.waitKey(1)&0xFF==ord('q'):
        break

cap.release()
cv2.destroyAllWindows()


# -------- GRAPH DASHBOARD --------
'''plt.figure()
plt.plot(blink_history)
plt.title("Blink Rate Over Time")
plt.show()

plt.figure()
plt.plot(fatigue_history)
plt.title("Fatigue Score Over Time")
plt.show()'''

# -------- CLOUD UPLOAD --------
if UPLOAD_TO_S3:
    upload_to_s3()