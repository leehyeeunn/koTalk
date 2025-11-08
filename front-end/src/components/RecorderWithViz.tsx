"use client";

import { useRef, useState } from "react";
import { callIpa, callStt, callLipSync, SttResp, IpaResp } from "@/lib/api";

type Phase =
  | "대기 중"
  | "녹음 중"
  | "업로드 중"
  | "처리 중"
  | "완료"
  | "오류";

export default function RecorderWithViz() {
  const [phase, setPhase] = useState<Phase>("대기 중");
  const [err, setErr] = useState<string | null>(null);
  const [ipa, setIpa] = useState<IpaResp | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);

  const media = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  async function start() {
    try {
      setErr(null);
      setIpa(null);
      setVideoUrl(null);

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const rec = new MediaRecorder(stream, { mimeType: "audio/webm" });
      chunks.current = [];

      rec.ondataavailable = (e) => e.data.size && chunks.current.push(e.data);

      rec.onstop = async () => {
        try {
          setPhase("업로드 중");
          const blob = new Blob(chunks.current, { type: "audio/webm" });
          setAudioUrl(URL.createObjectURL(blob));

          // 1️⃣ STT (음성 → 텍스트)
          setPhase("처리 중");
          const sttRes: SttResp = await callStt(blob);

          // 2️⃣ IPA 변환
          const text = sttRes.rawText || sttRes.normText || "";
          if (!text) throw new Error("STT 결과가 비어있습니다.");
          const ipaRes = await callIpa(text);
          setIpa(ipaRes);

          // 3️⃣ LipSync 영상 생성
          const lipSyncRes = await callLipSync(blob, "/face.jpg");
          const video =
            lipSyncRes?.output_video ||
            lipSyncRes?.output?.output_video ||
            lipSyncRes?.gooey?.output?.output_video;
          if (!video) throw new Error("영상 URL을 찾을 수 없습니다.");
          setVideoUrl(video);

          setPhase("완료");
        } catch (e: any) {
          console.error(e);
          setErr(e?.message || "처리 중 오류가 발생했습니다.");
          setPhase("오류");
        } finally {
          chunks.current = [];
          streamRef.current?.getTracks().forEach((t) => t.stop());
          streamRef.current = null;
        }
      };

      media.current = rec;
      rec.start();
      setPhase("녹음 중");
    } catch (e: any) {
      console.error(e);
      setErr("녹음 권한이 없거나 오류가 발생했습니다.");
      setPhase("오류");
    }
  }

  function stop() {
    media.current?.stop();
  }

  return (
    <div className="w-full max-w-2xl mx-auto flex flex-col gap-4">
      <div className="flex items-center justify-center gap-3">
        <button
          onClick={phase === "녹음 중" ? stop : start}
          className={`px-4 py-2 rounded text-white ${
            phase === "녹음 중" ? "bg-red-600" : "bg-blue-600"
          }`}
          disabled={phase === "업로드 중" || phase === "처리 중"}
        >
          {phase === "녹음 중" ? "녹음 종료" : "녹음 시작"}
        </button>
        <span className="text-sm text-gray-600">{phase}</span>
      </div>

      {err && <div className="text-red-600 bg-red-50 border p-2 rounded">{err}</div>}

      {audioUrl && (
        <div>
          <h2 className="font-semibold text-lg mb-1">녹음된 오디오</h2>
          <audio src={audioUrl} controls className="w-full" />
        </div>
      )}

      {ipa && (
        <div className="border-t pt-4 space-y-2">
          <h2 className="text-xl font-bold">IPA 및 로마자 변환 결과</h2>
          <div>
            <div className="text-xs text-gray-500">원문</div>
            <div className="text-lg">{ipa.original}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">IPA</div>
            <div className="font-mono break-words">{ipa.ipa}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">로마자 표기</div>
            <div className="font-mono break-words">{ipa.romanized}</div>
          </div>
        </div>
      )}

      {videoUrl && (
        <div className="mt-3">
          <h2 className="text-xl font-bold">결과 영상</h2>
          <video src={videoUrl} controls autoPlay loop className="w-full rounded-xl shadow" />
          <p className="text-xs text-gray-500 mt-1">AI 입모양 시각화 결과</p>
        </div>
      )}
    </div>
  );
}
