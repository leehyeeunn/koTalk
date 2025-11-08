from flask import Flask, request, jsonify
import os, requests, tempfile, subprocess, json
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()
app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("GOOEY_API_KEY")
WHISPER_BASE = "http://127.0.0.1:8000"  # Whisper 서버
GOOEY_URL = "https://api.gooey.ai/v2/Lipsync/form/"

# ---------- FFmpeg helpers ----------

def run_ffmpeg(cmd):
    """Run ffmpeg command with error capture."""
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {' '.join(cmd)}\n{res.stderr}")
    return res

def get_duration_seconds(path: str) -> float:
    """Probe media duration in seconds."""
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    try:
        return float(r.stdout.strip())
    except:
        return 0.0

def to_wav_mono_16k(src_path: str, dst_path: str):
    """Convert any audio to WAV mono 16kHz, with light loudness normalize."""
    cmd = [
        "ffmpeg", "-y",
        "-i", src_path,
        "-vn",
        "-ac", "1",            # mono
        "-ar", "16000",        # 16kHz
        "-af", "loudnorm=I=-20:LRA=11:TP=-2",  # 볼륨 표준화(너무 작은 음성 방지)
        dst_path
    ]
    run_ffmpeg(cmd)

def ensure_min_duration_wav(src_wav: str, dst_wav: str, min_sec: float = 2.5):
    """
    If duration < min_sec, pad with silence to min_sec.
    Keep WAV mono 16kHz.
    """
    dur = get_duration_seconds(src_wav)
    if dur >= min_sec - 0.05:   # 약간 여유
        # 그대로 복사
        run_ffmpeg(["ffmpeg", "-y", "-i", src_wav, "-ac", "1", "-ar", "16000", dst_wav])
        return dur, dur

    # 무음 패딩: apad + -t 로 총 길이 지정
    cmd = [
        "ffmpeg", "-y",
        "-i", src_wav,
        "-af", f"apad=pad_dur={min_sec}",
        "-t", f"{min_sec}",
        "-ac", "1", "-ar", "16000",
        dst_wav
    ]
    run_ffmpeg(cmd)
    new_dur = get_duration_seconds(dst_wav)
    return dur, new_dur

def ffmpeg_webm_to_wav(src_path, dst_path):
    run_ffmpeg(["ffmpeg", "-y", "-i", src_path, "-ar", "44100", "-ac", "1", dst_path])

# ---------- Endpoints ----------

@app.route("/stt", methods=["POST"])
def stt():
    """🎙️ 프론트 → (audio:webm) → 서버에서 wav 변환 → Whisper로 audio 필드 전달"""
    if "audio" not in request.files and "file" not in request.files:
        return jsonify({"error": "audio form field required"}), 400

    f = request.files.get("audio") or request.files.get("file")
    lang = request.form.get("language", "ko")
    timestamps = request.form.get("timestamps", "word")

    try:
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as src, \
             tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as dst:
            f.save(src.name)
            ffmpeg_webm_to_wav(src.name, dst.name)

            with open(dst.name, "rb") as fp:
                files = {"audio": ("record.wav", fp, "audio/wav")}  # Whisper가 audio 필드 기대
                data = {"language": lang, "timestamps": timestamps}
                r = requests.post(f"{WHISPER_BASE}/stt", files=files, data=data, timeout=120)

        return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type", "application/json")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/lipsync", methods=["POST"])
def lipsync():
    """
    🧠 Gooey Lipsync 프록시
    - 어떠한 입력이 와도: WAV mono 16kHz 로 변환하고
    - 최소 2.5초 이상이 되도록 패딩
    - 변환된 WAV를 Gooey에 input_audio 로 업로드
    """
    if not API_KEY:
        return jsonify({"error": "GOOEY_API_KEY not set"}), 500
    if "audio" not in request.files or "image" not in request.files:
        return jsonify({"error": "audio와 image 파일이 필요합니다."}), 400

    audio = request.files["audio"]
    image = request.files["image"]

    try:
        # 1) 업로드 오디오 → temp 저장
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as raw_in:
            audio.save(raw_in.name)

        # 2) 표준 WAV(16k mono)로 변환
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_std:
            to_wav_mono_16k(raw_in.name, wav_std.name)
            std_dur = get_duration_seconds(wav_std.name)

        # 3) 2.5초 미만이면 무음 패딩
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_final:
            before, after = ensure_min_duration_wav(wav_std.name, wav_final.name, min_sec=2.5)

            # 디버그: 길이/사이즈 로그
            size_bytes = os.path.getsize(wav_final.name)
            print(f"[LIPSYNC] duration_before={before:.3f}s duration_after={after:.3f}s size={size_bytes}B")

            audio_fp = open(wav_final.name, "rb")

        # 4) Gooey 업로드
        files = [
            ("input_face", (image.filename, image.stream, image.mimetype or "image/jpeg")),
            ("input_audio", ("voice.wav", audio_fp, "audio/wav")),
        ]
        data = {"json": json.dumps({})}
        headers = {"Authorization": f"Bearer {API_KEY}"}

        r = requests.post(GOOEY_URL, headers=headers, files=files, data=data, timeout=300)

        if not r.ok:
            # 실패 시 서버 로그와 함께 디버그 정보 첨부
            dbg = {
                "note": "Gooey returned non-200",
                "duration_before": before,
                "duration_after": after,
                "content_length": size_bytes,
                "gooey_status": r.status_code,
                "gooey_body": r.text,
            }
            print("[LIPSYNC][ERROR]", dbg)
            return jsonify({"error": "gooey error", "status": 500, "body": r.text, "debug": dbg}), 502

        res = r.json()
        out = (res.get("output") or {}).get("output_video")
        return jsonify({
            "ok": True,
            "output_video": out,
            "gooey": res,
            "debug": {
                "duration_after": after,
                "content_length": size_bytes
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
