from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from backend.app.conversion import ConversionError
import backend.app.main as api_main
from backend.app.sample_data import generate_demo_dataset
from backend.app.storage import SessionStore


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(api_main, "store", SessionStore(tmp_path / "sessions"))
    monkeypatch.setattr(api_main, "FRONTEND_DIST_DIR", tmp_path / "dist")
    with TestClient(api_main.app) as test_client:
        yield test_client


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_demo_session_returns_ready_dataset(client: TestClient) -> None:
    response = client.post("/api/demo")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["summary"]["scanCount"] > 0
    assert payload["sourceKind"] == "demo"


def test_mzml_upload_returns_ready_session(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(api_main, "parse_mzml_file", lambda _: generate_demo_dataset())

    response = client.post(
        "/api/uploads",
        files={"file": ("example.mzML", b"<mzML />", "application/xml")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["summary"]["sourceName"] == "demo-lcms.mzML"


def test_raw_upload_surfaces_conversion_errors(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_conversion(_: Path, __: Path) -> Path:
        raise ConversionError("converter missing")

    monkeypatch.setattr(api_main, "convert_raw_to_mzml", fail_conversion)

    response = client.post(
        "/api/uploads",
        files={"file": ("sample.raw", b"RAW", "application/octet-stream")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "conversion_error"
    assert "converter missing" in payload["message"]


def test_chemistry_metrics_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/chemistry/metrics",
        json={"neutral_mass": 500.0, "charge": 2, "observed_mz": 251.5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["theoreticalMz"] == pytest.approx(251.007276466812)
    assert payload["isotopeSpacing"] == pytest.approx(0.5)
    assert payload["ppmError"] == pytest.approx(1962.9850581369908)


def test_root_returns_404_without_frontend_build(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 404
    assert "Frontend build not found" in response.json()["message"]


def test_unknown_api_path_is_not_swallowed_by_spa_fallback(client: TestClient) -> None:
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Endpoint not found."
