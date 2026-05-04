from pydantic import BaseModel


class SceneElements(BaseModel):
    character: str
    background: str
    time: str
    place: str
    objects: list[str] = []
    action: str
    emotion: str
    mood: str
    color: str
    lighting: str
    camera_view: str
    composition: str


class ExtractionResult(BaseModel):
    """Call 1 출력: 12개 요소 + 각 요소의 출처 구분"""
    elements: SceneElements
    source_type: dict[str, str]


class PromptResult(BaseModel):
    """Call 2 출력: 이미지 생성용 프롬프트"""
    positive_prompt: str
    negative_prompt: str
    style: str = "cinematic"
    missing_info: list[str] = []


class SceneSchema(BaseModel):
    """최종 반환: 요소 + 출처 + 프롬프트"""
    elements: SceneElements
    source_type: dict[str, str]
    prompt: PromptResult
