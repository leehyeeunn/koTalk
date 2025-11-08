export type MouthGroup =
  | "AEI" | "FV" | "L" | "QW" | "CHJSH" | "U" | "R"
  | "CORE" | "BMP" | "TH" | "EE" | "O" | "NEUTRAL";

export const MOUTH_IMAGE: Record<MouthGroup, string> = {
  AEI: "/mouth/a_e_i.png",
  FV: "/mouth/f_v.png",
  L: "/mouth/l.png",
  QW: "/mouth/q_w.png",
  CHJSH: "/mouth/ch_j_sh.png",
  U: "/mouth/u.png",
  R: "/mouth/r.png",
  CORE: "/mouth/c_d_g_k_n_s_t_x_y_z.png",
  BMP: "/mouth/b_m_p.png",
  TH: "/mouth/th.png",
  EE: "/mouth/ee.png",
  O: "/mouth/o.png",
  NEUTRAL: "/mouth/neutral.png",
};

const IPA_PATTERNS: Array<[RegExp, MouthGroup]> = [
  [/aɪ|eɪ|oʊ|ɔɪ|aʊ/i, "O"],
  [/iː/i, "EE"],
  [/θ|ð/i, "TH"],
  [/t͡?ʃ|d͡?ʒ|tɕ|dʑ|ʃ|ʒ|ɕ/i, "CHJSH"],
  [/w/i, "QW"],
  [/l/i, "L"],
  [/ɹ|r/i, "R"],
  [/b|m|p/i, "BMP"],
  [/i|ɪ|e|ɛ|æ|a/i, "AEI"],
  [/u|ʊ|ɯ/i, "U"],
  [/o|ɔ|oʊ|ʌ/i, "O"],
  [/k|g|ŋ|t|d|n|s|z|j|x|ç|h/i, "CORE"],
];

export function ipaSymbolToGroup(sym: string): MouthGroup {
  if (!sym) return "NEUTRAL";
  for (const [re, grp] of IPA_PATTERNS) {
    if (re.test(sym)) return grp;
  }
  return "NEUTRAL";
}

export function ipaToGroups(ipa: string): MouthGroup[] {
  const raw = (ipa || "").split(/\s+/).filter(Boolean);
  const groups: MouthGroup[] = [];
  for (const token of raw) {
    const g = ipaSymbolToGroup(token);
    if (g !== "NEUTRAL") {
      groups.push(g);
      continue;
    }
    const parts = token.match(/t͡?ʃ|d͡?ʒ|tɕ|dʑ|[a-zɑ-ʒʃɕɯʊɔɪːʌ]+/gi) ?? [token];
    let placed = false;
    for (const p of parts) {
      const sub = ipaSymbolToGroup(p);
      if (sub !== "NEUTRAL") {
        groups.push(sub);
        placed = true;
        break;
      }
    }
    if (!placed) groups.push("NEUTRAL");
  }
  return groups;
}
