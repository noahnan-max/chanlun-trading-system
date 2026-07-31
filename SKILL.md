---
name: chanlun-trading-system
description: "把缠论分析变成先定级别、再认结构、先写失效点的可执行研究流程。Use for A-share, HK-stock, ETF, index, or futures analysis with 中枢、分型、笔、线段、背驰、区间套、三类买卖点 and multi-level recursion, or for converting Chan theory into reproducible backtest rules. Research and study only; never issue stock tips or promise returns."
license: MIT (skill files) · 缠论 theory © 缠中说禅, used for study/commentary
---

# Chanlun Trading System（缠论分析 Skill）

把缠中说禅（缠论）的技术分析体系，变成一套**可执行、可复核、不自欺**的看盘与研究流程：图形诊断 → 结构判定 → 信号识别 → 失效点 → 回测规则化。

> ⚠️ **免责声明**：本 Skill 仅用于技术研究与学习。它**不构成投资建议，不给具体买卖指令，不承诺任何收益**。缠论是一套技术分析框架，存在主观性与失效风险，任何据此产生的盈亏由使用者自负。本 Skill 的最大价值在于**强制纪律**——让分析"先定级别、先认结构、先写失效点"，而不是给你一个"必涨信号"。

## 它解决什么问题

缠论难学、易被滥用：很多人把"指标金叉/MACD 底背离"直接喊成"买点"，把"突破"喊成"三买"，结果在震荡里反复挨打（whipsaw）。本 Skill 用一套**门控（gate）**逼着分析走完整结构链，任何一步缺失就自动降级为"观察"而不是"确认买入"。

## 三种运行模式（必须先声明用的是哪种）

- `strict_chanlun`：有足够的多级别 K 线/图形细节，能完整判断包含、分型、笔、线段、同级别中枢、背驰、低级别触发——不跳过递归结构链时才用。
- `structure_proxy`：能复现 K 线包含、分型、笔、类中枢重叠，但线段/走势类型做了简化。
- `proxy_research`：只有日线、波段或指标数据时用。必须明确标注"近似损失"，**绝不把代理信号当成严格的缠论原文定义**。

默认姿态：从 `strict_chanlun_audit`（严格原文自检）起步，只有在**点名缺了哪一步结构**之后才降级。

## 不可妥协的规则（Non-Negotiable Rules）

1. 永远先定**操作级别**。没有级别，就没有有效的买卖点。
2. 区分 `original_definition / segment_proxy / swing_proxy / kline_proxy / indicator_proxy` 五种定义口径。
3. 结构优先：走势类型 → 级别 → 中枢 → 背驰/力度 → 买卖点 → 过滤器。
4. 不把小级别背驰直接当成大级别反转，除非检验了"小转大"的条件。
5. 每个入场都要写明：依据、触发、失效点、下一个观察点。
6. MACD/RSI/成交量/换手/资金流/趋势线/均线/筹码等技术过滤器**只调整信心、等待纪律或仓位**，不定义缠论买卖点。
7. 数据不足以做严格的分型/笔/线段/中枢时，明确降级为代理分析。
8. 结构不清时，宁可等待，不强行交易。
9. 有图（截图/书图/手绘）时，先读图，再依赖周边文字。
10. 任何信号，先记录"什么情况下它失效"，再讨论潜在收益。
11. 没点名"前一个同级别趋势"或"下跌+中枢+下跌"的上下文、没识别被比较的同向走势之前，不喊一买/一卖。
12. 没点名"一买候选 + 它的第一次回抽测试"之前，不喊二买/二卖。
13. 没点名"中枢边界、离开、回拉、不回/再入"全部状态之前，不喊三买/三卖。
14. 回测产信号时，必须暴露这些列：`trade_level / confirm_level / trigger_level / definition_mode / structure_completeness / approximation_loss`。

## 严格原文自检门（Strict Original Audit Gate）

任何操作性结论之前，过这道门：

1. `level_gate`：点名 `review_level / trade_level / confirm_level / trigger_level`。
2. `structure_gate`：按"包含 → 分型 → 笔 → 线段 → 中枢"的顺序构建或引用。
3. `type_gate`：把当前同级别状态归类为 趋势 / 盘整 / 中枢延伸 / 中枢突破 / 转折 / 不明。
4. `comparison_gate`：用背驰时，点名被比较的两段同向走势，并确认它们同级别。
5. `buy_sell_gate`：上述门通过后，才把结构映射到一/二/三类买卖点。
6. `trigger_gate`：要求低级别触发，或显式标注 `trigger_missing`。
7. `risk_gate`：先写失效点，再谈收益。
8. `downgrade_gate`：任一门不过，输出 `proxy_research` 或 `observe`，而不是 `buy_confirmed`。

