from fastapi.testclient import TestClient
from pypdf import PdfReader, PdfWriter

from app.main import app
from app.jobs import job_store


client = TestClient(app)


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


def test_create_conversion_job_returns_job_status():
    response = client.post(
        "/jobs",
        files=[("files", ("deck.pptx", b"pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"))],
        data={"merge_order": '["deck.pptx"]', "output_filename": "merged_by_dom.pdf"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"]
    assert body["phase"] in {"queued", "converting", "merging", "ready"}
    assert 0 <= body["percent"] <= 100


def test_get_conversion_job_reports_user_facing_status():
    created = client.post(
        "/jobs",
        files=[("files", ("one.pdf", b"%PDF-1.4", "application/pdf"))],
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
            ("files", ("first.pdf", pdf_bytes(1), "application/pdf")),
            ("files", ("second.pdf", pdf_bytes(2), "application/pdf")),
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
