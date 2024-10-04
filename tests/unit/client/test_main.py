import asyncio
from typing import cast
from unittest.mock import AsyncMock

import pytest
from kedung.client import Client
from kedung.utils.custom_types import Data
from kedung.utils.exceptions import MissingComponentError
from pytest_mock.plugin import MockerFixture


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture
def dummy_data() -> tuple[str, dict[str, str]]:
    return ("GET", {"key_1": "data_1"})


@pytest.mark.asyncio
async def test_create_connection(
    mocker: MockerFixture,
    client: Client,
) -> None:
    loop = asyncio.get_running_loop()
    mock_transport = mocker.Mock(spec=asyncio.Transport)
    mock_protocol = mocker.Mock(spec=asyncio.Protocol)

    mocker.patch.object(
        loop,
        "create_unix_connection",
        AsyncMock(return_value=(mock_transport, mock_protocol)),
    )
    await client.create_connection()

    assert client._connection_established


@pytest.mark.asyncio
async def test_close_connection(
    mocker: MockerFixture,
    client: Client,
) -> None:
    loop = asyncio.get_running_loop()
    mock_transport = mocker.Mock(spec=asyncio.Transport)
    mock_protocol = mocker.Mock(spec=asyncio.Protocol)

    # Mock metode create_unix_connection untuk mengembalikan mock transport dan protocol
    mocker.patch.object(
        loop,
        "create_unix_connection",
        AsyncMock(return_value=(mock_transport, mock_protocol)),
    )
    await client.create_connection()
    client.close_connection()

    assert mock_transport.is_closing()


def test_pre_processing_with_valid_data(
    client: Client,
    dummy_data: tuple[str, dict[str, str]],
) -> None:
    length_key = 12  # "GET_<8 karakter acak>"

    encoded_data, unique_key = client._pre_processing_data(
        dummy_data[0],
        cast(Data, dummy_data[1]),
    )

    assert len(unique_key) == length_key
    assert unique_key in encoded_data.decode()


def test_pre_processing_with_non_serializable_data_type(
    client: Client,
    dummy_data: tuple[str, dict[str, str]],
) -> None:
    with pytest.raises(TypeError) as exception:
        client._pre_processing_data(
            dummy_data[0],
            object,  # type: ignore[arg-type]
        )

    msg = "Parameter `data` harus dalam bentuk dictionary."
    assert str(exception.value) == msg


def test_get_injected_data_with_existing_key(
    mocker: MockerFixture,
    client: Client,
    dummy_data: tuple[str, dict[str, str]],
) -> None:
    unique_key = "GET_79885b2a"
    mock_response = {unique_key: dummy_data[1]}

    mocker.patch.object(
        client._tmp_storage,
        "get_data",
        return_value=mock_response,
    )

    result: tuple[Data | None, bool] = client._get_injected_data(unique_key)

    assert result[0]
    assert result[1]


def test_get_injected_data_with_non_existing_key(
    client: Client,
) -> None:
    unique_key = "GET_79885b2a"

    result: tuple[Data | None, bool] = client._get_injected_data(unique_key)

    assert result[0] is None
    assert not result[1]


@pytest.mark.asyncio
async def test_send(
    mocker: MockerFixture,
    client: Client,
    dummy_data: tuple[str, dict[str, str]],
) -> None:
    mocker.patch.object(
        client._transport,
        "write",
        return_value=mocker.Mock(),
    )
    mocker.patch.object(
        client,
        "_get_injected_data",
        return_value=({"key_1": True}, True),
    )
    result: Data = await client.send(
        command=dummy_data[0],
        data=cast(Data, dummy_data[1]),
    )

    assert result.get("key_1")


@pytest.mark.asyncio
async def test_send_non_flush_command_with_falsy_data(
    client: Client,
    dummy_data: tuple[str, dict[str, str]],
) -> None:
    msg = "Kecuali command `FLUSH`, argumen `data` tidak boleh `Falsy`"

    with pytest.raises(MissingComponentError) as exception:
        await client.send(
            command=dummy_data[0],
            data={},
        )

    assert str(exception.value) == msg
