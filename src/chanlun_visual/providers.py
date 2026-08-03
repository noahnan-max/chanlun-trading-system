"""Optional public-market adapter. CSV remains the canonical offline path."""

from __future__ import annotations

import re
from typing import Any, Dict, List


SYMBOL = re.compile(r"^[A-Za-z0-9.=_^-]{1,24}$")


def canonical_symbol(symbol: str) -> str:
    """Map common bare Greater-China codes to public-provider notation."""
    clean = symbol.strip().upper()
    if not SYMBOL.fullmatch(clean):
        raise ValueError("证券代码格式无效")
    if re.fullmatch(r"\d{6}", clean):
        if clean.startswith(("4", "8", "92")):
            return clean + ".BJ"
        if clean.startswith(("5", "6", "9")):
            return clean + ".SS"
        return clean + ".SZ"
    if re.fullmatch(r"\d{4,5}", clean):
        return clean.zfill(4) + ".HK"
    return clean


def yfinance_bars(symbol: str, timeframe: str) -> List[Dict[str, Any]]:
    symbol = canonical_symbol(symbol)
    mapping = {
        "1d": ("2y", "1d"),
        "60m": ("3mo", "60m"),
        "30m": ("1mo", "30m"),
        "5m": ("5d", "5m"),
    }
    if timeframe not in mapping:
        raise ValueError("不支持的周期")
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError("未安装公开行情扩展；请运行 pip install 'chanlun-visual[market]'") from exc
    period, interval = mapping[timeframe]
    frame = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=False)
    if frame.empty:
        raise RuntimeError("公开行情源没有返回数据")
    bars = []
    for at, row in frame.iterrows():
        bars.append(
            {
                "date": at.isoformat(),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": float(row["Volume"]) if row.get("Volume") is not None else None,
            }
        )
    return bars
