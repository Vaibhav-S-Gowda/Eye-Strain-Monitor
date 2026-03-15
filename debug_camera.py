import cv2
import mediapipe as mp
import numpy as np
import time

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

LEFT_EYE = [362,385,387,263,373,380]
RIGHT_EYE = [33,160,158,133,153,144]

def get_ear(landmarks, eye):
    points = [landmarks[i] for i in eye]
    v1 = np.linalg.norm(np.array([points[1].x, points[1].y]) - np.array([points[5].x, points[5].y]))
    v2 = np.linalg.norm(np.array([points[2].x, points[2].y]) - np.array([points[4].x, points[4].y]))
    h = np.linalg.norm(np.array([points[0].x, points[0].y]) - np.array([points[3].x, points[3].y]))
    return (v1 + v2) / (2 * h)

cap = cv2.VideoCapture(0)
print("Starting camera debug loop...", flush=True)

start = time.time()
while time.time() - start < 4:  # run for 4 seconds
    ret, frame = cap.read()
    if not ret: continue
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = face_mesh.process(rgb)
    if res.multi_face_landmarks:
        for f in res.multi_face_landmarks:
            ear = (get_ear(f.landmark, LEFT_EYE) + get_ear(f.landmark, RIGHT_EYE)) / 2
            print(f"EAR: {ear:.3f}", flush=True)

cap.release()
print("Done", flush=True)
