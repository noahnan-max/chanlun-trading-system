"""Deterministic Chanlun research-proxy engine with auditable evidence.

This module intentionally does not claim strict original-text equivalence and
does not produce executable trading instructions.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from . import __version__


class DataQualityError(ValueError):
    """Raised when OHLCV input cannot pass the fail-closed quality gate."""


def _number(value: Any, name: str, row: int, optional: bool = False) -> Any:
    if optional and (value is None or value == ""):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise DataQualityError("第 {} 行 {} 不是有效数字".format(row, name)) from exc
    if not math.isfinite(result):
        raise DataQualityError("第 {} 行 {} 不是有限数字".format(row, name))
    return result


def _parse_date(value: Any, row: int) -> Tuple[str, datetime]:
    raw = str(value or "").strip()
    if not raw:
        raise DataQualityError("第 {} 行缺少 date/time/datetime".format(row))
    normalized = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise DataQualityError("第 {} 行时间不是 ISO-8601: {}".format(row, raw)) from exc
    return raw, parsed


def normalize_bars(raw_bars: Sequence[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Normalize common OHLCV aliases and enforce a strict chronological gate."""
    if not raw_bars:
        raise DataQualityError("没有可分析的 K 线")
    bars: List[Dict[str, Any]] = []
    previous_time: Any = None
    volume_rows = 0
    for index, raw in enumerate(raw_bars):
        row = index + 1
        date, parsed = _parse_date(raw.get("date", raw.get("time", raw.get("datetime"))), row)
        if previous_time is not None and parsed <= previous_time:
            raise DataQualityError("时间必须严格递增；第 {} 行出现重复或倒序".format(row))
        previous_time = parsed
        open_ = _number(raw.get("open", raw.get("o")), "open", row)
        high = _number(raw.get("high", raw.get("h")), "high", row)
        low = _number(raw.get("low", raw.get("l")), "low", row)
        close = _number(raw.get("close", raw.get("c")), "close", row)
        volume = _number(raw.get("volume", raw.get("v")), "volume", row, optional=True)
        if min(open_, high, low, close) <= 0:
            raise DataQualityError("第 {} 行价格必须大于 0".format(row))
        if volume is not None and volume < 0:
            raise DataQualityError("第 {} 行成交量不能为负".format(row))
        if not (low <= min(open_, close) <= max(open_, close) <= high):
            raise DataQualityError("第 {} 行不满足 low <= open/close <= high".format(row))
        if volume is not None:
            volume_rows += 1
        bars.append(
            {
                "id": "bar:{}".format(index),
                "index": index,
                "date": date,
                "open": round(open_, 6),
                "high": round(high, 6),
                "low": round(low, 6),
                "close": round(close, 6),
                "volume": round(volume, 6) if volume is not None else None,
            }
        )
    coverage = volume_rows / len(bars)
    warnings = []
    if len(bars) < 30:
        warnings.append("少于 30 根 K 线，结构仅供预览")
    if coverage < 1:
        warnings.append("成交量覆盖率为 {:.1%}，量能证据可能不可用".format(coverage))
    return bars, {
        "status": "warn" if warnings else "pass",
        "row_count": len(bars),
        "volume_coverage": round(coverage, 4),
        "warnings": warnings,
    }


def _ema(values: Sequence[float], period: int) -> List[float]:
    factor = 2.0 / (period + 1)
    current = values[0]
    output = []
    for value in values:
        current = value * factor + current * (1 - factor)
        output.append(current)
    return output


def macd(closes: Sequence[float]) -> Dict[str, List[float]]:
    fast = _ema(closes, 12)
    slow = _ema(closes, 26)
    dif = [a - b for a, b in zip(fast, slow)]
    dea = _ema(dif, 9)
    hist = [(a - b) * 2 for a, b in zip(dif, dea)]
    return {
        "dif": [round(x, 6) for x in dif],
        "dea": [round(x, 6) for x in dea],
        "hist": [round(x, 6) for x in hist],
    }


