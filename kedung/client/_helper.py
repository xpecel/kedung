from hashlib import sha256
from uuid import uuid4

from kedung.utils.custom_types import Data

__all__ = ("create_unique_key", "inject_data")


def create_unique_key(command: str) -> str:
    """Membuat kunci unik berdasarkan UUID dan hash SHA-256.

    Contoh penggunaan:
    .. highlight:: python
    .. code-block:: python
        >>> create_unique_key("GET")
        GET_79885b2a

    :param command: command yg kompatibel dengan `HoarderClient.send`.
    :type command: str
    :return: Kunci unik yang terdiri dari `command` dan 8 karakter unik.
    :rtype: str
    """
    unique_id = uuid4()
    key = f"{unique_id}"
    unique_key = sha256(key.encode()).hexdigest()
    return f"{command}_{unique_key[:8]}"


def inject_data(target: Data, injected_data: str) -> Data:
    """Menambahkan `injected_data` ke dalam `target`.

    Contoh penggunaan:
    .. highlight:: python
    .. code-block:: python
        >>> my_data = {"key_1": "data_1"}
        >>> inject_data(my_data, "SET_79885b2a")
        {"key_1": "data_1", "injected_data": "SET_79885b2a"}

    :param target: data yg akan dikirim ke server.
    :type target: Data
    :param injected_data: data yg akan ditambhkan ke dalam `target`.
    :type data: str
    :return: dictionary dengan tambahan key `injected_data` di dalamnya.
    :rtype: Data
    """
    target["injected_data"] = injected_data
    return target
