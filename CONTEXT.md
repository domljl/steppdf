# StepPDF

StepPDF is a hosted document conversion app for a small trusted group.

## Language

**User Group**:
The small set of people allowed to use the hosted app.
_Avoid_: Public users, customers, tenants

**Link Access**:
Anyone with the app URL can use the converter; the app does not identify individual people.
_Avoid_: Accounts, login, authentication

**Conversion Job**:
A single request containing up to 50 uploaded files, with at most 1 GB total input, that produces one downloadable PDF. If any input fails, the job fails without producing a partial result.
_Avoid_: Batch, session, project

**Accepted Document**:
A user-uploaded `.pptx`, `.ppt`, `.docx`, or `.pdf` file that can participate in a conversion job.
_Avoid_: Any file, attachment, asset

**Merge Order**:
The user-controlled file order used to combine converted PDFs into the final PDF.
_Avoid_: Sort order, upload order

**Merged PDF**:
The single PDF produced by a conversion job after all accepted inputs are converted or passed through and combined in merge order. It is available for immediate download for up to one hour.
_Avoid_: Output files, export bundle

**Output Filename**:
The download name chosen by the user for the merged PDF; when omitted, the app uses `merged_by_dom.pdf`.
_Avoid_: Export name, job name
