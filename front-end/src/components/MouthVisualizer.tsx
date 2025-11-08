"use client";
import { useMemo } from "react";
import { ipaToGroups, MOUTH_IMAGE } from "@/lib/ipaToMouthGroup";

type WordTiming = { text: string; start: number; end: number };

type Props = {
  ipa: string;
  currentTime?: number;                 // 현재 오디오 재생 시각(초)
  wordTimings?: WordTiming[];           // Whisper 결과 words
};

export default function MouthVisualizer({ ipa, currentTime, wordTimings }: Props) {
  // 1) 현재 단어 인덱스 계산 (currentTime이 0일 수 있으므로 null/undefined만 제외)
  const activeIndex = useMemo(() => {
    if (currentTime == null || !wordTimings || wordTimings.length === 0) return -1;
    const idx = wordTimings.findIndex(w => currentTime >= w.start && currentTime < w.end);
    return idx; // 못 찾으면 -1
  }, [currentTime, wordTimings]);

  // 2) IPA를 "단어 단위"로 토큰화 (공백 기준)
  const ipaTokens = useMemo(() => {
    // 예: "tɕʌ nɯn hak s͈ɛŋ im ni da" -> ["tɕʌ","nɯn","hak","s͈ɛŋ","im","ni","da"]
    const parts = (ipa || "").trim().split(/\s+/).filter(Boolean);
    return parts.length > 0 ? parts : [ipa || ""];
  }, [ipa]);

  // 3) 현재 단어에 대응하는 IPA 토큰 선택
  const activeIpa = useMemo(() => {
    if (activeIndex < 0) {
      // 아직 재생 전/후: 전체 IPA 첫 토큰 사용
      return ipaTokens[0] ?? "";
    }
    // words 길이와 ipa 토큰 길이가 다를 수 있으므로 방어적으로 처리
    const safeIndex = Math.min(activeIndex, ipaTokens.length - 1);
    return ipaTokens[safeIndex] ?? ipaTokens[0] ?? "";
  }, [activeIndex, ipaTokens]);

  // 4) 입모양 그룹 결정 (현재 토큰 기준)
  const group = useMemo(() => {
    const groups = ipaToGroups(activeIpa);
    return groups[0] ?? "NEUTRAL";
  }, [activeIpa]);

  const src = MOUTH_IMAGE[group];

  // 5) 현재 단어 텍스트 표시 (디버깅/UX 보조)
  const activeWordText = useMemo(() => {
    if (!wordTimings || activeIndex < 0 || activeIndex >= wordTimings.length) return "(대기 중)";
    return wordTimings[activeIndex].text;
  }, [wordTimings, activeIndex]);

  return (
    <div className="flex flex-col items-center">
      <img
        src={src}
        alt={group}
        className="w-40 h-40 object-contain transition-all duration-200"
      />
      <div className="mt-2 text-sm text-gray-700">{activeWordText}</div>
    </div>
  );
}
