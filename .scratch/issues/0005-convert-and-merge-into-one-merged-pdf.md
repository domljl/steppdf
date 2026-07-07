---
title: Convert and merge into one Merged PDF
labels:
  - ready-for-agent
---

## Parent

.scratch/issues/0001-step-pdf-prd.md

## What to build

Convert Office Accepted Documents to PDF with LibreOffice, pass existing PDFs through, and merge every input into one Merged PDF in the user's Merge Order. When the job is ready, the browser should show a download action that uses the chosen Output Filename or `merged_by_dom.pdf` when omitted.

## Acceptance criteria

- [ ] `.pptx`, `.ppt`, and `.docx` files are converted to PDF through LibreOffice.
- [ ] Existing `.pdf` files are included without conversion.
- [ ] The final Merged PDF follows the submitted Merge Order.
- [ ] The app always produces one Merged PDF for a successful Conversion Job.
- [ ] The download uses the user-provided Output Filename when present.
- [ ] The download uses `merged_by_dom.pdf` when Output Filename is omitted.
- [ ] The Docker image installs LibreOffice and practical common fonts.
- [ ] A smoke test proves LibreOffice can convert at least one sample or generated document.
- [ ] Behavior tests verify merge order without depending on LibreOffice internals.

## Blocked by

- .scratch/issues/0004-create-conversion-job-and-estimated-progress.md
