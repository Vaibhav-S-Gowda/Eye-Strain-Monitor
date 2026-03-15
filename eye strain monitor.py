import mediapipe as mp
import cv2
import numpy as np
import time
import sys
import math
import winsound
import pandas as pd
import os
from pynput import keyboard, mouse
from sklearn.linear_model import LogisticRegression

# ---------------- CAMERA ----------------
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    sys.exit()

print("Webcam initialized")

# ---------------- CONFIG ----------------
BLINK_THRESHOLD = 0.22
BLINK_CONSEC_FRAMES = 3
HEAD_TILT_THRESHOLD = 15
MIN_DISTANCE_CM = 50
REMINDER_INTERVAL = 20 * 60

SESSION_LOG = "session_log.csv"

# ---------------- MEDIAPIPE ----------------
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)

LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

LEFT_FACE = 234
RIGHT_FACE = 454
NOSE = 1

# ---------------- ACTIVITY TRACKING ----------------
keyboard_count = 0
mouse_count = 0

def on_press(key):
    global keyboard_count
    keyboard_count += 1

def on_move(x, y):
    global mouse_count
    mouse_count += 1

keyboard.Listener(on_press=on_press).start()
mouse.Listener(on_move=on_move).start()

# ---------------- EAR FUNCTION ----------------
def get_ear(landmarks, eye_indices):

    points = [landmarks[i] for i in eye_indices]

    v1 = np.linalg.norm(np.array([points[1].x, points[1].y]) -
                        np.array([points[5].x, points[5].y]))

    v2 = np.linalg.norm(np.array([points[2].x, points[2].y]) -
                        np.array([points[4].x, points[4].y]))

    h = np.linalg.norm(np.array([points[0].x, points[0].y]) -
                       np.array([points[3].x, points[3].y]))

    return (v1 + v2) / (2.0 * h)

# ---------------- DISTANCE IN CM ----------------
def calculate_distance_cm(landmarks, w):

    left = landmarks[LEFT_FACE]
    right = landmarks[RIGHT_FACE]

    face_width = abs(left.x - right.x) * w

    distance = (16 * 600) / face_width

    return round(distance, 1)

# ---------------- HEAD TILT ----------------
def head_tilt_angle(landmarks, w, h):

    left = landmarks[LEFT_FACE]
    right = landmarks[RIGHT_FACE]

    angle = math.degrees(math.atan2((right.y - left.y) * h,
                                    (right.x - left.x) * w))

    return abs(angle)

# ---------------- POSTURE ----------------
def detect_posture(landmarks):

    nose = landmarks[NOSE]
    left = landmarks[LEFT_FACE]
    right = landmarks[RIGHT_FACE]

    avg = (left.y + right.y) / 2

    if nose.y > avg:
        return "Bad"

    return "Good"

# ---------------- ACTIVITY DETECTION ----------------
def detect_activity():

    global keyboard_count, mouse_count

    if keyboard_count > 40:
        activity = "Coding"

    elif mouse_count > 50:
        activity = "Gaming"

    elif keyboard_count < 5 and mouse_count < 5:
        activity = "Watching Video"

    else:
        activity = "Reading"

    keyboard_count = 0
    mouse_count = 0

    return activity

# ---------------- LIGHT ESTIMATION ----------------
def estimate_light(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)

    if brightness < 60:
        return "Too Dark"

    elif brightness > 180:
        return "Too Bright"

    return "Good"

# ---------------- FATIGUE AI MODEL ----------------
X_train = [[5,40,20],[15,60,5],[3,30,25],[20,70,2]]
y_train = [1,0,1,0]

model = LogisticRegression()
model.fit(X_train,y_train)

def fatigue_score(blink_rate, distance, tilt):

    blink_score = max(0,(10-blink_rate)*5)
    dist_score = max(0,(MIN_DISTANCE_CM-distance))
    tilt_score = max(0,(tilt-HEAD_TILT_THRESHOLD))

    score = blink_score*0.4 + dist_score*0.3 + tilt_score*0.3

    return min(100,round(score,2))

