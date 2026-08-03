#!/usr/bin/env python3
"""Agent-facing checker and launcher for the separately installed workbench."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from typing import Any, Dict, List


INSTALL_COMMAND = (
    'uv tool install "git+https://github.com/noahnan-max/'
    'chanlun-trading-system.git@v0.1.1"'
)


def status_report() -> Dict[str, Any]:
    executable = shutil.which("chanlun-visual")
    return {
        "status": "available" if executable else "missing",
        "command": "chanlun-visual" if executable else None,
        "install_command": None if executable else INSTALL_COMMAND,
        "auto_install": False,
        "execution_allowed": False,
    }


def _print_report(report: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return
    print("Chanlun workbench: {}".format(report["status"]))
    if report["install_command"]:
        print("Install after user approval: {}".format(report["install_command"]))


def main() -> None:
    parser = argparse.ArgumentParser(description="检查或启动缠论可视研究工作台")
    parser.add_argument("command", choices=("check", "doctor", "launch"), nargs="?", default="check")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--port", type=int, default=8791)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    report = status_report()
    if args.command == "check":
        _print_report(report, args.json)
        raise SystemExit(0 if report["status"] == "available" else 2)
    if report["status"] != "available":
        _print_report(report, args.json)
        raise SystemExit(2)

    executable = shutil.which("chanlun-visual")
    if args.command == "doctor":
        command: List[str] = [executable or "chanlun-visual", "doctor"]
        if args.json:
            command.append("--json")
        raise SystemExit(subprocess.call(command))

    command = [executable or "chanlun-visual", "--host", "127.0.0.1", "--port", str(args.port)]
    if args.no_browser:
        command.append("--no-browser")
    os.execv(command[0], command)


if __name__ == "__main__":
    main()
