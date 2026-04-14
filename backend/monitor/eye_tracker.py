import cv2
import mediapipe as mp
import numpy as np

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

LEFT_EYE = [362,385,387,263,373,380]
RIGHT_EYE = [33,160,158,133,153,144]

import collections
import time
import math
import winsound
import pandas as pd
import os

SESSION_LOG = "session_log.csv"

# ---------------- SAVE LOG ----------------
def save_to_csv(data):
    df = pd.DataFrame([data])
    if not os.path.isfile(SESSION_LOG):
        df.to_csv(SESSION_LOG, index=False)
    else:
        df.to_csv(SESSION_LOG, mode='a', header=False, index=False)

BLINK_THRESHOLD = 0.23 # Adjusted for better sensitivity
raw_blink_count = 0 # Track total session blinks raw

import collections
import time

blink_history = collections.deque(maxlen=600) # Increased capacity for 60s @ 10fps
frame_counter = 0

def get_ear(landmarks, eye):
    points = [landmarks[i] for i in eye]
    v1 = np.linalg.norm(np.array([points[1].x, points[1].y]) -
                        np.array([points[5].x, points[5].y]))
    v2 = np.linalg.norm(np.array([points[2].x, points[2].y]) -
                        np.array([points[4].x, points[4].y]))
    h = np.linalg.norm(np.array([points[0].x, points[0].y]) -
                       np.array([points[3].x, points[3].y]))
    return (v1 + v2) / (2 * h)

def analyze_frame(frame):
    global frame_counter
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # 1. Ambient Lighting
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)
    
    # 2. Posture / Slouching Detection
    pose_results = pose.process(rgb)
    is_slouching = False
    if pose_results.pose_landmarks:
        landmarks = pose_results.pose_landmarks.landmark
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        nose = landmarks[mp_pose.PoseLandmark.NOSE.value]
        shoulder_y_avg = (left_shoulder.y + right_shoulder.y) / 2
        # Text-Neck detection
        is_slouching = (shoulder_y_avg - nose.y) < 0.12

    # 3. FaceMesh (Blinks, Distance, 20-20-20 Head Pose)
    results = face_mesh.process(rgb)
    real_distance_cm = 50
    looking_away = False
    
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            landmarks = face_landmarks.landmark
            ear = (get_ear(landmarks, LEFT_EYE) + get_ear(landmarks, RIGHT_EYE)) / 2
            
            blink_detected = False
            if ear < BLINK_THRESHOLD:
                if frame_counter == 0:
                    blink_history.append(time.time())
                    blink_detected = True
                frame_counter += 1
            else:
                frame_counter = 0
                
            left_eye_center = np.mean([[landmarks[i].x, landmarks[i].y] for i in LEFT_EYE], axis=0)
            right_eye_center = np.mean([[landmarks[i].x, landmarks[i].y] for i in RIGHT_EYE], axis=0)
            # Head Pose & Tilt estimation
            h, w, _ = frame.shape
            left_face = landmarks[234]
            right_face = landmarks[454]
            
            # Head Tilt Angle (Roll)
            tilt_angle = math.degrees(math.atan2((right_face.y - left_face.y) * h, (right_face.x - left_face.x) * w))
            tilt_angle = abs(tilt_angle)

            # Distance via Face Width
            face_width = abs(left_face.x - right_face.x) * w
            if face_width > 0:
                real_distance_cm = (16 * 600) / face_width
            else:
                real_distance_cm = 50
            
            # Head Pose (20-20-20 Rule) estimation via eye-to-cheek ratio
            nose_lm = landmarks[1]
            left_cheek = landmarks[234]
            right_cheek = landmarks[454]
            left_dist = abs(nose_lm.x - left_cheek.x)
            right_dist = abs(nose_lm.x - right_cheek.x)
            ratio = max(left_dist, right_dist) / (min(left_dist, right_dist) + 1e-6)
            looking_away = ratio > 2.5

    # Calculate blinks per last 60 seconds
    now = time.time()
    while blink_history and blink_history[0] < (now - 60):
        blink_history.popleft()
        
    current_blink_rate = len(blink_history)
    
    return current_blink_rate, max(min(real_distance_cm, 120), 10), is_slouching, looking_away, int(brightness), tilt_angle, blink_detected

