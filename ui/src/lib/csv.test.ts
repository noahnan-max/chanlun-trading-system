import {describe, expect, it} from "vitest";
import {parseOhlcvCsv} from "./csv";

describe("parseOhlcvCsv", () => {
  it("normalizes common aliases", () => {
    const rows = parseOhlcvCsv("time,o,h,l,c,v\n2026-01-01,1,3,0.5,2,100");
    expect(rows).toEqual([{date: "2026-01-01", open: "1", high: "3", low: "0.5", close: "2", volume: "100"}]);
  });

  it("rejects a missing required column", () => {
    expect(() => parseOhlcvCsv("date,open,high,close\n2026-01-01,1,2,2")).toThrow("low");
  });

  it("supports quoted values and tabs", () => {
    const rows = parseOhlcvCsv('date\topen\thigh\tlow\tclose\n"2026-01-01 09:30"\t1\t2\t0.5\t1.5');
    expect(rows[0].date).toBe("2026-01-01 09:30");
  });
});
