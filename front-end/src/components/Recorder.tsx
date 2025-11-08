"use client";

import { useEffect, useRef, useState } from "react";

type Phase = "idle" | "recording" | "uploading" | "processing" | "done" | "error";

const BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://127.0.0.1:8000";

export default function Recorder() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [recording, setRecording] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [result, setResult] = useState<{ text?: string; ipa?: string; roman?: string }>({});
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  const media = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunks = useRef<Blob[]>([]);

  // ObjectURL 정리
  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
      stopTracks();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stopTracks = () => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  };

  const pickMimeType = () => {
    // Chrome/Edge: audio/webm; Safari iOS는 MediaRecorder 미지원(대체 필요)
    if (MediaRecorder.isTypeSupported("audio/webm")) return "audio/webm";
    if (MediaRecorder.isTypeSupported("audio/mp4")) return "audio/mp4";
    // 최후: 브라우저 기본
    return "";
  };

  const start = async () => {
    try {
      setErr(null);
      setResult({});
      setPhase("idle");

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mimeType = pickMimeType();
      const rec = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);

      chunks.current = [];
      rec.ondataavailable = (e) => e.data.size && chunks.current.push(e.data);
      rec.onerror = (e: any) => {
        console.error("MediaRecorder error:", e);
        setErr(e?.message || "녹음 중 오류");
        setPhase("error");
      };
      rec.onstop = async () => {
        try {
          setPhase("uploading");
          const blob = new Blob(chunks.current, { type: mimeType || "audio/webm" });
          const url = URL.createObjectURL(blob);
          setAudioUrl((prev) => {
            if (prev) URL.revokeObjectURL(prev);
            return url;
          });

          // 1) STT
          setPhase("processing");
          const fd = new FormData();
          fd.append("audio", blob, `record.${mimeType.includes("mp4") ? "m4a" : "webm"}`);
          fd.append("language", "ko");
          fd.append("timestamps", "word");

          const sttRes = await fetch(`${BASE}/stt`, { method: "POST", body: fd });
          if (!sttRes.ok) {
            const tx = await sttRes.text();
            throw new Error(`/stt ${sttRes.status}: ${tx}`);
          }
          const sttData = await sttRes.json();
          const text: string = sttData.rawText || sttData.normText || "";
          if (!text) throw new Error("STT 결과가 비었습니다.");

          // 2) IPA
          const ipaRes = await fetch(`${BASE}/ipa`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text }),
          });
          if (!ipaRes.ok) {
            const tx = await ipaRes.text();
            throw new Error(`/ipa ${ipaRes.status}: ${tx}`);
          }
          const ipaData = await ipaRes.json();

          // 3) 결과
          setResult({
            text: ipaData.original ?? text,
            ipa: ipaData.ipa,
            roman: ipaData.romanized,
          });
          setPhase("done");
        } catch (e: any) {
          console.error(e);
          setErr(e?.message || "처리 실패");
          setPhase("error");
        } finally {
          chunks.current = [];
          stopTracks();
        }
      };

      media.current = rec;
      rec.start();
      setRecording(true);
      setPhase("recording");
    } catch (e: any) {
      console.error(e);
      setErr(e?.name === "NotAllowedError" ? "마이크 권한이 거부되었습니다." : e?.message || "녹음 시작 실패");
      setPhase("error");
      stopTracks();
    }
  };

  const stop = () => {
    if (media.current && media.current.state !== "inactive") {
      media.current.stop();
    }
    setRecording(false);
  };

  const busy = recording || phase === "uploading" || phase === "processing";

  return (
    <div className="flex flex-col items-center gap-4 mt-4 w-full">
      <div className="flex items-center gap-3">
        <button
          onClick={recording ? stop : start}
          disabled={busy && !recording}
          className={`px-4 py-2 rounded text-white ${
            recording ? "bg-red-600 hover:bg-red-700" : "bg-blue-600 hover:bg-blue-700"
          } disabled:opacity-60`}
        >
          {recording ? "🎙️ 녹음 중지" : "🎤 녹음 시작"}
        </button>
        <span className="text-sm text-gray-600">
          {phase === "idle" && "대기 중"}
          {phase === "recording" && "녹음 중..."}
          {phase === "uploading" && "업로드 중..."}
          {phase === "processing" && "처리 중..."}
          {phase === "done" && "완료"}
          {phase === "error" && (err || "에러")}
        </span>
      </div>

      {audioUrl && (
        <audio src={audioUrl} controls className="w-full max-w-xl" />
      )}

      {result.text && (
        <div className="mt-4 w-full max-w-xl text-sm">
          <p><strong>🎧 인식된 문장:</strong> {result.text}</p>
          <p className="mt-1"><strong>📘 IPA:</strong> <span className="font-mono">{result.ipa}</span></p>
          <p className="mt-1"><strong>🔤 로마자 표기:</strong> <span className="font-mono">{result.roman}</span></p>
        </div>
      )}
    </div>
  );
}
