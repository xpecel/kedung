import pytest
from kedung.server._storage import DataHolder

DummyData = list[tuple[str, dict[str, str]]]

@pytest.fixture
def holder() -> DataHolder:
    return DataHolder()


@pytest.fixture
def dummy_data() -> DummyData:
    """Dummy data untuk testing."""
    return [
        ("unique_key_1", {"key_1": "MCDW 300"}),
        ("unique_key_2", {"key_2": "station 8"}),
    ]


def test_holder_has_storage_attr(holder: DataHolder) -> None:
    assert hasattr(holder, "_storage")


def test_set_data(holder: DataHolder, dummy_data: DummyData) -> None:
    key = dummy_data[0][0]

    holder.set_(key, dummy_data[0][1])

    assert holder._storage.get(key)


def test_get_data(holder: DataHolder, dummy_data: DummyData) -> None:
    key_1: str = dummy_data[0][0]

    holder.set_(key_1, dummy_data[0][1])
    get_data: dict[str, object] = holder.get(key_1)

    assert get_data.get(key_1)


def test_clear_data(holder: DataHolder, dummy_data: DummyData) -> None:
    key = dummy_data[0][0]

    holder.set_(key, dummy_data[0][1])

    assert holder.clear(key)

def test_clear_all_data(holder: DataHolder, dummy_data: DummyData) -> None:
    holder.set_(dummy_data[0][0], dummy_data[0][1])

    assert holder.clear_all()
