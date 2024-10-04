class PrefixError(Exception):  # noqa: D100
    """Dinaikan ketika terdapat kesalahan prefix."""


class CommandError(Exception):
    """Dinaikan ketika terdapat kesalahan command."""


class MissingComponentError(Exception):
    """Dinaikan ketika atribute yg dibutuhkan suatu method tidak ditemukan."""
