from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from chanlun_visual.engine import DataQualityError, analyze, demo_bundle, generate_demo_bars


def sample(count=90):
    return generate_demo_bars(count, timedelta(days=1), datetime(2026, 7, 31, 15, 0))


def test_analysis_contract_and_research_boundary():
    result = analyze(sample(), "TEST", "1d", "test_fixture")
    assert result["meta"]["schema_version"] == "chanlun.analysis.v1"
    assert result["meta"]["execution_allowed"] is False
    assert result["state"]["execution_allowed"] is False
    assert result["quality"]["status"] == "pass"
    assert result["layers"]["fractals"]
    assert result["layers"]["strokes"]


def test_structure_never_available_before_confirmation():
    result = analyze(sample())
    for layer in ("fractals", "strokes", "segments", "centers", "divergences"):
        for item in result["layers"][layer]:
            assert item["available_at"] >= item["confirmed_at"]
            assert item["available_at"] <= result["meta"]["as_of"]


def test_input_hash_is_deterministic():
    bars = sample()
    first = analyze(bars)
    second = analyze(bars)
    assert first["meta"]["input_sha256"] == second["meta"]["input_sha256"]


def test_quality_gate_rejects_non_monotonic_dates():
    bars = sample(35)
    bars[12]["date"] = bars[11]["date"]
    with pytest.raises(DataQualityError, match="严格递增"):
        analyze(bars)


def test_quality_gate_rejects_invalid_ohlc():
    bars = sample(35)
    bars[5]["low"] = bars[5]["high"] + 1
    with pytest.raises(DataQualityError, match="low"):
        analyze(bars)


def test_missing_volume_is_preserved_not_zero_filled():
    bars = sample(40)
    for bar in bars:
        bar.pop("volume")
    result = analyze(bars)
    assert result["quality"]["volume_coverage"] == 0
    assert all(bar["volume"] is None for bar in result["bars"])
    assert result["quality"]["status"] == "warn"


def test_demo_exposes_all_four_timeframes():
    bundle = demo_bundle()
    assert set(bundle["frames"]) == {"1d", "60m", "30m", "5m"}
    assert bundle["is_synthetic"] is True
