export function boundedReplayCount(requested: number, fullCount: number, minimum = 20): number {
  if (!Number.isFinite(requested) || fullCount <= 0) return 0;
  const lowerBound = Math.min(minimum, fullCount);
  return Math.max(lowerBound, Math.min(Math.trunc(requested), fullCount));
}
