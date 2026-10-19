export const MAX_UPLOAD_BYTES = 2 * 1024 * 1024;

export function validateUpload(file: Pick<File, "name" | "size">): string | null {
  if (!file.name.toLowerCase().endsWith(".csv")) return "Choose a .csv file";
  if (file.size === 0) return "This file is empty";
  if (file.size > MAX_UPLOAD_BYTES) return "The file is larger than 2 MB";
  return null;
}
