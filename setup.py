#!/usr/bin/env python3
"""
Cozy AI Productivity System — Setup Script

Automates environment setup:
1. Validates Python (>= 3.11) and Node.js (>= 18)
2. Creates Python virtual environment (`backend/venv`)
3. Installs backend dependencies
4. Copies `.env.example` to `.env` if missing
5. Runs database migrations (`alembic upgrade head`)
6. Installs frontend dependencies (`npm install`)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
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
    print(" Cozy AI Productivity System -- Project Setup")
    print("=" * 60)


def check_requirements():
    print("\n[Step 1/5] Checking system prerequisites...")

    # Python version check
    py_ver = sys.version_info
    if py_ver < (3, 11):
        print(f"❌ Error: Python 3.11+ is required. Found Python {py_ver.major}.{py_ver.minor}.")
        sys.exit(1)
    print(f"  [OK] Python {py_ver.major}.{py_ver.minor}.{py_ver.micro}")

    # Node.js check
    node_cmd = shutil.which("node")
    if not node_cmd:
        print("❌ Error: Node.js is not installed or not in PATH.")
        sys.exit(1)
    try:
        node_ver = subprocess.check_output([node_cmd, "--version"], text=True).strip()
        print(f"  [OK] Node.js {node_ver}")
    except Exception:
        print("  [WARN] Could not determine Node.js version.")

    # npm check
    npm_cmd = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm_cmd:
        print("❌ Error: npm is not installed or not in PATH.")
        sys.exit(1)
    try:
        npm_ver = subprocess.check_output([npm_cmd, "--version"], text=True).strip()
        print(f"  [OK] npm {npm_ver}")
    except Exception:
        print("  [WARN] Could not determine npm version.")


def get_venv_python() -> Path:
    if IS_WINDOWS:
        return BACKEND_DIR / "venv" / "Scripts" / "python.exe"
    return BACKEND_DIR / "venv" / "bin" / "python"


def get_venv_alembic() -> Path:
    if IS_WINDOWS:
        return BACKEND_DIR / "venv" / "Scripts" / "alembic.exe"
    return BACKEND_DIR / "venv" / "bin" / "alembic"


def setup_backend_venv():
    print("\n[Step 2/5] Setting up Python Virtual Environment...")
    venv_dir = BACKEND_DIR / "venv"
    venv_python = get_venv_python()

    if not venv_python.exists():
        print(f"  Creating venv at {venv_dir}...")
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
        print("  [OK] Virtual environment created.")
    else:
        print("  [OK] Virtual environment already exists.")

    print("  Upgrading pip...")
    subprocess.check_call([str(venv_python), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])

    print("  Installing backend dependencies...")
    requirements_file = BACKEND_DIR / "requirements.txt"
    subprocess.check_call(
        [str(venv_python), "-m", "pip", "install", "-r", str(requirements_file), "pytest", "ruff", "mypy"],
        cwd=str(BACKEND_DIR),
    )
    print("  [OK] Backend dependencies installed.")


def setup_environment_file():
    print("\n[Step 3/5] Checking environment configuration...")
    env_file = ROOT_DIR / ".env"
    env_example = ROOT_DIR / ".env.example"

    if not env_file.exists():
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print("  [OK] Created `.env` from `.env.example`.")
        else:
            print("  [WARN] `.env.example` not found; skipping `.env` creation.")
    else:
        print("  [OK] `.env` file already exists.")


def run_database_migrations():
    print("\n[Step 4/5] Running database migrations...")
    venv_python = get_venv_python()
    venv_alembic = get_venv_alembic()

    try:
        if venv_alembic.exists():
            subprocess.check_call([str(venv_alembic), "upgrade", "head"], cwd=str(BACKEND_DIR))
        else:
            subprocess.check_call([str(venv_python), "-m", "alembic", "upgrade", "head"], cwd=str(BACKEND_DIR))
        print("  [OK] Database schema is up to date.")
    except Exception as exc:
        print(f"  [WARN] Alembic migration note: {exc}")


def setup_frontend():
    print("\n[Step 5/5] Installing frontend dependencies...")
    npm_cmd = shutil.which("npm") or shutil.which("npm.cmd") or "npm"
    subprocess.check_call([npm_cmd, "install"], cwd=str(FRONTEND_DIR), shell=IS_WINDOWS)
    print("  [OK] Frontend dependencies installed.")


def main():
    print_banner()
    check_requirements()
    setup_backend_venv()
    setup_environment_file()
    run_database_migrations()
    setup_frontend()

    print("\n" + "=" * 60)
    print(" [SUCCESS] Setup completed successfully!")
    print(" To start the application, run:")
    print("    python start.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
