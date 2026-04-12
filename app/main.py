from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

import time
import threading
from pathlib import Path
from contextlib import asynccontextmanager

load_dotenv()

from app.api.routes import router

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)


# CLEANUP WORKER
def cleanup_old_files():
    print("[CLEANUP] Worker started")

    while True:
        print("[CLEANUP] Scanning...")

        try:
            now = time.time()
            for file in DOWNLOAD_DIR.iterdir():
                if not file.is_file():
                    continue

                # SKIP FILE THAT IS STILL DOWNLOADING
                if file.suffix in [".part", ".ytdl", ".temp"]:
                    continue

                age = now - file.stat().st_mtime
                print(f"[CLEANUP] {file} age: {age}")

                if age > 1800:
                    file.unlink()
                    print(f"[CLEANUP] Deleted: {file}")

        except Exception as e:
            print(f"[CLEANUP ERROR] {e}")

        time.sleep(300)

# LIFESPAN HANDLER (REPLACEMENT)
@asynccontextmanager
async def lifespan(app: FastAPI):
    #  startup
    thread = threading.Thread(target=cleanup_old_files, daemon=True)
    thread.start()
    print("[SYSTEM] Cleanup worker started")

    yield

    #  shutdown (optional)
    print("[SYSTEM] App shutting down...")


# APP INIT
app = FastAPI(
    title="Video Downloader API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://*.vercel.app",
        os.getenv("FRONTEND_URL", "*")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)