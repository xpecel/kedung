from datetime import datetime, tzinfo
from typing import TYPE_CHECKING, ClassVar, cast

from kedung.utils.custom_types import Storage
from kedung.utils.dateandtime import get_localzone
from kedung.utils.userconf import get_cache_duration

if TYPE_CHECKING:
    from collections.abc import MutableMapping

CACHE_DURATION: int = get_cache_duration()


class DataHolder:
    """Implementasi sederhana dari sebuah penyimpanan."""

    _storage: ClassVar[Storage] = {}

    @classmethod
    def clear(cls, key: str) -> bool:
        """Menghapus data yg tersimpan berdasarkan `key` yg diberikan."""
        if not bool(cls._storage.get(key)):
            return False

        cls._storage.pop(key)
        return True

    @classmethod
    def clear_all(cls) -> bool:
        """Menghapus semua data yg disimpan sementara di dalam memory."""
        cls._storage.clear()
        return bool(not cls._storage)

    @classmethod
    def get(cls, key: str) -> dict[str, object]:
        """Mendapatkan data yg tersimpan berdasarkan `key` yg diberikan."""
        data: MutableMapping[str, datetime | object] | None

        data = cls._storage.get(key)
        if not data:
            return {key: None}

        return {key: data["data"]} if data else {key: None}

    @classmethod
    def set_(cls, key: str, value: object) -> dict[str, bool]:
        """Membuat data baru yg akan di simpan sementara dalam memory.

        :param key: kata kunci untuk objek yg akan disimpan.
        :type key: str
        :param value: nilai value yang akan dimasukan ke dalam cache.
        :type value: object
        :return: dictionary dengan `key` yg merepresentasikan kata kunci
            untuk mencari data di dalam `_storage` dan `value` berupa
            `bool`. jika value `True` maka data berhasil dibuat, jika
            `False` berarti data sudah ada di dalam `_storage` atau belum
            kadaluarsa.
        :rtype: dict[str, bool]
        """
        local_timezone: tzinfo = get_localzone()
        now: datetime = datetime.now(tz=local_timezone)

        # jika data ada dan tidak kadalurasa, tidak perlu
        # memperbaruinya/overwrite.
        if (key in cls._storage) and not cls._is_data_expired(key):
            return {key: False}

        expired: float = now.timestamp() + (CACHE_DURATION * 60)

        cls._storage[key] = {
            "expired": expired,
            "data": value,
        }

        return {key: True}

    @classmethod
    def all_items(cls) -> Storage:
        """Mengembalikan semuat item yg tersimpan di _storage."""
        return cls._storage

    @classmethod
    def _is_data_expired(cls, key: str) -> bool:
        local_timezone: tzinfo = get_localzone()
        now: float = datetime.now(tz=local_timezone).timestamp()
        data = cast(dict[str, object | float], cls._storage.get(key))

        expiration_date = cast(float, data.get("expired"))
        return now >= expiration_date
