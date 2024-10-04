from kedung.utils.userconf import get_preallocate_space

PREALLOCATE_SPACE: int = get_preallocate_space()


def allocate_data_length(data: str) -> bytes:
    """Mengalokasikan panjang data ke dalam JSON dan mengembalikannya sebagai bytes.

    :param data: Data JSON yang akan dikonversi menjadi bytes dengan
        panjang yang ditentukan.
    :type data: str
    :return: Data JSON yang sudah dilengkapi dengan panjangnya dan dikonversi
        menjadi bytes.
    :rtype: bytes

    **Contoh Penggunaan**:
    .. highlight:: python
    .. code-block:: python
        >>> data = {"command": "GET", "data": {"key_1": "value_1"}}
        >>> allocate_data_length(json.dumps(data))
        b'00000048{"command": "GET", "data": {"key_1": "value_1"}}'
    """
    length_data = len(data)
    max_length_digits = PREALLOCATE_SPACE
    result = str(length_data).zfill(max_length_digits)
    return f"{result}{data}".encode()
