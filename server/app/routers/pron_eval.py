# server/app/routers/pron_eval.py

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Tuple
import difflib
import re
import os
import json

from openai import OpenAI  # Upstage Solar API가 OpenAI 호환 인터페이스라 이거 사용

router = APIRouter()

# ---------- Upstage Solar API 설정 ----------

# 윈도우 환경변수/ .env 등에 미리 설정한 값 사용
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")

upstage_client = None
if UPSTAGE_API_KEY:
    upstage_client = OpenAI(
        api_key=UPSTAGE_API_KEY,
        # Upstage Solar Chat API base URL (OpenAI 호환)
        # -> 이 아래에 /chat/completions가 붙는 구조
        base_url="https://api.upstage.ai/v1/solar",
    )


# ---------- 유틸 함수들 (정량 점수 계산) ----------

def normalize_korean(text: str) -> str:
    """한글/숫자만 남기고 나머지는 제거"""
    text = re.sub(r"[^가-힣0-9]", "", text)
    return text


def char_accuracy(ref: str, hyp: str) -> float:
    """문자 단위 유사도로 정확도(0~100) 계산"""
    ref_n = normalize_korean(ref)
    hyp_n = normalize_korean(hyp)
    if not ref_n:
        return 0.0
    sm = difflib.SequenceMatcher(None, ref_n, hyp_n)
    return sm.ratio() * 100.0


def speech_rate_score(text: str, duration_sec: float) -> Tuple[float, float]:
    """
    말 속도(음절/초)와 유창성 점수(0~100)를 반환
    이상적인 속도 범위를 3.0~5.0 음절/초 정도로 가정
    """
    norm = normalize_korean(text)
    syllables = len(norm)
    if duration_sec <= 0 or syllables == 0:
        return 0.0, 0.0

    rate = syllables / duration_sec  # 음절/초
    ideal_min, ideal_max = 3.0, 5.0

    if ideal_min <= rate <= ideal_max:
        score = 100.0
    else:
        diff = min(abs(rate - ideal_min), abs(rate - ideal_max))
        score = max(0.0, 100.0 - diff * 20.0)

    return rate, score


def build_pron_report(reference_text: str, recognized_text: str, duration_sec: float) -> Dict[str, Any]:
    acc = char_accuracy(reference_text, recognized_text)
    rate, flu = speech_rate_score(recognized_text, duration_sec)
    overall = round(0.7 * acc + 0.3 * flu, 1)

    return {
        "overall": overall,
        "accuracy": round(acc, 1),
        "fluency": {
            "score": round(flu, 1),
            "syllables_per_second": round(rate, 2),
        },
    }


# ---------- 룰 기반 fallback (Solar 안 될 때용) ----------

def build_rule_based_feedback(reference_text: str, recognized_text: str, report: Dict[str, Any]) -> Dict[str, Any]:
    overall = report["overall"]
    accuracy = report["accuracy"]
    flu = report["fluency"]["score"]
    rate = report["fluency"]["syllables_per_second"]

    if overall >= 90:
        level = "고급"
    elif overall >= 75:
        level = "중급"
    else:
        level = "초급"

    if accuracy >= 90:
        summary = "발음이 전반적으로 매우 정확해요. 자연스럽게 잘 읽어주셨어요."
    elif accuracy >= 75:
        summary = "전체적으로 잘 읽었지만, 몇몇 부분에서 다소 부정확한 발음이 보여요."
    else:
        summary = "스크립트와 다른 부분이 꽤 있어서, 조금 더 천천히 따라 읽어보면 좋아요."

    tips: List[str] = []
    if accuracy < 90:
        tips.append("스크립트를 눈으로 한 번 더 따라 읽으면서, 글자를 하나씩 또박또박 소리 내 보세요.")

    if rate > 0:
        if rate < 3.0:
            tips.append("말 속도가 조금 느린 편이에요. 문장을 더 끊김 없이 이어서 말해 보세요.")
        elif rate > 5.0:
            tips.append("조금 빠르게 말하는 경향이 있어요. 한 단어씩 분리해서 더 또렷하게 읽어보면 좋습니다.")
        else:
            tips.append("말 속도가 적당해서 듣기 편해요. 지금 속도를 유지하면서 발음만 조금 더 또박또박 하면 좋아요.")

    if not tips:
        tips.append("지금처럼 연습을 꾸준히 이어가면 발음이 더 자연스러워질 거예요!")

    intended = reference_text.strip() or recognized_text.strip()

    return {
        "summary": summary,
        "tips": tips,
        "level": level,
        "recommended_sentence": intended,
        "intended_sentence": intended,
    }


# ---------- Solar LLM 기반 피드백 ----------

