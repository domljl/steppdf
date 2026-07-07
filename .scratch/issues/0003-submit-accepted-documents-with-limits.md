---
title: Submit Accepted Documents with limits
labels:
  - ready-for-agent
---

## Parent

.scratch/issues/0001-step-pdf-prd.md

## What to build

Allow users to add Accepted Documents through drag-and-drop or file browsing, see and manage the selected files, reorder them into the desired Merge Order, and submit only jobs that satisfy the file type, file count, and total size limits. Include the privacy notice that files are processed for conversion and automatically deleted after one hour.

## Acceptance criteria

- [ ] Users can add files by dropping them onto the upload area.
- [ ] Users can add files by using a file picker.
- [ ] The UI accepts `.pptx`, `.ppt`, `.docx`, and `.pdf` files.
- [ ] Unsupported file types are rejected with a clear message before conversion.
- [ ] Duplicate filenames are allowed and displayed as separate selected files.
- [ ] Users can remove selected files before submitting.
- [ ] Users can drag selected files into the intended Merge Order.
- [ ] Submission preserves the displayed Merge Order.
- [ ] More than 50 files is rejected with a clear message.
- [ ] More than 1 GB total input is rejected with a clear message.
- [ ] The page shows a privacy notice that files are processed for conversion and automatically deleted after one hour.

## Blocked by

- .scratch/issues/0002-bootstrap-single-fastapi-tool-shell.md
