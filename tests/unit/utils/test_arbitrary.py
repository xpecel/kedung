"""Mengkover test yg belum atau tidak terkover di modul lain."""

from datetime import timezone

import pytest
from kedung.utils.dateandtime import get_localzone
from kedung.utils.exceptions import (
    CommandError,
    MissingComponentError,
    PrefixError,
)


def test_timezone() -> None:
    assert isinstance(get_localzone(), timezone)


def test_prefix_error() -> None:
    msg = "Kesalahan prefix"
    with pytest.raises(PrefixError) as exc_info:
        raise PrefixError(msg)

    assert str(exc_info.value) == "Kesalahan prefix"


def test_command_error() -> None:
    msg = "Kesalahan command"
    with pytest.raises(CommandError) as exc_info:
        raise CommandError(msg)

    assert str(exc_info.value) == "Kesalahan command"


def test_missing_component_error() -> None:
    msg = "Atribut yang dibutuhkan tidak ditemukan"
    with pytest.raises(MissingComponentError) as exc_info:
        raise MissingComponentError(msg)

    assert str(exc_info.value) == "Atribut yang dibutuhkan tidak ditemukan"
