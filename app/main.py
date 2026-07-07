from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.jobs import job_store

app = FastAPI(title="Step PDF")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {"default_filename": "merged_by_dom.pdf"},
    )


@app.post("/jobs")
async def create_job(
    files: Annotated[list[UploadFile], File()],
    merge_order: Annotated[str, Form()],
    output_filename: Annotated[str, Form()] = "merged_by_dom.pdf",
) -> dict[str, str | int]:
    _ = merge_order
    return await job_store.create(files, output_filename)


@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, str | int]:
    if job_id not in job_store.jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_store.snapshot(job_id)
