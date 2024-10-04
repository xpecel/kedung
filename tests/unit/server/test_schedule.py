import asyncio
from datetime import datetime

import pytest
from freezegun import freeze_time
from kedung.server._schdule import (
    _is_expired,
    _remove_expired_items,
    schedule_task,
)
from kedung.server._storage import DataHolder
from kedung.utils.dateandtime import get_localzone
from pytest_mock.plugin import MockerFixture

DummyData = dict[str, dict[str, str | float | object]]
LOCAL_ZONE = get_localzone()


@pytest.fixture
def dummy_data() -> DummyData:
    """Dummy data dengan durasi kadalurasa 5 menit."""
    expired = datetime.now(tz=LOCAL_ZONE).timestamp() + (5 * 60)
    return {
        "key_1": {
            "expired": expired,
            "data": "value_1",
        },
    }


@pytest.fixture
def dummy_data_1_ms() -> DummyData:
    """Dummy data dengan durasi kadaluarsa 0.1 detik."""
    expired = datetime.now(tz=LOCAL_ZONE).timestamp() + 0.1
    return {
        "key_1": {
            "expired": expired,
            "data": "value_1",
        },
    }


@pytest.mark.asyncio
async def test_schedule_task_with_expired_data_in_1_ms(
    mocker: MockerFixture,
    dummy_data_1_ms: DummyData,
) -> None:
    mock_storage = mocker.Mock()
    mock_storage.all_items.return_value = dummy_data_1_ms
    mocker.patch(
        "kedung.server._schdule.CLEANER_DURATION",
        0.1,
    )
    mocker.patch.object(
        DataHolder,
        "_storage",
        dummy_data_1_ms,
    )
    with pytest.raises(TimeoutError):  # noqa: PT012
        # `schedule_task` adalah long-running, perlu dihentikan secara
        # manual.
        await asyncio.wait_for(schedule_task(), timeout=0.2)

    assert not bool(mock_storage.all_items())


@pytest.mark.asyncio
async def test_remove_expired_items(
    mocker: MockerFixture,
    dummy_data: DummyData,
) -> None:
    mock_storage = mocker.Mock()
    mock_storage.all_items.return_value = dummy_data
    mocker.patch.object(
        DataHolder,
        "_storage",
        dummy_data,
    )
    with freeze_time("2025-01-01"):
        await _remove_expired_items()
        wo_data = await _remove_expired_items()  # type: ignore[func-returns-value]

        assert wo_data is None


def test_item_is_not_expired(
    dummy_data: DummyData,
) -> None:
    assert  not _is_expired(dummy_data["key_1"])

def test_item_is_expired(
    dummy_data: DummyData,
) -> None:
    with freeze_time("2025-01-01"):
        assert _is_expired(dummy_data["key_1"])

