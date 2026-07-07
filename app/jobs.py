import asyncio
import json
import os
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable

from fastapi import UploadFile
from pypdf import PdfWriter


JOB_TIMEOUT_SECONDS = 600
JOB_EXPIRY_SECONDS = 3600


@dataclass
class ConversionJob:
    job_id: str
    phase: str
    percent: int
    message: str
    output_filename: str
    output_path: str | None = None
    error_file: str | None = None
    error_detail: str | None = None
    created_at: float = 0
    expires_at: float = 0


class JobFailure(Exception):
    def __init__(self, message: str, file_name: str | None = None, detail: str | None = None) -> None:
        super().__init__(message)
        self.file_name = file_name
        self.detail = detail


async def libreoffice_convert(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    process = await asyncio.to_thread(
        subprocess.run,
        ["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(destination.parent), str(source)],
        check=True,
        capture_output=True,
        text=True,
    )
    produced = destination.parent / f"{source.stem}.pdf"
    if produced != destination:
        shutil.move(produced, destination)
    _ = process


def merge_pdfs(paths: list[Path], output: Path) -> None:
    writer = PdfWriter()
    for path in paths:
        writer.append(str(path))
    with output.open("wb") as file:
        writer.write(file)


class JobStore:
    job_class = ConversionJob

    def __init__(
        self,
        concurrency_limit: int | None = None,
        root: Path | None = None,
        clock: Callable[[], float] = time.time,
        expiry_seconds: int = JOB_EXPIRY_SECONDS,
    ) -> None:
        self.jobs: dict[str, ConversionJob] = {}
        self.semaphore = asyncio.Semaphore(concurrency_limit or int(os.getenv("CONVERSION_CONCURRENCY", "2")))
        self.root = root or Path(os.getenv("JOB_ROOT", "tmp/jobs"))
        self.converter = libreoffice_convert
        self.clock = clock
        self.expiry_seconds = expiry_seconds
        self.load()

    def snapshot(self, job_id: str) -> dict[str, str | int | float | None]:
        self.cleanup_expired()
        return asdict(self.jobs[job_id])

    async def create(self, files: list[UploadFile], merge_order: str, output_filename: str) -> dict[str, str | int | float | None]:
        self.cleanup_expired()
        job_id = uuid.uuid4().hex
        job_dir = self.root / job_id
        input_dir = job_dir / "inputs"
        input_dir.mkdir(parents=True, exist_ok=True)
        saved_files: list[Path] = []
        for index, upload in enumerate(files):
            path = input_dir / f"{index}-{Path(upload.filename or 'file').name}"
            path.write_bytes(await upload.read())
            saved_files.append(path)

        self.jobs[job_id] = ConversionJob(
            job_id=job_id,
            phase="queued",
            percent=0,
            message="Queued",
            output_filename=output_filename or "merged_by_dom.pdf",
            created_at=self.clock(),
            expires_at=self.clock() + self.expiry_seconds,
        )
        self.persist(job_id)
        _ = merge_order
        asyncio.create_task(self._run(job_id, saved_files, job_dir))
        return self.snapshot(job_id)

    def load(self) -> None:
        for metadata in self.root.glob("*/job.json"):
            data = json.loads(metadata.read_text())
            job = self.job_class(**data)
            if job.phase in {"queued", "converting", "merging"}:
                job.phase = "failed"
                job.percent = 100
                job.message = "Job stopped because the app restarted."
                job.output_path = None
            self.jobs[job.job_id] = job
            self.persist(job.job_id)

    def persist(self, job_id: str) -> None:
        job_dir = self.root / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "job.json").write_text(json.dumps(asdict(self.jobs[job_id])))

    def cleanup_expired(self) -> None:
        for job_id, job in list(self.jobs.items()):
            if job.expires_at and self.clock() >= job.expires_at:
                job.phase = "expired"
                job.percent = 100
                job.message = "This job has expired."
                job.output_path = None
                shutil.rmtree(self.root / job_id, ignore_errors=True)

    async def _run(self, job_id: str, files: list[Path], job_dir: Path) -> None:
        try:
            async with asyncio.timeout(JOB_TIMEOUT_SECONDS):
                async with self.semaphore:
                    pdfs = await self._convert_files(job_id, files, job_dir)
                    await self._set(job_id, "merging", 80, "Merging")
                    output = job_dir / "merged.pdf"
                    merge_pdfs(pdfs, output)
                    self.jobs[job_id].output_path = str(output)
                    await self._set(job_id, "ready", 100, "Ready")
        except TimeoutError as error:
            await self._fail(job_id, "Conversion timed out.", detail=str(error))
        except JobFailure as error:
            await self._fail(job_id, str(error), file_name=error.file_name, detail=error.detail)
        except Exception as error:
            await self._fail(job_id, "Could not create merged PDF.", detail=str(error))

    async def _convert_files(self, job_id: str, files: list[Path], job_dir: Path) -> list[Path]:
        converted_dir = job_dir / "converted"
        converted_dir.mkdir(exist_ok=True)
        pdfs: list[Path] = []

        for index, path in enumerate(files, start=1):
            await self._set(job_id, "converting", round((index - 1) / len(files) * 70), f"Converting {index} of {len(files)}")
            if path.suffix.lower() == ".pdf":
                pdfs.append(path)
                continue
            output = converted_dir / f"{path.stem}.pdf"
            try:
                await self.converter(path, output)
            except Exception as error:
                file_name = path.name.split("-", 1)[-1]
                raise JobFailure(f"Could not convert {file_name}.", file_name=file_name, detail=str(error)) from error
            pdfs.append(output)

        return pdfs

    async def _set(self, job_id: str, phase: str, percent: int, message: str) -> None:
        job = self.jobs[job_id]
        job.phase = phase
        job.percent = percent
        job.message = message
        self.persist(job_id)

    async def _fail(self, job_id: str, message: str, file_name: str | None = None, detail: str | None = None) -> None:
        await self._set(job_id, "failed", 100, message)
        job = self.jobs[job_id]
        job.output_path = None
        job.error_file = file_name
        job.error_detail = detail
        self.persist(job_id)


job_store = JobStore()
