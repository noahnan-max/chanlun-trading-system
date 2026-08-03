import {BarChart, CandlestickChart, LineChart, ScatterChart} from "echarts/charts";
import {AxisPointerComponent, DataZoomComponent, GridComponent, MarkAreaComponent, TooltipComponent} from "echarts/components";
import * as echarts from "echarts/core";
import type {EChartsCoreOption} from "echarts/core";
import {CanvasRenderer} from "echarts/renderers";
import {useEffect, useMemo, useRef} from "react";
import type {Analysis, LayerVisibility} from "../types";

echarts.use([
  BarChart,
  CandlestickChart,
  LineChart,
  ScatterChart,
  AxisPointerComponent,
  DataZoomComponent,
  GridComponent,
  MarkAreaComponent,
  TooltipComponent,
  CanvasRenderer,
]);

interface Props {
  analysis: Analysis;
  layers: LayerVisibility;
  selectedId: string | null;
  onSelect: (id: string) => void;
}

function pointsForUnits(units: Analysis["layers"]["strokes"], selectedId: string | null) {
  return units.flatMap((unit) => [
    {
      id: unit.id,
      name: unit.id,
      value: [unit.start_index, unit.start_price],
      symbolSize: unit.id === selectedId ? 9 : 5,
    },
    {
      id: unit.id,
      name: unit.id,
      value: [unit.end_index, unit.end_price],
      symbolSize: unit.id === selectedId ? 9 : 5,
    },
    {value: [null, null]},
  ]);
}

