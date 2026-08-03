"""Console entry point."""

from __future__ import annotations

import argparse
import json
import threading
import webbrowser

import uvicorn

from . import __version__
from .diagnostics import doctor_report


def _print_doctor_human(report: dict) -> None:
    print("Chanlun Visual doctor: {}".format(report["status"]))
    print("version: {}".format(report["version"]))
    for item in report["checks"]:
        print("[{status}] {name}: {detail}".format(**item))


def main() -> None:
    parser = argparse.ArgumentParser(description="启动本地缠论可视研究工作台")
    parser.add_argument("command", nargs="?", choices=("serve", "doctor"), default="serve")
    parser.add_argument("--version", action="version", version="%(prog)s {}".format(__version__))
    parser.add_argument("--host", default="127.0.0.1", help="默认仅绑定本机")
    parser.add_argument("--port", default=8791, type=int)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--json", action="store_true", help="doctor 使用 JSON 输出")
    args = parser.parse_args()
    if args.command == "doctor":
        report = doctor_report()
        if args.json:
            print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        else:
            _print_doctor_human(report)
        if report["status"] == "fail":
            raise SystemExit(1)
        return
    url = "http://{}:{}".format(args.host, args.port)
    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    uvicorn.run("chanlun_visual.api:app", host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
