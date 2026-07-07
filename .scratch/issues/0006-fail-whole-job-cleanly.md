---
title: Fail whole job cleanly
labels:
  - ready-for-agent
---

## Parent

.scratch/issues/0001-step-pdf-prd.md

## What to build

If any Accepted Document fails conversion or merging, fail the whole Conversion Job and do not expose a partial Merged PDF. Show a friendly failure message naming the failed file where possible, with expandable technical details for debugging.

## Acceptance criteria

- [ ] A failure in any input marks the whole Conversion Job failed.
- [ ] Failed jobs do not expose a download for a partial Merged PDF.
- [ ] The user sees friendly error text.
- [ ] The error identifies the failed file when known.
- [ ] Technical details are available in an expandable section.
- [ ] Tests cover a failed file in a multi-file job.

## Blocked by

- .scratch/issues/0005-convert-and-merge-into-one-merged-pdf.md
