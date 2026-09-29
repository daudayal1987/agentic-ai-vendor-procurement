import pytest

from app.retrieval.config import RetrievalConfig


def test_default_config() -> None:
    config = RetrievalConfig()

    assert config.default_top_k == 5
    assert config.max_top_k == 20
    assert config.minimum_score is None


def test_default_top_k_cannot_exceed_max_top_k() -> None:
    with pytest.raises(ValueError):
        RetrievalConfig(
            default_top_k=21,
            max_top_k=20,
        )


def test_zero_default_top_k_is_rejected() -> None:
    with pytest.raises(ValueError):
        RetrievalConfig(
            default_top_k=0
        )


def test_zero_max_top_k_is_rejected() -> None:
    with pytest.raises(ValueError):
        RetrievalConfig(
            max_top_k=0
        )