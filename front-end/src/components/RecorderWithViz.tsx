"use client";

import { useRef, useState } from "react";
import {
  callIpa,
  callStt,
  callLipSync,
  callPronEval,
  SttResp,
  IpaResp,
  PronReport,
  AiFeedback,
} from "@/lib/api";

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

  // 🔹 STT + 발음 평가 상태
  const [stt, setStt] = useState<SttResp | null>(null);
  const [report, setReport] = useState<PronReport | null>(null);
  const [feedback, setFeedback] = useState<AiFeedback | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);

  const media = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  async function start() {
    try {
      setErr(null);
      setIpa(null);
      setVideoUrl(null);
      setStt(null);
      setReport(null);
      setFeedback(null);

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
          setStt(sttRes);

          const text = sttRes.rawText || sttRes.normText || "";
          if (!text) throw new Error("STT 결과가 비어있습니다.");

          // 2️⃣ IPA 변환
          const ipaRes = await callIpa(text);
          setIpa(ipaRes);

          // 3️⃣ 발음 평가 + AI 스타일 피드백
          try {
            setIsEvaluating(true);

            // 기준 문장: 우선 IPA 원문이 있으면 그걸, 아니면 인식 텍스트 사용
            const referenceText = ipaRes.original || text;
            const durationSec =
              typeof sttRes.duration === "number" ? sttRes.duration : 0;

            const evalRes = await callPronEval({
              referenceText,
              recognizedText: text,
              durationSec,
            });

            setReport(evalRes.report);
            setFeedback(evalRes.ai_feedback);
          } finally {
            setIsEvaluating(false);
          }

          // 4️⃣ LipSync 영상 생성
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
        <span className="text-sm text-gray-600">
          {phase}
          {isEvaluating && " · 발음 평가 중..."}
        </span>
      </div>

      {err && (
        <div className="text-red-600 bg-red-50 border p-2 rounded">
          {err}
        </div>
      )}

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

      {/* 🔹 AI 발음 리포트 & 피드백 */}
      {report && feedback && (
        <div className="border-t pt-4 space-y-3">
          <h2 className="text-xl font-bold">AI 발음 리포트</h2>

          <div className="text-lg font-semibold">
            종합 점수:{" "}
            <span className="text-blue-600">{report.overall}</span>점
          </div>

          <div className="space-y-2 text-sm">
            <div>
              <div className="flex justify-between mb-1">
                <span>정확도</span>
                <span>{report.accuracy}%</span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500"
                  style={{ width: `${report.accuracy}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span>유창성</span>
                <span>
                  {report.fluency.score}% (
                  {report.fluency.syllables_per_second} 음절/초)
                </span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500"
                  style={{ width: `${report.fluency.score}%` }}
                />
              </div>
            </div>
          </div>

          <div className="text-sm text-gray-800">
            <div className="font-semibold mb-1">AI 코치 요약</div>
            <p>{feedback.summary}</p>
          </div>

          <div className="text-sm text-gray-800">
            <div className="font-semibold mb-1">연습 팁</div>
            <ul className="list-disc list-inside space-y-1">
              {feedback.tips.map((tip, i) => (
                <li key={i}>{tip}</li>
              ))}
            </ul>
          </div>

          <div className="text-xs text-gray-500">
            수준: {feedback.level} · 추천 문장: “
            {feedback.recommended_sentence}”
          </div>
        </div>
      )}

      {videoUrl && (
        <div className="mt-3">
          <h2 className="text-xl font-bold">결과 영상</h2>
          <video
            src={videoUrl}
            controls
            className="w-full rounded-xl shadow"
          />
          <p className="text-xs text-gray-500 mt-1">
            AI 입모양 시각화 결과
          </p>
        </div>
      )}
    </div>
  );
}