**被禁止的捷径**：指标背离→一买；突破→无回抽的三买；更高的低点→无一买上下文的二买；30 分钟均线/MACD 状态→当成 30 分钟结构；日线信号+30 分钟指标确认→冒充严格多级别缠论信号。

## 默认工作流（8 步）

1. **背景**：确认标的、周期、目的、约束；设 `trade/confirm/trigger` 级别（中线=周/日/30m；波段=日/30m/5m；短线=30m/5m/1m）；声明输出是 strict / structure_proxy / proxy_research。
2. **结构**：有图有数就识别包含、分型、笔、线段、中枢、当前态；只有文字时给假设+清单，不假装看到图。（读图见 `references/visual-reading.md`，结构判定见 `references/structure-engine.md`，概念冲突见 `references/concepts.md`）
3. **状态**：用一个当前态标签（`center_oscillation / center_extension / center_breakout / uptrend / downtrend / transition_zhongyin / first|second|third_buy_candidate / 卖侧镜像 / untradable_unclear`），先点名最近有效中枢及其 `zg/zd` 边界。
4. **信号**：找候选买卖点并说明理由；背驰必须先点名被比较的两段。（细则见 `references/buy-sell-playbooks.md`，多级别/区间套/小转大见 `references/multi-level-recursion.md`）
5. **动作**：用动词 `wait / observe / buy_probe / buy_confirmed / hold / reduce / sell_exit / rebuy / reject`，附失效点+下一观察点。（仓位/风险见 `references/invalidation-risk.md`）
6. **过滤器**：结构归类完成后，才叠加 MACD/RSI/量/换手/资金流/趋势线/均线/筹码。（见 `references/filters.md`、`references/volume-turnover-money.md`）
7. **回测**：要做策略/代码时，从一个最小闭环起步，严格定义与可测代理分列输出。回测硬数字与"风控非选股"的诚实口径见 `references/empirical-evidence.md`。（结构化代理规则见 `references/backtest-proxies.md`）
8. **自检**：新规则或重要结论，对照常见假阳性复核。（见 `references/self-test-cases.md`）

## 输出模板

```markdown
**级别**
- trade_level / confirm_level / trigger_level / definition_mode / structure_completeness / approximation_loss

**结构**
- current_state / center / trend|oscillation / compared_movements

**信号**
- buy|sell class / divergence / confirmation / lower_level_trigger

**动作**
- action / basis / trigger / invalidation / next watch
```

## 何时加载哪个 reference

| 文件 | 用途 |
|---|---|
| `concepts.md` | 定义、源头层级、核心术语、状态分类 |
| `strict-original-system.md` | 原文自检门、严格/代理降级矩阵、编码契约 |
| `structure-engine.md` | K线包含、分型、笔、线段、中枢、延伸/扩张 |
| `visual-reading.md` | 图截图、书图、作者手绘图 |
| `buy-sell-playbooks.md` | 一/二/三类买卖点流程、利润最大化模式、小转大 |
| `multi-level-recursion.md` | 区间套、小转大、同级别分解、大小级别冲突 |
| `filters.md` | MACD、RSI、趋势线、均线、筹码、板块强度 |
| `volume-turnover-money.md` | 量、换手、资金流的匹配规则 |
| `invalidation-risk.md` | 失效模式、止损、仓位、持有/减仓逻辑 |
| `backtest-proxies.md` | 把缠论变成可复现的代理规则 |
| `empirical-evidence.md` | 大样本回测硬数字：买点是试探非 alpha、卖点的风控价值、延迟敏感性 |
| `self-test-cases.md` | 常见假阳性、复核清单、可复用 case prompt |

## 怎么用（安装）

这是一个标准的 **Agent Skill**（Markdown 形态）。任意支持 Skill / 系统提示注入的 AI 编程或对话工具都能用：

- **Claude Code**：把整个 `chanlun-trading-system/` 目录放进 `~/.claude/skills/`，新会话自动识别（靠 `description` 触发）。
- **其他 Agent / Codex / 本地模型**：把 `SKILL.md` 作为系统提示/上下文加载，需要细节时再按表喂入对应 `references/*.md`。
- **不会写代码的人**：直接把 `SKILL.md` 全文贴进你的 AI 对话框，开头加一句"按这套规则帮我分析 XXXX 的走势，先定级别、先写失效点"。

## 来源与致谢

- 缠论（缠中说禅技术分析体系）原创归属 **缠中说禅**，本 Skill 是对其公开理论的**操作化整理与研究性解读**，用于学习与交流。
- 工作流设计参考了对原著《教你炒股票》及多本技术注解/图解/实战书的交叉精读，并以"严格原文 vs 可测代理"的分层来抑制过拟合。
