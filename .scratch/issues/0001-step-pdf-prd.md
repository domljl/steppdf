---
title: StepPDF conversion app PRD
labels:
  - ready-for-agent
---

## Problem Statement

The User Group needs a hosted app at `steppdf.dominiclim.dev` where anyone with Link Access can upload presentation, Word, and PDF files, reorder them, convert them to PDF where needed, and download one Merged PDF. Today this workflow requires manual conversion in office tools and separate PDF merging, which is slow and error-prone when many files need to be combined in a specific Merge Order.

## Solution

Build StepPDF as a single FastAPI web app deployed as a Docker-based Render service. The first screen is the tool itself: a dropzone, draggable file list, Output Filename field defaulting to `merged_by_dom.pdf`, convert button, progress display, and final download or failure state.

Users can upload up to 50 Accepted Documents with a total input size of 1 GB. Accepted Documents are `.pptx`, `.ppt`, `.docx`, and `.pdf`. Office documents are converted to PDF with LibreOffice, existing PDFs pass through, and every input is combined into one Merged PDF using the user-controlled Merge Order. If any input fails, the whole Conversion Job fails without producing a partial result.

Conversion Jobs run asynchronously, with at most two jobs running at once by default and excess jobs queued. Progress is shown as an estimated percentage: upload progress is measured directly, while conversion and merge progress are estimated from completed files and job phase. Job metadata is stored on disk as JSON, outputs are available for up to one hour, and files are cleaned up automatically.

## User Stories

1. As a user with the StepPDF link, I want to open the app without an account, so that I can start converting files immediately.
2. As a user, I want the first screen to be the conversion tool, so that I do not have to pass through a landing page.
3. As a user, I want to drag files onto a dropzone, so that I can quickly add documents.
4. As a user, I want to browse for files, so that I can upload documents without drag-and-drop.
5. As a user, I want to upload `.pptx` files, so that I can convert PowerPoint presentations to PDF.
6. As a user, I want to upload `.ppt` files, so that I can convert older PowerPoint presentations.
7. As a user, I want to upload `.docx` files, so that I can include Word documents in the final PDF.
8. As a user, I want to upload existing `.pdf` files, so that I can merge them with converted documents.
9. As a user, I want unsupported files rejected before conversion, so that I know what must be fixed.
10. As a user, I want duplicate filenames allowed, so that I do not have to rename files before upload.
11. As a user, I want to see all selected files in a list, so that I can confirm the documents in my Conversion Job.
12. As a user, I want to remove a selected file before conversion, so that mistakes are easy to correct.
13. As a user, I want to reorder files by dragging them, so that the Merged PDF follows the correct Merge Order.
14. As a user, I want the app to preserve my Merge Order when submitting, so that the output matches what I arranged.
15. As a user, I want to set an Output Filename, so that the downloaded Merged PDF has a useful name.
16. As a user, I want `merged_by_dom.pdf` used when I leave the Output Filename blank, so that downloads still have a predictable name.
17. As a user, I want one Merged PDF every time, so that the workflow is consistent.
18. As a user, I want a clear file limit, so that I know a Conversion Job can contain at most 50 files.
19. As a user, I want a clear size limit, so that I know a Conversion Job can contain at most 1 GB total input.
20. As a user, I want oversized jobs rejected clearly, so that I can split the work and retry.
21. As a user, I want upload progress, so that I know large files are still transferring.
22. As a user, I want conversion progress, so that I know the job is still moving.
23. As a user, I want progress shown as a percentage, so that status is easy to scan.
24. As a user, I want progress to show the current phase, so that I understand whether the app is uploading, converting, merging, ready, or failed.
25. As a user, I want queued jobs to show that they are waiting, so that I understand delays when other jobs are running.
26. As a user, I want the final download button to appear when the Merged PDF is ready, so that I can download it immediately.
27. As a user, I want the Merged PDF to be available for one hour, so that brief interruptions do not lose the result.
28. As a user, I want files deleted automatically after one hour, so that uploaded documents do not sit around indefinitely.
29. As a user, I want a privacy notice near upload, so that I know files are processed for conversion and automatically deleted after one hour.
30. As a user, I want a friendly error when conversion fails, so that I know which file needs attention.
31. As a user, I want expandable technical details on failure, so that debugging information is available when needed.
32. As a user, I want the whole job to fail if any file fails, so that I do not accidentally use an incomplete Merged PDF.
33. As a user, I want conversion to aim for PowerPoint or Word export fidelity, so that the PDF looks as close as practical to the source file.
34. As a user, I want common fonts supported where possible, so that converted slides and documents look closer to the originals.
35. As a maintainer, I want LibreOffice used first, so that conversion works in Docker without Microsoft automation.
36. As a maintainer, I want Microsoft-based conversion left out of the first version, so that the app can ship without external office API setup.
37. As a maintainer, I want only two concurrent Conversion Jobs by default, so that LibreOffice does not exhaust server memory.
38. As a maintainer, I want the concurrency limit configurable, so that I can tune it after seeing real Render resource use.
39. As a maintainer, I want disk-backed job metadata, so that completed jobs can survive a server restart when files still exist.
40. As a maintainer, I want queued or running jobs marked failed after restart, so that the app does not pretend interrupted conversions are still valid.
41. As a maintainer, I want a conversion timeout of 10 minutes per job, so that stuck LibreOffice processes do not block the service forever.
42. As a maintainer, I want no database in the first version, so that deployment stays simple.
43. As a maintainer, I want one FastAPI app serving UI and API, so that deployment has one service and one URL.
44. As a maintainer, I want Docker deployment on Render, so that LibreOffice and fonts can be installed consistently.
45. As a maintainer, I want a LibreOffice smoke test with sample files, so that we know the conversion binary works in the target environment.

