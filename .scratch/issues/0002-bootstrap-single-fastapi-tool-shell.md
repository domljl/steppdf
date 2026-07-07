---
title: Bootstrap single FastAPI tool shell
labels:
  - ready-for-agent
---

## Parent

.scratch/issues/0001-step-pdf-prd.md

## What to build

Create the initial Step PDF application as a single FastAPI app that serves the first-screen tool shell and a basic health endpoint. The app should be Docker-ready for Render and should establish the simplest structure needed for later Conversion Job slices without adding unused abstractions.

## Acceptance criteria

- [ ] Visiting the app shows the conversion tool as the first screen, not a landing page.
- [ ] The page includes the core tool regions: upload area, file list area, Output Filename field, convert action, progress/result area.
- [ ] The Output Filename field defaults to `merged_by_dom.pdf`.
- [ ] The app exposes a health endpoint suitable for deployment checks.
- [ ] The project can run locally with documented commands.
- [ ] The project includes a Dockerfile suitable for a Render web service.

## Blocked by

None - can start immediately
