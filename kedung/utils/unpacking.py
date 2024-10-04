from typing import ClassVar, Self, cast

from kedung.utils.userconf import get_preallocate_space

PREALLOCATE_SPACE: int = get_preallocate_space()


class UnpackRawData:
    """Proses data mentah dari socket menjadi serializable json.

    **Contoh Penggunaan**:
    .. highlight:: python
    .. code-block:: python
        >>> import json
        >>> from kedung.utils.unpacking import UnpackRawData
        >>> from kedung.utils.common_tasks import allocate_data_length
        >>>
        >>> raw_data: bytes = allocate_data_length(
        ...     json.dumps({"key_1": "data_1", "injected_data": "SET_79885b2a"})
        ... )
        >>>
        >>> for user in ("client", "server"):
        ...     result: dict[str, str] = {}
        ...     for chunk in UnpackRawData(raw_data, user):
        ...         assert json.loads(chunk)
        ...         result = {**result, **json.loads(chunk)}
        ...     result.get("key_1") == "data_1"
        ...     result.get("key_2") == "data_2"
    """

    _broken_data: ClassVar[dict[str, bytes]] = {
        "client": b"",  # menampung broken data untuk client.
        "server": b"",  # menampung broken data untuk server.
    }

    def __init__(self, raw_data: bytes, user: str) -> None:  # noqa: D107
        self._remaining_data: bytes = raw_data
        self._available_data: list[bytes] = []  # data yg siap dideserialisasi.
        self._current_index = 0
        self._user = user
        self._unpack()

    def __iter__(self) -> Self:  # noqa: D105
        return self

    def __next__(self) -> bytes:  # noqa: D105
        if self._current_index >= len(self._available_data):
            raise StopIteration

        result = self._available_data[self._current_index]
        self._current_index += 1

        return result

    def _unpack(self) -> None:
        """Menyiapkan data untuk dideserialisasi."""
        if self._broken_data_status:
            self._remaining_data = self._get_broken_data + self._remaining_data

        while self._remaining_data:
            length_data: int
            prefix = self._remaining_data[:PREALLOCATE_SPACE]  # Berisi panjang data.

            try:
                w_o_zero = self._convert_into_int(prefix)
                length_data = int(w_o_zero)
            except ValueError:
                # karena <n> karkater pertama data yg datang dari socket
                # dialokasikan sebagai prefix, maka data yg berakhir di
                # sini bisa diasumsikan sebagai lanjutan dari data yg
                # sebelumnya terpotong.
                self._set_broken_data(self._user, self._remaining_data)
                break

            # Berisi data yg bisa dideserialisasi atau yg tidak menyebabakan
            # exception.
            data = self._remaining_data[
                PREALLOCATE_SPACE:length_data + PREALLOCATE_SPACE
            ]
            if not data and len(self._remaining_data) >= length_data:
                self._set_broken_data(self._user, self._remaining_data)
                break

            if length_data != len(data):
                # data yg datang dari socket tertopong(tidak komplet),
                # tahan terlebih dahulu dengan harapan data yg datang
                # selanjutnya dari socket adalah lanjutan dari data yg tidak
                # komplet tsb.
                self._set_broken_data(self._user, self._remaining_data)
                break

            self._available_data.append(data)

            remaining_data = self._remaining_data[length_data + PREALLOCATE_SPACE:]

            if not remaining_data:
                # semua data sudah selesai diproses. mengosongkan
                # `self._broken_data[self._user]`, dengan asumsi data yg tidak
                # komplet sudah mendapatkan lanjutan data dari socket, agar
                # bisa digunakan untuk pemprosesannya data yg datang selanjutnya.
                self._set_broken_data(self._user, b"")
                break

            self._remaining_data = remaining_data

    def _convert_into_int(self, prefix: bytes) -> bytes:
        """Mengembalikan string angka tanpa angka 0 disebalah kiri."""
        index = 0
        for counter, character in enumerate(prefix.decode()):
            if character != "0":
                break
            index = counter
        return prefix[index:]

    def _set_broken_data(self, user: str, data: bytes) -> None:
        self.__class__._broken_data[user] = data  # noqa: SLF001

    @property
    def _broken_data_status(self) -> bool:
        data = self.__class__._broken_data.get(self._user)  # noqa: SLF001
        return bool(data)

    @property
    def _get_broken_data(self) -> bytes:
        return cast(bytes, self.__class__._broken_data.get(self._user))  # noqa: SLF001
