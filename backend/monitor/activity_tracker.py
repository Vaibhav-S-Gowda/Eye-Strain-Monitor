from pynput import keyboard, mouse

import collections
import time

keyboard_events = collections.deque(maxlen=30)
mouse_events = collections.deque(maxlen=30)

def on_press(key):
    keyboard_events.append(time.time())

def on_move(x, y):
    mouse_events.append(time.time())

keyboard.Listener(on_press=on_press).start()
mouse.Listener(on_move=on_move).start()

def detect_activity():
    now = time.time()
    # Clean up old events (older than 30s)
    cutoff = now - 30
    while keyboard_events and keyboard_events[0] < cutoff:
        keyboard_events.popleft()
    while mouse_events and mouse_events[0] < cutoff:
        mouse_events.popleft()

    k_count = len(keyboard_events)
    m_count = len(mouse_events)

    if k_count > 40:
        return "Coding"
    elif m_count > 50:
        return "Gaming"
    elif k_count < 5 and m_count < 5:
        return "Watching Video"
    else:
        return "Reading"