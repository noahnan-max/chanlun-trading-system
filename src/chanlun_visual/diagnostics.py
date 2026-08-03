"""Read-only installation diagnostics for the local workbench."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List

from . import __version__


def _check(name: str, status: str, detail: str, required: bool) -> Dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "required": required,
        "detail": detail,
    }


def doctor_report() -> Dict[str, Any]:
    """Return a path-safe, network-free installation report."""
    static = Path(__file__).resolve().parent / "static"
    index_ok = (static / "index.html").is_file()
    assets = static / "assets"
    asset_ok = assets.is_dir() and any(
        item.is_file() and item.suffix in {".css", ".js"} for item in assets.iterdir()
    )
    python_ok = sys.version_info >= (3, 9)
    market_ok = importlib.util.find_spec("yfinance") is not None

    checks: List[Dict[str, Any]] = [
        _check(
            "python",
            "pass" if python_ok else "fail",
            "Python {}.{}.{}; requires >=3.9".format(*sys.version_info[:3]),
            True,
        ),
        _check(
            "frontend_index",
            "pass" if index_ok else "fail",
            "bundled index.html is available" if index_ok else "bundled index.html is missing",
            True,
        ),
        _check(
            "frontend_assets",
            "pass" if asset_ok else "fail",
            "bundled CSS/JavaScript assets are available" if asset_ok else "bundled frontend assets are missing",
            True,
        ),
        _check(
            "local_bind_default",
            "pass",
            "default host is 127.0.0.1; network exposure requires an explicit override",
            True,
        ),
        _check(
            "market_adapter",
            "pass" if market_ok else "warn",
            "optional public-market adapter is installed"
            if market_ok
            else "optional public-market adapter is not installed; demo and CSV remain available",
            False,
        ),
    ]
    failed = any(item["required"] and item["status"] == "fail" for item in checks)
    warned = any(item["status"] == "warn" for item in checks)
    status = "fail" if failed else "pass_with_warnings" if warned else "pass"
    return {
        "status": status,
        "version": __version__,
        "execution_allowed": False,
        "network_checked": False,
        "checks": checks,
    }
