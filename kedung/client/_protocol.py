import asyncio
import json
from typing import TYPE_CHECKING, cast

from kedung.utils.unpacking import UnpackRawData

from ._tmp_storage import TmpStorage

if TYPE_CHECKING:
    from kedung.utils.custom_types import Data


class ClientBufferedProtocol(asyncio.BufferedProtocol):
    def __init__(self) -> None:
        self.buffer = bytearray(512 * 1024)
        self.tmp_storage = TmpStorage()

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport

    def connection_lost(self, exc: Exception | None = None) -> None:  # noqa: ARG002
        self.transport.close()

    def get_buffer(self, sizehint: int) -> bytearray:  # noqa: ARG002
        return self.buffer

    def buffer_updated(self, nbytes: int) -> None:
        raw_data: bytearray = self.buffer[:nbytes]
        for data in UnpackRawData(raw_data, "client"):
            decoded_data = data.decode(encoding="utf-8")
            actual_data: Data = json.loads(decoded_data)
            unique_key: str = cast(str, actual_data.pop("injected_data"))

            # data yg datang disimpan di `TmpStorage`. jadi method yg
            # berkomunikasi dengan server bisa mengecek apakah jawaban
            # atas permintaan dia sudah tersedia apa belum.
            self.tmp_storage.add_data(unique_key, actual_data)
