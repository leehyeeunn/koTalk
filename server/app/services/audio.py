import os, subprocess, tempfile
from pydub import AudioSegment
from typing import Tuple
from app.config import MAX_SECONDS

SUPPORTED_MIME = {"audio/webm", "audio/wav", "audio/x-wav", "audio/m4a", "audio/mp4", "audio/aac"}

def ensure_supported_mime(mime: str) -> bool:
    return mime in SUPPORTED_MIME

def webm_to_wav16k(in_path: str, out_path: str) -> None:
    # ffmpeg로 16kHz mono PCM wav
    cmd = [
        "ffmpeg", "-y", "-i", in_path,
        "-ac", "1", "-ar", "16000", "-f", "wav", out_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def get_duration_seconds(path: str) -> float:
    # pydub으로 길이(ms) → s
    audio = AudioSegment.from_file(path)
    return round(len(audio) / 1000.0, 2)

def to_standard_wav(file_path: str) -> Tuple[str, float]:
    """
    입력 파일을 16kHz mono WAV로 변환해서 temp 파일 경로와 길이(s)를 반환
    """
    tmp_wav = tempfile.mktemp(suffix=".wav")
    webm_to_wav16k(file_path, tmp_wav)
    dur = get_duration_seconds(tmp_wav)
    return tmp_wav, dur

def enforce_limits(duration_s: float, content_length: int):
    if duration_s > MAX_SECONDS:
        from fastapi import HTTPException
        raise HTTPException(status_code=413, detail={
            "code": "PAYLOAD_TOO_LARGE",
            "message": f"Audio length exceeds {MAX_SECONDS} seconds.",
            "hint": "Try recording a shorter clip.",
            "details": {"maxSeconds": MAX_SECONDS}
        })
    # content_length는 라우터에서 헤더로 검증(옵션)
