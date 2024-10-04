"""Mengkover test yg belum atau tidak terkover di modul lain."""

from typing import cast

import pytest
from kedung.client._helper import create_unique_key, inject_data
from kedung.client._tmp_storage import TmpStorage
from kedung.utils.custom_types import Data


@pytest.fixture
def dummy_data() -> dict[str, str]:
    return {"key_1": "data_1"}


@pytest.fixture
def storage() -> TmpStorage:
    return TmpStorage()


def test_add_data_into_storage(
    dummy_data: dict[str, str],
    storage: TmpStorage,
) -> None:
    unique_key = "unique_1"

    storage.add_data(unique_key, cast(Data, dummy_data))

    assert storage._bucket.get(unique_key)


def test_get_data_from_storage(
    dummy_data: dict[str, str],
    storage: TmpStorage,
) -> None:
    unique_key = "unique_1"

    storage.add_data(unique_key, cast(Data, dummy_data))
    result = storage.get_data(unique_key)

    assert result
    assert storage._bucket.get(unique_key) is None


def test_inject_data(dummy_data: dict[str, str]) -> None:
    result = inject_data(cast(Data, dummy_data), "test_injected_data")
    assert result.get("injected_data")


def test_crete_unique_key() -> None:
    command = "GET"
    result_length = 12
    result = create_unique_key(command)

    assert len(result) == result_length
    assert command in result
