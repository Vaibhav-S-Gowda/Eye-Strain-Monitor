import time
from winotify import Notification, audio

class AlertManager:
    def __init__(self, cooldown_seconds=300):
        self.last_alert_time = 0
        self.cooldown_seconds = cooldown_seconds

    def send_fatigue_alert(self, fatigue_score, blink_rate, distance, muted=False):
        now = time.time()
        # Enforce cooldown to prevent spamming the user
        if now - self.last_alert_time < self.cooldown_seconds:
            return False

        self.last_alert_time = now

        msg = (f"Your eyes are showing signs of heavy strain (Fatigue: {int(fatigue_score)}%).\n"
               f"Distance: {int(distance)}cm | Blinks: {blink_rate}/min")

        toast = Notification(
            app_id="Visio-Fatigue Monitor",
            title="⚠️ High Fatigue Detected",
            msg=msg,
            duration="long"
        )
        
        # Respect the user's mute settings for the toast sound
        if muted:
            toast.set_audio(audio.Silent, loop=False)
        else:
            toast.set_audio(audio.Default, loop=False)

        # Add a helpful action button that opens the analytics dashboard
        toast.add_actions(label="View Stats", launch="http://localhost:5000/analytics")

        try:
            print(f"DISPATCHING TOAST NOTIFICATION: Fatigue={fatigue_score}")
            toast.show()
            return True
        except Exception as e:
            print("Failed to show Windows toast notification:", e)
            return False

# Global instance with a 5-minute cooldown
fatigue_alerts = AlertManager(cooldown_seconds=300)
