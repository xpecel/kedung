import asyncio
import json
from pathlib import Path
from typing import TypeVar, cast

from kedung.client import _helper as helper
from kedung.client._protocol import ClientBufferedProtocol
from kedung.client._tmp_storage import TmpStorage
from kedung.utils.common_tasks import allocate_data_length
from kedung.utils.custom_types import Data
from kedung.utils.exceptions import MissingComponentError
from kedung.utils.files import SocketPath
from kedung.utils.userconf import get_sock_path

T = TypeVar("T", bound="Client")


class Client:
    """Utilitas utuk berkomonukasi dengan storage server.

    contoh penggunaan:
    .. highlight:: python
    .. code-block:: python
        >>> import asyncio
        >>> from kedung.client import Client
        >>> from kedung.utils.custom_types import Data
        >>>
        >>> client = Client()
        >>> command = "SET"
        >>> data = {"key_data_1": "value_data_1"}
        >>>
        >>> async def main() -> None:
        >>>     await client.create_connection()
        >>>     result: Data = await client.send(command, data)
        >>>     result.get("key_data_1") == "value_data_1"
        >>>
        >>> asyncio.run(main())

    Command yg dapat digunakan bisa dikategorikan menjadi dua kelompok.
    Untuk satu operasi dan multi-operasi.

    Untuk `command` satu operasi, bentuknya seperti contoh di atas.

    Sedangkan `command` untuk multi operasi, `command` diawali dengan
    prefix `B` dilanjutkan nama operasinya.
    Untuk contoh data multi operasi bisa seperti,
    `{"key_data_1": "value_data_1", "key_data_2": "value_data_2"}`.

    Command yg dapat digunakan diantaranya sebagai berikut,

    # Operasi tungggal
    `SET` untuk menyimpan data baru ke storage.
    `GET` untuk mendapatkan data dari storage berdasarkan key yg ada di
        dalam `data`.
    `DEL` untuk Menghapus data dari storage berdasarkan key yg ada di
        daalam `data`.
    `EXIST` untuk mengembalikan status kebardaan object di storage
        berdasarkan key yg ada di dalam `data`.

    # Multi operasi
    `BSET` untuk Menyimpan multiple data dalam sekali operasi ke dalam
        storage.
    `BGET` untuk mendapatkan multiple data dalam sekali operasi dari
        dalam storage berdasarkan keys yg ada di dalam `data`.
    `BDEL` untuk menghapus multiple data dalam sekali operasi dari dalam
        storage berdasarkan keys yg ada di dalam `data`.
    `BEXISTS` untuk mengembalikan multiple status kebardaan object di
        dalam storage berdasarkan keys yg ada di dalam `data`.

    `FLUSH` untuk menghapus semua data yang tersimpan di dalam storage.
    """

    _connection_established = False
    _sock_file: Path | None = None
    _transport: asyncio.Transport
    _protocol: asyncio.Protocol

    def __init__(self, socket_path: str | None = None) -> None:  # noqa: D107
        self._tmp_storage = TmpStorage()
        path = socket_path or get_sock_path()
        socket_obj = SocketPath()
        socket_obj.set_path(path)
        self.__class__._sock_file = Path(socket_obj.path_file)  # noqa: SLF001

    @classmethod
    def close_connection(cls) -> None:
        """Menutup koneksi ke server."""
        cls._transport.close()

    @classmethod
    async def create_connection(cls) -> None:
        """Membuat koneksi ke server.

        Setidaknya harus dipanggil sekali selama runtime.
        """
        if not cls._connection_established:
            loop = asyncio.get_running_loop()
            cls._transport, cls._protocol = await loop.create_unix_connection(
                protocol_factory=ClientBufferedProtocol,  # type: ignore[arg-type]
                path=str(cls._sock_file),
            )
            cls._connection_established = True

    async def send(self, command: str, data: Data | None = None) -> Data:
        """Mengirimkan perintah dan data melalui soket.

        :param command: Perintah yang akan dikirimkan.
        :type command: str
        :param data: Kecuali untuk command `FLUSH`, parameter `data`
            memiliki tipe dictionary. Key merepresentasikan id dengan
            tipe string, sedangkan value berisi tipe data yg dapat
            diserialisasi ke dalam format json.
        :type data: Data | None
        :raises TypeError: Mengindikasikan jika paramter `data` tidak
            dapat konversi ke dalam format json.
        :return: Data, dalam bentuk dictionary, yg dikembalikna oleh
            server atas permintaan client.
        :rtype: Data
        """
        if not data and command == "FLUSH":
            data = {}
        elif not data and command != "FLUSH":
            msg = "Kecuali command `FLUSH`, argumen `data` tidak boleh `Falsy`"
            raise MissingComponentError(msg)

        encoded_data, unique_key = self._pre_processing_data(
            command.upper(),
            cast(Data, data),
        )
        self._transport.write(encoded_data)

        operation_result: Data
        while True:
            result, status = self._get_injected_data(unique_key)
            if status:
                operation_result = cast(Data, result)
                break
            await asyncio.sleep(0.01)

        return operation_result

    def _pre_processing_data(
        self,
        command: str,
        data: Data,
    ) -> tuple[bytes, str]:
        # membuatkan identitas untuk setiap pemanggilan method `send`.
        # ketika menggunakan soket, data yang dikirim dan diterima tidak
        # selalu tersegmentasi dengan benar. ini berarti beberapa pesan
        # dapat digabungkan menjadi satu atau bisa juga pesan tunggal
        # dipotong menjadi beberapa bagian, tergantung pada kapan data
        # diterima oleh protokol. berikut adalah data yg kemungkinan dikirim
        # dan diterma:
        # >>> y = b'0018{"key_1":"data_1"}'
        # >>> x = b'0018{"key_1":"data_1"}0018{"key_2":"data_2"}'
        #
        # jadi untuk mengetahui data yg datang itu milik siapa, maka
        # ditambhakn identitas untuk setiap kali pemnggilan method
        # `send`. berikut adalah data yg kemungkinan dikirm dan diterima:
        # >>> y = b'0051{"key_1":"data_1", "injected_data": "SET_79885b2a"}'
        # >>> x = b'0051{"key_1":"data_1", "injected_data":
        # "SET_79885b2a"}0051{"key_2":"data_2", , "injected_data": "SET_28e6da17"}'
        #
        # dengan begini method bisa memerika apakah data yg mereka
        # harapakan sudah tersedia atau belum.

        unique_key: str = helper.create_unique_key(command)

        try:
            injected_data = helper.inject_data(data, unique_key)
        except TypeError as exc:
            msg = "Parameter `data` harus dalam bentuk dictionary."
            raise TypeError(msg) from exc

        injected_data = helper.inject_data(data, unique_key)
        informations = {"command": command, "data": injected_data}

        json_data: str = json.dumps(informations)

        return (allocate_data_length(json_data), unique_key)

    def _get_injected_data(self, unique_key: str) -> tuple[Data | None, bool]:
        """Mendaptakn data dari `TmpStorage`.

        :param unique_key: Kunci unik yg dibuatkan setiap kali
            pemnggilan method `send`.
        :type unique_key: str
        :return: Jika `unique_key` ada di dalam `TmpStorage`, maka
            kemablikan Tuple dengan index pertama adalah data yg datang
            dari server dan index kedua adalah `True`. Jika tidak, tuple
            dengan index pertama `None` dan index kedua `False`.
        :rtype: tuple[Data | None, bool]
        """
        result = self._tmp_storage.get_data(unique_key)

        if result:
            return result, True

        return None, False
