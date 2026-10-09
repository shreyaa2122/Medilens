import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CircleAlert, Loader2, RotateCw } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { type PageText, getDocument, getDocumentPages, retryDocument } from "../api/documents";
import { ConfidenceBadge } from "../components/ConfidenceBadge";
import { LOW_CONFIDENCE_THRESHOLD } from "../lib/confidence";
import { fileTypeLabel, formatFileSize } from "../lib/format";

function PageCard({ page }: { page: PageText }) {
  return (
    <article className="rounded-lg border border-line bg-surface p-5">
      <header className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-base font-semibold">Page {page.page_number}</h3>
        {page.method === "native" ? (
          <span className="text-sm text-slate">Read directly from the PDF's text</span>
        ) : (
          <span className="flex flex-wrap items-center gap-2 text-sm text-slate">
            Read with OCR (image recognition)
            {page.ocr_confidence !== null && <ConfidenceBadge value={page.ocr_confidence} />}
          </span>
        )}
      </header>
      {page.text.trim() ? (
        <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded bg-paper p-3 font-mono text-sm leading-relaxed">
          {page.text}
        </pre>
      ) : (
        <p className="text-sm text-slate">No text was found on this page.</p>
      )}
    </article>
  );
}

export function DocumentProcessing() {
  const { documentId = "" } = useParams();
  const queryClient = useQueryClient();

  const documentQuery = useQuery({
    queryKey: ["document", documentId],
    queryFn: () => getDocument(documentId),
    // Keep checking until the server has finished with the document.
    refetchInterval: (query) => {
      const status = query.state.data?.processing_status;
      return status === "uploaded" || status === "processing" ? 1500 : false;
    },
  });

  const status = documentQuery.data?.processing_status;
  const pagesQuery = useQuery({
    queryKey: ["document-pages", documentId],
    queryFn: () => getDocumentPages(documentId),
    enabled: status === "completed",
  });

  const retry = useMutation({
    mutationFn: () => retryDocument(documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["document", documentId] });
      queryClient.invalidateQueries({ queryKey: ["document-pages", documentId] });
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  const document = documentQuery.data;
  const pages = pagesQuery.data ?? [];
  const hasLowConfidencePage = pages.some(
    (page) => page.ocr_confidence !== null && page.ocr_confidence < LOW_CONFIDENCE_THRESHOLD,
  );

  return (
    <div className="space-y-6">
      <Link to="/" className="inline-flex items-center gap-1.5 text-sm text-slate hover:text-ink">
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Back to dashboard
      </Link>

      {documentQuery.isPending && <p className="text-sm text-slate">Loading…</p>}
      {documentQuery.error && (
        <p role="alert" className="text-rust">
          {documentQuery.error.message}
        </p>
      )}

      {document && (
        <>
          <header>
            <h1 className="break-words text-3xl font-semibold">{document.file_name}</h1>
            <p className="mt-1 text-sm text-slate">
              {fileTypeLabel(document.mime_type)} · {formatFileSize(document.file_size_bytes)}
            </p>
          </header>

          <section aria-live="polite" className="rounded-lg border border-line bg-surface p-5">
            {(status === "uploaded" || status === "processing") && (
              <p className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-teal motion-reduce:animate-none" aria-hidden="true" />
                Reading your document… scanned pages and photos take a little longer.
              </p>
            )}

            {status === "failed" && (
              <div className="space-y-3">
                <p className="flex items-start gap-2 text-rust">
                  <CircleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                  <span>{document.error_message ?? "This document could not be processed."}</span>
                </p>
                <button
                  type="button"
                  onClick={() => retry.mutate()}
                  disabled={retry.isPending}
                  className="inline-flex items-center gap-2 rounded-md bg-teal px-4 py-2 text-sm font-medium text-white hover:bg-teal/90 disabled:opacity-60"
                >
                  <RotateCw className="h-4 w-4" aria-hidden="true" />
                  Try again
                </button>
                {retry.error && <p className="text-sm text-rust">{retry.error.message}</p>}
              </div>
            )}

            {status === "completed" && (
              <p>
                Text was read from {pages.length} {pages.length === 1 ? "page" : "pages"}. The
                next steps (finding lab values and checking them against the report's own
                reference ranges) are not available yet.
              </p>
            )}
          </section>

          {status === "completed" && hasLowConfidencePage && (
            <p
              role="note"
              className="flex gap-2 rounded-md border border-amber/30 bg-amber-soft px-4 py-3 text-sm"
            >
              <CircleAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber" aria-hidden="true" />
              Some pages were read with low confidence. Please verify the text below against the
              original document.
            </p>
          )}

          {status === "completed" && (
            <section aria-labelledby="text-heading" className="space-y-4">
              <h2 id="text-heading" className="text-xl font-semibold">
                Text read from the document
              </h2>
              {pagesQuery.isPending && <p className="text-sm text-slate">Loading text…</p>}
              {pagesQuery.error && <p className="text-sm text-rust">{pagesQuery.error.message}</p>}
              {pages.map((page) => (
                <PageCard key={page.page_number} page={page} />
              ))}
            </section>
          )}
        </>
      )}
    </div>
  );
}
