from json import dumps, loads
from unittest.mock import MagicMock

import pytest
from kedung.server._protocol import ServerBufferedProtocol
from kedung.utils.common_tasks import allocate_data_length
from kedung.utils.custom_types import Data
from kedung.utils.exceptions import CommandError
from pytest_mock.plugin import MockerFixture


@pytest.fixture
def protocol() -> ServerBufferedProtocol:
    return ServerBufferedProtocol()


@pytest.fixture
def dummy_data() -> Data:
    return {
        "command": "SET",
        "data": {"key_1": "data_1", "injected_data": "injected_value"},
    }


@pytest.fixture
def dummy_data_wo_command() -> Data:
    return {
        "data": {"key_1": "data_1", "injected_data": "injected_value"},
    }


@pytest.fixture
def dummy_data_with_invalid_command() -> Data:
    return {
        "command": "XSET",
        "data": {"key_1": "data_1", "injected_data": "injected_value"},
    }


def test_connection_made(
    mocker: MockerFixture,
    protocol: ServerBufferedProtocol,
) -> None:
    mock_transport = mocker.Mock()
    protocol.connection_made(mock_transport)

    assert protocol.transport is mock_transport


def test_connection_close(
    mocker: MockerFixture,
    protocol: ServerBufferedProtocol,
) -> None:
    mock_transport = mocker.Mock()

    protocol.connection_made(mock_transport)
    protocol.connection_lost()

    assert protocol.transport.is_closing()


def test_get_buffer(protocol: ServerBufferedProtocol) -> None:
    buffer = protocol.get_buffer(8)

    assert len(buffer) == (512 * 1024)


def _buffer_update_executor(
    dummydata: Data,
    mocker: MockerFixture,
    protocol: ServerBufferedProtocol,
) -> MagicMock:
    raw_data = allocate_data_length(dumps(dummydata))
    size_hint = len(raw_data)
    protocol.buffer = bytearray(
        raw_data + protocol.buffer[size_hint:],
    )

    mock_transport = mocker.MagicMock()

    protocol.transport = mock_transport
    protocol.buffer_updated(size_hint)

    return mock_transport  # type: ignore[no-any-return]


def test_buffer_updated(
    protocol: ServerBufferedProtocol,
    mocker: MockerFixture,
    dummy_data: Data,
) -> None:
    result: MagicMock = _buffer_update_executor(
        dummy_data,
        mocker,
        protocol,
    )

    result.write.assert_called_with(
        b'0000050{"key_1": true, "injected_data": "injected_value"}',
    )


def test_buffer_updated_with_invalid_command(
    protocol: ServerBufferedProtocol,
    mocker: MockerFixture,
    dummy_data_with_invalid_command: Data,
) -> None:
    result = _buffer_update_executor(
        dummy_data_with_invalid_command,
        mocker,
        protocol,
    )

    result.write.assert_called_with(
        b'0000082{"errors": ["Perintah `XSET` tidak dikenali!"],'
        b' "injected_data": "injected_value"}',
    )


def test_buffer_updated_wo_command(
    protocol: ServerBufferedProtocol,
    mocker: MockerFixture,
    dummy_data_wo_command: Data,
) -> None:
    result = _buffer_update_executor(
        dummy_data_wo_command,
        mocker,
        protocol,
    )

    result.write.assert_called_with(
        b'0000087{"errors": ["Tidak dapat menemukan key `command`!"],'
        b' "injected_data": "injected_value"}',
    )


def test_process_command(
    protocol: ServerBufferedProtocol,
    dummy_data: Data,
) -> None:
    valid_result = loads(protocol._process_command(dummy_data))

    assert isinstance(valid_result.get("key_1"), bool)


def test_process_command_with_invalid_command_value(
    protocol: ServerBufferedProtocol,
    dummy_data_with_invalid_command: Data,
) -> None:
    with pytest.raises(CommandError) as invalid_exc:
        protocol._process_command(dummy_data_with_invalid_command)

    assert "Perintah `XSET` tidak dikenali!" in str(invalid_exc.value)


def test_process_command_with_missing_key_command(
    protocol: ServerBufferedProtocol,
    dummy_data_wo_command: Data,
) -> None:
    with pytest.raises(CommandError) as missing_command_exc:
        protocol._process_command(dummy_data_wo_command)

    msg = "Tidak dapat menemukan key `command`!"
    assert msg in str(missing_command_exc.value)
