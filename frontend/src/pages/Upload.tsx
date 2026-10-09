import { FileDropzone } from "../components/FileDropzone";
import { UploadItemRow } from "../components/UploadItemRow";
import { useUploads } from "../hooks/useUploads";

export function Upload() {
  const { items, addFiles, dismiss } = useUploads();

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold">Upload a document</h1>
        <p className="mt-2 max-w-prose text-slate">
          Add a lab report or prescription as a PDF, or as a photo or scan.
        </p>
      </header>

      <FileDropzone onFiles={addFiles} />

      {items.length > 0 && (
        <ul aria-live="polite" className="space-y-3">
          {items.map((item) => (
            <UploadItemRow key={item.id} item={item} onDismiss={dismiss} />
          ))}
        </ul>
      )}

      <p className="max-w-prose text-sm text-slate">
        Your files are stored only on the server running MediLens, under random file names. You can
        delete any document from the dashboard at any time.
      </p>
    </div>
  );
}
