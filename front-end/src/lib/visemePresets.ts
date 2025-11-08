export type MouthParams = {
  open: number;   // 세로 열림(0~1)
  spread: number; // 가로 벌림(0~1)
  round: number;  // 둥글림(0~1) - 둥근 입모양
  teeth: number;  // 치아 노출(0~1)
  tongue: number; // 혀 높이(0~1)
};

export type VisemeKey =
  | "NEUTRAL" | "BMP" | "CORE" | "AEI" | "EE" | "O" | "U"
  | "CHJSH" | "FV" | "TH" | "R" | "L" | "QW";

export const VISEME_PRESET: Record<VisemeKey, MouthParams> = {
  NEUTRAL: { open: 0.05, spread: 0.15, round: 0.05, teeth: 0.0, tongue: 0.2 },
  BMP:     { open: 0.00, spread: 0.10, round: 0.05, teeth: 0.0, tongue: 0.2 },
  CORE:    { open: 0.10, spread: 0.20, round: 0.05, teeth: 0.0, tongue: 0.3 },
  AEI:     { open: 0.35, spread: 0.60, round: 0.05, teeth: 0.8, tongue: 0.4 },
  EE:      { open: 0.30, spread: 0.65, round: 0.05, teeth: 0.8, tongue: 0.4 },
  O:       { open: 0.45, spread: 0.15, round: 0.60, teeth: 0.0, tongue: 0.3 },
  U:       { open: 0.30, spread: 0.10, round: 0.70, teeth: 0.0, tongue: 0.3 },
  CHJSH:   { open: 0.20, spread: 0.25, round: 0.10, teeth: 0.8, tongue: 0.5 },
  FV:      { open: 0.12, spread: 0.15, round: 0.05, teeth: 0.9, tongue: 0.2 },
  TH:      { open: 0.18, spread: 0.20, round: 0.05, teeth: 0.9, tongue: 0.7 },
  R:       { open: 0.14, spread: 0.20, round: 0.06, teeth: 0.0, tongue: 0.6 },
  L:       { open: 0.14, spread: 0.20, round: 0.06, teeth: 0.0, tongue: 0.55 },
  QW:      { open: 0.24, spread: 0.18, round: 0.45, teeth: 0.0, tongue: 0.3 },
};
