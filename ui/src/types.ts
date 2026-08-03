export type Timeframe = "1d" | "60m" | "30m" | "5m";

export interface Bar {
  id: string;
  index: number;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number | null;
}

export interface StructureUnit {
  id: string;
  direction: "up" | "down";
  start_index: number;
  end_index: number;
  start_price: number;
  end_price: number;
  raw_start: number;
  raw_end: number;
  confirmed_at: string;
  available_at: string;
  definition_mode?: string;
  method?: string;
  stroke_ids?: string[];
  approximation_loss?: string[];
  power: Record<string, number | null>;
}

export interface Fractal {
  id: string;
  kind: "top" | "bottom";
  raw_index: number;
  price: number;
  confirmed_at: string;
  available_at: string;
}

export interface Center {
  id: string;
  unit_type: "stroke" | "segment_proxy";
  component_ids: string[];
  zd: number;
  zg: number;
  gg: number;
  dd: number;
  raw_start: number;
  raw_end: number;
  confirmed_at: string;
  available_at: string;
  definition_mode: string;
  approximation_loss: string[];
}

export interface Divergence {
  id: string;
  direction: "bullish" | "bearish";
  unit_type: string;
  compared_ids: string[];
  new_extreme: boolean;
  baseline: {
    method: string;
    previous: number;
    current: number;
    weaker: boolean | null;
    supports_candidate: boolean;
  };
  u1: {
    method: string;
    role: string;
    votes: Record<string, boolean | null>;
    weaker_votes: number;
    available_votes: number;
    supports_candidate: boolean;
  };
  decision: "candidate" | "not_present" | "insufficient_evidence";
  confirmed_at: string;
  available_at: string;
  invalidation: string;
}

export interface Analysis {
  meta: {
    schema_version: string;
    engine_version: string;
    symbol: string;
    timeframe: Timeframe;
    generated_at: string;
    as_of: string;
    source: string;
    input_sha256: string;
    definition_mode: string;
    execution_allowed: false;
  };
  quality: {
    status: "pass" | "warn" | "fail";
    row_count: number;
    volume_coverage: number;
    warnings: string[];
  };
  bars: Bar[];
  indicators: {
    macd: {dif: number[]; dea: number[]; hist: number[]};
  };
  layers: {
    merged_bars: Array<Record<string, unknown>>;
    fractals: Fractal[];
    strokes: StructureUnit[];
    segments: StructureUnit[];
    centers: Center[];
    divergences: Divergence[];
  };
  state: {
    structure: string;
    current_center_id: string | null;
    candidate_signals: Array<{
      id: string;
      label: string;
      kind: string;
      at_index: number;
      price: number;
      evidence_ids: string[];
      status: string;
      action: "NO_ACTION";
    }>;
    invalidation: string[];
    execution_allowed: false;
  };
}

export interface AnalysisBundle {
  symbol: string;
  source: string;
  is_synthetic: boolean;
  frames: Partial<Record<Timeframe, Analysis>>;
  failures?: Partial<Record<Timeframe, string>>;
}

export interface LayerVisibility {
  fractals: boolean;
  strokes: boolean;
  segments: boolean;
  centers: boolean;
  divergence: boolean;
  signals: boolean;
  volume: boolean;
  macd: boolean;
}
