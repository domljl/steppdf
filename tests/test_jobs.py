import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader, PdfWriter

from app.main import app
from app.jobs import JobStore, job_store


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_job_store():
    root = job_store.root
    converter = job_store.converter
    yield
    job_store.root = root
    job_store.converter = converter


def pdf_bytes(page_count: int = 1) -> bytes:
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=72, height=72)
    output = __import__("io").BytesIO()
    writer.write(output)
    return output.getvalue()


def wait_until_ready(job_id: str) -> dict:
    for _ in range(10):
        body = client.get(f"/jobs/{job_id}").json()
        if body["phase"] == "ready":
            return body
    return body


def wait_until_done(job_id: str) -> dict:
    for _ in range(10):
        body = client.get(f"/jobs/{job_id}").json()
        if body["phase"] in {"ready", "failed"}:
            return body
    return body


def test_create_conversion_job_returns_job_status():
    response = client.post(
        "/jobs",
        files=[("files", ("deck.pdf", pdf_bytes(), "application/pdf"))],
        data={"merge_order": '["deck.pdf"]', "output_filename": "merged_by_dom.pdf"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"]
    assert body["phase"] in {"queued", "converting", "merging", "ready"}
    assert 0 <= body["percent"] <= 100


def test_get_conversion_job_reports_user_facing_status():
    created = client.post(
        "/jobs",
        files=[("files", ("one.pdf", pdf_bytes(), "application/pdf"))],
        data={"merge_order": '["one.pdf"]', "output_filename": "out.pdf"},
    ).json()

    response = client.get(f"/jobs/{created['job_id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == created["job_id"]
    assert body["phase"] in {"queued", "converting", "merging", "ready"}
    assert isinstance(body["message"], str)
    assert 0 <= body["percent"] <= 100


def test_successful_job_downloads_one_merged_pdf_in_merge_order(tmp_path):
    job_store.root = tmp_path
    response = client.post(
        "/jobs",
        files=[
            ("files", ("second.pdf", pdf_bytes(2), "application/pdf")),
            ("files", ("first.pdf", pdf_bytes(1), "application/pdf")),
        ],
        data={"merge_order": '["second.pdf","first.pdf"]', "output_filename": "ordered.pdf"},
    )
    job_id = response.json()["job_id"]

    job = wait_until_ready(job_id)
    download = client.get(f"/jobs/{job_id}/download")

    assert job["phase"] == "ready"
    assert download.status_code == 200
    assert download.headers["content-disposition"] == 'attachment; filename="ordered.pdf"'
    assert len(PdfReader(__import__("io").BytesIO(download.content)).pages) == 3


def test_duplicate_filenames_are_merged_without_overwrite(tmp_path):
    job_store.root = tmp_path
    response = client.post(
        "/jobs",
        files=[
            ("files", ("same.pdf", pdf_bytes(1), "application/pdf")),
            ("files", ("same.pdf", pdf_bytes(2), "application/pdf")),
        ],
        data={"merge_order": '["same.pdf","same.pdf"]', "output_filename": "duplicates.pdf"},
    )
    job_id = response.json()["job_id"]

    job = wait_until_ready(job_id)
    download = client.get(f"/jobs/{job_id}/download")

    assert job["phase"] == "ready"
    assert len(PdfReader(__import__("io").BytesIO(download.content)).pages) == 3


def test_office_documents_are_converted_before_merge(tmp_path):
    job_store.root = tmp_path
    converted = pdf_bytes(1)

    async def fake_converter(source, destination):
        destination.write_bytes(converted)

    job_store.converter = fake_converter
    response = client.post(
        "/jobs",
        files=[("files", ("deck.pptx", b"deck", "application/vnd.openxmlformats-officedocument.presentationml.presentation"))],
        data={"merge_order": '["deck.pptx"]', "output_filename": ""},
    )
    job_id = response.json()["job_id"]

    job = wait_until_ready(job_id)
    download = client.get(f"/jobs/{job_id}/download")

    assert job["phase"] == "ready"
    assert download.headers["content-disposition"] == 'attachment; filename="merged_by_dom.pdf"'
    assert len(PdfReader(__import__("io").BytesIO(download.content)).pages) == 1


def test_failed_file_fails_whole_job_without_download(tmp_path):
    job_store.root = tmp_path

    async def fake_converter(source, destination):
        raise RuntimeError("LibreOffice said no")

    job_store.converter = fake_converter
    response = client.post(
        "/jobs",
        files=[
            ("files", ("first.pdf", pdf_bytes(1), "application/pdf")),
            ("files", ("bad.pptx", b"deck", "application/vnd.openxmlformats-officedocument.presentationml.presentation")),
        ],
        data={"merge_order": '["first.pdf","bad.pptx"]', "output_filename": "never.pdf"},
    )
    job_id = response.json()["job_id"]

    job = wait_until_done(job_id)
    download = client.get(f"/jobs/{job_id}/download")

    assert job["phase"] == "failed"
    assert job["message"] == "Could not convert bad.pptx."
    assert job["error_file"] == "bad.pptx"
    assert "LibreOffice said no" in job["error_detail"]
    assert download.status_code == 404


def test_ready_job_metadata_survives_restart(tmp_path):
    job_store.root = tmp_path
    response = client.post(
        "/jobs",
        files=[("files", ("one.pdf", pdf_bytes(1), "application/pdf"))],
        data={"merge_order": '["one.pdf"]', "output_filename": "kept.pdf"},
    )
    job_id = response.json()["job_id"]
    assert wait_until_ready(job_id)["phase"] == "ready"

    restarted = JobStore(root=tmp_path)

    assert restarted.snapshot(job_id)["phase"] == "ready"
    assert (tmp_path / job_id / "job.json").exists()


@pytest.mark.parametrize("phase", ["queued", "converting", "merging"])
def test_unfinished_jobs_are_failed_after_restart(tmp_path, phase):
    job_dir = tmp_path / phase
    job_dir.mkdir()
    (job_dir / "job.json").write_text(
        f'{{"job_id":"{phase}","phase":"{phase}","percent":10,"message":"Converting",'
        '"output_filename":"out.pdf","output_path":null,"error_file":null,"error_detail":null,'
        '"created_at":1.0,"expires_at":9999.0}'
    )

    restarted = JobStore(root=tmp_path, clock=lambda: 2.0)

    job = restarted.snapshot(phase)
    assert job["phase"] == "failed"
    assert job["message"] == "Job stopped because the app restarted."


def test_expired_jobs_are_reported_expired_and_deleted(tmp_path):
    now = 1_000.0
    store = JobStore(root=tmp_path, clock=lambda: now, expiry_seconds=1)
    job_dir = tmp_path / "done"
    job_dir.mkdir(parents=True)
    output = job_dir / "merged.pdf"
    output.write_bytes(pdf_bytes(1))
    store.jobs["done"] = store.job_class(
        job_id="done",
        phase="ready",
        percent=100,
        message="Ready",
        output_filename="out.pdf",
        output_path=str(output),
        created_at=now - 2,
        expires_at=now - 1,
    )
    store.persist("done")

    assert store.snapshot("done")["phase"] == "expired"
    assert not job_dir.exists()
