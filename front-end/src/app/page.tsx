"use client";

import RecorderWithViz from "@/components/RecorderWithViz";

export default function Page() {
  return (
    <main className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-6">
      <div className="max-w-xl w-full bg-white shadow-md rounded-2xl p-8">
        <h1 className="text-2xl font-bold text-center mb-6 text-gray-800">
          🎙️ KoTalk Pronunciation Test
        </h1>

        <p className="text-gray-600 text-center mb-8">
          아래 버튼을 눌러 음성을 녹음하면 Whisper가 텍스트로 변환하고,<br />
          IPA(국제 발음 기호)와 로마자 표기, 그리고 <b>입모양 시각화</b>가 타이밍에 맞춰 표시됩니다.
        </p>

        {/* 녹음 → /stt → /ipa → 입모양 싱크 시각화까지 한 번에 처리 */}
        <RecorderWithViz />

        <p className="text-xs text-gray-400 text-center mt-6">
          * Whisper + G2P(K) + IPA Mapping 기반
        </p>
      </div>
    </main>
  );
}
