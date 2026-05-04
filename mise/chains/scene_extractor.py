import json
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI

from mise.config import GOOGLE_API_KEY, MODEL_NAME, MAX_INPUT_LENGTH, API_TIMEOUT
from mise.models.scene_schema import ExtractionResult, PromptResult, SceneSchema, SceneElements
from mise.prompts.extraction_prompt import _prompt_template as extraction_template
from mise.prompts.prompt_generator import _prompt_template as prompt_template


def _create_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.3,
        request_timeout=API_TIMEOUT,
    )


def _validate_input(novel_text: str, mode: str, prev_scene: Optional[dict]) -> None:
    if not novel_text or not novel_text.strip():
        raise ValueError("입력 텍스트가 비어있습니다.")
    if len(novel_text) > MAX_INPUT_LENGTH:
        raise ValueError(f"입력 텍스트가 {MAX_INPUT_LENGTH}자를 초과합니다. (현재: {len(novel_text)}자)")
    if mode not in ("generate", "regenerate"):
        raise ValueError(f"잘못된 mode: '{mode}'. 'generate' 또는 'regenerate'만 허용됩니다.")
    if mode == "regenerate" and prev_scene is None:
        raise ValueError("regenerate 모드에서는 prev_scene이 필요합니다.")


def _call_extract(novel_text: str, llm: ChatGoogleGenerativeAI) -> ExtractionResult:
    chain = extraction_template | llm.with_structured_output(ExtractionResult)
    return chain.invoke({"novel_text": novel_text})


def _call_prompt(elements: SceneElements, style: str, llm: ChatGoogleGenerativeAI) -> PromptResult:
    elements_dict = elements.model_dump()
    elements_json = json.dumps(elements_dict, ensure_ascii=False)
    chain = prompt_template | llm.with_structured_output(PromptResult)
    return chain.invoke({"elements_json": elements_json, "style": style})


def extract_scene(
    novel_text: str,
    mode: str = "generate",
    prev_scene: Optional[dict] = None,
) -> SceneSchema:
    _validate_input(novel_text, mode, prev_scene)
    llm = _create_llm()

    if mode == "generate":
        extraction = _call_extract(novel_text, llm)
        elements = extraction.elements
        source_type = extraction.source_type
        style = "cinematic"
    else:
        elements = SceneElements.model_validate(prev_scene["elements"])
        source_type = prev_scene.get("source_type", {})
        style = prev_scene.get("prompt", {}).get("style", "cinematic")

    prompt_result = _call_prompt(elements, style, llm)

    return SceneSchema(
        elements=elements,
        source_type=source_type,
        prompt=prompt_result,
    )
