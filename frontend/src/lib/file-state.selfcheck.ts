import assert from "node:assert/strict";
import { mergeOrder, moveEntry, validateFiles, type FileEntry, type FileLike } from "./file-state.ts";

const pdf = (name: string, size = 1): FileLike => ({ name, size });
const files: FileEntry[] = [
  { id: 1, file: pdf("one.pdf") },
  { id: 2, file: pdf("two.docx") },
];

assert.equal(validateFiles(files, [pdf("bad.txt")]), "Unsupported file type: bad.txt");
assert.equal(validateFiles(files, Array.from({ length: 49 }, (_, index) => pdf(`${index}.pdf`))), "You can add up to 50 files.");
assert.equal(validateFiles(files, [pdf("huge.pdf", 1024 * 1024 * 1024)]), "Total input must be 1 GB or less.");
assert.deepEqual(moveEntry(files, 0, 1).map((entry) => entry.id), [2, 1]);
assert.equal(mergeOrder(files), '["one.pdf","two.docx"]');
