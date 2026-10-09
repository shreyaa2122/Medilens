export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDateTime(isoDate: string): string {
  return new Date(isoDate).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export function fileTypeLabel(mimeType: string): string {
  if (mimeType === "application/pdf") return "PDF";
  if (mimeType === "image/png") return "PNG image";
  if (mimeType === "image/jpeg") return "JPEG image";
  return "File";
}

export function fileTypeLabelFromName(fileName: string): string {
  const extension = fileName.split(".").pop()?.toLowerCase() ?? "";
  if (extension === "pdf") return "PDF";
  if (extension === "png") return "PNG image";
  if (extension === "jpg" || extension === "jpeg") return "JPEG image";
  return extension ? extension.toUpperCase() : "Unknown";
}
