from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import shutil
import time
import os
import universal_scrubber  # your existing file
import sqlite3

app = FastAPI(title="Metadata Scrubbing Proxy")

OUTBOX = Path("outbox")
DB_PATH = "proxy_logs.db"
OUTBOX.mkdir(exist_ok=True)

# Initialize DB
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        scrubbed_file TEXT,
        action TEXT,
        timestamp INTEGER
    )''')
    conn.commit()
    conn.close()

init_db()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), forward_url: str = Form(None)):
    # Save temp file
    temp_path = OUTBOX / f"temp_{int(time.time())}_{file.filename}"
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Scrub
    universal_scrubber.detect_and_scrub(temp_path)
    scrubbed_path = temp_path.with_name(f"scrubbed_{temp_path.name}")

    # Log
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO logs (filename, scrubbed_file, action, timestamp) VALUES (?,?,?,?)",
              (file.filename, str(scrubbed_path), "scrubbed", int(time.time())))
    conn.commit()
    conn.close()

    return {
        "status": "ok",
        "original": file.filename,
        "scrubbed": str(scrubbed_path),
        "download_url": f"/download/{scrubbed_path.name}"
    }

@app.get("/download/{fname}")
async def download(fname: str):
    path = OUTBOX / fname
    if path.exists():
        return FileResponse(path)
    return JSONResponse({"error": "not found"}, status_code=404)

@app.get("/logs")
async def get_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, filename, scrubbed_file, action, timestamp FROM logs ORDER BY id DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    return {"logs": rows}
