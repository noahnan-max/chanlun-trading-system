import {describe, expect, it} from "vitest";
import {boundedReplayCount} from "./replay";

describe("boundedReplayCount", () => {
  it("keeps replay inside the available history", () => {
    expect(boundedReplayCount(220, 240)).toBe(220);
    expect(boundedReplayCount(500, 240)).toBe(240);
    expect(boundedReplayCount(1, 240)).toBe(20);
  });

  it("supports short or invalid histories", () => {
    expect(boundedReplayCount(1, 12)).toBe(12);
    expect(boundedReplayCount(Number.NaN, 240)).toBe(0);
    expect(boundedReplayCount(20, 0)).toBe(0);
  });
});
