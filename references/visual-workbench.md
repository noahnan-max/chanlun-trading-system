# 可视研究工作台

## 用途

把结构研究从文字判断变成可交互证据链：输入 OHLCV → 标准化/质量门 → 包含处理 → 分型 → 笔 → 线段代理 → 中枢 → 背驰对照 → 图上选择与导出。

它是研究工具，不是行情终端、选股器或交易系统。任何候选点都保持 `NO_ACTION / execution_allowed=false`。

## 安装与启动

正式使用优先安装固定 Git tag：

```bash
uv tool install "git+https://github.com/noahnan-max/chanlun-trading-system.git@v0.1.0"
chanlun-visual doctor --json
chanlun-visual
```

一次性运行可用 `uvx --from "git+https://github.com/noahnan-max/chanlun-trading-system.git@v0.1.0" chanlun-visual`。远端命令要求对应 tag 已发布；仓库开发者使用 `uv sync --all-extras && uv run chanlun-visual`。

默认只监听 `127.0.0.1:8791`。启动后可直接查看四周期合成示例，无需网络。`doctor` 不联网、不读取用户行情文件；可选行情未安装时输出 `pass_with_warnings`，不阻断 CSV 和示例。

Skill 侧可运行：

```bash
python scripts/skill_workbench.py check --json
python scripts/skill_workbench.py launch
```

助手只检查/启动已安装的命令，找不到时给出安装建议并退出，不自动安装。

可选公开行情入口会把六位 A 股代码自动映射为 `.SS/.SZ/.BJ`，把四至五位港股代码映射为 `.HK`；返回结果始终展示最终 provider symbol，避免市场歧义。

开发前端：

```bash
npm --prefix ui ci
npm --prefix ui run dev
```

发布包前构建：

```bash
npm --prefix ui run build
uv build
uv run python tools/build_skill_package.py --output-dir dist
```

## CSV 契约

必填列：

```text
date,open,high,low,close
```

可选列：`volume`。也接受 `time/datetime/timestamp` 与 `o/h/l/c/v/vol` 别名。时间必须是 ISO-8601 且严格递增；重复时间、非有限数、负价格/成交量、非法 OHLC 均 fail-closed。

缺失成交量保持 `null` 并降低 coverage，绝不补零。少于 30 根允许预览，但状态必须标记 `insufficient_history`。

## 图层

- 分型：在右侧至少出现一根合并 K 线后才确认。
- 笔：严格交替分型，默认端点间隔至少 4 根合并 K。
- 线段 β：固定三笔研究代理，显式列出未实现特征序列递归的近似损失。
- 中枢：三个同类走势单元的重叠区；显示 `ZD/ZG/DD/GG`。
- 背驰：同向走势创新极值后，以 MACD 柱面积衰减作为基线；U1 多角度力度为可选对照。
- 买卖点：仅在证据满足时显示候选标签，不输出操作按钮或交易授权。

## 时点回放

拖动 as-of 后，客户端会把截断后的 K 线重新送入引擎计算。它不是简单隐藏右侧图形，因此未来分型、中枢或背驰不会残留在历史时点。

## 分享

- JSON：完整 `chanlun.analysis.v1` 证据契约，适合机器复核。
- HTML：自包含、断网可打开、打印友好的研究快照，包含结构、中枢、质量警告、失效条件、输入哈希和免责声明。

导出不包含绝对路径、用户名、账户、持仓或凭据。

## 当前近似损失

1. 线段采用三笔固定分组代理，尚未实现严格特征序列分型与线段破坏递归。
2. 中枢继承组成单元的定义模式；segment proxy 中枢不能冒充严格同级别走势中枢。
3. 背驰只比较当前可复现力度代理，尚未覆盖完整走势类型递归。
4. 公开行情适配器的覆盖、复权与交易日口径受上游限制，CSV 才是首版确定性入口。
