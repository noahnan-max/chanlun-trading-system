import {Badge} from "@astryxdesign/core/Badge";
import {X} from "lucide-react";
import type {Analysis} from "../types";

interface Props {
  analysis: Analysis;
  selectedId: string | null;
  useU1: boolean;
  isOpen: boolean;
  onSelect: (id: string) => void;
  onClose: () => void;
}

function number(value: number | null | undefined) {
  return value == null ? "缺失" : value.toLocaleString("zh-CN", {maximumFractionDigits: 4});
}

export function EvidencePanel({analysis, selectedId, useU1, isOpen, onSelect, onClose}: Props) {
  const currentCenter = analysis.layers.centers.find((item) => item.id === analysis.state.current_center_id);
  const divergence = analysis.layers.divergences.at(-1);
  const selected = [
    ...analysis.layers.fractals,
    ...analysis.layers.strokes,
    ...analysis.layers.segments,
    ...analysis.layers.centers,
    ...analysis.layers.divergences,
  ].find((item) => item.id === selectedId) as Record<string, unknown> | undefined;

  return (
    <aside className={`evidence-panel ${isOpen ? "is-open" : ""}`} aria-label="证据抽屉">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">EVIDENCE</span>
          <h2>结构证据</h2>
        </div>
        <button className="mobile-close" onClick={onClose} aria-label="关闭证据抽屉"><X size={18} /></button>
      </div>

      {selected && (
        <section className="evidence-block selected-evidence">
          <div className="evidence-title"><span>当前选择</span><Badge variant="cyan" label={String(selected.id)} /></div>
          {"available_at" in selected && <p><b>可用时间</b><br />{String(selected.available_at)}</p>}
          {"confirmed_at" in selected && <p><b>确认时间</b><br />{String(selected.confirmed_at)}</p>}
          {"approximation_loss" in selected && Array.isArray(selected.approximation_loss) && selected.approximation_loss.length > 0 && (
            <p className="warning-copy"><b>近似损失</b><br />{selected.approximation_loss.join("；")}</p>
          )}
        </section>
      )}

      <section className="evidence-block">
        <div className="evidence-title"><span>当前中枢</span><Badge variant={currentCenter ? "blue" : "neutral"} label={currentCenter ? currentCenter.unit_type : "未完成"} /></div>
        {currentCenter ? (
          <button className="evidence-link" onClick={() => onSelect(currentCenter.id)}>
            <span>ZD <b>{number(currentCenter.zd)}</b></span><span>ZG <b>{number(currentCenter.zg)}</b></span>
            <span>DD <b>{number(currentCenter.dd)}</b></span><span>GG <b>{number(currentCenter.gg)}</b></span>
          </button>
        ) : <p>当前样本未形成完成中枢；不会强行补画。</p>}
      </section>

      <section className="evidence-block">
        <div className="evidence-title">
          <span>背驰对照</span>
          <Badge variant={divergence?.decision === "candidate" ? "warning" : "neutral"} label={useU1 ? "U1 多角度" : "MACD 基线"} />
        </div>
        {divergence ? (
          <button className="divergence-detail" onClick={() => onSelect(divergence.id)}>
            {useU1 ? (
              <>
                <strong>{divergence.u1.supports_candidate ? "多数力度维度支持" : "多数力度维度不支持"}</strong>
                <span>{divergence.u1.weaker_votes}/{divergence.u1.available_votes} 个可用维度衰减</span>
                <small>仅作对照证据，不覆盖基线结论</small>
              </>
            ) : (
              <>
                <strong>{divergence.baseline.supports_candidate ? "出现背驰候选" : "未见基线背驰"}</strong>
                <span>MACD 面积 {number(divergence.baseline.previous)} → {number(divergence.baseline.current)}</span>
                <small>{divergence.new_extreme ? "价格已创新极值" : "价格未创新极值"}</small>
              </>
            )}
          </button>
        ) : <p>同向走势不足，背驰保持“证据不足”。</p>}
      </section>

      <section className="evidence-block">
        <div className="evidence-title"><span>可追溯性</span><Badge variant="success" label={analysis.quality.status.toUpperCase()} /></div>
        <dl className="trace-list">
          <div><dt>定义</dt><dd>{analysis.meta.definition_mode}</dd></div>
          <div><dt>as of</dt><dd>{analysis.meta.as_of}</dd></div>
          <div><dt>样本</dt><dd>{analysis.quality.row_count} bars</dd></div>
          <div><dt>输入哈希</dt><dd>{analysis.meta.input_sha256.slice(0, 12)}</dd></div>
        </dl>
      </section>

      <div className="risk-note"><strong>研究用途 · NO_ACTION</strong><span>未连接券商，execution_allowed=false</span></div>
    </aside>
  );
}
