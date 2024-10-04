import pytest
from kedung.client._protocol import ClientBufferedProtocol
from kedung.utils.common_tasks import allocate_data_length
from pytest_mock.plugin import MockerFixture


@pytest.fixture
def protocol() -> ClientBufferedProtocol:
    return ClientBufferedProtocol()


@pytest.fixture
def raw_data_wtih_prefix() -> bytes:
    raw_data = [
        b'{"key_1": "data_1", "injected_data": "SET_79885b2a"}',
        b'{"key_2": "data_2", "injected_data": "SET_28e6da17"}',
    ]
    result: list[bytes] = [
        # karena panjang prefix tergantung dari file konfigurasi, lebih
        # baik menggunakan fungsi lain untuk mengalokasikan panjang data
        # alih-alih dengan hardcoded.
        allocate_data_length(data.decode())
        for data in raw_data
    ]
    return b"".join(result)


def test_connection_made(
    mocker: MockerFixture,
    protocol: ClientBufferedProtocol,
) -> None:
    mock_transport = mocker.Mock()
    protocol.connection_made(mock_transport)

    assert protocol.transport is mock_transport


def test_connection_close(
    mocker: MockerFixture,
    protocol: ClientBufferedProtocol,
) -> None:
    mock_transport = mocker.Mock()

    protocol.connection_made(mock_transport)
    protocol.connection_lost()

    assert protocol.transport.is_closing()


def test_get_buffer(protocol: ClientBufferedProtocol) -> None:
    buffer = protocol.get_buffer(8)
    assert len(buffer) == (512 * 1024)


def test_buffer_updated(
    raw_data_wtih_prefix: bytes,
    protocol: ClientBufferedProtocol,
) -> None:
    size_hint = len(raw_data_wtih_prefix)
    protocol.buffer = bytearray(
        raw_data_wtih_prefix + protocol.buffer[size_hint:],
    )

    protocol.buffer_updated(size_hint)

    assert bool(protocol.tmp_storage._bucket)
