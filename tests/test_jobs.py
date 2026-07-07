from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


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
