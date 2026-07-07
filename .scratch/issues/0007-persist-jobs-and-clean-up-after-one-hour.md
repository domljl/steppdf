---
title: Persist jobs and clean up after one hour
labels:
  - ready-for-agent
---

## Parent

.scratch/issues/0001-step-pdf-prd.md

## What to build

Store Conversion Job metadata on disk as JSON and keep Merged PDFs downloadable for up to one hour. Completed jobs should survive app restart when files still exist. Queued or running jobs should be marked failed after restart. Expired originals, intermediates, outputs, and metadata should be cleaned up automatically.

## Acceptance criteria

- [ ] Job metadata is written to disk as JSON.
- [ ] Completed non-expired jobs can still be downloaded after app restart when files still exist.
- [ ] Queued jobs are marked failed after app restart.
- [ ] Running jobs are marked failed after app restart.
- [ ] Merged PDFs expire after one hour.
- [ ] Uploaded originals, intermediate PDFs, final outputs, and metadata are deleted after expiry.
- [ ] Expired jobs are reported as expired instead of ready.
- [ ] Cleanup behavior is covered by tests using time control or configurable short expiry.

## Blocked by

- .scratch/issues/0005-convert-and-merge-into-one-merged-pdf.md
