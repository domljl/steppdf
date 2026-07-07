---
title: Create Conversion Job and estimated progress
labels:
  - ready-for-agent
---

## Parent

.scratch/issues/0001-step-pdf-prd.md

## What to build

Turn a valid submission into an asynchronous Conversion Job. The browser should show real upload progress, then poll job state and display queued, converting, merging, ready, failed, or expired status with estimated percentage progress. At most two Conversion Jobs should run at once by default, with the limit configurable.

## Acceptance criteria

- [ ] Submitting a valid selection creates a Conversion Job and returns a job identifier.
- [ ] Upload progress is displayed while files transfer.
- [ ] The browser polls job status after submission.
- [ ] Job status includes a user-facing phase and percentage.
- [ ] Queued jobs are visibly marked as waiting.
- [ ] At most two jobs run concurrently by default.
- [ ] The concurrency limit can be changed by environment variable.
- [ ] A Conversion Job has a 10 minute timeout.
- [ ] Tests use a fake converter or worker so progress behavior is deterministic.

## Blocked by

- .scratch/issues/0003-submit-accepted-documents-with-limits.md
