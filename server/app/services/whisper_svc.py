import whisper, torch
from typing import Dict, Any, List
from app.config import MODEL_NAME, LANGUAGE_DEFAULT

_model = None
_device = "cuda" if torch.cuda.is_available() else "cpu"
_ready_error = None

def load_model():
    global _model, _ready_error
    try:
        _model = whisper.load_model(MODEL_NAME, device=_device)
        _ready_error = None
    except Exception as e:
        _ready_error = str(e)

def is_ready() -> bool:
    return _model is not None and _ready_error is None

def ready_error() -> str:
    return _ready_error or ""

def device_name() -> str:
    return _device

def transcribe_wav(path: str, language: str = LANGUAGE_DEFAULT, want_word_ts: bool = True) -> Dict[str, Any]:
    """
    Whisper transcribe 호출. word timestamps를 원하면 True.
    """
    result = _model.transcribe(
        path,
        language=language if language != "auto" else None,
        word_timestamps=want_word_ts,
        # 초기엔 VAD off (문장 자르기 이슈 방지). 필요시 넣기: vad_filter=True
        # fp16=True if _device == "cuda" else False
    )
    return result