def start_eye_monitor():
    from pymongo import MongoClient
    from backend.monitor.activity_tracker import detect_activity
    from backend.monitor.fatigue_model import calculate_ers
    from backend.monitor.health_advisor import give_advice
    from backend.monitor.idle_detector import get_idle_time
    from backend.monitor.alert_manager import fatigue_alerts
    
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
    db = client.eye_monitor
    logs = db.logs
    
    print("Starting Eye Monitor Thread V2.5...")
    cap = cv2.VideoCapture(0)
    
    last_log_time = time.time()
    last_reminder = time.time()
    distance_history = []
    tilt_angle_history = []
    muted = False
    
    while True:
        try:
            idle_seconds = get_idle_time()
            if idle_seconds > 60:
                print(f"User idle for {idle_seconds}s. Pausing camera...")
                time.sleep(5)
                continue
                
            if cap.isOpened():
                ret, frame = cap.read()
            else:
                ret = False
                
            timestamp = int(time.time() * 1000)
            
            if ret:
                global raw_blink_count
                try:
                    blink_rate, distance, is_slouching, looking_away, brightness, tilt_angle, blink_detected = analyze_frame(frame)
                    if blink_detected:
                        raw_blink_count += 1
                except Exception as e:
                    print("Error analyzing frame:", e)
                    continue
                
                # Smoothing Distance & Tilt
                distance_history.append(distance)
                if len(distance_history) > 10: distance_history.pop(0)
                smooth_dist = int(sum(distance_history) / len(distance_history))

                tilt_angle_history.append(tilt_angle)
                if len(tilt_angle_history) > 10: tilt_angle_history.pop(0)
                smooth_tilt = sum(tilt_angle_history) / len(tilt_angle_history)

                # Sound Alerts
                if not muted:
                    if smooth_dist < 50:
                        winsound.Beep(900, 100)
                    if smooth_tilt > 15:
                        winsound.Beep(1000, 100)
                
                if (timestamp/1000) - last_log_time >= 2:
                    activity = detect_activity()
                    # Calculate new ERS using updated arguments
                    fatigue = calculate_ers(blink_rate, smooth_dist, smooth_tilt)
                    health_score = 100 - fatigue
                    
                    # Dispatch visual Windows notification if fatigue is high (handles own cooldown)
                    if fatigue >= 65:
                        fatigue_alerts.send_fatigue_alert(fatigue, blink_rate, smooth_dist, muted)
                    
                    if is_slouching:
                        advice = "⚠️ Sit up straight! Text-Neck detected."
                        health_score -= 10
                    elif looking_away:
                        advice = "🌿 Good job looking away! Restoring eyes."
                        health_score = min(100, health_score + 10)
                    elif brightness < 60 and activity == "Coding":
                        advice = "⚠️ Room too dark! Prevent screen glare."
                    elif brightness > 180:
                         advice = "⚠️ Room is too bright! Consider reducing glare."
                    else:
                        advice = give_advice(fatigue)
                    
                    # Smart Break Logic
                    if (time.time() - last_reminder) > 20 * 60:
                        if activity in ["Watching Video", "Reading"]:
                            advice = "TAKE A BREAK - LOOK 20FT AWAY"
                            last_reminder = time.time()

                    data = {
                        "timestamp": timestamp,
                        "blink_rate": blink_rate,
                        "activity": activity,
                        "distance": smooth_dist,
                        "tilt": smooth_tilt,
                        "fatigue": fatigue,
                        "advice": advice,
                        "health_score": health_score,
                        "is_slouching": is_slouching,
                        "looking_away": looking_away,
                        "brightness": brightness,
                        "blink_detected": blink_detected
                    }
                    logs.insert_one(data)
                    save_to_csv({"Timestamp": timestamp, "BlinkRate": blink_rate, "Distance": smooth_dist, "Tilt": smooth_tilt, "FatigueScore": fatigue, "Activity": activity})
                    last_log_time = timestamp / 1000
                # Fallback gracefully if camera is blocked but we need to log activity
                if (timestamp/1000) - last_log_time >= 5:
                    activity = detect_activity()
                    data = {
                        "timestamp": timestamp,
                        "blink_rate": 0,
                        "activity": activity,
                        "distance": 0,
                        "tilt": 0,
                        "fatigue": 0,
                        "advice": "System status: Active (Camera session in progress)",
                        "health_score": 100,
                        "is_slouching": False,
                        "looking_away": False,
                        "brightness": 120
                    }
                    logs.insert_one(data)
                    last_log_time = timestamp / 1000
            
            time.sleep(0.05) 
        except Exception as e:
            print("Monitor thread error:", e)
            time.sleep(2)