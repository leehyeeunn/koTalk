import time, unicodedata, re
from typing import Tuple

def now_ms() -> int:
    return int(time.time() * 1000)

def normalize_text(text: str) -> str:
    # Unicode NFC + 연속 공백 정리
    t = unicodedata.normalize("NFC", text or "")
    t = re.sub(r"\s+", " ", t).strip()
    return t

def seconds_from_millis(ms: int) -> float:
    return round(ms / 1000.0, 2)
