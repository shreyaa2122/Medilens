import { UploadCloud } from "lucide-react";
import { type ChangeEvent, type DragEvent, useRef, useState } from "react";

import { MAX_UPLOAD_MB } from "../lib/validateFile";

interface FileDropzoneProps {
  onFiles: (files: File[]) => void;
}

export function FileDropzone({ onFiles }: FileDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    setIsDragging(false);
    onFiles(Array.from(event.dataTransfer.files));
  }

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    onFiles(Array.from(event.target.files ?? []));
    event.target.value = ""; // lets the same file be chosen again
  }

  return (
    <label
      onDragOver={(event) => {
        event.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      className={`flex cursor-pointer flex-col items-center gap-3 rounded-lg border-2 border-dashed px-6 py-12 text-center focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-teal ${
        isDragging ? "border-teal bg-teal-soft" : "border-line bg-surface hover:border-slate"
      }`}
    >
      <UploadCloud className="h-9 w-9 text-teal" aria-hidden="true" />
      <span className="text-base font-medium">Drag files here, or click to choose</span>
      <span className="text-sm text-slate">
        PDF, JPG, JPEG or PNG · up to {MAX_UPLOAD_MB} MB each
      </span>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
        onChange={handleChange}
        className="sr-only"
      />
    </label>
  );
}
