import threading
from flask import Flask, render_template, request, redirect, url_for, jsonify
from bot import MonitorBot
from utils import CONFIG, save_config

app = Flask(__name__)

LOCK = threading.Lock()
BOT = MonitorBot()


def start_bot():
    """Start bot if not already running."""
    with LOCK:
        if BOT.status in (
            "starting",
            "running",
            "stopping",
            "crashed",
        ):
            return False
        BOT.start()
        return True


@app.route("/")
def home():
    "Render home page"
    return render_template(
        "index.html",
        config=CONFIG,
        bot_status=BOT.status,
    )


@app.route("/status")
def status():
    "Return bot status as JSON"
    return jsonify({"status": BOT.status})


@app.route("/start", methods=["POST"])
def start():
    "Start the bot"
    print("Starting the bot")
    start_bot()
    return jsonify({"success": True, "status": BOT.status})


@app.route("/stop", methods=["POST"])
def stop():
    "Stop the bot"
    BOT.stop()
    return jsonify({"success": True, "status": BOT.status})


@app.route("/save", methods=["POST"])
def save():
    "Save configuration from form data"
    config = {
        "requests": {
            "timeout": int(request.form["timeout"]),
            "max_concurrent_requests": int(request.form["max_concurrent_requests"]),
            "recheck_interval": int(request.form["recheck_interval"]),
            "max_retries": int(request.form["max_retries"]),
            "retry_delay": int(request.form["retry_delay"]),
        },
        "targeted_website": {
            "endpoint": request.form["appointment_slot_endpoint"],
            "auth_token": request.form["auth_token"],
        },
        "proxy": {
            "http": request.form["proxy_http"],
            "https": request.form["proxy_https"],
        },
        "telegram": {
            "bot_token": request.form["bot_token"],
            "dev_chat_id": request.form["dev_chat_id"],
            "users_chat_ids": [
                x.strip()
                for x in request.form["users_chat_ids"].split(",")
                if x.strip()
            ],
        },
        "dates": [x.strip() for x in request.form["dates"].split(",") if x.strip()],
        "date_range": {
            "enabled": request.form.get("date_range_enabled") == "on",
            "start": request.form["date_range_start"],
            "end": request.form["date_range_end"],
        },
    }
    CONFIG.clear()
    CONFIG.update(config)

    save_config(config)

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
