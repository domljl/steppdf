export const acceptedExtensions = new Set(["pptx", "ppt", "docx", "pdf"]);
export const maxFiles = 50;
export const maxTotalBytes = 1024 * 1024 * 1024;

export type FileLike = {
  name: string;
  size: number;
};

export type FileEntry<T extends FileLike = FileLike> = {
  id: number;
  file: T;
};

export function extensionFor(file: FileLike) {
  return file.name.split(".").pop()?.toLowerCase() ?? "";
}

export function validateFiles<T extends FileLike>(
  existing: FileEntry<T>[],
  incoming: T[],
  limits = { maxFiles, maxTotalBytes },
) {
  const nextFiles = [...existing.map((entry) => entry.file), ...incoming];

  if (nextFiles.length > limits.maxFiles) return "You can add up to 50 files.";

  const unsupportedFile = incoming.find((file) => !acceptedExtensions.has(extensionFor(file)));
  if (unsupportedFile) return `Unsupported file type: ${unsupportedFile.name}`;

  const totalBytes = nextFiles.reduce((total, file) => total + file.size, 0);
  if (totalBytes > limits.maxTotalBytes) return "Total input must be 1 GB or less.";

  return "";
}

export function moveEntry<T>(entries: T[], fromIndex: number, toIndex: number) {
  if (toIndex < 0 || toIndex >= entries.length || fromIndex === toIndex) return entries;

  const next = entries.slice();
  const [entry] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, entry);
  return next;
}

export function mergeOrder(entries: FileEntry[]) {
  return JSON.stringify(entries.map((entry) => entry.file.name));
}
