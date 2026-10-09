import { ApiError, API_BASE_URL, apiDelete, apiGet, unwrapEnvelope } from "./client";

export type ProcessingStatus = "uploaded" | "processing" | "completed" | "failed";
export type DocumentType = "lab_report" | "prescription" | "unknown";

export interface MedicalDocument {
  id: string;
  file_name: string;
  mime_type: string;
  file_size_bytes: number;
  document_type: DocumentType;
  processing_status: ProcessingStatus;
  overall_extraction_confidence: number | null;
  upload_date: string;
}

export const listDocuments = () => apiGet<MedicalDocument[]>("/documents");
export const deleteDocument = (id: string) => apiDelete(`/documents/${id}`);

// fetch() cannot report upload progress, so uploads use XMLHttpRequest.
export function uploadDocument(
  file: File,
  onProgress: (percent: number) => void,
): Promise<MedicalDocument> {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open("POST", `${API_BASE_URL}/documents/upload`);

    request.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress(Math.round((event.loaded / event.total) * 100));
    };

    request.onload = () => {
      let body: unknown = null;
      try {
        body = JSON.parse(request.responseText);
      } catch {
        // leave body as null; unwrapEnvelope turns this into a clean error
      }
      try {
        resolve(unwrapEnvelope<MedicalDocument>(request.status >= 200 && request.status < 300, body));
      } catch (error) {
        reject(error);
      }
    };

    request.onerror = () =>
      reject(new ApiError("network_error", "Could not reach the MediLens server."));

    const form = new FormData();
    form.append("file", file);
    request.send(form);
  });
}
