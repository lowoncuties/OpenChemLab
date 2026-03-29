from __future__ import annotations

from collections import defaultdict, deque
from ipaddress import ip_address
from math import ceil
from pathlib import Path
import shutil
from threading import Lock
from time import monotonic

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
import uvicorn

from .chemistry import isotope_spacing_hint, neutral_mass_to_mz, ppm_error
from .config import SETTINGS
from .conversion import ConversionError, convert_raw_to_mzml
from .models import SessionRecord
from .parser import build_xic, nearest_spectrum, parse_mzml_file, serialize_spectrum
from .sample_data import generate_demo_dataset
from .storage import SessionStore

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIST_DIR = SETTINGS.frontend_dist_dir
store = SessionStore(SETTINGS.data_dir)
MAX_UPLOAD_BYTES = SETTINGS.max_upload_bytes


class UploadTooLargeError(Exception):
    pass


class UploadRateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, client_key: str) -> int | None:
        if self.limit <= 0 or self.window_seconds <= 0:
            return None

        now = monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            events = self._events[client_key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.limit:
                return max(1, ceil(self.window_seconds - (now - events[0])))
            events.append(now)
        return None


UPLOAD_RATE_LIMITER = UploadRateLimiter(
    SETTINGS.upload_rate_limit_count,
    SETTINGS.upload_rate_limit_window_seconds,
)

app = FastAPI(
    title="LCMS RAW Viewer",
    description="Simple LC-MS viewer with Thermo RAW conversion and mzML fallback.",
)
if SETTINGS.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=SETTINGS.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def upload_guardrails(request: Request, call_next) -> Response:
    if request.method == "POST" and request.url.path == "/api/uploads":
        rate_limit_response = _enforce_upload_rate_limit(request)
        if rate_limit_response is not None:
            return rate_limit_response
        content_length_response = _enforce_content_length_limit(request)
        if content_length_response is not None:
            return content_length_response
    return await call_next(request)


class ChemistryRequest(BaseModel):
    neutral_mass: float = Field(..., gt=0)
    charge: int
    observed_mz: float | None = Field(default=None, gt=0)

    @field_validator("charge")
    @classmethod
    def validate_charge(cls, value: int) -> int:
        if value == 0:
            raise ValueError("Charge must be non-zero.")
        return value


def _format_byte_size(size: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            if value.is_integer():
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def _is_private_proxy_hop(client_host: str | None) -> bool:
    if not client_host:
        return False
    try:
        client_ip = ip_address(client_host)
    except ValueError:
        return False
    return client_ip.is_private or client_ip.is_loopback or client_ip.is_link_local


def _client_key(request: Request) -> str:
    client_host = request.client.host if request.client else None
    if _is_private_proxy_hop(client_host):
        forwarded_for = request.headers.get("x-forwarded-for", "")
        forwarded_ip = forwarded_for.split(",")[0].strip()
        if forwarded_ip:
            return forwarded_ip
        real_ip = request.headers.get("x-real-ip", "").strip()
        if real_ip:
            return real_ip
    if client_host:
        return client_host
    return "unknown"


def _safe_upload_filename(filename: str | None) -> str:
    candidate = Path(filename or "uploaded-file").name.strip()
    return candidate or "uploaded-file"


def _enforce_upload_rate_limit(request: Request) -> Response | None:
    retry_after = UPLOAD_RATE_LIMITER.check(_client_key(request))
    if retry_after is None:
        return None
    return JSONResponse(
        {
            "detail": (
                f"Too many uploads from this client. Try again in about {retry_after} seconds."
            )
        },
        status_code=429,
        headers={"Retry-After": str(retry_after)},
    )


def _enforce_content_length_limit(request: Request) -> Response | None:
    content_length = request.headers.get("content-length")
    if not content_length:
        return None
    try:
        declared_size = int(content_length)
    except ValueError:
        return None
    if declared_size <= MAX_UPLOAD_BYTES:
        return None
    return JSONResponse(
        {"detail": f"Upload exceeds the {_format_byte_size(MAX_UPLOAD_BYTES)} limit."},
        status_code=413,
    )


async def _save_upload(file: UploadFile, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    bytes_written = 0
    with destination.open("wb") as handle:
        while chunk := await file.read(1024 * 1024):
            bytes_written += len(chunk)
            if bytes_written > MAX_UPLOAD_BYTES:
                raise UploadTooLargeError(
                    f"Upload exceeds the {_format_byte_size(MAX_UPLOAD_BYTES)} limit."
                )
            handle.write(chunk)


def _build_ready_record(
    session_id: str,
    source_path: Path,
    filename: str,
    source_kind: str,
    message: str,
    converted_path: Path | None = None,
) -> SessionRecord:
    dataset = parse_mzml_file(converted_path or source_path)
    return SessionRecord(
        session_id=session_id,
        source_path=source_path,
        filename=filename,
        source_kind=source_kind,
        status="ready",
        message=message,
        converted_path=converted_path,
        dataset=dataset,
        notes=[
            "Use the TIC or LC-MS map to choose retention time windows.",
            "Extracted ion chromatograms use ppm tolerance around the requested m/z.",
        ],
    )


def _get_session_or_404(session_id: str) -> SessionRecord:
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/demo")
def create_demo_session() -> dict[str, object]:
    session_id, session_dir = store.create_session_dir()
    record = SessionRecord(
        session_id=session_id,
        source_path=session_dir / "demo-lcms.mzML",
        filename="demo-lcms.mzML",
        source_kind="demo",
        status="ready",
        message="Loaded the synthetic demo dataset.",
        dataset=generate_demo_dataset(),
        notes=["Demo mode is useful for UI exploration before RAW conversion is configured."],
    )
    store.save(record)
    return record.to_response()


@app.post("/api/uploads")
async def upload_dataset(file: UploadFile = File(...)) -> dict[str, object]:
    session_id, session_dir = store.create_session_dir()
    filename = _safe_upload_filename(file.filename)
    source_path = session_dir / filename
    try:
        await _save_upload(file, source_path)
    except UploadTooLargeError as error:
        shutil.rmtree(session_dir, ignore_errors=True)
        raise HTTPException(status_code=413, detail=str(error)) from error

    suffix = source_path.suffix.lower()
    try:
        if suffix == ".raw":
            converted_dir = session_dir / "converted"
            converted_path = convert_raw_to_mzml(source_path, converted_dir)
            record = _build_ready_record(
                session_id=session_id,
                source_path=source_path,
                filename=filename,
                source_kind="raw",
                message="RAW file converted successfully and is ready to explore.",
                converted_path=converted_path,
            )
        elif suffix == ".mzml":
            record = _build_ready_record(
                session_id=session_id,
                source_path=source_path,
                filename=filename,
                source_kind="mzml",
                message="mzML file loaded successfully.",
            )
        else:
            record = SessionRecord(
                session_id=session_id,
                source_path=source_path,
                filename=filename,
                source_kind=suffix.lstrip(".") or "unknown",
                status="parse_error",
                message="Unsupported file type. Upload Thermo RAW or mzML.",
                notes=["The first version supports `.raw` and `.mzML` only."],
            )
    except ConversionError as error:
        record = SessionRecord(
            session_id=session_id,
            source_path=source_path,
            filename=filename,
            source_kind="raw",
            status="conversion_error",
            message=str(error),
            notes=[
                "RAW files are converted automatically when an installed `ThermoRawFileParser` is available.",
                "If the parser is not built yet, the backend can also fall back to ProteoWizard `msconvert`.",
                "You can still use the demo dataset to try the interface while converter support is set up.",
            ],
        )
    except Exception as error:  # noqa: BLE001
        record = SessionRecord(
            session_id=session_id,
            source_path=source_path,
            filename=filename,
            source_kind=suffix.lstrip(".") or "unknown",
            status="parse_error",
            message=f"Unable to read the uploaded data: {error}",
            notes=["Try a known-good mzML export to validate the pipeline."],
        )

    store.save(record)
    return record.to_response()


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str) -> dict[str, object]:
    return _get_session_or_404(session_id).to_response()


@app.get("/api/sessions/{session_id}/spectrum")
def get_spectrum(session_id: str, rt: float = Query(..., ge=0)) -> dict[str, object]:
    session = _get_session_or_404(session_id)
    if not session.dataset:
        raise HTTPException(status_code=409, detail="No parsed dataset available for this session.")
    spectrum = nearest_spectrum(session.dataset, rt)
    return serialize_spectrum(spectrum)


@app.get("/api/sessions/{session_id}/xic")
def get_xic(
    session_id: str,
    mz: float = Query(..., gt=0),
    ppm: float = Query(10.0, gt=0, le=100),
) -> dict[str, object]:
    session = _get_session_or_404(session_id)
    if not session.dataset:
        raise HTTPException(status_code=409, detail="No parsed dataset available for this session.")
    return {
        "targetMz": mz,
        "ppmTolerance": ppm,
        "trace": build_xic(session.dataset, target_mz=mz, ppm_tolerance=ppm),
    }


@app.post("/api/chemistry/metrics")
def calculate_chemistry_metrics(payload: ChemistryRequest) -> dict[str, float | None]:
    theoretical_mz = neutral_mass_to_mz(payload.neutral_mass, payload.charge)
    observed_ppm_error = None
    if payload.observed_mz is not None:
        observed_ppm_error = ppm_error(payload.observed_mz, theoretical_mz)
    return {
        "theoreticalMz": theoretical_mz,
        "ppmError": observed_ppm_error,
        "isotopeSpacing": isotope_spacing_hint(payload.charge),
    }


def _frontend_index_path() -> Path:
    return FRONTEND_DIST_DIR / "index.html"


def _frontend_build_exists() -> bool:
    return _frontend_index_path().is_file()


def _safe_frontend_file(requested_path: str) -> Path | None:
    candidate = (FRONTEND_DIST_DIR / requested_path).resolve()
    try:
        candidate.relative_to(FRONTEND_DIST_DIR.resolve())
    except ValueError:
        return None
    if candidate.is_file():
        return candidate
    return None


if (FRONTEND_DIST_DIR / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST_DIR / "assets"), name="assets")


@app.get("/", include_in_schema=False, response_model=None)
def serve_root() -> Response:
    if not _frontend_build_exists():
        return JSONResponse(
            {
                "message": "Frontend build not found. Run `npm run dev` for local development or `npm run build` for production."
            },
            status_code=404,
        )
    return FileResponse(_frontend_index_path())


@app.get("/{full_path:path}", include_in_schema=False, response_model=None)
def serve_frontend(full_path: str) -> Response:
    if full_path == "api" or full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Endpoint not found.")
    if not _frontend_build_exists():
        raise HTTPException(status_code=404, detail="Frontend build not found.")

    requested_file = _safe_frontend_file(full_path)
    if requested_file:
        return FileResponse(requested_file)
    return FileResponse(_frontend_index_path())


def run() -> None:
    uvicorn.run(
        "backend.app.main:app",
        host=SETTINGS.host,
        port=SETTINGS.port,
        reload=False,
    )


if __name__ == "__main__":
    run()
