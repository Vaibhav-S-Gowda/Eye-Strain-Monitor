
import threading
from backend.monitor.eye_tracker import start_eye_monitor
from backend.server import start_server


def start_system():
    # By default, we do not start the python background camera (cv2) 
    # to ensure it strictly respects user consent.
    # The monitoring will instead be activated via the web dashboard (JS camera)
    # when the user clicks 'Start Tracking' and explicitly allows the browser camera.
    start_server()


if __name__ == "__main__":
    start_system()