# ---------------- SAVE LOG ----------------
def save_to_csv(data):

    df = pd.DataFrame([data])

    if not os.path.isfile(SESSION_LOG):
        df.to_csv(SESSION_LOG,index=False)
    else:
        df.to_csv(SESSION_LOG,mode='a',header=False,index=False)

# ---------------- MAIN ----------------
def main():
    # --- Initialization ---
    blink_count = 0
    frame_counter = 0
    start_time = time.time()
    last_reminder = time.time()
    muted = False  # Track if sound is muted
    
    print("Eye Strain Monitor Started")
    print("Shortcuts: [q] Quit, [r] Reset, [s] Screenshot, [m] Mute/Unmute")

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            break

        image = cv2.flip(image, 1)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        posture = "Detecting"
        distance_cm = 0
        tilt_angle = 0

        # --- Face Processing ---
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                landmarks = face_landmarks.landmark
                h, w, _ = image.shape

                l_ear = get_ear(landmarks, LEFT_EYE)
                r_ear = get_ear(landmarks, RIGHT_EYE)
                ear = (l_ear + r_ear) / 2.0

                if ear < BLINK_THRESHOLD:
                    frame_counter += 1
                else:
                    if frame_counter >= BLINK_CONSEC_FRAMES:
                        blink_count += 1
                    frame_counter = 0

                posture = detect_posture(landmarks)
                distance_cm = calculate_distance_cm(landmarks, w)
                tilt_angle = head_tilt_angle(landmarks, w, h)

        # --- Metrics & AI ---
        elapsed_minutes = (time.time() - start_time) / 60
        blink_rate = blink_count / elapsed_minutes if elapsed_minutes > 0 else 0
        activity = detect_activity()
        light = estimate_light(image)
        fatigue = fatigue_score(blink_rate, distance_cm, tilt_angle)
        prediction = model.predict([[blink_rate, distance_cm, tilt_angle]])[0]

        # --- Sound Alerts (Integrated with Mute) ---
        if not muted:
            # We use 100ms instead of 400ms to prevent the video from lagging
            if distance_cm < MIN_DISTANCE_CM:
                winsound.Beep(900, 100) 
            if tilt_angle > HEAD_TILT_THRESHOLD:
                winsound.Beep(1000, 100)

        # --- UI Display ---
        cv2.putText(image, f"Blinks: {blink_count}", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(image, f"Blink Rate: {blink_rate:.1f}/min", (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(image, f"Distance: {distance_cm} cm", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(image, f"Head Tilt: {tilt_angle:.1f}", (30, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(image, f"Posture: {posture}", (30, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(image, f"Lighting: {light}", (30, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(image, f"Activity: {activity}", (30, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(image, f"Fatigue: {fatigue}", (30, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        if muted:
            cv2.putText(image, "SOUND MUTED", (30, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        if prediction == 1:
            cv2.putText(image, "AI: FATIGUED", (200, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

        # --- Smart Break ---
        if (time.time() - last_reminder) > REMINDER_INTERVAL:
            if activity in ["Watching Video", "Reading"]:
                cv2.putText(image, "TAKE A BREAK - LOOK 20FT AWAY", (120, 350), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                # Note: last_reminder reset logic can be placed here or via keypress

        # --- Log Data ---
        save_to_csv({"BlinkRate": blink_rate, "Distance": distance_cm, "Tilt": tilt_angle, "FatigueScore": fatigue})

        cv2.imshow("AI Eye Strain Monitor", image)

        # --- Keyboard Shortcuts Logic ---
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):  # Quit
            break
        elif key == ord('r'):  # Reset Blinks
            blink_count = 0
            start_time = time.time()
            print("Session metrics reset.")
        elif key == ord('s'):  # Screenshot
            fname = f"snapshot_{int(time.time())}.png"
            cv2.imwrite(fname, image)
            print(f"Saved: {fname}")
        elif key == ord('m'):  # Toggle Mute
            muted = not muted
            print(f"Mute: {muted}")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
