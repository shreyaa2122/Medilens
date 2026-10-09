import { CircleAlert, CircleCheck, X } from "lucide-react";

import type { UploadItem } from "../hooks/useUploads";
import { fileTypeLabelFromName, formatFileSize } from "../lib/format";

interface UploadItemRowProps {
  item: UploadItem;
  onDismiss: (id: number) => void;
}

export function UploadItemRow({ item, onDismiss }: UploadItemRowProps) {
  const { file, status, progress, error } = item;

  return (
    <li className="rounded-lg border border-line bg-surface p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-medium">{file.name}</p>
          <p className="text-sm text-slate">
            {fileTypeLabelFromName(file.name)} · {formatFileSize(file.size)}
          </p>
        </div>
        {status !== "uploading" && (
          <button
            type="button"
            onClick={() => onDismiss(item.id)}
            aria-label={`Dismiss ${file.name}`}
            className="rounded p-1 text-slate hover:bg-paper hover:text-ink"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        )}
      </div>

      {status === "uploading" && (
        <div className="mt-3">
          <div
            role="progressbar"
            aria-label={`Uploading ${file.name}`}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={progress}
            className="h-2 overflow-hidden rounded-full bg-line"
          >
            <div className="h-full bg-teal transition-[width]" style={{ width: `${progress}%` }} />
          </div>
          <p className="mt-1 text-sm text-slate">Uploading… {progress}%</p>
        </div>
      )}

      {status === "done" && (
        <p className="mt-3 flex items-start gap-2 text-sm">
          <CircleCheck className="mt-0.5 h-4 w-4 shrink-0 text-teal" aria-hidden="true" />
          <span>Saved. Reading the document's text is not available yet.</span>
        </p>
      )}

      {status === "error" && (
        <p className="mt-3 flex items-start gap-2 text-sm text-rust">
          <CircleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </p>
      )}
    </li>
  );
}
