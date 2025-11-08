import os, tempfile
from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import JSONResponse
from app.schemas import STTResponse, ErrorResponse
from app.config import API_VERSION, MAX_BYTES
from app.common_utils import now_ms, normalize_text
from app.services.audio import ensure_supported_mime, to_standard_wav, enforce_limits
from app.services.whisper_svc import is_ready, transcribe_wav

router = APIRouter()

def error_response(code: str, message: str, status: int = 400, hint: str = None, details: dict = None):
    return JSONResponse(status_code=status, content={
        "error": {"code": code, "message": message, "hint": hint, "details": details}
    })

@router.post("/stt", response_model=STTResponse, responses={400: {"model": ErrorResponse}})
async def stt(
    request: Request,
    audio: UploadFile = File(...),
    language: str = Form("ko"),
    timestamps: str = Form("word")
):
    if not is_ready():
        return error_response("MODEL_NOT_READY", "Model not loaded yet", 503)

    # Content-Length(옵션): 큰 파일 사전 차단
    cl = request.headers.get("content-length")
    if cl and int(cl) > MAX_BYTES:
        return error_response("PAYLOAD_TOO_LARGE", f"Payload exceeds {MAX_BYTES} bytes", 413)

    if not ensure_supported_mime(audio.content_type or ""):
        return error_response("UNSUPPORTED_MEDIA_TYPE", "Only webm/wav/m4a/mp4/aac supported", 415)

    # 업로드 파일 임시 저장
    tmp_in = tempfile.mktemp(suffix=os.path.splitext(audio.filename or ".dat")[1])
    with open(tmp_in, "wb") as f:
        f.write(await audio.read())

    try:
        # 표준 WAV 변환 + 길이 측정
        tmp_wav, duration_s = to_standard_wav(tmp_in)
        enforce_limits(duration_s, int(cl) if cl else 0)

        t0 = now_ms()
        result = transcribe_wav(tmp_wav, language=language, want_word_ts=(timestamps == "word"))
        t1 = now_ms()

        raw_text = result.get("text", "") or ""
        norm_text = normalize_text(raw_text)

        words = []
        # Whisper의 word timestamps는 segments[*].words[*]에 존재
        if timestamps == "word":
            for seg in result.get("segments", []):
                for w in seg.get("words", []):
                    wtext = (w.get("word") or "").strip()
                    if not wtext:
                        continue
                    words.append({
                        "word": wtext,
                        "start": round(float(w.get("start", 0.0)), 2),
                        "end": round(float(w.get("end", 0.0)), 2),
                    })

        return STTResponse(
            rawText=raw_text,
            normText=norm_text,
            words=words,
            duration=round(float(duration_s), 2),
            processing_ms=int(t1 - t0),
            language=language if language != "auto" else (result.get("language") or "auto"),
            model=result.get("model", "unknown"),
            version=API_VERSION
        )

    except HTTPException:
        raise
    except Exception as e:
        return error_response("SERVER_ERROR", f"Unexpected server error: {e}", 500)
    finally:
        # 임시 파일 정리
        try:
            if os.path.exists(tmp_in): os.remove(tmp_in)
        except: pass
        try:
            if os.path.exists(tmp_wav): os.remove(tmp_wav)
        except: pass
