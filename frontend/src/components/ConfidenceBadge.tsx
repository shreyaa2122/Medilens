import { CircleAlert, CircleCheck, Info } from "lucide-react";

import { confidenceLevel } from "../lib/confidence";

const STYLES = {
  high: { icon: CircleCheck, classes: "bg-teal-soft text-teal", text: "High extraction confidence" },
  medium: { icon: Info, classes: "bg-paper text-slate", text: "Medium extraction confidence" },
  low: {
    icon: CircleAlert,
    classes: "bg-amber-soft text-amber",
    text: "Low extraction confidence — please verify against the original document.",
  },
} as const;

interface ConfidenceBadgeProps {
  value: number; // 0 to 1
}

export function ConfidenceBadge({ value }: ConfidenceBadgeProps) {
  const { icon: Icon, classes, text } = STYLES[confidenceLevel(value)];
  return (
    <span className={`inline-flex items-start gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium ${classes}`}>
      <Icon className="mt-px h-3.5 w-3.5 shrink-0" aria-hidden="true" />
      <span>
        {text} <span className="font-normal">({Math.round(value * 100)}%)</span>
      </span>
    </span>
  );
}
