export type SttWord = { text: string; start: number; end: number };

export type SttResp = {
  rawText?: string;
  normText?: string;
  words?: SttWord[];
  duration?: number;
  model?: string;
  version?: string;
};

export type IpaResp = {
  original: string;
  phonetic: string;
  ipa: string;
  romanized: string;
  syllables: { char: string; ipa: string; roman: string }[];
};

const STT_BASE = "http://127.0.0.1:5000";   // ✅ Flask 프록시
const GOOEY_BASE = "http://127.0.0.1:5000"; // ✅ Flask 프록시

/** 🎙️ STT 호출 (Flask가 webm→wav 변환 처리) */
export async function callStt(file: Blob): Promise<SttResp> {
  const fd = new FormData();
  const webm = new File([file], "record.webm", { type: "audio/webm" });
  fd.append("audio", webm); // ✅ Whisper 서버는 audio 필드 필요
  fd.append("language", "ko");
  fd.append("timestamps", "word");

  const r = await fetch(`${STT_BASE}/stt`, { method: "POST", body: fd });
  const txt = await r.text();
  if (!r.ok) throw new Error(`/stt failed: ${r.status} - ${txt}`);
  try {
    return JSON.parse(txt);
  } catch {
    return { rawText: txt } as any;
  }
}

/** 🔤 IPA 변환 호출 */
export async function callIpa(text: string): Promise<IpaResp> {
  const r = await fetch(`http://127.0.0.1:8000/ipa`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!r.ok) throw new Error(`/ipa failed: ${r.status} - ${await r.text()}`);
  return r.json();
}

/** 🧠 Gooey 입모양 생성 호출 */
export async function callLipSync(audioBlob: Blob, facePublicPath = "/face.jpg") {
  const imgRes = await fetch(facePublicPath);
  if (!imgRes.ok) throw new Error(`face image not found at ${facePublicPath}`);
  const imgBlob = await imgRes.blob();

  const form = new FormData();
  form.append("audio", new File([audioBlob], "voice.webm", { type: "audio/webm" }));
  form.append("image", new File([imgBlob], "face.jpg", { type: imgBlob.type || "image/jpeg" }));

  const r = await fetch(`${GOOEY_BASE}/api/lipsync`, { method: "POST", body: form });
  const txt = await r.text();
  if (!r.ok) throw new Error(`/api/lipsync failed: ${r.status} - ${txt}`);
  try {
    return JSON.parse(txt);
  } catch {
    return { raw: txt } as any;
  }
}
