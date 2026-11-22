from __future__ import annotations

import random
from datetime import datetime, timedelta

from chanlun_visual.engine import analyze, build_centers


def unit(uid: str, start: float, end: float, order: int):
    """最小可用组成单元：只需 build_centers 读取的字段。"""
    return {
        "id": uid,
        "start_price": start,
        "end_price": end,
        "raw_start": order * 10,
        "raw_end": order * 10 + 9,
        "confirmed_at": "2026-07-31T15:00:00",
        "available_at": "2026-07-31T15:00:00",
    }


def test_touching_units_do_not_form_center():
    """三段只在同一价位相接时，重叠区间是一个点，不构成中枢。"""
    items = [
        unit("u0", 108.293, 107.017, 0),
        unit("u1", 107.017, 104.050, 1),
        unit("u2", 104.050, 108.412, 2),
    ]
    assert build_centers(items, "TEST", "segment_proxy") == []


def test_overlapping_units_still_form_center():
    """有真实重叠区间时仍然产出中枢，且 ZG/ZD/GG/DD 取值不变。"""
    items = [
        unit("u0", 100.0, 104.0, 0),
        unit("u1", 104.0, 102.0, 1),
        unit("u2", 102.0, 105.0, 2),
    ]
    centers = build_centers(items, "TEST", "segment_proxy")
    assert len(centers) == 1
    center = centers[0]
    assert center["zg"] == 104.0
    assert center["zd"] == 102.0
    assert center["gg"] == 105.0
    assert center["dd"] == 100.0


def test_no_zero_height_center_on_long_series():
    """长序列回归：任何中枢都必须满足 ZG > ZD 严格成立。"""
    random.seed(7)
    bars, price, stamp = [], 100.0, datetime(2026, 1, 1, 15, 0)
    for _ in range(2000):
        open_ = price
        price *= 1 + random.gauss(0, 0.012)
        close = price
        high = max(open_, close) * (1 + abs(random.gauss(0, 0.004)))
        low = min(open_, close) * (1 - abs(random.gauss(0, 0.004)))
        bars.append(
            {
                "date": stamp.isoformat(),
                "open": round(open_, 3),
                "high": round(high, 3),
                "low": round(low, 3),
                "close": round(close, 3),
                "volume": 1e6,
            }
        )
        stamp += timedelta(days=1)

    centers = analyze(bars, "TEST", "1d", "test_fixture")["layers"]["centers"]
    assert centers
    for center in centers:
        assert center["zg"] > center["zd"], center["id"]
