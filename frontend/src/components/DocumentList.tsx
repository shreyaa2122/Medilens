import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, Trash2 } from "lucide-react";

import { type ProcessingStatus, deleteDocument, listDocuments } from "../api/documents";
import { fileTypeLabel, formatDateTime, formatFileSize } from "../lib/format";

const STATUS_LABELS: Record<ProcessingStatus, string> = {
  uploaded: "Uploaded",
  processing: "Processing",
  completed: "Ready",
  failed: "Failed",
};

export function DocumentList() {
  const queryClient = useQueryClient();
  const { data: documents, error, isPending } = useQuery({
    queryKey: ["documents"],
    queryFn: listDocuments,
  });

  const removal = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });

  function handleDelete(id: string, fileName: string) {
    if (window.confirm(`Delete "${fileName}"? The file and its data will be permanently removed.`)) {
      removal.mutate(id);
    }
  }

  if (isPending) return <p className="text-sm text-slate">Loading documents…</p>;
  if (error) return <p className="text-sm text-rust">{error.message}</p>;
  if (documents.length === 0) {
    return <p className="text-sm text-slate">No documents yet. Upload one to get started.</p>;
  }

  return (
    <>
      {removal.error && (
        <p role="alert" className="mb-3 text-sm text-rust">
          {removal.error.message}
        </p>
      )}
      <ul className="divide-y divide-line">
        {documents.map((document) => (
          <li key={document.id} className="flex items-center gap-3 py-3">
            <FileText className="h-5 w-5 shrink-0 text-slate" aria-hidden="true" />
            <div className="min-w-0 flex-1">
              <p className="truncate font-medium">{document.file_name}</p>
              <p className="text-sm text-slate">
                {fileTypeLabel(document.mime_type)} · {formatFileSize(document.file_size_bytes)} ·{" "}
                {formatDateTime(document.upload_date)}
              </p>
            </div>
            <span className="rounded-full bg-paper px-2.5 py-1 text-xs font-medium text-slate">
              {STATUS_LABELS[document.processing_status]}
            </span>
            <button
              type="button"
              onClick={() => handleDelete(document.id, document.file_name)}
              disabled={removal.isPending}
              aria-label={`Delete ${document.file_name}`}
              className="rounded p-2 text-slate hover:bg-paper hover:text-rust disabled:opacity-50"
            >
              <Trash2 className="h-4 w-4" aria-hidden="true" />
            </button>
          </li>
        ))}
      </ul>
    </>
  );
}
