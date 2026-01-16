"""Stop local servers listening on common dev ports (8000, 8001).

Usage:
  python scripts/stop_servers.py        # prompts and kills processes on 8000 & 8001
  python scripts/stop_servers.py --yes  # do not prompt
  python scripts/stop_servers.py --ports 8000,8001  # custom ports

Cross-platform implementation:
- Windows: parses `netstat -ano` output and uses `taskkill /PID <pid> /F`
- Unix: tries `lsof -ti:<port>` then `kill -9 <pid>`

This is a minimal helper so you can quickly stop dev servers when ports are in use.
"""

from __future__ import annotations

import argparse
import platform
import re
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

DEFAULT_PORTS = (8000, 8001)


def _run(cmd: str) -> str:
    return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode(
        errors="ignore"
    )


def find_pids_on_port_unix(port: int) -> set[int]:
    try:
        out = _run(f"lsof -ti:{port}")
    except Exception:
        # fallback: try `ss -ltnp` parsing
        try:
            out = _run("ss -ltnp")
        except Exception:
            return set()
        else:
            pids: set[int] = set()
            # lines like: LISTEN 0 128 127.0.0.1:8000 *:* users:("python3",pid=12345,fd=3)
            for line in out.splitlines():
                if re.search(rf":{port}(?:\\s|$)", line):
                    m = re.search(r"pid=(\d+)", line)
                    if m:
                        pids.add(int(m.group(1)))
            return pids
    else:
        return {int(line.strip()) for line in out.splitlines() if line.strip()}


def find_pids_on_port_windows(port: int) -> set[int]:
    try:
        out = _run("netstat -ano")
    except Exception:
        return set()
    pids: set[int] = set()
    for line in out.splitlines():
        # Normalize whitespace
        parts = re.split(r"\s+", line.strip())
        if len(parts) < 5:
            continue
        # Local Address may be like 0.0.0.0:8000 or [::]:8000
        local_addr = parts[1]
        pid = parts[-1]
        if local_addr.endswith(f":{port}") and pid.isdigit():
            pids.add(int(pid))
    return pids


def kill_pid_unix(pid: int) -> bool:
    try:
        _run(f"kill -9 {pid}")
    except Exception:
        return False
    else:
        return True


def kill_pid_windows(pid: int) -> bool:
    try:
        _run(f"taskkill /PID {pid} /F")
    except Exception:
        return False
    else:
        return True


def find_and_kill_ports(ports: Iterable[int], yes: bool = False) -> list[str]:
    system = platform.system()
    results: list[str] = []

    for port in ports:
        if system == "Windows":
            pids = find_pids_on_port_windows(port)
        else:
            pids = find_pids_on_port_unix(port)

        if not pids:
            results.append(f"Port {port}: no process found")
            continue

        results.append(f"Port {port}: found PIDs {sorted(pids)}")
        if not yes:
            resp = (
                input(f"Kill processes on port {port} (pids={sorted(pids)})? [y/N]: ")
                .strip()
                .lower()
            )
            if resp not in ("y", "yes"):
                results.append(f"Port {port}: skipped by user")
                continue

        for pid in sorted(pids):
            ok = kill_pid_windows(pid) if system == "Windows" else kill_pid_unix(pid)
            results.append(f"PID {pid}: {'killed' if ok else 'failed to kill'}")
    return results


def parse_ports(value: str) -> list[int]:
    return [int(p.strip()) for p in value.split(",") if p.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Stop local dev servers by killing processes listening on ports"
    )
    parser.add_argument(
        "--ports",
        type=str,
        default=",".join(str(p) for p in DEFAULT_PORTS),
        help="Comma-separated ports to stop",
    )
    parser.add_argument(
        "--yes", action="store_true", help="Don't prompt, kill automatically"
    )
    args = parser.parse_args(argv)

    ports = parse_ports(args.ports)
    print(f"Stopping ports: {ports} (platform={platform.system()})")
    results = find_and_kill_ports(ports, yes=args.yes)
    for r in results:
        print(r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
