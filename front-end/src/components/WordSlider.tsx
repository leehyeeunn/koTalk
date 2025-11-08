"use client";
import { useMemo } from "react";

export type WordTiming = { text: string; start: number; end: number };

type Props = {
  words: WordTiming[];
  audioEl?: HTMLAudioElement | null;
  value: number;                         // 현재 선택한 단어 인덱스
  onChange: (idx: number) => void;       // 슬라이더 변경 핸들러
  followAudio: boolean;                  // 오디오-슬라이더 자동 싱크 여부
  onToggleFollow: (v: boolean) => void;  // 토글 핸들러
};

export default function WordSlider({
  words,
  audioEl,
  value,
  onChange,
  followAudio,
  onToggleFollow,
}: Props) {
  const max = Math.max(words.length - 1, 0);

  const label = useMemo(() => {
    if (!words.length || value < 0 || value >= words.length) return "(없음)";
    const w = words[value];
    return `${w.text} (${w.start.toFixed(2)}–${w.end.toFixed(2)}s)`;
  }, [words, value]);

  const seekTo = (idx: number) => {
    if (!words.length || idx < 0 || idx >= words.length) return;
    const t = words[idx].start + 0.001; // 경계에서 멈춤 방지
    if (audioEl) audioEl.currentTime = t;
  };

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm text-gray-600">
          단어 스크럽: <span className="font-mono">{label}</span>
        </div>
        <label className="text-xs text-gray-600 flex items-center gap-2">
          <input
            type="checkbox"
            checked={followAudio}
            onChange={(e) => onToggleFollow(e.target.checked)}
          />
          오디오 따라가기
        </label>
      </div>

      <input
        type="range"
        min={0}
        max={max}
        step={1}
        value={Math.min(value, max)}
        onChange={(e) => {
          const idx = Number(e.target.value);
          onChange(idx);
          seekTo(idx);
        }}
        className="w-full"
      />

      {/* 단어 버튼으로도 점프 가능 */}
      {words.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {words.map((w, i) => (
            <button
              key={`${w.text}-${i}-${w.start}`}
              onClick={() => {
                onChange(i);
                seekTo(i);
              }}
              className={`px-1.5 py-0.5 rounded text-xs border ${
                i === value ? "bg-blue-600 text-white border-blue-600" : "bg-white text-gray-700"
              }`}
              title={`${w.start.toFixed(2)}s`}
            >
              {w.text}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
