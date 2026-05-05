"""D 단계 (인터랙션 UI) 컴포넌트 단독 데모.

C 단계 메인 흐름이 통합되기 전에 D 컴포넌트만 따로 시연하기 위한 페이지.
실제 Gemini 호출 없이 더미 SceneSchema와 PIL로 그린 가짜 이미지로 동작한다.

실행:
    streamlit run mise/app_d_demo.py
"""
from __future__ import annotations

from PIL import Image, ImageDraw

import streamlit as st

from mise.components.history import (
    encode_image_to_bytes,
    render_history_detail,
    render_history_strip,
)
from mise.components.regenerate import render_regenerate_button
from mise.components.scene_card import render_scene_cards, reset_card_widgets
from mise.components.style_preset import render_style_preset
from mise.models.scene_schema import PromptResult, SceneElements, SceneSchema
from mise.state import (
    HistoryItem,
    Keys,
    append_history,
    build_prev_scene_payload,
    get_edited_elements,
    init_state,
    reset_regen_count,
    set_current_scene,
)

DUMMY_NOVEL = (
    "붉은 노을 아래 무너진 성벽 너머로 거대한 마법진이 떠오르고 있었다. "
    "검은 갑옷을 입은 기사가 폐허 위에 홀로 서서 하늘을 올려다보았다. "
    "바람이 그의 망토를 흔들었다."
)

DUMMY_ELEMENTS = SceneElements(
    character="검은 갑옷을 입은 기사, 망토가 바람에 흔들림",
    background="폐허가 된 성벽, 무너진 돌무더기",
    time="저녁",
    place="무너진 성벽 위",
    objects=["거대한 마법진", "검", "흩날리는 망토"],
    action="하늘을 올려다보고 있다",
    emotion="경외",
    mood="장엄하고 불길한 분위기",
    color="붉은색과 주황색 노을",
    lighting="노을빛, 역광",
    camera_view="성벽 너머를 바라보는 와이드샷",
    composition="배경 중심 구도",
)

DUMMY_SOURCE_TYPE = {
    "character": "original",
    "background": "original",
    "time": "inferred",
    "place": "original",
    "objects": "original",
    "action": "original",
    "emotion": "inferred",
    "mood": "inferred",
    "color": "original",
    "lighting": "inferred",
    "camera_view": "inferred",
    "composition": "inferred",
}

DUMMY_PROMPT = PromptResult(
    positive_prompt=(
        "cinematic, a knight in black armor with cloak fluttering, looking up at the sky, "
        "ruined castle wall, giant magic circle floating, sunset, red and orange tones, "
        "wide shot, dramatic lighting, high quality, detailed"
    ),
    negative_prompt=(
        "excessive gore, explicit content, hate symbols, blurry, low quality, deformed, "
        "text, watermark, signature, out of frame"
    ),
    style="cinematic",
    missing_info=[],
)


def _make_dummy_image(seed_text: str, style_value: str) -> bytes:
    """텍스트와 스타일에 따라 색이 달라지는 단순 이미지 (실 API 대체용)."""
    palette = {
        "cinematic": (180, 60, 40),
        "watercolor painting": (90, 130, 200),
        "pixel art": (50, 200, 120),
        "webtoon style": (240, 160, 90),
    }
    color = palette.get(style_value, (120, 120, 120))
    img = Image.new("RGB", (640, 360), color=color)
    draw = ImageDraw.Draw(img)
    title = seed_text[:24]
    draw.text((20, 160), f"[{style_value}]\n{title}", fill=(255, 255, 255))
    return encode_image_to_bytes(img) or b""


def _reset_state() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def _load_dummy_scene() -> None:
    scene = SceneSchema(
        elements=DUMMY_ELEMENTS,
        source_type=DUMMY_SOURCE_TYPE,
        prompt=DUMMY_PROMPT,
    )
    set_current_scene(scene, DUMMY_NOVEL)
    reset_regen_count()
    reset_card_widgets()
    style_value = st.session_state.get(Keys.STYLE_LABEL, "시네마틱")
    image_bytes = _make_dummy_image(DUMMY_NOVEL, style_value)
    append_history(HistoryItem(
        novel_text=DUMMY_NOVEL,
        elements=DUMMY_ELEMENTS.model_dump(),
        prompt=DUMMY_PROMPT.model_dump(),
        style_label=style_value,
        image_bytes=image_bytes,
        mode="generate",
    ))


def _on_regenerate() -> None:
    """편집된 요소를 새 SceneSchema로 만들어 history에 추가하는 더미 콜백.

    실제 통합에서는 여기서 extract_scene(mode='regenerate', prev_scene=...)을 호출하고,
    그 결과로 image_generator.generate_image()를 부른다.
    """
    edited = get_edited_elements() or DUMMY_ELEMENTS.model_dump()
    style_label = st.session_state[Keys.STYLE_LABEL]
    new_scene = SceneSchema(
        elements=SceneElements.model_validate(edited),
        source_type=DUMMY_SOURCE_TYPE,
        prompt=DUMMY_PROMPT.model_copy(update={"style": style_label}),
    )
    set_current_scene(new_scene, st.session_state[Keys.NOVEL_TEXT])
    reset_card_widgets()
    style_value = st.session_state.get(Keys.STYLE_LABEL, "시네마틱")
    seed = edited.get("character") or DUMMY_NOVEL
    image_bytes = _make_dummy_image(seed, style_value)
    append_history(HistoryItem(
        novel_text=st.session_state[Keys.NOVEL_TEXT],
        elements=edited,
        prompt=new_scene.prompt.model_dump(),
        style_label=style_value,
        image_bytes=image_bytes,
        mode="regenerate",
    ))


def main() -> None:
    st.set_page_config(page_title="Mise — D 단계 데모", layout="wide")
    init_state()

    st.title("Mise — D 단계 인터랙션 UI 데모")
    st.caption(
        "C 단계 메인 흐름 통합 전 단독 데모. 더미 SceneSchema와 가짜 이미지로 동작하며, "
        "session_state 키 명세는 mise/state.py 참고."
    )

    with st.sidebar:
        st.markdown("### 데모 컨트롤")
        st.button(
            "더미 분석 결과 로드",
            type="primary",
            width="stretch",
            key="d_demo_load",
            on_click=_load_dummy_scene,
        )
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

    if st.session_state.get(Keys.CURRENT_SCENE) is None:
        st.info("왼쪽 사이드바의 '더미 분석 결과 로드'를 눌러 시작하세요.")
        return

    st.subheader("1. 12 요소 카드 (편집 가능)")
    render_scene_cards()

    st.subheader("2. 스타일 프리셋")
    render_style_preset()

    st.subheader("3. 재생성")
    render_regenerate_button(on_regenerate=_on_regenerate)

    st.subheader("4. 히스토리")
    render_history_strip()
    render_history_detail()


if __name__ == "__main__":
    main()
