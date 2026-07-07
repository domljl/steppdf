import asyncio
import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path

from fastapi import UploadFile
from pypdf import PdfWriter


JOB_TIMEOUT_SECONDS = 600


@dataclass
class ConversionJob:
    job_id: str
    phase: str
    percent: int
    message: str
    output_filename: str
    output_path: str | None = None


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
    def __init__(self, concurrency_limit: int | None = None, root: Path | None = None) -> None:
        self.jobs: dict[str, ConversionJob] = {}
        self.semaphore = asyncio.Semaphore(concurrency_limit or int(os.getenv("CONVERSION_CONCURRENCY", "2")))
        self.root = root or Path(os.getenv("JOB_ROOT", "tmp/jobs"))
        self.converter = libreoffice_convert

    def snapshot(self, job_id: str) -> dict[str, str | int | None]:
        return asdict(self.jobs[job_id])

    async def create(self, files: list[UploadFile], merge_order: str, output_filename: str) -> dict[str, str | int | None]:
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
        )
        _ = merge_order
        asyncio.create_task(self._run(job_id, saved_files, job_dir))
        return self.snapshot(job_id)

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
        except TimeoutError:
            await self._set(job_id, "failed", 100, "Conversion timed out")
        except Exception as error:
            await self._set(job_id, "failed", 100, str(error))

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
            await self.converter(path, output)
            pdfs.append(output)

        return pdfs

    async def _set(self, job_id: str, phase: str, percent: int, message: str) -> None:
        job = self.jobs[job_id]
        job.phase = phase
        job.percent = percent
        job.message = message


job_store = JobStore()
