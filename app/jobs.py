import asyncio
import os
import uuid
from dataclasses import dataclass, asdict

from fastapi import UploadFile


JOB_TIMEOUT_SECONDS = 600


@dataclass
class ConversionJob:
    job_id: str
    phase: str
    percent: int
    message: str
    output_filename: str


class JobStore:
    def __init__(self, concurrency_limit: int | None = None) -> None:
        self.jobs: dict[str, ConversionJob] = {}
        self.semaphore = asyncio.Semaphore(concurrency_limit or int(os.getenv("CONVERSION_CONCURRENCY", "2")))

    def snapshot(self, job_id: str) -> dict[str, str | int]:
        return asdict(self.jobs[job_id])

    async def create(self, files: list[UploadFile], output_filename: str) -> dict[str, str | int]:
        job_id = uuid.uuid4().hex
        self.jobs[job_id] = ConversionJob(
            job_id=job_id,
            phase="queued",
            percent=0,
            message="Queued",
            output_filename=output_filename or "merged_by_dom.pdf",
        )
        asyncio.create_task(self._run(job_id, len(files)))
        return self.snapshot(job_id)

    async def _run(self, job_id: str, file_count: int) -> None:
        try:
            async with asyncio.timeout(JOB_TIMEOUT_SECONDS):
                async with self.semaphore:
                    await self._set(job_id, "converting", 40, f"Converting 1 of {file_count}")
                    await asyncio.sleep(0)
                    await self._set(job_id, "merging", 80, "Merging")
                    await asyncio.sleep(0)
                    await self._set(job_id, "ready", 100, "Ready")
        except TimeoutError:
            await self._set(job_id, "failed", 100, "Conversion timed out")

    async def _set(self, job_id: str, phase: str, percent: int, message: str) -> None:
        job = self.jobs[job_id]
        job.phase = phase
        job.percent = percent
        job.message = message


job_store = JobStore()
