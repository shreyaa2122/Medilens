import { ShieldAlert } from "lucide-react";

// Required wording from the product spec. Shown on every results page.
export function DisclaimerBanner() {
  return (
    <div
      role="note"
      className="flex gap-3 rounded-md border border-amber/30 bg-amber-soft px-4 py-3 text-sm text-ink"
    >
      <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber" aria-hidden="true" />
      <p>
        <strong className="font-semibold">Important:</strong> MediLens provides informational
        document summaries and does not diagnose medical conditions or replace advice from a
        qualified healthcare professional.
      </p>
    </div>
  );
}
