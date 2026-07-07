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
