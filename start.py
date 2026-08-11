#!/usr/bin/env python3
"""
Cozy AI Productivity System — One-Command System Launcher

Starts the full development system:
1. Validates setup (runs `setup.py` if environment is missing)
2. Starts FastAPI backend server on http://127.0.0.1:8000
3. Starts React Vite frontend dev server on http://localhost:3000
4. Waits for backend health checks
5. Automatically opens http://localhost:3000 in your web browser
6. Handles graceful shutdown on Ctrl+C
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

# Safe Unicode output for Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
IS_WINDOWS = os.name == "nt"


def print_banner():
    print("=" * 60)
    print(" Cozy AI Productivity System -- System Launcher")
    print("=" * 60)


def get_venv_python() -> Path:
    if IS_WINDOWS:
        return BACKEND_DIR / "venv" / "Scripts" / "python.exe"
    return BACKEND_DIR / "venv" / "bin" / "python"


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0


def check_and_run_setup():
    venv_python = get_venv_python()
    node_modules = FRONTEND_DIR / "node_modules"

    if not venv_python.exists() or not node_modules.exists():
        print("  [WARN] Environment setup incomplete. Running `setup.py` first...\n")
        setup_script = ROOT_DIR / "setup.py"
        subprocess.check_call([sys.executable, str(setup_script)])


def wait_for_backend(url: str = "http://127.0.0.1:8000/health/live", timeout: float = 30.0):
    print("  Waiting for backend API server to become ready...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2.0) as response:
                if response.status == 200:
                    print("  [OK] Backend API server is online!")
                    return True
        except Exception:
            time.sleep(1.0)
    print("  [WARN] Backend health check timed out. Proceeding anyway...")
    return False


def start_system():
    print_banner()
    check_and_run_setup()

    # Port checks
    if is_port_in_use(8000):
        print("  [WARN] Port 8000 is already in use. Backend might fail to bind.")
    if is_port_in_use(3000):
        print("  [WARN] Port 3000 is already in use. Frontend may use an alternate port.")

    venv_python = get_venv_python()
    npm_cmd = shutil.which("npm") or shutil.which("npm.cmd") or "npm"

    processes: list[subprocess.Popen] = []

    try:
        # Start Backend Server
        print("\n[LAUNCH] Starting FastAPI Backend Server (http://127.0.0.1:8000)...")
        backend_proc = subprocess.Popen(
            [str(venv_python), "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
            cwd=str(BACKEND_DIR),
        )
        processes.append(backend_proc)

        # Wait for backend health
        wait_for_backend()

        # Start Frontend Dev Server
        print("\n[LAUNCH] Starting React Vite Frontend Server (http://localhost:3000)...")
        frontend_proc = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=str(FRONTEND_DIR),
            shell=IS_WINDOWS,
        )
        processes.append(frontend_proc)

        print("\n" + "=" * 60)
        print(" [SUCCESS] Cozy AI System is running!")
        print(" App URL:     http://localhost:3000")
        print(" API Docs:    http://127.0.0.1:8000/docs")
        print(" Press Ctrl+C to stop all servers gracefully.")
        print("=" * 60 + "\n")

        # Open web browser automatically
        time.sleep(2.0)
        webbrowser.open("http://localhost:3000")

        # Keep main thread alive monitoring child processes
        while True:
            for p in processes:
                if p.poll() is not None:
                    print(f"  [WARN] Process {p.args} exited with code {p.returncode}")
            time.sleep(2.0)

    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Stopping Cozy AI System...")
    finally:
        for p in processes:
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=3.0)
                except subprocess.TimeoutExpired:
                    p.kill()
        print("  [OK] All servers stopped cleanly. Goodbye!")


if __name__ == "__main__":
    start_system()