def build_ai_style_feedback(reference_text: str, recognized_text: str, report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upstage Solar LLM(solar-1-mini-chat)을 사용해서:
    - 사용자가 원래 말하려던 문장(intended_sentence) 추측
    - 점수 기반 전문 코칭 리포트 생성
    Solar 호출 실패 시에는 룰 기반으로 fallback.
    """

    if upstage_client is None:
        return build_rule_based_feedback(reference_text, recognized_text, report)

    system_msg = (
        "너는 한국어 발음 전문 코치이자 언어치료사야. "
        "학습자의 발음 결과와 정량 점수(report)를 바탕으로, "
        "전문적인 코칭 리포트를 한국어로 작성해야 한다. "
        "반드시 JSON만 출력하고, 다른 텍스트는 출력하지 마."
    )

    user_msg = f"""
[입력 정보]
- 연습해야 했던 문장(reference_text): {reference_text}
- 실제 음성 인식 결과(recognized_text): {recognized_text}
- 발음 평가 점수(report): {json.dumps(report, ensure_ascii=False)}

[설명]
- report.overall: 종합 점수 (0~100)
- report.accuracy: 발음 정확도 (스크립트와 일치하는 정도, 0~100)
- report.fluency.score: 유창성 점수 (속도 안정성, 0~100)
- report.fluency.syllables_per_second: 초당 음절 수

[역할]
너는 위 정보를 바탕으로 다음을 수행해야 한다:
1. recognized_text가 다소 부정확해도, reference_text와 비교하여
   학습자가 원래 말하려던 자연스러운 문장(intended_sentence)을 추론한다.
2. 발음을 다음 네 가지 축으로 전문적으로 분석한다:
   - 발음 정확도 (스크립트 일치도, 음운 대치/탈락 여부)
   - 말 속도 및 유창성 (너무 빠름/느림, 끊김 여부)
   - 리듬·억양 (문장 전체의 강세/억양 패턴이 자연스러운지)
   - 명료도 (자음·모음 분리, 끝소리 처리 등)

[summary 필드 작성 규칙]
- 3~5줄 정도의 짧은 리포트로 작성하되, 줄바꿈과 번호를 활용해 전문적인 느낌을 내라.
- 예시:
  "1) 발음 정확도: OO%로, 주요 내용은 잘 전달되지만 '~' 부분에서 소리가 흐려집니다.
   2) 말 속도·유창성: 초당 X음절로, 약간 빠른 편이라 모음이 뭉개지는 경향이 있습니다.
   3) 리듬·명료도: 문장 끝에서 음절이 약해지는 습관이 있어 마무리가 조금 흐립니다."

[tips 필드 작성 규칙]
- 최소 2개, 최대 4개 정도의 구체적인 연습 팁을 제공하라.
- 각 팁은 실제 발음 연습에서 바로 사용할 수 있을 정도로 구체적으로 작성한다.
- 예를 들어:
  - "‘좋네요’의 'ㅈ'과 'ㄴ' 자음을 또박또박 구분해서 읽는 연습을 해보세요."
  - "문장 첫 단어를 한 박자 길게 끌어서 시작하면, 전체 리듬이 안정됩니다."

[level 필드 작성 규칙]
- overall, accuracy, fluency.score를 종합해서 '초급', '중급', '고급' 중 하나로 판단한다.
- 대략적인 기준 예시:
  - overall ≥ 90 또는 accuracy ≥ 90 AND fluency.score ≥ 85 → "고급"
  - overall ≥ 70 → "중급"
  - 그 이하는 "초급"

[recommended_sentence 필드 작성 규칙]
- intended_sentence와 비슷한 패턴이지만, 더 짧고 발음 연습에 좋은 문장을 하나 제안한다.
- 발음 연습용 문장으로, 받침·모음이 골고루 섞여 있으면서도 길이가 너무 길지 않게 한다.

[최종 출력 형식(JSON만 출력)]
{{
  "intended_sentence": "사용자가 원래 말하려던 자연스러운 한국어 문장",
  "summary": "번호/줄바꿈을 활용한 전문적인 발음 리포트 (3~5줄, 한국어)",
  "tips": [
    "첫 번째 구체적인 발음 연습 팁(한국어)",
    "두 번째 구체적인 발음 연습 팁(한국어)"
  ],
  "level": "초급/중급/고급 중 하나",
  "recommended_sentence": "연습용으로 좋은 한국어 문장 1개"
}}
"""

    try:
        resp = upstage_client.chat.completions.create(
            model="solar-1-mini-chat",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.7,
        )
        content = resp.choices[0].message.content or "{}"

        # JSON 부분만 안전하게 추출
        import re as _re
        m = _re.search(r"\{.*\}", content, _re.DOTALL)
        raw_json = m.group(0) if m else content
        data = json.loads(raw_json)

        intended = data.get("intended_sentence") or reference_text or recognized_text
        summary = data.get("summary") or "전반적인 발음 경향을 분석한 결과입니다."
        tips = data.get("tips") or [
            "조금 더 천천히, 입 모양을 크게 벌려서 발음해 보세요.",
            "문장을 짧게 나눠서 여러 번 반복해서 읽어보세요.",
        ]
        level = data.get("level") or "중급"
        recommended = data.get("recommended_sentence") or intended

        return {
            "summary": summary,
            "tips": tips,
            "level": level,
            "recommended_sentence": recommended,
            "intended_sentence": intended,
        }

    except Exception as e:
        print(f"[pron_eval] Solar API error: {e}")
        return build_rule_based_feedback(reference_text, recognized_text, report)



# ---------- Pydantic 모델 / 엔드포인트 ----------

class PronEvalRequest(BaseModel):
    reference_text: str
    recognized_text: str
    duration_sec: float


class PronEvalResponse(BaseModel):
    recognized_text: str
    report: Dict[str, Any]
    ai_feedback: Dict[str, Any]


@router.post("/pron-eval", response_model=PronEvalResponse)
async def pron_eval(req: PronEvalRequest):
    report = build_pron_report(req.reference_text, req.recognized_text, req.duration_sec)
    feedback = build_ai_style_feedback(req.reference_text, req.recognized_text, report)

    return {
        "recognized_text": req.recognized_text,
        "report": report,
        "ai_feedback": feedback,
    }