export function ChanlunChart({analysis, layers, selectedId, onSelect}: Props) {
  const host = useRef<HTMLDivElement>(null);
  const option = useMemo(() => {
    const {bars} = analysis;
    const dates = bars.map((bar) => bar.date);
    const volumes = bars.map((bar) => bar.volume ?? 0);
    const macd = analysis.indicators.macd;
    const centers: [Record<string, unknown>, Record<string, unknown>][] = analysis.layers.centers.map((center) => [
      {
        id: center.id,
        name: center.id,
        xAxis: center.raw_start,
        yAxis: center.zd,
        itemStyle: {
          color: center.id === selectedId ? "rgba(56,189,248,.25)" : "rgba(59,130,246,.13)",
          borderColor: center.id === selectedId ? "#67e8f9" : "#3b82f6",
          borderWidth: center.id === selectedId ? 2 : 1,
        },
      },
      {xAxis: center.raw_end, yAxis: center.zg},
    ]);
    // ECharts' public union types cannot express heterogeneous markArea and
    // callback-colored bar series in one inferred array; the final option is
    // still validated by the runtime chart renderer and browser tests.
    const series: Array<Record<string, unknown>> = [
      {
        name: "K线",
        type: "candlestick",
        data: bars.map((bar) => [bar.open, bar.close, bar.low, bar.high]),
        itemStyle: {
          color: "#24d18b",
          color0: "#ff6b7a",
          borderColor: "#24d18b",
          borderColor0: "#ff6b7a",
        },
      },
      ...(layers.centers
        ? [
            {
              name: "中枢",
              type: "line" as const,
              data: [],
              markArea: {silent: false, label: {show: false}, data: centers},
            },
          ]
        : []),
      ...(layers.strokes
        ? [
            {
              name: "笔",
              type: "line" as const,
              data: pointsForUnits(analysis.layers.strokes, selectedId),
              connectNulls: false,
              showSymbol: true,
              lineStyle: {color: "#f5a742", width: 2},
              itemStyle: {color: "#f5a742"},
            },
          ]
        : []),
      ...(layers.segments
        ? [
            {
              name: "线段 β",
              type: "line" as const,
              data: pointsForUnits(analysis.layers.segments, selectedId),
              connectNulls: false,
              showSymbol: true,
              lineStyle: {color: "#c084fc", width: 3, type: "dashed" as const},
              itemStyle: {color: "#c084fc"},
            },
          ]
        : []),
      ...(layers.fractals
        ? [
            {
              name: "分型",
              type: "scatter" as const,
              data: analysis.layers.fractals.map((item) => ({
                id: item.id,
                name: item.id,
                value: [item.raw_index, item.price],
                symbol: item.kind === "top" ? "triangle" : "triangle",
                symbolRotate: item.kind === "top" ? 180 : 0,
                itemStyle: {color: item.kind === "top" ? "#fb7185" : "#34d399"},
              })),
              symbolSize: 9,
            },
          ]
        : []),
      ...(layers.divergence
        ? [
            {
              name: "背驰证据",
              type: "scatter" as const,
              data: analysis.layers.divergences.map((item) => {
                const unit = [...analysis.layers.segments, ...analysis.layers.strokes].find(
                  (candidate) => candidate.id === item.compared_ids[1],
                );
                return {
                  id: item.id,
                  name: item.id,
                  value: [unit?.end_index ?? bars.length - 1, unit?.end_price ?? bars.at(-1)?.close],
                  symbol: "pin",
                  symbolSize: item.decision === "candidate" ? 42 : 28,
                  itemStyle: {color: item.direction === "bullish" ? "#22d3ee" : "#f472b6"},
                };
              }),
            },
          ]
        : []),
      ...(layers.signals
        ? [
            {
              name: "买卖点候选",
              type: "scatter" as const,
              data: analysis.state.candidate_signals.map((item) => ({
                id: item.id,
                name: item.id,
                value: [item.at_index, item.price],
                label: {show: true, formatter: item.label, color: "#dff7ff", position: "top" as const},
                itemStyle: {color: item.kind.startsWith("B") ? "#24d18b" : "#ff6b7a"},
              })),
              symbolSize: 14,
            },
          ]
        : []),
      {
        name: "成交量",
        type: "bar",
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: layers.volume ? volumes : volumes.map(() => 0),
        itemStyle: {
          color: (params: {dataIndex: number}) => (bars[params.dataIndex].close >= bars[params.dataIndex].open ? "#24d18b77" : "#ff6b7a77"),
        },
      },
      {
        name: "MACD柱",
        type: "bar",
        xAxisIndex: 2,
        yAxisIndex: 2,
        data: layers.macd ? macd.hist : macd.hist.map(() => 0),
        itemStyle: {color: (params: {value: unknown}) => ((params.value as number) >= 0 ? "#24d18b99" : "#ff6b7a99")},
      },
      ...(layers.macd
        ? [
            {name: "DIF", type: "line" as const, xAxisIndex: 2, yAxisIndex: 2, data: macd.dif, showSymbol: false, lineStyle: {color: "#38bdf8", width: 1}},
            {name: "DEA", type: "line" as const, xAxisIndex: 2, yAxisIndex: 2, data: macd.dea, showSymbol: false, lineStyle: {color: "#f5a742", width: 1}},
          ]
        : []),
    ];
    return {
      animation: false,
      backgroundColor: "transparent",
      axisPointer: {link: [{xAxisIndex: "all"}], label: {backgroundColor: "#183346"}},
      tooltip: {
        trigger: "axis",
        confine: true,
        backgroundColor: "rgba(7,19,31,.94)",
        borderColor: "#24475d",
        textStyle: {color: "#dceaf4", fontSize: 12},
      },
      grid: [
        {left: 60, right: 18, top: 24, height: "57%"},
        {left: 60, right: 18, top: "67%", height: "9%"},
        {left: 60, right: 18, top: "80%", height: "11%"},
      ],
      xAxis: [0, 1, 2].map((index) => ({
        type: "category",
        data: dates,
        gridIndex: index,
        boundaryGap: true,
        axisLine: {lineStyle: {color: "#25465a"}},
        axisLabel: {show: index === 2, color: "#718c9e", formatter: (value: string) => value.slice(5, 16)},
        axisTick: {show: false},
        splitLine: {show: false},
      })),
      yAxis: [0, 1, 2].map((index) => ({
        scale: true,
        gridIndex: index,
        axisLine: {show: false},
        axisTick: {show: false},
        axisLabel: {color: "#718c9e", fontSize: 10},
        splitLine: {lineStyle: {color: "rgba(48,81,101,.24)"}},
      })),
      dataZoom: [
        {type: "inside", xAxisIndex: [0, 1, 2], start: 38, end: 100},
        {type: "slider", xAxisIndex: [0, 1, 2], height: 16, bottom: 2, borderColor: "transparent", fillerColor: "rgba(34,211,238,.12)", textStyle: {color: "#718c9e"}},
      ],
      series,
    } as EChartsCoreOption;
  }, [analysis, layers, selectedId]);

  useEffect(() => {
    if (!host.current) return;
    const chart = echarts.init(host.current, undefined, {renderer: "canvas"});
    chart.setOption(option);
    chart.on("click", (event) => {
      const data = event.data as {id?: string; name?: string} | undefined;
      const id = data?.id ?? data?.name ?? event.name;
      if (id && id.includes(":")) onSelect(id);
    });
    const observer = new ResizeObserver(() => chart.resize());
    observer.observe(host.current);
    return () => {
      observer.disconnect();
      chart.dispose();
    };
  }, [option, onSelect]);

  return <div className="chart-host" ref={host} aria-label="缠论结构图表" data-testid="chanlun-chart" />;
}
