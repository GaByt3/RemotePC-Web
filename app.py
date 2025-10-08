# app.py
import io
import time
import uuid
import base64
import threading
import subprocess
from functools import wraps

import mss
from PIL import Image
import pyautogui
import qrcode
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Replace with your domain or localhost

# ------------------------------
# Screen settings
# ------------------------------
monitor_index = 1
monitor_count = len(mss.mss().monitors) - 1  # ignore monitor 0 (all screens)

# ------------------------------
# Session and token control
# ------------------------------
TOKEN = uuid.uuid4().hex          # single-use token
TOKEN_VALID = True
SESSION_ACTIVE = False
AUTHORIZED_SIDS = set()
AUTHORIZED_IPS = set()
auth_lock = threading.Lock()


# ------------------------------
# Decorators
# ------------------------------
def require_session(f):
    """Ensures the route is accessed only by IPs with an active session."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        client_ip = request.remote_addr
        with auth_lock:
            if not SESSION_ACTIVE or client_ip not in AUTHORIZED_IPS:
                return jsonify(success=False, error="Session active by another user or unauthorized IP"), 401
        return f(*args, **kwargs)
    return wrapped


# ------------------------------
# Main functions
# ------------------------------
def capture_screen():
    """Capture frames from the selected monitor and send them to authorized clients via Socket.IO."""
    global monitor_index
    with mss.mss() as sct:
        while True:
            monitor = sct.monitors[monitor_index]
            img = sct.grab(monitor)
            im = Image.frombytes("RGB", img.size, img.rgb)

            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=70)
            frame_b64 = base64.b64encode(buf.getvalue()).decode('ascii')

            with auth_lock:
                sids = list(AUTHORIZED_SIDS)

            for sid in sids:
                try:
                    socketio.emit('frame', frame_b64, room=sid)
                except Exception:
                    with auth_lock:
                        AUTHORIZED_SIDS.discard(sid)

            time.sleep(0.05)


def generate_qr(url: str) -> str:
    """Generate a QR code as a data URI from a URL."""
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"


# ------------------------------
# Flask routes
# ------------------------------
@app.route("/")
def index():
    host_url = request.host_url.rstrip('/')
    connect_url = f"{host_url}/?token={TOKEN}"
    qr_data_uri = generate_qr(connect_url)
    with auth_lock:
        token_valid = TOKEN_VALID
        session_active = SESSION_ACTIVE
    return render_template(
        "index.html",
        monitor_count=monitor_count,
        current_monitor=monitor_index,
        qr_data_uri=qr_data_uri,
        connect_url=connect_url,
        token_valid=token_valid,
        session_active=session_active,
        token_preview=TOKEN[:8],
        authorized_ips=list(AUTHORIZED_IPS)
    )


@app.route("/click", methods=["POST"])
@require_session
def click():
    """Click on a relative position on the active monitor."""
    data = request.json
    x, y = data["x"], data["y"]
    width, height = data["width"], data["height"]
    button = data.get("button", "left")

    with mss.mss() as sct:
        mon = sct.monitors[monitor_index]
        screen_x = int(mon["left"] + (x / width) * mon["width"])
        screen_y = int(mon["top"] + (y / height) * mon["height"])

    pyautogui.click(screen_x, screen_y, button=button)
    return jsonify(success=True)


@app.route("/set_monitor", methods=["POST"])
@require_session
def set_monitor():
    """Set which monitor will be captured."""
    global monitor_index
    idx = int(request.json.get("monitor", 1))
    if 1 <= idx <= monitor_count:
        monitor_index = idx
        return jsonify(success=True)
    return jsonify(success=False), 400


@app.route("/type_text", methods=["POST"])
@require_session
def type_text():
    """Type text in the system, optionally sending Enter."""
    data = request.json
    text = data.get("text", "")
    press_enter = data.get("enter", True)

    if text:
        pyautogui.typewrite(text)
        if press_enter:
            pyautogui.press('enter')
        return jsonify(success=True)

    return jsonify(success=False), 400


@app.route("/cmd", methods=["POST"])
@require_session
def cmd():
    """Execute shell commands on the server and return stdout + stderr."""
    command = request.json.get("command", "")
    if not command or command.lower() == "cmd":
        return jsonify(success=False, output="Invalid command")

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return jsonify(success=True, output=result.stdout + result.stderr)
    except Exception as e:
        return jsonify(success=False, output=str(e))


@app.route("/type_key", methods=["POST"])
@require_session
def type_key():
    """Press a key or key combination."""
    keys = request.json.get("keys", [])
    if not keys:
        return jsonify(success=False, error="No keys sent")

    try:
        if len(keys) == 1:
            pyautogui.press(keys[0])
        else:
            pyautogui.hotkey(*keys)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))


# ------------------------------
# Socket.IO Events
# ------------------------------
@socketio.on('connect')
def handle_connect():
    """Validate single-use token and start session for the authorized IP."""
    global TOKEN_VALID, SESSION_ACTIVE
    token = request.args.get('token')
    sid = request.sid
    client_ip = request.remote_addr

    with auth_lock:
        if SESSION_ACTIVE or token != TOKEN:
            return False

        TOKEN_VALID = False
        SESSION_ACTIVE = True
        AUTHORIZED_SIDS.add(sid)
        AUTHORIZED_IPS.add(client_ip)

    print(f"[INFO] Authorized session started (sid={sid}, ip={client_ip})")

    # notify client to update UI (hide QR)
    socketio.emit('session_started', room=sid)


@socketio.on('disconnect')
def handle_disconnect():
    """End session when the client disconnects."""
    global SESSION_ACTIVE
    sid = request.sid
    with auth_lock:
        AUTHORIZED_SIDS.discard(sid)
        SESSION_ACTIVE = False
    print(f"[INFO] Session disconnected (sid={sid})")


# ------------------------------
# Startup
# ------------------------------
if __name__ == '__main__':
    threading.Thread(target=capture_screen, daemon=True).start()
    print(f"[INFO] Single-use token: {TOKEN} (DEBUG console)")
    print("[INFO] Open / in the browser on the PC or scan the QR code.")
    socketio.run(app, host="0.0.0.0", port=5000)
