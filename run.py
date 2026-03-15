# import cv2
# import time

# from backend.monitor.eye_tracker import detect_blink
# from backend.monitor.activity_tracker import detect_activity
# from backend.monitor.idle_detector import get_idle_time
# from backend.database.mongo_db import save_log
# cap = cv2.VideoCapture(0)

# start = time.time()

# while True:

#     idle = get_idle_time()

#     if idle > 300:
#         continue

#     ret, frame = cap.read()

#     if not ret:
#         break

#     blink_count = detect_blink(frame)

#     activity = detect_activity()

#     screen_time = (time.time() - start) / 60

#     data = {

#         "blink_count": blink_count,
#         "activity": activity,
#         "screen_time": screen_time

#     }

#     save_log(data)

#     cv2.imshow("Eye Monitor", frame)

#     if cv2.waitKey(1) == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()


import threading
from backend.monitor.eye_tracker import start_eye_monitor
from backend.server import start_server


def start_system():

    monitor_thread = threading.Thread(target=start_eye_monitor)
    monitor_thread.daemon = True
    monitor_thread.start()
    start_server()


if __name__ == "__main__":
    start_system()