"""Local-only FastAPI application for the visual workbench."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__
from .engine import DataQualityError, analyze, demo_bundle
from .export import snapshot_html
from .providers import canonical_symbol, yfinance_bars


class AnalyzeRequest(BaseModel):
    symbol: str = Field(default="LOCAL", max_length=32)
    timeframe: str = Field(default="1d", max_length=8)
    source: str = Field(default="user_csv", max_length=64)
    bars: List[Dict[str, Any]] = Field(min_length=1, max_length=20000)


class ExportRequest(BaseModel):
    analysis: Dict[str, Any]


app = FastAPI(
    title="Chanlun Visual Research Workbench",
    version=__version__,
    description="Local research proxy only; no trading execution.",
)


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "version": __version__, "execution_allowed": False}


@app.get("/api/demo")
def demo(symbol: str = Query(default="DEMO", max_length=24)) -> Dict[str, Any]:
    return demo_bundle(symbol)


@app.post("/api/analyze")
def analyze_bars(request: AnalyzeRequest) -> Dict[str, Any]:
    try:
        return analyze(request.bars, request.symbol, request.timeframe, request.source)
    except DataQualityError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/quote")
def quote(symbol: str = Query(min_length=1, max_length=24)) -> Dict[str, Any]:
    try:
        provider_symbol = canonical_symbol(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    frames = {}
    failures = {}
    for timeframe in ("1d", "60m", "30m", "5m"):
        try:
            bars = yfinance_bars(provider_symbol, timeframe)
            frames[timeframe] = analyze(bars, provider_symbol, timeframe, "yfinance_public_optional")
        except Exception as exc:  # provider failures must remain visible per timeframe
            failures[timeframe] = str(exc)
    if not frames:
        raise HTTPException(status_code=503, detail={"message": "公开行情暂不可用", "failures": failures})
    return {
        "symbol": provider_symbol,
        "requested_symbol": symbol,
        "source": "yfinance_public_optional",
        "is_synthetic": False,
        "frames": frames,
        "failures": failures,
    }


@app.post("/api/export/html", response_class=HTMLResponse)
def export_html(request: ExportRequest) -> HTMLResponse:
    try:
        return HTMLResponse(snapshot_html(request.analysis))
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="分析结果不符合导出契约") from exc


STATIC = Path(__file__).resolve().parent / "static"
if (STATIC / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC / "assets")), name="assets")


@app.get("/{path:path}", include_in_schema=False)
def spa(path: str = "") -> Any:
    index = STATIC / "index.html"
    if not index.exists():
        return HTMLResponse(
            "<h1>前端尚未构建</h1><p>请运行 <code>npm --prefix ui run build</code>。</p>",
            status_code=503,
        )
    candidate = (STATIC / path).resolve()
    if path and candidate.is_file() and STATIC in candidate.parents:
        return FileResponse(candidate)
    return FileResponse(index)
