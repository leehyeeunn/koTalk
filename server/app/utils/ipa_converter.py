from g2pk import G2p
import hgtk
from hgtk import checker, letter

# ==========================
# IPA & Romanization 매핑
# ==========================
ONSET_IPA = {
    "ㄱ": "k", "ㄲ": "k͈", "ㄴ": "n", "ㄷ": "t", "ㄸ": "t͈", "ㄹ": "ɾ", "ㅁ": "m", "ㅂ": "p", "ㅃ": "p͈",
    "ㅅ": "s", "ㅆ": "s͈", "ㅇ": "", "ㅈ": "tɕ", "ㅉ": "tɕ͈", "ㅊ": "tɕʰ", "ㅋ": "kʰ", "ㅌ": "tʰ", "ㅍ": "pʰ", "ㅎ": "h"
}
NUCLEUS_IPA = {
    "ㅏ": "a", "ㅐ": "ɛ", "ㅑ": "ja", "ㅒ": "jɛ", "ㅓ": "ʌ", "ㅔ": "e", "ㅕ": "jʌ", "ㅖ": "je",
    "ㅗ": "o", "ㅘ": "wa", "ㅙ": "wɛ", "ㅚ": "we", "ㅛ": "jo", "ㅜ": "u", "ㅝ": "wʌ", "ㅞ": "we",
    "ㅟ": "wi", "ㅠ": "ju", "ㅡ": "ɯ", "ㅢ": "ɰi", "ㅣ": "i"
}
CODA_IPA = {
    "": "", "ㄱ": "k̚", "ㄲ": "k̚", "ㅋ": "k̚", "ㄴ": "n", "ㄷ": "t̚", "ㅌ": "t̚", "ㅅ": "t̚",
    "ㅆ": "t̚", "ㅈ": "t̚", "ㅊ": "t̚", "ㅎ": "t̚", "ㄹ": "l", "ㅁ": "m", "ㅂ": "p̚", "ㅍ": "p̚", "ㅇ": "ŋ"
}

ONSET_ROMA = {
    "ㄱ": "g", "ㄲ": "kk", "ㄴ": "n", "ㄷ": "d", "ㄸ": "tt", "ㄹ": "r", "ㅁ": "m", "ㅂ": "b", "ㅃ": "pp",
    "ㅅ": "s", "ㅆ": "ss", "ㅇ": "", "ㅈ": "j", "ㅉ": "jj", "ㅊ": "ch", "ㅋ": "k", "ㅌ": "t", "ㅍ": "p", "ㅎ": "h"
}
NUCLEUS_ROMA = {
    "ㅏ": "a", "ㅐ": "ae", "ㅑ": "ya", "ㅒ": "yae", "ㅓ": "eo", "ㅔ": "e", "ㅕ": "yeo", "ㅖ": "ye",
    "ㅗ": "o", "ㅘ": "wa", "ㅙ": "wae", "ㅚ": "oe", "ㅛ": "yo", "ㅜ": "u", "ㅝ": "wo", "ㅞ": "we",
    "ㅟ": "wi", "ㅠ": "yu", "ㅡ": "eu", "ㅢ": "ui", "ㅣ": "i"
}
CODA_ROMA = {
    "": "", "ㄱ": "k", "ㄲ": "k", "ㅋ": "k", "ㄴ": "n", "ㄷ": "t", "ㅌ": "t", "ㅅ": "t",
    "ㅆ": "t", "ㅈ": "t", "ㅊ": "t", "ㅎ": "t", "ㄹ": "l", "ㅁ": "m", "ㅂ": "p", "ㅍ": "p", "ㅇ": "ng"
}


# ==========================
# Helper: 한 글자 변환
# ==========================
def map_syllable(ch: str):
    if not checker.is_hangul(ch):
        return ch, ch
    onset, nucleus, coda = letter.decompose(ch)
    if coda == " ":
        coda = ""

    ipa = ONSET_IPA.get(onset, "") + NUCLEUS_IPA.get(nucleus, "") + CODA_IPA.get(coda, "")
    roma = ONSET_ROMA.get(onset, "") + NUCLEUS_ROMA.get(nucleus, "") + CODA_ROMA.get(coda, "")
    return ipa, roma


# ==========================
# Main: 문장 변환
# ==========================
def text_to_ipa(sentence: str):
    g2p = G2p()
    phonetic = g2p(sentence)  # "좋아요" → "조아요"

    words = phonetic.split()
    ipa_words, roman_words = [], []
    syllable_list = []  # 음절별 구조

    for word in words:
        ipa_word, roma_word = [], []

        for ch in word:
            ipa, roma = map_syllable(ch)
            ipa_word.append(ipa)
            roma_word.append(roma)
            syllable_list.append({"char": ch, "ipa": ipa, "roman": roma})

        ipa_words.append("".join(ipa_word))
        roman_words.append("".join(roma_word))
        syllable_list.append({"char": " ", "ipa": " ", "roman": " "})  # 단어 간 구분

    return {
        "original": sentence,
        "phonetic": phonetic,
        "ipa": " ".join(ipa_words),
        "romanized": " ".join(roman_words),
        "syllables": syllable_list,
    }


# ==========================
# Test Run
# ==========================
if __name__ == "__main__":
    result = text_to_ipa("저는 학생입니다.")
    from pprint import pprint
    pprint(result)
