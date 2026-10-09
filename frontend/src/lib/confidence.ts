// Bands from the product spec. This is EXTRACTION confidence (how sure the system is that
// it read the characters correctly). It is never medical certainty.
export type ConfidenceLevel = "high" | "medium" | "low";

export function confidenceLevel(value: number): ConfidenceLevel {
  if (value >= 0.9) return "high";
  if (value >= 0.7) return "medium";
  return "low";
}

export const LOW_CONFIDENCE_THRESHOLD = 0.7;
