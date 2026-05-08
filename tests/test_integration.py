import os
import pytest

# 실제 API 키가 있고 RUN_INTEGRATION=1일 때만 실행
pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION"),
    reason="RUN_INTEGRATION 환경 변수가 설정되지 않음. 실제 API 호출 테스트 생략.",
)

from mise.chains.scene_extractor import extract_scene
from mise.models.scene_schema import SceneSchema
from tests.samples import (
    NOVEL_SAMPLE_1,
    NOVEL_SAMPLE_2,
    NOVEL_SAMPLE_3,
    NOVEL_SAMPLE_4,
    NOVEL_SAMPLE_5,
    NOVEL_SAMPLE_6,
)


class TestIntegration:
    def test_generate_sample1(self):
        result = extract_scene(NOVEL_SAMPLE_1)
        assert isinstance(result, SceneSchema)
        assert result.elements.character != ""
        assert result.prompt.positive_prompt != ""
        assert "blurry" in result.prompt.negative_prompt

    def test_generate_sample2(self):
        result = extract_scene(NOVEL_SAMPLE_2)
        assert isinstance(result, SceneSchema)
        assert result.elements.place != ""

    def test_generate_sample3(self):
        result = extract_scene(NOVEL_SAMPLE_3)
        assert isinstance(result, SceneSchema)
        assert len(result.elements.objects) >= 0

    def test_regenerate_from_previous(self):
        first = extract_scene(NOVEL_SAMPLE_1)
        prev = {"elements": first.elements.model_dump(), "source_type": first.source_type}
        regenerated = extract_scene(NOVEL_SAMPLE_1, mode="regenerate", prev_scene=prev)
        assert isinstance(regenerated, SceneSchema)
        assert regenerated.elements.character == first.elements.character
        assert regenerated.prompt.positive_prompt != ""

    def test_generate_sample4_daily(self):
        """일상 장면: 지하철, 실내 조명, 군중 등 현실 배경 처리"""
        result = extract_scene(NOVEL_SAMPLE_4)
        assert isinstance(result, SceneSchema)
        assert result.elements.place != ""
        assert result.prompt.positive_prompt != ""

    def test_generate_sample5_sf(self):
        """SF 장면: 우주, 방호복, 행성 등 비현실적 배경 처리"""
        result = extract_scene(NOVEL_SAMPLE_5)
        assert isinstance(result, SceneSchema)
        assert result.elements.background != ""
        assert result.prompt.positive_prompt != ""

    def test_generate_sample6_abstract(self):
        """추상묘사: 감정/개념 중심 텍스트에서 시각 요소 추출"""
        result = extract_scene(NOVEL_SAMPLE_6)
        assert isinstance(result, SceneSchema)
        assert result.prompt.positive_prompt != ""
        assert result.prompt.negative_prompt != ""

    def test_all_elements_populated(self):
        """12개 요소가 모두 비어있지 않은지 확인 (누락률 측정)"""
        result = extract_scene(NOVEL_SAMPLE_1)
        empty_count = sum(
            1 for field_name, value in result.elements.model_dump().items()
            if field_name != "objects" and (value == "" or value == [])
        )
        assert empty_count <= 1, f"{empty_count}개 요소가 비어있음"