def merge_inclusion(bars: Sequence[Dict[str, Any]], timeframe: str) -> List[Dict[str, Any]]:
    first = dict(bars[0])
    first.update({"id": "merged:{}:0".format(timeframe), "raw_start": 0, "raw_end": 0, "direction": "flat"})
    merged = [first]
    direction = "up"
    for raw_index, bar in enumerate(bars[1:], 1):
        last = merged[-1]
        contains = last["high"] >= bar["high"] and last["low"] <= bar["low"]
        contained = bar["high"] >= last["high"] and bar["low"] <= last["low"]
        if contains or contained:
            if direction == "up":
                last["high"] = max(last["high"], bar["high"])
                last["low"] = max(last["low"], bar["low"])
            else:
                last["high"] = min(last["high"], bar["high"])
                last["low"] = min(last["low"], bar["low"])
            last["close"] = bar["close"]
            last["date"] = bar["date"]
            if last["volume"] is None or bar["volume"] is None:
                last["volume"] = None
            else:
                last["volume"] = round(last["volume"] + bar["volume"], 6)
            last["raw_end"] = raw_index
            last["direction"] = direction
        else:
            direction = "up" if bar["high"] > last["high"] else "down"
            item = dict(bar)
            item.update(
                {
                    "id": "merged:{}:{}".format(timeframe, len(merged)),
                    "raw_start": raw_index,
                    "raw_end": raw_index,
                    "direction": direction,
                }
            )
            merged.append(item)
    return merged


def find_fractals(merged: Sequence[Dict[str, Any]], timeframe: str) -> List[Dict[str, Any]]:
    candidates = []
    for index in range(1, len(merged) - 1):
        before, current, after = merged[index - 1], merged[index], merged[index + 1]
        kind = None
        price = None
        if (
            current["high"] > before["high"]
            and current["high"] > after["high"]
            and current["low"] > before["low"]
            and current["low"] > after["low"]
        ):
            kind, price = "top", current["high"]
        elif (
            current["low"] < before["low"]
            and current["low"] < after["low"]
            and current["high"] < before["high"]
            and current["high"] < after["high"]
        ):
            kind, price = "bottom", current["low"]
        if kind:
            candidates.append(
                {
                    "kind": kind,
                    "merged_index": index,
                    "raw_index": current["raw_end"],
                    "price": price,
                    "confirmed_at": after["date"],
                    "available_at": after["date"],
                }
            )
    cleaned: List[Dict[str, Any]] = []
    for item in candidates:
        if cleaned and cleaned[-1]["kind"] == item["kind"]:
            more_extreme = (
                item["kind"] == "top" and item["price"] > cleaned[-1]["price"]
            ) or (item["kind"] == "bottom" and item["price"] < cleaned[-1]["price"])
            if more_extreme:
                cleaned[-1] = item
        else:
            cleaned.append(item)
    for index, item in enumerate(cleaned):
        item["id"] = "fractal:{}:{}".format(timeframe, index)
        item["price"] = round(item["price"], 6)
    return cleaned


