import asyncio
from pathlib import Path

import structlog

from kedung.utils.files import SocketPath
from kedung.utils.logging import default_strouctlog_config
from kedung.utils.userconf import get_sock_path

from ._protocol import ServerBufferedProtocol
from ._schdule import schedule_task
from ._storage import DataHolder

logger = structlog.get_logger()


class Server:
    """Sebuah TCP server yg memanfaatkan unix socket untuk berkomunikasi.

    contoh penggunaan:
    .. highlight:: python
    .. code-block:: python
        >>> import asyncio
        >>> from kedung import Server
        >>> from kedung.utils.custom_types import Data
        >>>
        >>> async def main() -> None:
        >>>    server = Server()
        >>>    loop = asyncio.get_event_loop()
        >>>
        >>>    try:
        >>>        await server.run()
        >>>    except asyncio.CancelledError:
        >>>        if loop.is_running():
        >>>            loop.close()
        >>>
        >>> asyncio.run(main())
    """

    def __init__(self, socket_path: str | None = None) -> None:  # noqa: D107
        default_strouctlog_config()
        path = socket_path or get_sock_path()
        socket_obj = SocketPath()
        socket_obj.set_path(path)
        self._socket_file = Path(socket_obj.path_file)

    async def _create_server(self, sock_name: str | Path) -> asyncio.Server:
        loop = asyncio.get_event_loop()
        server: asyncio.Server = await loop.create_unix_server(
            ServerBufferedProtocol,
            path=sock_name,
        )
        return server

    async def _prepare_socket_file(self) -> None:
        if not self._socket_file.exists():
            await logger.ainfo("Membuat socket file.")
            self._socket_file.touch()

    async def _start_server(self) -> asyncio.Server:
        os_error = {106, 98}

        try:
            await logger.ainfo("Memuat server ...")
            return await self._create_server(self._socket_file)
        except OSError as OE:
            error_code: int = OE.args[0]

            if error_code in os_error:
                await logger.awarning("Terjadi kesalahan ketika memulai server.")
                await logger.awarning(OE)
                await logger.ainfo("Memulai ulang server ...")
                self._socket_file.unlink()
                return await self._create_server(self._socket_file)

            await logger.awarning("Kesalahan tak terduga terjadi.")
            await logger.awarning(OE)
            raise

    async def run(self) -> None:
        """Menjalankan server."""
        await self._prepare_socket_file()
        server = await self._start_server()

        try:
            await schedule_task()
            async with server:
                await server.serve_forever()
        except asyncio.CancelledError:
            await logger.ainfo("Menerima sinyal `SIGINT`, mengehentikan server!")
            server.close()
            storage = DataHolder()
            storage.clear_all()
