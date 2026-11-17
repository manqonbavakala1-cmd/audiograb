import os
import threading
import uuid
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory, render_template

from audiograb.downloader import download, ffmpeg_available
from audiograb.tagger import tag
from audiograb.utils import ensure_dir

app = Flask(__name__)
BASE = Path(__file__).parent
DOWNLOADS_DIR = BASE / "downloads"
ensure_dir(DOWNLOADS_DIR)

# Real-time in-memory task tracker
tasks_db = {}

def process_download_task(task_id, query):
    tasks_db[task_id]["status"] = "PROCESSING"
    
    def cb(pct):
        # Scale download to 90% (reserve 10% for tagging)
        real_pct = int(pct * 0.9)
        if real_pct > tasks_db[task_id]["progress"]:
            tasks_db[task_id]["progress"] = real_pct

    try:
        results = download(query, DOWNLOADS_DIR, "320", progress_callback=cb)
    except Exception as e:
        tasks_db[task_id]["status"] = "FAILED"
        tasks_db[task_id]["error"] = str(e)
        return

    if not results:
        tasks_db[task_id]["status"] = "FAILED"
        tasks_db[task_id]["error"] = "No results found."
        return

    r = results[0]
    path = Path(r["file_path"])
    if not path.exists() or path.stat().st_size == 0:
        tasks_db[task_id]["status"] = "FAILED"
        tasks_db[task_id]["error"] = "Downloaded file missing or empty."
        return

    tasks_db[task_id]["title"] = r["title"]
    tasks_db[task_id]["status"] = "TAGGING"
    tasks_db[task_id]["progress"] = 95
    
    try:
        tag(r["file_path"], r["title"], r["artist"], None, track=r.get("track"))
    except Exception as e:
        tasks_db[task_id]["status"] = "FAILED"
        tasks_db[task_id]["error"] = f"Tagging error: {e}"
        return

    tasks_db[task_id]["status"] = "SUCCESS"
    tasks_db[task_id]["progress"] = 100
    tasks_db[task_id]["filename"] = path.name

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {"status": "PENDING", "progress": 0, "query": url, "title": "Extracting metadata..."}
    
    threading.Thread(target=process_download_task, args=(task_id, url), daemon=True).start()
    
    return jsonify({"task_id": task_id}), 202

@app.route("/api/status/<task_id>")
def api_status(task_id):
    t = tasks_db.get(task_id)
    if not t:
        return jsonify({"error": "not found"}), 404
    return jsonify(t)

@app.route("/api/downloads/<path:filename>")
def serve_download(filename):
    return send_from_directory(str(DOWNLOADS_DIR), filename, as_attachment=True)

if __name__ == "__main__":
    if not ffmpeg_available():
        print("WARNING: ffmpeg not found in local folder or PATH.")
    app.run(port=5000, debug=True, use_reloader=False)