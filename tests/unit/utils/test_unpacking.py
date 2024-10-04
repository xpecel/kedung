from collections.abc import Iterable
from json import dumps, loads

import pytest
from kedung.utils.common_tasks import allocate_data_length
from kedung.utils.unpacking import UnpackRawData
from kedung.utils.userconf import get_preallocate_space

PREALOCATE_SPACE = get_preallocate_space()


@pytest.fixture
def valid_data() -> bytes:
    dummy = [
        b'{"valid_key_1": "data_1", "injected_data": "SET_79885b2a"}',
        b'{"valid_key_2": "data_2", "injected_data": "SET_28e6da17"}',
    ]
    result: list[bytes] = [
        # karena panjang prefix tergantung dari file konfigurasi, lebih
        # baik menggunakan fungsi lain untuk mengalokasikan panjang data
        # alih-alih dengan hardcoded.
        allocate_data_length(data.decode())
        for data in dummy
    ]
    return b"".join(result)


@pytest.fixture
def broken_data() -> list[bytes]:
    chunk: str = dumps({
        "broken_key_1": "data_1",
        "injected_data": "SET_28esd317",
    })
    raw_data: bytes = allocate_data_length(chunk)
    return [raw_data[:PREALOCATE_SPACE + 4], raw_data[PREALOCATE_SPACE + 4:]]


def executor(chunks: Iterable[bytes]) -> dict[str, dict[str, str]]:
    """Unpack data yg diberikan dan kembalikan hasil dari operasi tsb."""
    UnpackRawData._broken_data["client"] = b""
    UnpackRawData._broken_data["server"] = b""

    result: dict[str, dict[str, str]] = {}

    for user in ("client", "server"):
        current_data: dict[str, str] = {}
        for chunk in chunks:
            for raw_data in UnpackRawData(chunk, user):
                current_data = {**current_data, **loads(raw_data)}

        result[user] = current_data

    return result


def test_unpacking_data_with_valid_data(valid_data: bytes) -> None:
    result = executor([valid_data])
    for user in ("client", "server"):
        data = result.get(user)
        if isinstance(data, dict):
            assert data.get("valid_key_1") == "data_1"
            assert data.get("valid_key_2") == "data_2"


def test_unpacking_data_with_broken_data(broken_data: list[bytes]) -> None:
    result = executor(broken_data)
    for user in ("client", "server"):
        data = result.get(user)
        if isinstance(data, dict):
            assert data.get("broken_key_1") == "data_1"


def test_unpacking_data_with_both_data_types(
    broken_data: list[bytes], valid_data: bytes,
) -> None:
    result = executor([*broken_data, valid_data])
    for user in ("client", "server"):
        data = result.get(user)
        if isinstance(data, dict):
            assert data.get("broken_key_1") == "data_1"
            assert data.get("valid_key_1") == "data_1"
