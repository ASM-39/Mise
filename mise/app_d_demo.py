"""D 단계 (인터랙션 UI) 데모 — 실제 Gemini API 연동 버전.

사용자 입력 소설 텍스트를 백엔드 파이프라인(extract_scene)으로 분석하고,
Gemini 이미지 생성 API(generate_image)로 실제 이미지를 만든다.

실행:
    streamlit run mise/app_d_demo.py

필수 환경 변수:
    GOOGLE_API_KEY (mise/.env)
"""
from __future__ import annotations

import sys
from pathlib import Path

# streamlit run 실행 시 sys.path[0]은 스크립트 디렉토리(mise/)가 되어
# `from mise.xxx import ...`가 실패한다. 프로젝트 루트를 명시적으로 추가.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from mise.chains.scene_extractor import extract_scene
from mise.components.history import (
    encode_image_to_bytes,
    render_history_detail,
    render_history_strip,
)
from mise.components.regenerate import render_regenerate_button
from mise.components.scene_card import render_scene_cards, reset_card_widgets
from mise.components.style_preset import render_style_preset
from mise.generators.image_generator import generate_image
from mise.models.scene_schema import SceneElements, SceneSchema
from mise.state import (
    HistoryItem,
    Keys,
    append_history,
    build_prev_scene_payload,
    get_edited_elements,
    get_style_value,
    init_state,
    reset_regen_count,
    set_current_scene,
)

SAMPLE_NOVEL = (
    "붉은 노을 아래 무너진 성벽 너머로 거대한 마법진이 떠오르고 있었다. "
    "검은 갑옷을 입은 기사가 폐허 위에 홀로 서서 하늘을 올려다보았다. "
    "바람이 그의 망토를 흔들었다."
)


def _reset_state() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def _run_pipeline(novel_text: str) -> None:
    """소설 텍스트 → 장면 분석 → 이미지 생성 (최초 1회)."""
    style_label = st.session_state.get(Keys.STYLE_LABEL)
    style_value = get_style_value()

    with st.spinner("장면을 분석하는 중... (10–15초)"):
        scene = extract_scene(novel_text)

    # 사용자가 사이드바에서 선택한 스타일을 prompt.style에 반영
    scene = SceneSchema(
        elements=scene.elements,
        source_type=scene.source_type,
        prompt=scene.prompt.model_copy(update={"style": style_value}),
    )

    with st.spinner("이미지를 생성하는 중... (10–20초)"):
        image = generate_image(
            positive=scene.prompt.positive_prompt,
            negative=scene.prompt.negative_prompt,
            style=style_value,
        )

    set_current_scene(scene, novel_text)
    reset_regen_count()
    reset_card_widgets()
    append_history(HistoryItem(
        novel_text=novel_text,
        elements=scene.elements.model_dump(),
        prompt=scene.prompt.model_dump(),
        style_label=style_label,
        image_bytes=encode_image_to_bytes(image),
        mode="generate",
    ))


def _on_regenerate() -> None:
    """편집된 요소 + 사용자 선택 스타일로 재생성.

    extract_scene(mode='regenerate', prev_scene=...)을 호출하고
    그 결과로 generate_image()를 부른다. Streamlit 콜백이라 다음 rerun 직전에 실행된다.
    """
    edited = get_edited_elements()
    if edited is None:
        return

    style_label = st.session_state[Keys.STYLE_LABEL]
    style_value = get_style_value()
    novel_text = st.session_state[Keys.NOVEL_TEXT]

    prev = build_prev_scene_payload()
    if prev is None:
        return
    # 사용자가 사이드바에서 바꾼 스타일을 backend에 전달
    prev["prompt"]["style"] = style_value

    try:
        with st.spinner("재분석 중... (10–15초)"):
            scene = extract_scene(novel_text, mode="regenerate", prev_scene=prev)

        scene = SceneSchema(
            elements=scene.elements,
            source_type=scene.source_type,
            prompt=scene.prompt.model_copy(update={"style": style_value}),
        )

        with st.spinner("이미지를 재생성 중... (10–20초)"):
            image = generate_image(
                positive=scene.prompt.positive_prompt,
                negative=scene.prompt.negative_prompt,
                style=style_value,
            )
    except Exception as exc:
        st.session_state["_d_demo_error"] = f"재생성 실패: {exc}"
        return

    set_current_scene(scene, novel_text)
    reset_card_widgets()
    append_history(HistoryItem(
        novel_text=novel_text,
        elements=scene.elements.model_dump(),
        prompt=scene.prompt.model_dump(),
        style_label=style_label,
        image_bytes=encode_image_to_bytes(image),
        mode="regenerate",
    ))


def main() -> None:
    st.set_page_config(page_title="Mise — D 단계 데모", layout="wide")
    init_state()

    st.title("Mise — D 단계 인터랙션 UI 데모 (실 API)")
    st.caption(
        "사용자 입력 소설 텍스트를 backend 파이프라인으로 분석하고 Gemini로 이미지를 생성한다. "
        "GOOGLE_API_KEY가 mise/.env에 설정되어 있어야 한다."
    )

    with st.sidebar:
        st.markdown("### 데모 컨트롤")
        st.button(
            "상태 초기화",
            width="stretch",
            key="d_demo_reset",
            on_click=_reset_state,
        )
        st.markdown("---")
        st.markdown("**현재 session_state**")
        st.json({
            "regen_count": st.session_state.get(Keys.REGEN_COUNT, 0),
            "style_label": st.session_state.get(Keys.STYLE_LABEL),
            "history_len": len(st.session_state.get(Keys.HISTORY, [])),
            "selected_history_idx": st.session_state.get(Keys.SELECTED_HISTORY_IDX),
        }, expanded=False)

    error = st.session_state.pop("_d_demo_error", None)
    if error:
        st.error(error)

    st.subheader("0. 소설 텍스트 입력")
    novel_text = st.text_area(
        "장면을 그릴 소설 텍스트 (최대 1000자)",
        value=st.session_state.get(Keys.NOVEL_TEXT) or SAMPLE_NOVEL,
        height=160,
        key="d_demo_novel_input",
    )

    st.subheader("스타일 프리셋 (생성 전 선택 권장)")
    render_style_preset()

    if st.button("장면 분석 + 이미지 생성", type="primary", key="d_demo_run"):
        if not novel_text.strip():
            st.warning("소설 텍스트를 입력하세요.")
        elif len(novel_text) > 1000:
            st.warning(f"입력이 너무 깁니다. (현재 {len(novel_text)}자, 최대 1000자)")
        else:
            try:
                _run_pipeline(novel_text)
            except Exception as exc:
                st.error(f"파이프라인 실패: {exc}")

    if st.session_state.get(Keys.CURRENT_SCENE) is None:
        st.info("위 입력창에 텍스트를 넣고 '장면 분석 + 이미지 생성'을 누르세요.")
        return

    st.subheader("1. 12 요소 카드 (편집 가능)")
    render_scene_cards()

    st.subheader("2. 재생성 (편집된 요소 + 현재 스타일로)")
    render_regenerate_button(on_regenerate=_on_regenerate)

    st.subheader("3. 히스토리")
    render_history_strip()
    render_history_detail()


if __name__ == "__main__":
    main()
