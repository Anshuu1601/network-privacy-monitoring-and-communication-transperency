"""One-command launcher for the full project.

Usage:
    python start.py            # starts backend only
    python start.py --frontend # also starts the frontend dev server
"""
import argparse
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def run_backend():
    print("Starting backend on http://127.0.0.1:8000 ...")
    subprocess.call([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"], cwd=BASE / "backend")


def run_frontend():
    print("Starting frontend dev server ...")
    subprocess.call(["npm", "run", "dev"], cwd=BASE / "frontend")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Network Privacy Monitor launcher")
    parser.add_argument("--frontend", action="store_true", help="Also launch the React frontend")
    args = parser.parse_args()

    if args.frontend:
        import threading

        t = threading.Thread(target=run_frontend, daemon=True)
        t.start()
        run_backend()
    else:
        run_backend()