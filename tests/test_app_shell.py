from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint_reports_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_homepage_is_conversion_tool_shell():
    response = client.get("/")

    assert response.status_code == 200
    assert "StepPDF" in response.text
    assert "Browse files" in response.text
    assert "Auto convert and combine PDFs in the order you want." in response.text
    assert 'id="file-input"' in response.text
    assert 'id="start-page"' in response.text
    assert "_app/immutable" in response.text
    assert "/static/app.js" not in response.text


def test_homepage_exposes_accepted_document_constraints():
    response = client.get("/")

    assert 'data-max-files="50"' in response.text
    assert 'data-max-total-bytes="1073741824"' in response.text
    assert 'name="merge_order"' in response.text
    assert "Files are automatically deleted after one hour." in response.text


def test_built_frontend_assets_include_validation_remove_and_reorder():
    assets = "\n".join(path.read_text() for path in sorted(Path("frontend/build/_app").rglob("*.js")))

    assert "Unsupported file type" in assets
    assert "You can add up to 50 files." in assets
    assert "Total input must be 1 GB or less." in assets
    assert "Remove file" in assets
    assert "Move file up" in assets
    assert "merge_order" in assets


def test_built_frontend_submits_jobs_and_polls_progress():
    assets = "\n".join(path.read_text() for path in sorted(Path("frontend/build/_app").rglob("*.js")))

    assert 'open("POST","/jobs")' in assets
    assert "upload.addEventListener" in assets
    assert "fetch(`/jobs/${" in assets
    assert "setTimeout" in assets


def test_built_frontend_shows_failed_job_details():
    assets = "\n".join(path.read_text() for path in sorted(Path("frontend/build/_app").rglob("*.js")))

    assert "Technical details" in assets
    assert "error_detail" in assets
