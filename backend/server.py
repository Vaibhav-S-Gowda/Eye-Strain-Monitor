from flask import Flask, jsonify, render_template, request, session, redirect, url_for
from pymongo import MongoClient
import os
import uuid
from bson import ObjectId
import requests
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


app = Flask(
    __name__,
    template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/templates")),
    static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/static"))
)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = "eye_health_secret_key"
UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB limit
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

client = MongoClient("mongodb://localhost:27017/")
import sys
import os

# Add the project root to sys.path to allow running from any subdirectory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.monitor.activity_tracker import detect_activity

db = client.eye_monitor
logs = db.logs
users = db.users
profiles = db.profiles
chat_history_coll = db.chat_history

# --- Authentication Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"error": "Unauthorized"}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# --- Auth Routes ---
@app.route("/login")
def login_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template("login.html")

@app.route("/api/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    if users.find_one({"username": username}):
        return jsonify({"error": "Username already exists"}), 400
    
    user_id = users.insert_one({
        "username": username,
        "password": generate_password_hash(password)
    }).inserted_id
    
    # Initialize default profile
    profiles.insert_one({
        "user_id": str(user_id),
        "full_name": username,
        "role": "General User",
        "goals": {
            "screen_time": 480, # 8 hours
            "blink_rate": 15
        },
        "preferences": {
            "coaching_style": "Friendly",
            "notifications": True
        }
    })
    
    session['user_id'] = str(user_id)
    return jsonify({"success": True})

@app.route("/api/login", methods=["POST"])
def login_api():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password")
    
    user = users.find_one({"username": username})
    if user and check_password_hash(user['password'], password):
        session['user_id'] = str(user['_id'])
        return jsonify({"success": True})
    
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# --- Protected Routes ---
@app.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/analytics")
@login_required
def analytics_page():
    return render_template("analytics.html")

@app.route("/timeline")
@login_required
def timeline_page():
    return render_template("timeline.html")

@app.route("/real-time")
@login_required
def real_time_page():
    return render_template("real_time.html")

@app.route("/camera")
@login_required
def camera_page():
    return render_template("camera.html")

@app.route("/profile")
@login_required
def profile_page():
    return render_template("profile.html")

@app.route("/api/upload-avatar", methods=["POST"])
@login_required
def upload_avatar():
    if 'avatar' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
        filename = secure_filename(f"{session['user_id']}_{uuid.uuid4().hex[:8]}.{file.filename.rsplit('.', 1)[1].lower()}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        avatar_url = f"/static/uploads/{filename}"
        profiles.update_one(
            {"user_id": session['user_id']},
            {"$set": {"avatar_url": avatar_url}},
            upsert=True
        )
        return jsonify({"success": True, "avatar_url": avatar_url})
    
    return jsonify({"error": "Invalid file type"}), 400

@app.route("/api/profile", methods=["GET", "POST"])
@login_required
def profile_api():
    uid = ObjectId(session['user_id']) if isinstance(session['user_id'], str) and len(session['user_id']) == 24 else session['user_id']
    
    if request.method == "GET":
        user = users.find_one({"_id": uid})
        profile = profiles.find_one({"user_id": session['user_id']}) or {}
        return jsonify({
            "username": user["username"] if user else session['user_id'],
            "full_name": profile.get("full_name", ""),
            "role": profile.get("role", "Other"),
            "avatar_url": profile.get("avatar_url", ""),
            "goals": profile.get("goals", {"screen_time": 480, "blink_rate": 15}),
            "preferences": profile.get("preferences", {"coaching_style": "Friendly", "notifications": True})
        })

    data = request.json
    
    # Handle username change
    new_username = data.get("username")
    if new_username:
        existing = users.find_one({"username": new_username, "_id": {"$ne": uid}})
        if existing:
            return jsonify({"error": "Username already taken"}), 400
        users.update_one({"_id": uid}, {"$set": {"username": new_username}})

    profiles.update_one(
        {"user_id": session['user_id']},
        {"$set": {
            "full_name": data.get("full_name"),
            "role": data.get("role"),
            "goals": data.get("goals"),
            "preferences": data.get("preferences")
        }},
        upsert=True
    )
    return jsonify({"success": True})

@app.route("/api/record", methods=["POST"])
@login_required
def record_data():
    import time
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Enrich data with server-side info
    data["user_id"] = session['user_id']
    if "timestamp" not in data:
        data["timestamp"] = int(time.time() * 1000)
    
    # Save to MongoDB
    logs.insert_one(data)
    return jsonify({"success": True})

@app.route("/api/activity")
@login_required
def get_activity():
    return jsonify({"activity": detect_activity()})

@app.route("/api/data")
@login_required
def api():
    data = list(logs.find({"user_id": session['user_id']}).sort("timestamp", -1).limit(50))
    for d in data:
        d["_id"] = str(d["_id"])
    response = jsonify(data)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

@app.route("/api/timeline")
@login_required
def api_timeline():
    import datetime
    # Build a day timeline from today's logs
    midnight_dt = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    midnight_ms  = midnight_dt.timestamp() * 1000
    end_of_day_ms = midnight_ms + 86400000  # 24h window

    today_logs = list(
        logs.find({"user_id": session['user_id'], "timestamp": {"$gte": midnight_ms}})
            .sort("timestamp", 1)
    )

    segments = []
    for i, log in enumerate(today_logs):
        ts = log.get("timestamp", 0)
        activity = log.get("activity", "Idle")
        # Duration = gap to next log, capped at 5 min; last segment = 2 min
        if i + 1 < len(today_logs):
            gap_ms = today_logs[i + 1]["timestamp"] - ts
            duration_ms = min(gap_ms, 300000)
        else:
            duration_ms = 120000

        # Position as fraction of day (0.0 – 1.0)
        start_frac = max(0.0, (ts - midnight_ms) / 86400000)
        width_frac  = min(duration_ms / 86400000, 1.0 - start_frac)

        segments.append({
            "activity": activity,
            "start": round(start_frac * 100, 4),   # percent
            "width": max(round(width_frac * 100, 4), 0.1),  # at least 0.1%
            "timestamp": ts
        })

    return jsonify(segments)


def _get_summary_data(user_id):
    import time, datetime
    # Start of today (midnight)
    midnight = datetime.datetime.combine(datetime.date.today(), datetime.time.min).timestamp() * 1000
    
    # Get all logs from today for this user
    today_logs = list(logs.find({"user_id": user_id, "timestamp": {"$gte": midnight}}).sort("timestamp", 1))
    
    if not today_logs:
        return {"total_blinks": 0, "screen_time_minutes": 0, "avg_health_score": 0}
        
    # Correct total blinks: blink_rate is already per-minute, but logged every 2s
    # However, since blink_rate is a rolling minute average, we should average it over the segments
    # or just sum the raw increments if we had them. 
    # Since blink_rate in my fix IS the count of blinks in the LAST 60 seconds at that moment:
    # A better way is to average the blink_rate across the day segments or find a better aggregator.
    # For simplicity here, let's take the latest blink rate as current per-min, and sum screen time.
    
    avg_blink_rate = sum(log.get("blink_rate", 0) for log in today_logs) / len(today_logs)
    total_score = sum(log.get("health_score", 0) for log in today_logs)
    avg_score = total_score / len(today_logs)
    
    # Screen time: count gaps between logs. If gap > 5s, it's idle.
    total_screen_ms = 0
    for i in range(1, len(today_logs)):
        gap = today_logs[i]["timestamp"] - today_logs[i-1]["timestamp"]
        if gap < 10000: # 10s threshold for continuous session
            total_screen_ms += gap
            
    screen_time_minutes = int(total_screen_ms / 60000)
    # If we have activity but minutes round to 0, show at least 1m for tracking progress
    if total_screen_ms > 0 and screen_time_minutes == 0:
        screen_time_minutes = 1
    
    # Estimate total blinks today based on avg blink rate and screen time
    estimated_total_blinks = int(avg_blink_rate * screen_time_minutes)
    
    return {
        "total_blinks": estimated_total_blinks,
        "screen_time_minutes": max(0, screen_time_minutes),
        "avg_health_score": int(avg_score)
    }


@app.route("/api/summary")
@login_required
def summary():
    response = jsonify(_get_summary_data(session['user_id']))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

@app.route("/api/history")
@login_required
def history_api():
    import datetime
    history_data = []
    # Fetch last 14 days
    for i in range(13, -1, -1):
        d = datetime.date.today() - datetime.timedelta(days=i)
        start_ts = datetime.datetime.combine(d, datetime.time.min).timestamp() * 1000
        end_ts = datetime.datetime.combine(d, datetime.time.max).timestamp() * 1000
        
        day_logs = list(logs.find({"user_id": session['user_id'], "timestamp": {"$gte": start_ts, "$lte": end_ts}}))
        
        if not day_logs:
            score = 0
            level = 0
        else:
            avg_score = sum(l.get("health_score", 0) for l in day_logs) / len(day_logs)
            score = int(avg_score)
            if score > 80: level = 4
            elif score > 60: level = 3
            elif score > 40: level = 2
            else: level = 1
            
        history_data.append({
            "date": d.strftime("%Y-%m-%d"),
            "score": score,
            "level": level
        })
    return jsonify(history_data)


@app.route("/api/chat/history")
@login_required
def chat_history():
    history = list(chat_history_coll.find({"user_id": session['user_id']}).sort("time", 1).limit(50))
    for h in history:
        h["_id"] = str(h["_id"])
    return jsonify(history)

@app.route("/api/chat/clear", methods=["POST"])
@login_required
def chat_clear():
    chat_history_coll.delete_many({"user_id": session['user_id']})
    return jsonify({"success": True})

@app.route("/api/chat", methods=["POST"])
@login_required
def chat():
    import time

    data = request.json
    user_msg = data.get("message", "").strip()

    if not user_msg:
        return jsonify({"reply": "I'm listening! What's on your mind?"})

    # -----------------------------
    # 1. Gather Telemetry Context
    # -----------------------------
    recent_telemetry = list(logs.find({"user_id": session['user_id']}).sort("timestamp", -1).limit(10))
    summary_data = _get_summary_data(session['user_id'])
    user_profile = profiles.find_one({"user_id": session['user_id']}) or {}

    telemetry_summary = "Sensors offline or no recent metrics."
    avg_dist = 60
    avg_fatigue = 0
    slouch_count = 0
    activity = "active"

    if recent_telemetry:
        avg_dist = sum(l.get("distance", 50) for l in recent_telemetry) / len(recent_telemetry)
        avg_fatigue = sum(l.get("fatigue", 0) for l in recent_telemetry) / len(recent_telemetry)
        slouch_count = sum(1 for l in recent_telemetry if l.get("is_slouching"))
        activity = recent_telemetry[0].get("activity", "active")
        telemetry_summary = (
            f"Activity: {activity}, "
            f"Distance: {int(avg_dist)}cm, "
            f"Fatigue: {int(avg_fatigue)}%, "
            f"Slouching: {slouch_count}, "
            f"ScreenTime: {summary_data['screen_time_minutes']} minutes."
        )

    # -----------------------------
    # 2. Build personalized context
    # -----------------------------
    name = user_profile.get("full_name", "there")
    role = user_profile.get("role", "User")
    goals = user_profile.get("goals", {})
    personalized_context = f"You are assisting {name}, who is a {role}. "
    if isinstance(goals, dict):
        personalized_context += (
            f"Their daily screen time goal is {goals.get('screen_time', 120)} minutes "
            f"and target blink rate is {goals.get('blink_rate', 15)} per minute."
        )

    # SMART LOCAL FALLBACK - only if no API key
    if not OPENROUTER_API_KEY:
        msg_lower = user_msg.lower()
        if any(w in msg_lower for w in ["hello", "hi", "hey"]):
            reply = f"Hello {name}! I'm your Neural Nexus AI assistant. Ask me about your fatigue, posture, breaks, or anything else!"
        elif any(w in msg_lower for w in ["fatigue", "tired", "sleepy"]):
            risk = "high" if avg_fatigue > 60 else "low"
            reply = f"Your fatigue is at **{int(avg_fatigue)}%** — a {risk} risk. Try blinking more and taking a short break!"
        elif any(w in msg_lower for w in ["posture", "slouch", "back"]):
            s_msg = "looks great!" if slouch_count == 0 else f"needs attention ({slouch_count} slouches detected)"
            reply = f"Your posture {s_msg}. Average screen distance: **{int(avg_dist)}cm** (aim for >50cm)."
        elif any(w in msg_lower for w in ["break", "rest"]):
            reply = f"You've had **{summary_data['screen_time_minutes']} minutes** of screen time. Try the 20-20-20 rule: look 20 feet away for 20 seconds!"
        elif any(w in msg_lower for w in ["stats", "status", "summary"]):
            reply = (
                f"**Your Current Snapshot:**\n"
                f"- Activity: **{activity.title()}**\n"
                f"- Distance: **{int(avg_dist)} cm**\n"
                f"- Fatigue: **{int(avg_fatigue)}%**\n"
                f"- Screen Time: **{summary_data['screen_time_minutes']} min**"
            )
        else:
            reply = f"I'm in offline mode. Here's your data: **Distance:** {int(avg_dist)}cm | **Fatigue:** {int(avg_fatigue)}% | **Slouches:** {slouch_count}"

        chat_history_coll.insert_one({"user_id": session['user_id'], "role": "user", "text": user_msg, "time": time.time()})
        chat_history_coll.insert_one({"user_id": session['user_id'], "role": "assistant", "text": reply, "time": time.time()})
        return jsonify({"reply": reply})

    # -----------------------------
    # 3. Build messages for OpenRouter (exact working pattern)
    # -----------------------------
    history = list(chat_history_coll.find({"user_id": session['user_id']}).sort("time", -1).limit(8))
    history.reverse()

    messages = [
        {
            "role": "system",
            "content": (
                "You are Neural Nexus AI — a helpful, witty, and engaging chatbot who chats like a friendly human. "
                "You can answer ANY question — coding, science, health, general knowledge, anything. "
                f"{personalized_context} "
                f"You also have access to the user's real-time eye health data (use only if asked or critical): {telemetry_summary}"
            )
        }
    ]

    for h in history:
        role_msg = "assistant" if h["role"] in ["assistant", "bot"] else "user"
        messages.append({"role": role_msg, "content": h["text"]})

    messages.append({"role": "user", "content": user_msg})

    # -----------------------------
    # 4. Call OpenRouter API (working pattern)
    # -----------------------------
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": messages,
                "max_tokens": 1024
            }
        )

        result = response.json()

        # Handle API-level errors (e.g. invalid key, rate limit, bad model)
        if "error" in result:
            api_err = result["error"]
            err_msg = api_err.get("message", str(api_err)) if isinstance(api_err, dict) else str(api_err)
            print("OpenRouter API Error:", err_msg)
            # Fall back to smart local reply
            raise Exception(f"API error: {err_msg}")

        if "choices" not in result or not result["choices"]:
            print("Unexpected OpenRouter response:", result)
            raise Exception("No choices returned from API")

        reply = result["choices"][0]["message"]["content"]

    except Exception as e:
        print("OpenRouter Exception:", e)
        # Provide a helpful local fallback instead of showing raw error
        msg_lower = user_msg.lower()
        if any(w in msg_lower for w in ["hello", "hi", "hey"]):
            reply = f"Hello {name}! I'm your Neural Nexus assistant. (AI offline — API issue)"
        elif any(w in msg_lower for w in ["fatigue", "tired", "sleepy"]):
            risk = "high" if avg_fatigue > 60 else "low"
            reply = f"Your fatigue is at **{int(avg_fatigue)}%** — a {risk} risk. Try blinking more and taking a short break!"
        elif any(w in msg_lower for w in ["posture", "slouch", "back"]):
            s_msg = "looks great!" if slouch_count == 0 else f"needs attention ({slouch_count} slouches detected)"
            reply = f"Your posture {s_msg}. Avg screen distance: **{int(avg_dist)}cm** (aim for >50cm)."
        elif any(w in msg_lower for w in ["break", "rest"]):
            reply = f"You've had **{summary_data['screen_time_minutes']} min** of screen time. Try the 20-20-20 rule!"
        elif any(w in msg_lower for w in ["stats", "status", "summary"]):
            reply = (
                f"**Your Snapshot:**\n"
                f"- Activity: **{activity.title()}**\n"
                f"- Distance: **{int(avg_dist)} cm**\n"
                f"- Fatigue: **{int(avg_fatigue)}%**\n"
                f"- Screen Time: **{summary_data['screen_time_minutes']} min**"
            )
        else:
            reply = f"I'm having trouble connecting to AI right now. Your stats — **Distance:** {int(avg_dist)}cm | **Fatigue:** {int(avg_fatigue)}% | **Slouches:** {slouch_count}"
        chat_history_coll.insert_one({"user_id": session['user_id'], "role": "user", "text": user_msg, "time": time.time()})
        chat_history_coll.insert_one({"user_id": session['user_id'], "role": "assistant", "text": reply, "time": time.time()})
        return jsonify({"reply": reply})

    # -----------------------------
    # 5. Save to MongoDB & return
    # -----------------------------
    chat_history_coll.insert_one({"user_id": session['user_id'], "role": "user", "text": user_msg, "time": time.time()})
    chat_history_coll.insert_one({"user_id": session['user_id'], "role": "assistant", "text": reply, "time": time.time()})

    return jsonify({"reply": reply})

def start_server():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

@app.route("/api/switch-session", methods=["POST"])
@login_required
def switch_session():
    data = request.json
    target_username = data.get("username")
    
    if not target_username:
        return jsonify({"error": "Username required"}), 400
        
    # In a real app, we'd verify a persistent "machine token" or similar.
    # For this project, we'll allow switching between previously logged-in accounts.
    user = users.find_one({"username": target_username})
    if user:
        session['user_id'] = str(user['_id'])
        session['username'] = user['username']
        return jsonify({"success": True})
    
    return jsonify({"error": "User not found"}), 404

if __name__ == "__main__":
    start_server()