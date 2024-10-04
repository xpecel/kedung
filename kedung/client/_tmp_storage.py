from typing import ClassVar

from kedung.utils.custom_types import Data


class TmpStorage:
    """Menampung sementara data yg diterima dari server."""

    _bucket: ClassVar[dict[str, Data]] = {}

    @classmethod
    def add_data(cls, unique_key: str, value: Data) -> None:
        """Menyimpan sementara data yg berasal dari server.

        :param key: Key unik yg ada di dalam data yg datangnya dari server.
        :type key: str
        :param value: Data yg dikembalikan oleh server.
        :type value: object
        """
        cls._bucket[unique_key] = value

    @classmethod
    def get_data(cls, unique_key: str) -> Data | None:
        """Mengembalikan semua data sementara yg disimpan.

        :return: Dictionary berisi key unik dengan value berupa response
            data yg berasal dari server.
        :rtype: dict[str, object]
        """
        result: Data | None = None

        if unique_key in cls._bucket:
            result = cls._bucket.pop(unique_key)

        return result
