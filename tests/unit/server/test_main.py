import asyncio
from collections.abc import Generator
from pathlib import Path
from shutil import rmtree
from tempfile import mkstemp
from unittest.mock import AsyncMock

import pytest
from kedung.server import Server
from pytest_mock.plugin import MockerFixture


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown() -> Generator[None]:  # noqa: PT004
    yield
    junk_dir = list(Path("/tmp/").glob("kedung_*/"))
    junk_file = list(Path("/tmp/").glob("kedung_test*.sock"))

    for junk in [*junk_dir, *junk_file]:
        if junk.is_dir():
            rmtree(junk)
        elif junk.is_file():
            junk.unlink()


@pytest.fixture
def server() -> Server:
    return Server()


@pytest.fixture
def socket_path() -> str:
    """Menyediakan path socket untuk testing."""
    _, location = mkstemp(prefix="kedung_test_", suffix=".sock", dir="/tmp/")
    return location


@pytest.mark.asyncio
async def test_create_server(
    mocker: MockerFixture,
    server: Server,
    socket_path: str,
) -> None:
    loop = asyncio.get_running_loop()
    mock_server = mocker.Mock(spec=asyncio.Server)
    mocker.patch.object(
        loop,
        "create_unix_server",
        AsyncMock(return_value=mock_server),
    )

    _server = await server._create_server(str(socket_path))

    assert _server == mock_server


@pytest.mark.asyncio
async def test_prepare_socket_file(
    mocker: MockerFixture,
    server: Server,
) -> None:
    socket_path = Path("/tmp/kedung_test.sock")
    mocker.patch.object(
        server,
        "_socket_file",
        socket_path,
    )
    await server._prepare_socket_file()

    socket_file = Path(server._socket_file)
    assert socket_file.exists()
    assert socket_file.is_file()


@pytest.mark.asyncio
async def test_start_server(
    mocker: MockerFixture,
    server: Server,
) -> None:
    loop = asyncio.get_running_loop()
    mock_server = mocker.Mock(spec=asyncio.Server)
    mocker.patch.object(
        loop,
        "create_unix_server",
        AsyncMock(return_value=mock_server),
    )

    result = await server._start_server()

    assert result == mock_server


@pytest.mark.asyncio
async def test_successfully_run(
    mocker: MockerFixture,
    server: Server,
) -> None:
    mock_schedule_task = AsyncMock()
    mock_start_server = AsyncMock(spec=asyncio.Server)
    mock_serve_forever = AsyncMock()

    mocker.patch(
        "kedung.server.schedule_task",
        side_effect=mock_schedule_task,
    )
    mocker.patch.object(
        Server,
        "_start_server",
        return_value=mock_start_server,
    )
    mocker.patch.object(
        mock_start_server,
        "serve_forever",
        side_effect=mock_serve_forever,
    )

    await server.run()

    mock_serve_forever.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_server_with_timeout_limit(
    mocker: MockerFixture,
    server: Server,
) -> None:
    mock_schedule_task = AsyncMock()

    mocker.patch(
        "kedung.server.schedule_task",
        side_effect=mock_schedule_task,
    )
    await asyncio.wait_for(server.run(), timeout=0.2)
