from fastapi import APIRouter
from app.schemas import HealthResponse
from app.config import API_VERSION, MODEL_NAME
from app.services.whisper_svc import is_ready, ready_error, device_name

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health():
    ok = is_ready()
    return HealthResponse(
        ready=ok,
        model=MODEL_NAME,
        device=device_name(),
        version=API_VERSION,
        error=None if ok else ready_error()
    )
