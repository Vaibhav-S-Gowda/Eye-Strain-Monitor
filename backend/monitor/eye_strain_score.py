def calculate_ers(blink_rate, distance, screen_time, lighting, fatigue):

    score = 0

    # blink factor
    if blink_rate < 8:
        score += 20

    elif blink_rate < 12:
        score += 10

    # distance factor
    if distance < 40:
        score += 25

    elif distance < 50:
        score += 10

    # screen time factor
    if screen_time > 120:
        score += 20

    elif screen_time > 60:
        score += 10

    # lighting factor
    if lighting == "Dark":
        score += 15

    # fatigue prediction
    score += fatigue * 0.3

    return min(int(score),100)