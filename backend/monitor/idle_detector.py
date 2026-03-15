import ctypes


def get_idle_time():

    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint),
                    ("dwTime", ctypes.c_uint)]

    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = ctypes.sizeof(lastInputInfo)

    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo))

    millis = ctypes.windll.kernel32.GetTickCount() - lastInputInfo.dwTime

    return millis / 1000

# import time
# import pyautogui


# def is_user_idle():

#     x1,y1 = pyautogui.position()

#     time.sleep(5)

#     x2,y2 = pyautogui.position()

#     return (x1,y1)==(x2,y2)