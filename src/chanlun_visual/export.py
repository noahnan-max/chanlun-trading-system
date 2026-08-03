"""Self-contained, print-friendly research snapshot."""

from __future__ import annotations

import html
from typing import Any, Dict


def _sparkline(analysis: Dict[str, Any]) -> str:
    bars = analysis["bars"][-120:]
    if not bars:
        return ""
    values = [bar["close"] for bar in bars]
    low, high = min(values), max(values)
    spread = high - low or 1
    width, height = 960, 260
    points = []
    for index, value in enumerate(values):
        x = index * width / max(1, len(values) - 1)
        y = height - (value - low) / spread * (height - 20) - 10
        points.append("{:.1f},{:.1f}".format(x, y))
    center_boxes = []
    offset = len(analysis["bars"]) - len(bars)
    for center in analysis["layers"]["centers"][-3:]:
        x0 = max(0, center["raw_start"] - offset) * width / max(1, len(values) - 1)
        x1 = max(0, center["raw_end"] - offset) * width / max(1, len(values) - 1)
        y0 = height - (center["zg"] - low) / spread * (height - 20) - 10
        y1 = height - (center["zd"] - low) / spread * (height - 20) - 10
        center_boxes.append(
            '<rect x="{:.1f}" y="{:.1f}" width="{:.1f}" height="{:.1f}" fill="#38bdf833" stroke="#38bdf8"/>'.format(
                x0, min(y0, y1), max(2, x1 - x0), max(2, abs(y1 - y0))
            )
        )
    return '<svg viewBox="0 0 960 260" role="img" aria-label="收盘价与中枢快照">{}<polyline points="{}" fill="none" stroke="#22d3ee" stroke-width="3"/></svg>'.format(
        "".join(center_boxes), " ".join(points)
    )


def snapshot_html(analysis: Dict[str, Any]) -> str:
    meta, state, quality = analysis["meta"], analysis["state"], analysis["quality"]
    center = next(
        (item for item in analysis["layers"]["centers"] if item["id"] == state["current_center_id"]),
        None,
    )
    center_text = "无完成中枢"
    if center:
        center_text = "ZD {} / ZG {} / DD {} / GG {}".format(center["zd"], center["zg"], center["dd"], center["gg"])
    warnings = "".join("<li>{}</li>".format(html.escape(item)) for item in quality["warnings"]) or "<li>无数据质量警告</li>"
    return """<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width\"><title>{symbol} 缠论研究快照</title><style>
body{{margin:0;background:#07131f;color:#dceaf4;font:15px/1.6 system-ui,sans-serif}}main{{max-width:1080px;margin:auto;padding:36px}}header{{display:flex;justify-content:space-between;gap:24px;border-bottom:1px solid #244156;padding-bottom:20px}}h1{{margin:0;color:#f3f8fb}}.tag{{color:#67e8f9}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:20px 0}}.cell{{background:#0d2030;border:1px solid #1d3b50;padding:14px;border-radius:8px}}svg{{width:100%;background:#091a28;border:1px solid #1d3b50;border-radius:8px}}small{{color:#91aabb}}.risk{{border-left:3px solid #f59e0b;padding:12px 16px;background:#2b210f}}@media(max-width:720px){{header{{display:block}}.grid{{grid-template-columns:1fr}}main{{padding:20px}}}}@media print{{body{{background:#fff;color:#182633}}.cell,svg{{background:#fff}}}}
</style></head><body><main><header><div><small>CHANLUN VISUAL · RESEARCH SNAPSHOT</small><h1>{symbol} · {timeframe}</h1><div class=\"tag\">{structure}</div></div><div><small>as of</small><br>{as_of}<br><small>生成于 {generated}</small></div></header><section class=\"grid\"><div class=\"cell\"><small>定义模式</small><br>{mode}</div><div class=\"cell\"><small>当前中枢</small><br>{center}</div><div class=\"cell\"><small>数据质量</small><br>{quality}</div></section>{chart}<section><h2>质量与失效条件</h2><ul>{warnings}{invalidations}</ul></section><p class=\"risk\"><strong>研究用途 · NO_ACTION</strong><br>本页使用研究代理定义，不构成投资建议或交易授权；execution_allowed=false。</p><small>schema {schema} · engine {engine} · input {digest}</small></main></body></html>""".format(
        symbol=html.escape(str(meta["symbol"])),
        timeframe=html.escape(str(meta["timeframe"])),
        structure=html.escape(str(state["structure"])),
        as_of=html.escape(str(meta["as_of"])),
        generated=html.escape(str(meta["generated_at"])),
        mode=html.escape(str(meta["definition_mode"])),
        center=html.escape(center_text),
        quality=html.escape(str(quality["status"])),
        chart=_sparkline(analysis),
        warnings=warnings,
        invalidations="".join("<li>{}</li>".format(html.escape(item)) for item in state["invalidation"]),
        schema=html.escape(str(meta["schema_version"])),
        engine=html.escape(str(meta["engine_version"])),
        digest=html.escape(str(meta["input_sha256"][:16])),
    )
