from kedung.utils.exceptions import PrefixError
from kedung.utils.userconf import get_preallocate_space

PREALLOCATE_SPACE: int = get_preallocate_space()


def allocate_data_length(data: bytes) -> bytes:
    """Menambahkan panjang data pada awal payload dalam bentuk ASCII.

    Panjang data diubah menjadi string angka dan diisi dengan ``zfill`` agar
    sesuai ``PREALLOCATE_SPACE``. Nilai tersebut ditempatkan pada awal
    paket sebelum payload asli.

    :param data: Payload dalam bentuk bytes.
    :type data: bytes
    :return: Paket dengan panjang data di bagian awal.
    :rtype: bytes
    :raises TypeError: Jika argumen bukan bytes.
    :raises PrefixError: Jika panjang data melebihi kapasitas alokasi.

    **Contoh Penggunaan**:
    .. highlight:: python
    .. code-block:: python
        >>> data = {"command": "GET", "data": {"key_1": "value_1"}}
        >>> allocate_data_length(orjson.dumps(data))
        b'00000048{"command": "GET", "data": {"key_1": "value_1"}}'
    """
    if not isinstance(data, bytes):
        error_message = "allocate_data_length hanya menerima bytes"
        raise TypeError(error_message)

    length_data = len(data)

    max_value = 10**PREALLOCATE_SPACE - 1
    if length_data > max_value:
        error_mesage = (
            f"data tidak boleh lebih besar, ({length_data} bytes), dar"
            f" PREALLOCATE_SPACE={PREALLOCATE_SPACE}"
        )
        raise PrefixError(error_mesage)


    allocated_space = str(length_data).zfill(PREALLOCATE_SPACE).encode("ascii")

    packet = bytearray(PREALLOCATE_SPACE + length_data)
    packet[:PREALLOCATE_SPACE] = allocated_space
    packet[PREALLOCATE_SPACE:] = data

    return bytes(packet)
