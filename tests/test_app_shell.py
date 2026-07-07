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
    assert "Step PDF" in response.text
    assert "Drop documents here" in response.text
    assert "Selected files" in response.text
    assert "Output filename" in response.text
    assert "merged_by_dom.pdf" in response.text
    assert "Convert" in response.text
    assert "Progress" in response.text
    assert 'id="file-input"' in response.text
    assert 'id="selected-files"' in response.text
    assert "/static/app.js" in response.text


def test_homepage_exposes_accepted_document_constraints():
    response = client.get("/")

    assert 'data-max-files="50"' in response.text
    assert 'data-max-total-bytes="1073741824"' in response.text
    assert 'name="merge_order"' in response.text
    assert "Files are processed for conversion and automatically deleted after one hour." in response.text


def test_upload_script_supports_validation_remove_and_reorder():
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "Unsupported file type" in response.text
    assert "You can add up to 50 files." in response.text
    assert "Total input must be 1 GB or less." in response.text
    assert "removeFile" in response.text
    assert "moveFile" in response.text
    assert "mergeOrderInput.value" in response.text


def test_upload_script_submits_jobs_and_polls_progress():
    response = client.get("/static/app.js")

    assert 'xhr.open("POST", "/jobs")' in response.text
    assert "xhr.upload.addEventListener" in response.text
    assert "pollJob" in response.text
    assert "fetch(`/jobs/${jobId}`)" in response.text


def test_upload_script_shows_failed_job_details():
    response = client.get("/static/app.js")

    assert "Technical details" in response.text
    assert 'document.createElement("details")' in response.text
    assert "error_detail" in response.text
