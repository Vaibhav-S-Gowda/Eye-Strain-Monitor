import mediapipe as mp
import time
import numpy as np
import cv2
import sys

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam. Check if it is plugged in or used by another app.")
    sys.exit()
else:
    print("Webcam successfully initialized!")

# --- Configuration ---
BLINK_THRESHOLD = 0.22
BLINK_CONSEC_FRAMES = 3
REMINDER_INTERVAL = 20 * 60

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)

LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]


def get_ear(landmarks, eye_indices):
    points = [landmarks[i] for i in eye_indices]

    v1 = np.linalg.norm(np.array([points[1].x, points[1].y]) - np.array([points[5].x, points[5].y]))
    v2 = np.linalg.norm(np.array([points[2].x, points[2].y]) - np.array([points[4].x, points[4].y]))

    h = np.linalg.norm(np.array([points[0].x, points[0].y]) - np.array([points[3].x, points[3].y]))

    return (v1 + v2) / (2.0 * h)


def main():

    blink_count = 0
    frame_counter = 0
    start_time = time.time()
    last_reminder = time.time()

    print("Eye Strain Monitor Started. Press 'q' to quit.")

    cv2.namedWindow("Eye Strain Monitor")

    while cap.isOpened():

        success, image = cap.read()

        if not success:
            break

        image = cv2.flip(image, 1)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        results = face_mesh.process(rgb_image)

        if results.multi_face_landmarks:

            for face_landmarks in results.multi_face_landmarks:

                l_ear = get_ear(face_landmarks.landmark, LEFT_EYE)
                r_ear = get_ear(face_landmarks.landmark, RIGHT_EYE)

                ear = (l_ear + r_ear) / 2.0

                if ear < BLINK_THRESHOLD:
                    frame_counter += 1
                else:
                    if frame_counter >= BLINK_CONSEC_FRAMES:
                        blink_count += 1
                    frame_counter = 0

        # UI Overlays
        cv2.putText(image, f"Blinks: {blink_count}", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # 20-20-20 Timer
        time_since_break = time.time() - last_reminder

        timer_text = f"Next Break: {int((REMINDER_INTERVAL - time_since_break)/60)}m"

        cv2.putText(image, timer_text, (30, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        if time_since_break > REMINDER_INTERVAL:

            cv2.putText(image, "LOOK AWAY! 20ft for 20s", (100, 200),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)

            if time_since_break > REMINDER_INTERVAL + 20:
                last_reminder = time.time()

        cv2.imshow("Eye Strain Monitor", image)

        # EXIT IF WINDOW CLOSED
        if cv2.getWindowProperty("Eye Strain Monitor", cv2.WND_PROP_VISIBLE) < 1:
            break

        # EXIT IF Q PRESSED
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()