from json import dumps
from typing import cast

import pytest
from kedung.server._serdes import deserializer, serilizer
from kedung.utils.custom_types import Data


@pytest.fixture
def dummy_data() -> dict[str, str]:
    """Dummy data untuk testing."""
    return {"key_1": "value_1"}


def test_deserializer(dummy_data: dict[str, str]) -> None:
    encoded_data: str = dumps(dummy_data)
    assert isinstance(deserializer(encoded_data), dict)


def test_serializer(dummy_data: dict[str, str]) -> None:
    serializer_data = serilizer(cast(Data, dummy_data))
    assert isinstance(serializer_data, str)
