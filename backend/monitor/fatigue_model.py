from sklearn.linear_model import LogisticRegression

# ---------------- FATIGUE AI MODEL ----------------
# Training Data: [BlinkRate, Distance, Tilt]
X_train = [[5, 40, 20], [15, 60, 5], [3, 30, 25], [20, 70, 2]]
# Labels: 1=Fatigued, 0=Not Fatigued
y_train = [1, 0, 1, 0]

model = LogisticRegression()
model.fit(X_train, y_train)

def predict_fatigue(blink_rate, distance, tilt):
    prediction = model.predict([[blink_rate, distance, tilt]])[0]
    return prediction == 1

def calculate_ers(blink_rate, distance, tilt=0):
    BLINK_THRESHOLD = 0.22 # Using constant logic from script
    MIN_DISTANCE_CM = 50
    HEAD_TILT_THRESHOLD = 15

    # Scale individual metrics to 0-100 range before weighting
    blink_score = max(0, (15 - blink_rate) * 6.66)     # 0 blinks = ~100
    dist_score = max(0, (MIN_DISTANCE_CM - distance) * 2.5) # 10cm distance = 100
    tilt_score = max(0, (tilt - HEAD_TILT_THRESHOLD) * 3.33)  # 45deg tilt = ~100

    score = blink_score * 0.4 + dist_score * 0.3 + tilt_score * 0.3

    return min(100, round(score, 2))