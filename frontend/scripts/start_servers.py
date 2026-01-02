"""start_servers.py
Small Python helper to start backend and frontend for Playwright's webServer.
- Probes ports and only starts services whose ports are closed
- Starts processes using the same Python interpreter
- Waits for HTTP readiness on both URLs
- Keeps processes running until signaled

Usage: python start_servers.py
Environment variables:
  FRONTEND_PLAYWRIGHT_PORT / FRONTEND_PORT (default 8001)
  BACKEND_PORT (default 8000)
  FRONTEND_BASE_URL / BACKEND_BASE_URL (optional)

Note: This script uses only the Python standard library.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from urllib.request import Request, urlopen

FRONTEND_PORT = int(
    os.environ.get("FRONTEND_PLAYWRIGHT_PORT")
    or os.environ.get("FRONTEND_PORT")
    or 8001
)
BACKEND_PORT = int(os.environ.get("BACKEND_PORT") or 8000)
FRONTEND_URL = (
    os.environ.get("FRONTEND_BASE_URL") or f"http://127.0.0.1:{FRONTEND_PORT}"
)
BACKEND_URL = (
    os.environ.get("BACKEND_BASE_URL") or f"http://127.0.0.1:{BACKEND_PORT}/health"
)

PYTHON = (
    os.environ.get("PYTHON") or sys.executable or "python"
)  # allow overriding the interpreter with env var for CI/Playwright

FRONTEND_CWD = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)  # frontend root
# Repo root is one level above the frontend root
REPO_ROOT = os.path.abspath(os.path.join(FRONTEND_CWD, ".."))


SPAWNED: list[subprocess.Popen[bytes]] = []


def is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        try:
            return s.connect_ex((host, port)) == 0
        except Exception:
            return False


def start_backend() -> subprocess.Popen[bytes] | None:
    if is_port_open("127.0.0.1", BACKEND_PORT):
        print(f"Backend port {BACKEND_PORT} open; not starting backend.")
        return None
    print("Starting backend...")
    uv_path = shutil.which("uv")
    if uv_path:
        cmd = [
            uv_path,
            "run",
            "--project",
            REPO_ROOT,
            "python",
            "-m",
            "d3_item_salvager",
            "api",
        ]
    else:
        cmd = [PYTHON, "-m", "d3_item_salvager", "api"]
    print(f"Using command: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr, cwd=REPO_ROOT)
    SPAWNED.append(proc)
    return proc


def start_frontend() -> subprocess.Popen[bytes] | None:
    if is_port_open("127.0.0.1", FRONTEND_PORT):
        print(f"Frontend port {FRONTEND_PORT} open; not starting frontend.")
        return None
    print("Starting frontend...")
    uv_path = shutil.which("uv")
    if uv_path:
        cmd = [
            uv_path,
            "run",
            "--project",
            REPO_ROOT,
            "python",
            "-m",
            "flask",
            "--app",
            "app:create_app",
            "run",
            "--port",
            str(FRONTEND_PORT),
        ]
    else:
        cmd = [
            PYTHON,
            "-m",
            "flask",
            "--app",
            "app:create_app",
            "run",
            "--port",
            str(FRONTEND_PORT),
        ]
    print(f"Using command: {' '.join(cmd)}")
    proc = subprocess.Popen(
        cmd,
        cwd=FRONTEND_CWD,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    SPAWNED.append(proc)
    return proc


def wait_for_url(url: str, timeout_sec: int = 5) -> None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            req = Request(url, method="GET")
            with urlopen(req, timeout=2) as resp:  # type: ignore
                if resp.status == 200:
                    return
        except Exception:
            pass
        time.sleep(0.5)
    msg = f"Timed out waiting for {url}"
    raise RuntimeError(msg)


def shutdown(signal_received: int | None, _frame: object | None) -> None:
    print(f"Received signal {signal_received}; shutting down children")
    for p in SPAWNED:
        with contextlib.suppress(Exception):
            p.terminate()  # polite

    # give them a second
    time.sleep(1)
    for p in SPAWNED:
        if p.poll() is None:
            with contextlib.suppress(Exception):
                p.kill()
    sys.exit(0)


def main() -> None:
    print("start_servers.py: beginning startup")
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    backend_proc = start_backend()
    frontend_proc = start_frontend()

    started_ok = False
    try:
        print(f"Waiting for backend at {BACKEND_URL}...")
        wait_for_url(BACKEND_URL, timeout_sec=10)
        print("Backend is up.")

        print(f"Waiting for frontend at {FRONTEND_URL}...")
        wait_for_url(FRONTEND_URL, timeout_sec=10)
        print("Frontend is up.")

        started_ok = True
    except Exception:
        print("Error during startup; shutting down spawned processes.", file=sys.stderr)
        raise
    finally:
        if not started_ok:
            # Ensure any processes we started are terminated
            for p in (backend_proc, frontend_proc):
                if p is None:
                    continue
                with contextlib.suppress(Exception):
                    p.terminate()

            # give them a second
            time.sleep(1)
            for p in (backend_proc, frontend_proc):
                if p is None:
                    continue
                if p.poll() is None:
                    with contextlib.suppress(Exception):
                        p.kill()

    print("Both servers are ready. Sleeping until signalled.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown(None, None)


if __name__ == "__main__":
    main()
