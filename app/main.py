from typing import Annotated
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.jobs import job_store

app = FastAPI(title="StepPDF")
frontend_build = Path("frontend/build")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/jobs")
async def create_job(
    files: Annotated[list[UploadFile], File()],
    merge_order: Annotated[str, Form()],
    output_filename: Annotated[str, Form()] = "merged_by_dom.pdf",
) -> dict[str, str | int | float | None]:
    return await job_store.create(files, merge_order, output_filename)


@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, str | int | float | None]:
    if job_id not in job_store.jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_store.snapshot(job_id)


@app.get("/jobs/{job_id}/download")
def download_job(job_id: str) -> FileResponse:
    if job_id not in job_store.jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    job_store.snapshot(job_id)
    job = job_store.jobs[job_id]
    if job.phase != "ready" or not job.output_path:
        raise HTTPException(status_code=404, detail="Merged PDF not ready")
    return FileResponse(
        Path(job.output_path),
        media_type="application/pdf",
        filename=job.output_filename,
    )


app.mount("/", StaticFiles(directory=frontend_build, html=True, check_dir=False), name="frontend")
