import asyncio
from collections.abc import MutableMapping
from typing import TYPE_CHECKING, cast

import structlog

from kedung.utils.common_tasks import allocate_data_length
from kedung.utils.custom_types import Data
from kedung.utils.exceptions import CommandError, MissingComponentError
from kedung.utils.unpacking import UnpackRawData

from ._commands import Command
from ._serdes import deserializer, serilizer

if TYPE_CHECKING:
    from ._types import CommandCall

logger = structlog.get_logger()


class ServerBufferedProtocol(asyncio.BufferedProtocol):
    def __init__(self) -> None:
        self.buffer = bytearray(512 * 1024)
        self.command = Command()
        super().__init__()

    def connection_made(
        self, transport: asyncio.Transport,  # type: ignore[override]
    ) -> None:
        self.transport = transport
        logger.info("Koneksi dibuat!")

    def connection_lost(self, exc: Exception | None = None) -> None:  # noqa: ARG002
        self.transport.close()
        logger.info("Koneksi terputus!")

    def get_buffer(self, sizehint: int) -> bytearray:  # noqa: ARG002
        return self.buffer

    def buffer_updated(self, nbytes: int) -> None:
        raw_data: bytearray = self.buffer[:nbytes]

        for data in UnpackRawData(raw_data, "server"):
            result: Data = deserializer(data)
            try:
                response: str = self._process_command(result)
            except (MissingComponentError, CommandError) as exc:
                response = serilizer(exc.args[0])
            finally:
                mapped_data: bytes = allocate_data_length(response)
                self.transport.write(mapped_data)

    def _process_command(self, user_data: Data) -> str:
        error_msg: list[str]
        result: Data

        data_value = cast(
            MutableMapping[object, object], user_data.get("data"),
        )
        injected_data = cast(str, data_value.get("injected_data"))
        command = cast(str | None, user_data.get("command"))

        # Validasi jika  key `command` ada di dalam `user_data` dan
        # terdaftar di kelas `Command` sebagai salah satu method.
        if not isinstance(command, str):
            error_msg = ["Tidak dapat menemukan key `command`!"]
            result = {"errors": error_msg, "injected_data": injected_data}
            raise CommandError(result)

        command_call: CommandCall | None = self.command.get_command(command)

        if not command_call:
            error_msg = [f"Perintah `{command}` tidak dikenali!"]
            result = {"errors": error_msg, "injected_data": injected_data}
            raise CommandError(result)

        result = command_call(user_data)
        return serilizer(result)