def _linear_metrics(values: Sequence[float]) -> Dict[str, float]:
    size = len(values)
    if size < 2:
        return {"slope": 0.0, "rsq": 0.0, "snr": 0.0, "accel": 0.0}
    mean_x = (size - 1) / 2.0
    mean_y = sum(values) / size
    denominator = sum((x - mean_x) ** 2 for x in range(size)) or 1.0
    slope = sum((x - mean_x) * (value - mean_y) for x, value in enumerate(values)) / denominator
    fitted = [mean_y + slope * (x - mean_x) for x in range(size)]
    residual = sum((value - fit) ** 2 for value, fit in zip(values, fitted))
    total = sum((value - mean_y) ** 2 for value in values)
    rsq = 1 - residual / total if total else 1.0
    noise = math.sqrt(residual / size) if residual > 0 else 0.0
    snr = abs(slope) / noise if noise else abs(slope) * size
    midpoint = max(2, size // 2)
    first_slope = (values[midpoint - 1] - values[0]) / max(1, midpoint - 1)
    second_slope = (values[-1] - values[midpoint - 1]) / max(1, size - midpoint)
    return {
        "slope": round(slope, 6),
        "rsq": round(max(0.0, min(1.0, rsq)), 6),
        "snr": round(snr, 6),
        "accel": round(second_slope - first_slope, 6),
    }


def _stroke_power(
    bars: Sequence[Dict[str, Any]],
    raw_start: int,
    raw_end: int,
    direction: str,
    hist: Sequence[float],
) -> Dict[str, Any]:
    closes = [bar["close"] for bar in bars[raw_start : raw_end + 1]]
    metrics = _linear_metrics(closes)
    signed_hist = hist[raw_start : raw_end + 1]
    macd_area = sum(value for value in signed_hist if value > 0) if direction == "up" else abs(
        sum(value for value in signed_hist if value < 0)
    )
    volumes = [bar["volume"] for bar in bars[raw_start : raw_end + 1] if bar["volume"] is not None]
    start = closes[0]
    price_power = abs(closes[-1] - start) / start if start else 0.0
    return {
        "power_price": round(price_power, 6),
        "power_volume": round(sum(volumes), 6) if volumes else None,
        "macd_area": round(macd_area, 6),
        **metrics,
    }


def build_strokes(
    fractals: Sequence[Dict[str, Any]],
    merged: Sequence[Dict[str, Any]],
    bars: Sequence[Dict[str, Any]],
    hist: Sequence[float],
    timeframe: str,
    min_gap: int = 4,
) -> List[Dict[str, Any]]:
    if len(fractals) < 2:
        return []
    points = [fractals[0]]
    for item in fractals[1:]:
        last = points[-1]
        if item["kind"] == last["kind"]:
            more_extreme = (
                item["kind"] == "top" and item["price"] > last["price"]
            ) or (item["kind"] == "bottom" and item["price"] < last["price"])
            if more_extreme:
                points[-1] = item
        elif item["merged_index"] - last["merged_index"] >= min_gap:
            points.append(item)
    strokes = []
    for index, (start, end) in enumerate(zip(points, points[1:])):
        direction = "up" if start["kind"] == "bottom" else "down"
        raw_start = merged[start["merged_index"]]["raw_start"]
        raw_end = merged[end["merged_index"]]["raw_end"]
        strokes.append(
            {
                "id": "stroke:{}:{}".format(timeframe, index),
                "direction": direction,
                "start_fractal_id": start["id"],
                "end_fractal_id": end["id"],
                "start_index": start["raw_index"],
                "end_index": end["raw_index"],
                "start_price": start["price"],
                "end_price": end["price"],
                "raw_start": raw_start,
                "raw_end": raw_end,
                "confirmed_at": end["confirmed_at"],
                "available_at": end["available_at"],
                "power": _stroke_power(bars, raw_start, raw_end, direction, hist),
            }
        )
    return strokes


def build_segments(strokes: Sequence[Dict[str, Any]], timeframe: str) -> List[Dict[str, Any]]:
    """Build a deliberately conservative fixed-three-stroke segment proxy."""
    segments = []
    start = 0
    while start + 2 < len(strokes):
        group = list(strokes[start : start + 3])
        first, last = group[0], group[-1]
        segments.append(
            {
                "id": "segment:{}:{}".format(timeframe, len(segments)),
                "definition_mode": "segment_proxy",
                "method": "fixed_3_stroke_proxy",
                "direction": first["direction"],
                "stroke_ids": [item["id"] for item in group],
                "start_index": first["start_index"],
                "end_index": last["end_index"],
                "start_price": first["start_price"],
                "end_price": last["end_price"],
                "raw_start": first["raw_start"],
                "raw_end": last["raw_end"],
                "confirmed_at": last["confirmed_at"],
                "available_at": last["available_at"],
                "power": last["power"],
                "approximation_loss": [
                    "未实现特征序列分型递归",
                    "未区分线段破坏的第一/第二种情况",
                    "仅可作可视研究代理",
                ],
            }
        )
        start += 3
    return segments


def build_centers(items: Sequence[Dict[str, Any]], timeframe: str, unit_type: str) -> List[Dict[str, Any]]:
    centers = []
    for start in range(0, len(items) - 2):
        group = list(items[start : start + 3])
        highs = [max(item["start_price"], item["end_price"]) for item in group]
        lows = [min(item["start_price"], item["end_price"]) for item in group]
        zg, zd = min(highs), max(lows)
        if zd > zg:
            continue
        centers.append(
            {
                "id": "center:{}:{}:{}".format(timeframe, unit_type, len(centers)),
                "unit_type": unit_type,
                "component_ids": [item["id"] for item in group],
                "zd": round(zd, 6),
                "zg": round(zg, 6),
                "gg": round(max(highs), 6),
                "dd": round(min(lows), 6),
                "raw_start": group[0]["raw_start"],
                "raw_end": group[-1]["raw_end"],
                "confirmed_at": group[-1]["confirmed_at"],
                "available_at": group[-1]["available_at"],
                "definition_mode": "center_overlap_proxy",
                "approximation_loss": [] if unit_type == "stroke" else ["组成单元为 segment_proxy"],
            }
        )
    return centers


def _weaker(current: Any, previous: Any) -> Any:
    if current is None or previous in (None, 0):
        return None
    return current < previous * 0.9


def build_divergence(items: Sequence[Dict[str, Any]], timeframe: str) -> List[Dict[str, Any]]:
    if len(items) < 3:
        return []
    direction = items[-1]["direction"]
    same = [item for item in items if item["direction"] == direction]
    if len(same) < 2:
        return []
    previous, current = same[-2], same[-1]
    new_extreme = current["end_price"] > previous["end_price"] if direction == "up" else current["end_price"] < previous["end_price"]
    base_weaker = _weaker(current["power"]["macd_area"], previous["power"]["macd_area"])
    baseline_flag = bool(new_extreme and base_weaker)
    metric_names = ["power_price", "power_volume", "snr", "slope", "rsq", "accel"]
    votes = {}
    for name in metric_names:
        current_value = abs(current["power"].get(name)) if current["power"].get(name) is not None else None
        previous_value = abs(previous["power"].get(name)) if previous["power"].get(name) is not None else None
        votes[name] = _weaker(current_value, previous_value)
    available_votes = [value for value in votes.values() if value is not None]
    weak_votes = sum(1 for value in available_votes if value)
    u1_supports = bool(new_extreme and available_votes and weak_votes > len(available_votes) / 2)
    side = "bearish" if direction == "up" else "bullish"
    decision = "candidate" if baseline_flag else "not_present"
    return [
        {
            "id": "divergence:{}:0".format(timeframe),
            "direction": side,
            "unit_type": "segment_proxy" if current["id"].startswith("segment:") else "stroke",
            "compared_ids": [previous["id"], current["id"]],
            "new_extreme": new_extreme,
            "baseline": {
                "method": "same_direction_macd_area_10pct",
                "previous": previous["power"]["macd_area"],
                "current": current["power"]["macd_area"],
                "weaker": base_weaker,
                "supports_candidate": baseline_flag,
            },
            "u1": {
                "method": "multi_angle_majority_vote",
                "role": "optional_evidence_only",
                "votes": votes,
                "weaker_votes": weak_votes,
                "available_votes": len(available_votes),
                "supports_candidate": u1_supports,
            },
            "decision": decision,
            "confirmed_at": current["confirmed_at"],
            "available_at": current["available_at"],
            "invalidation": "后续走势不再创新极值，或力度衰减条件不成立",
        }
    ]


def _structure_state(
    bars: Sequence[Dict[str, Any]],
    strokes: Sequence[Dict[str, Any]],
    centers: Sequence[Dict[str, Any]],
) -> Tuple[str, Any, List[str]]:
    if len(bars) < 30:
        return "insufficient_history", None, ["补足至少 30 根同口径 K 线"]
    current_center = centers[-1] if centers else None
    close = bars[-1]["close"]
    if current_center:
        if current_center["zd"] <= close <= current_center["zg"]:
            state = "center_oscillation"
        elif close > current_center["zg"]:
            state = "trend_up"
        else:
            state = "trend_down"
    elif strokes:
        state = "trend_up" if strokes[-1]["direction"] == "up" else "trend_down"
    else:
        state = "unknown"
    invalidation = ["结构对象只在 available_at 之后可用", "线段与中枢为研究代理，不等同严格原著递归"]
    return state, current_center, invalidation


def analyze(
    raw_bars: Sequence[Dict[str, Any]],
    symbol: str = "LOCAL",
    timeframe: str = "1d",
    source: str = "user_csv",
) -> Dict[str, Any]:
    bars, quality = normalize_bars(raw_bars)
    canonical = json.dumps(bars, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    indicators = macd([bar["close"] for bar in bars])
    merged = merge_inclusion(bars, timeframe)
    fractals = find_fractals(merged, timeframe)
    strokes = build_strokes(fractals, merged, bars, indicators["hist"], timeframe)
    segments = build_segments(strokes, timeframe)
    center_units = segments if len(segments) >= 3 else strokes
    unit_type = "segment_proxy" if center_units is segments else "stroke"
    centers = build_centers(center_units, timeframe, unit_type)
    divergence_units = segments if len([item for item in segments if item["direction"] == (segments[-1]["direction"] if segments else None)]) >= 2 else strokes
    divergences = build_divergence(divergence_units, timeframe)
    structure, current_center, invalidation = _structure_state(bars, strokes, centers)
    candidate_signals = []
    if divergences and divergences[-1]["decision"] == "candidate":
        bullish = divergences[-1]["direction"] == "bullish"
        candidate_signals.append(
            {
                "id": "signal:{}:0".format(timeframe),
                "label": "一买候选" if bullish else "一卖候选",
                "kind": "B1_candidate" if bullish else "S1_candidate",
                "at_index": bars[-1]["index"],
                "price": bars[-1]["close"],
                "evidence_ids": [divergences[-1]["id"]],
                "status": "research_candidate",
                "action": "NO_ACTION",
            }
        )
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "meta": {
            "schema_version": "chanlun.analysis.v1",
            "engine_version": __version__,
            "symbol": symbol,
            "timeframe": timeframe,
            "generated_at": generated,
            "as_of": bars[-1]["date"],
            "source": source,
            "input_sha256": hashlib.sha256(canonical).hexdigest(),
            "definition_mode": "research_proxy",
            "execution_allowed": False,
        },
        "quality": quality,
        "bars": bars,
        "indicators": {"macd": indicators},
        "layers": {
            "merged_bars": merged,
            "fractals": fractals,
            "strokes": strokes,
            "segments": segments,
            "centers": centers,
            "divergences": divergences,
        },
        "state": {
            "structure": structure,
            "current_center_id": current_center["id"] if current_center else None,
            "candidate_signals": candidate_signals,
            "invalidation": invalidation,
            "execution_allowed": False,
        },
    }


def generate_demo_bars(count: int, step: timedelta, end: datetime) -> List[Dict[str, Any]]:
    """Create deterministic synthetic bars for UI/demo tests; never market facts."""
    bars = []
    previous = 82.0
    start = end - step * (count - 1)
    for index in range(count):
        regime = (index // 36) % 4
        drift = (0.045, -0.02, 0.065, -0.05)[regime]
        wave = 3.8 * math.sin(index / 5.6) + 1.7 * math.sin(index / 14.0)
        close = 82.0 + drift * (index % 36) + wave + index * 0.012
        open_ = previous + 0.45 * math.sin(index / 3.1)
        high = max(open_, close) + 0.7 + 0.25 * abs(math.sin(index))
        low = min(open_, close) - 0.7 - 0.22 * abs(math.cos(index))
        volume = 820000 + 180000 * (1 + math.sin(index / 6.2)) + regime * 65000
        at = start + step * index
        bars.append(
            {
                "date": at.isoformat(),
                "open": round(open_, 3),
                "high": round(high, 3),
                "low": round(low, 3),
                "close": round(close, 3),
                "volume": round(volume),
            }
        )
        previous = close
    return bars


def demo_bundle(symbol: str = "DEMO") -> Dict[str, Any]:
    end = datetime(2026, 7, 31, 15, 0)
    specs = {
        "1d": (180, timedelta(days=1)),
        "60m": (240, timedelta(minutes=60)),
        "30m": (280, timedelta(minutes=30)),
        "5m": (360, timedelta(minutes=5)),
    }
    return {
        "symbol": symbol,
        "source": "bundled_synthetic_demo",
        "is_synthetic": True,
        "frames": {
            timeframe: analyze(generate_demo_bars(count, step, end), symbol, timeframe, "bundled_synthetic_demo")
            for timeframe, (count, step) in specs.items()
        },
    }
