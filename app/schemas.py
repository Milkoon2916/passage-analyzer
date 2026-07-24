"""
Claude API가 반환해야 하는 구조화된 분석 결과의 스키마.
스킬(passage-analysis-pdf)의 references/format-guide.md 규칙을 데이터 구조로 옮긴 것.

핵심 설계 원칙: Claude에게 자유 형식 HTML을 직접 만들게 하지 않고,
이 스키마에 맞는 JSON만 반환하도록 강제한다. -> 파싱/렌더링이 훨씬 안정적.
"""
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    """문장을 이루는 조각 하나. 일반 텍스트이거나, 색상 태그가 붙은 단어/구."""
    type: Literal["text", "tag", "conn", "hl"]
    text: str  # 원문 그대로의 영어 단어/구 (또는 일반 텍스트 조각)
    tag_class: Optional[Literal["g", "v", "gv"]] = None  # type == "tag"일 때만
    caption: Optional[str] = None  # type == "tag"일 때만, 2-6자 한글 캡션


class Note(BaseModel):
    category: Literal[
        "comprehension",  # 독해 포인트
        "grammar",        # 어법 포인트
        "blank",          # 빈칸
        "writing",        # 서술형
        "implication",    # 함의추론
        "theme",          # 주제/요지
    ]
    body: str  # 2-4문장, 캐주얼한 tutor 어투


class Sentence(BaseModel):
    num: int
    badge: Optional[Literal["topic", "insert", "target"]] = None  # 주제문 / 문장삽입 / 목표 어법
    tokens: list[Token]
    translation: str  # 자연스러운 한글 번역 (직역 아님)
    notes: list[Note] = Field(default_factory=list)


class Summary(BaseModel):
    theme: str        # 주제
    flow: str          # 흐름: "도입 (...) → 전개 (...) → 결론 (...)"
    background: str    # 배경지식 4-7문장


class PassageAnalysis(BaseModel):
    title_en: str
    title_kr: str
    passage_index: int = 1
    target_grammar: Optional[str] = None  # 사용자가 지정한 목표 어법 (예: "가정법 도치, 분사구문")
    sentences: list[Sentence]
    summary: Summary


# Claude에게 요구할 최종 JSON의 최상위 형태 (여러 지문을 한 번에 받을 수도 있게)
class AnalysisResponse(BaseModel):
    passages: list[PassageAnalysis]
