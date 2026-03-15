def give_advice(ers):

    if ers < 30:
        return "Your eyes are healthy."

    elif ers < 60:
        return "Consider blinking more frequently."

    elif ers < 80:
        return "Take a 5 minute break and look at distant objects."

    else:
        return "High eye strain detected. Stop screen usage for 10 minutes."