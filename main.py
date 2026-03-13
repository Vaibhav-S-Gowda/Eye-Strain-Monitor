import cv2
import mediapipe as mp
import numpy as np
import time
import math

# Initialize mediapipe
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh()

# Webcam
cap = cv2.VideoCapture(0)

blink_count = 0
start_time = time.time()

EAR_THRESHOLD = 0.20
DISTANCE_THRESHOLD = 250

def eye_aspect_ratio(eye):
    A = np.linalg.norm(np.array(eye[1]) - np.array(eye[5]))
    B = np.linalg.norm(np.array(eye[2]) - np.array(eye[4]))
    C = np.linalg.norm(np.array(eye[0]) - np.array(eye[3]))
    ear = (A + B) / (2.0 * C)
    return ear

while True:
    ret, frame = cap.read()
    h, w, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    posture_status = "Good"
    distance_status = "Safe"

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:

            landmarks = []

            for lm in face_landmarks.landmark:
                x = int(lm.x * w)
                y = int(lm.y * h)
                landmarks.append((x, y))

            # Left eye landmarks
            left_eye = [landmarks[i] for i in [33,160,158,133,153,144]]
            ear = eye_aspect_ratio(left_eye)

            if ear < EAR_THRESHOLD:
                blink_count += 1

            # Distance estimation
            left = landmarks[234]
            right = landmarks[454]
            face_width = abs(left[0] - right[0])

            if face_width > DISTANCE_THRESHOLD:
                distance_status = "Too Close!"

            # Head tilt detection
            nose = landmarks[1]
            left_ear = landmarks[234]
            right_ear = landmarks[454]

            dx = right_ear[0] - left_ear[0]
            dy = right_ear[1] - left_ear[1]

            angle = math.degrees(math.atan2(dy, dx))

            if abs(angle) > 10:
                posture_status = "Bad Posture"

            # Draw landmarks
            for point in left_eye:
                cv2.circle(frame, point, 2, (0,255,0), -1)

    elapsed = time.time() - start_time
    blink_rate = int(blink_count / elapsed * 60) if elapsed > 0 else 0

    # Alerts
    if blink_rate < 8:
        cv2.putText(frame, "Blink More!", (30,50),
                    cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2)

    if distance_status == "Too Close!":
        cv2.putText(frame, "Move Away From Screen", (30,100),
                    cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2)

    if posture_status == "Bad Posture":
        cv2.putText(frame, "Straighten Your Neck", (30,150),
                    cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2)

    # Display info
    cv2.putText(frame,f"Blink Rate: {blink_rate}/min",(30,200),
                cv2.FONT_HERSHEY_SIMPLEX,0.8,(255,255,255),2)

    cv2.imshow("Eye Strain Monitor", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()