## Implementation Decisions

- Build one FastAPI app that serves both the browser UI and JSON/file endpoints.
- Use plain browser JavaScript for drag-and-drop upload, drag reorder, upload progress, polling, and download state.
- Use Link Access only. No accounts, login, sessions, roles, or per-user history.
- Use Accepted Documents: `.pptx`, `.ppt`, `.docx`, and `.pdf`.
- Enforce 50 files maximum, 1 GB total input maximum, and 10 minutes maximum per Conversion Job.
- Model each submission as a Conversion Job with phases: queued, uploading, converting, merging, ready, failed, expired.
- Store job metadata on disk as JSON. Store uploaded originals, intermediate converted PDFs, and final Merged PDF in job-specific directories.
- On restart, reload non-expired completed jobs when files still exist. Mark queued or running jobs failed.
- Run at most two conversions at once by default. Make this limit configurable by environment variable.
- Convert Office documents to PDF using LibreOffice. Pass existing PDFs through without conversion.
- Merge all PDFs into one Merged PDF in Merge Order.
- Fail the whole Conversion Job if any Accepted Document fails conversion or merge.
- Provide friendly error text and expandable technical details for failed jobs.
- Keep Merged PDFs available for up to one hour. Rely on automatic cleanup only; no manual delete button in the first version.
- Use `merged_by_dom.pdf` as the default Output Filename.
- Deploy to Render as a Docker web service at `steppdf.dominiclim.dev`.
- Install LibreOffice and common Microsoft-compatible fonts in the Docker image where legally and practically available.
- Treat LibreOffice fidelity as good enough for the first version based on the local sample spike. Keep Microsoft-based conversion as the likely upgrade path if fidelity is not good enough.

## Testing Decisions

- Prefer one high-level FastAPI app seam for most tests: submit files, poll job progress, download the Merged PDF, and inspect externally visible outcomes.
- Use a fake converter in behavior tests so tests are fast and deterministic.
- Add one small LibreOffice smoke test using sample files or generated documents to prove the real conversion binary works in the environment.
- Test external behavior, not implementation details: limits, accepted extensions, Merge Order, Output Filename, job phases, failure behavior, cleanup, and download availability.
- Test that any single failed input fails the whole Conversion Job and does not expose a partial Merged PDF.
- Test disk-backed job metadata by simulating restart behavior for completed, queued, and running jobs.
- Test that duplicate filenames are accepted and still merge in the intended list order.
- Test cleanup behavior with time control or configurable short expiry.
- No prior test patterns exist because the repo currently has no application code.

## Out of Scope

- User accounts, authentication, authorization, billing, teams, or audit logs.
- Public marketing site or landing page.
- Database-backed persistence.
- Manual delete button for jobs.
- Permanent file storage or download history.
- Real per-slide LibreOffice progress.
- Exact PowerPoint rendering guarantees.
- Microsoft Graph, OneDrive, SharePoint, or desktop PowerPoint automation.
- Antivirus scanning.
- OCR, image conversion, `.doc`, `.xlsx`, `.xls`, `.odt`, or arbitrary file conversion.
- Separate frontend service, Next.js, React, or a split backend/frontend deployment.
- Multiple Render services or worker fleet.

## Further Notes

LibreOffice was tested locally against five sample PPTX files and produced PDFs successfully when run outside the local sandbox. The sandbox failure was macOS-specific process execution, not a sample conversion failure. Generated spike outputs live under `tmp/conversion-spike/` and should be treated as disposable.
