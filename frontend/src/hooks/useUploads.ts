import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useRef, useState } from "react";

import { type MedicalDocument, uploadDocument } from "../api/documents";
import { validateFile } from "../lib/validateFile";

export interface UploadItem {
  id: number;
  file: File;
  status: "uploading" | "done" | "error";
  progress: number;
  error?: string;
  document?: MedicalDocument;
}

export function useUploads() {
  const [items, setItems] = useState<UploadItem[]>([]);
  const nextId = useRef(1);
  const queryClient = useQueryClient();

  const update = useCallback((id: number, changes: Partial<UploadItem>) => {
    setItems((current) => current.map((item) => (item.id === id ? { ...item, ...changes } : item)));
  }, []);

  const addFiles = useCallback(
    (files: File[]) => {
      for (const file of files) {
        const id = nextId.current++;
        const problem = validateFile(file);

        if (problem) {
          setItems((current) => [...current, { id, file, status: "error", progress: 0, error: problem }]);
          continue;
        }

        setItems((current) => [...current, { id, file, status: "uploading", progress: 0 }]);
        uploadDocument(file, (progress) => update(id, { progress }))
          .then((document) => {
            update(id, { status: "done", progress: 100, document });
            queryClient.invalidateQueries({ queryKey: ["documents"] });
          })
          .catch((error: Error) => update(id, { status: "error", error: error.message }));
      }
    },
    [queryClient, update],
  );

  const dismiss = useCallback((id: number) => {
    setItems((current) => current.filter((item) => item.id !== id));
  }, []);

  return { items, addFiles, dismiss };
}
