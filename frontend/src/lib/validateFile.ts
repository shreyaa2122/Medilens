// Quick checks in the browser so people get instant feedback.
// The server repeats these checks (and also inspects the real file content),
// so this is a convenience, not the security boundary.

const ALLOWED_EXTENSIONS = ["pdf", "png", "jpg", "jpeg"];
export const MAX_UPLOAD_MB = Number(import.meta.env.VITE_MAX_UPLOAD_MB ?? 10);

export function validateFile(file: File): string | null {
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  if (!file.name.includes(".") || !ALLOWED_EXTENSIONS.includes(extension)) {
    return "Unsupported file type. Please upload a PDF, JPG, JPEG, or PNG.";
  }
  if (file.size === 0) {
    return "The file is empty. Please choose a file that contains a document.";
  }
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
    return `The file is larger than ${MAX_UPLOAD_MB} MB. Please upload a smaller file.`;
  }
  return null;
}
