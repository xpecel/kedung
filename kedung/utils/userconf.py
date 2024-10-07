import tomllib
from functools import lru_cache
from pathlib import Path
from typing import cast

_UC = dict[str, dict[str, str | int]] | None


@lru_cache(8)
def _user_conf() -> _UC:
    """Menyediakan konfigurasi yg diperlukan agar app bisa berfungsi."""
    r_file: dict[str, _UC]

    try:
        with Path("config.toml").open("r+b") as file:
            r_file = tomllib.load(file)
    except FileNotFoundError:
        default_path = "/tmp/kedung/"  # noqa: S108
        r_file = {
            "kedung": {
                "location": {
                    "socket": default_path,
                    "log": default_path,
                },
                "runtime": {
                    "logging": "INFO",
                    "cache_duration": 10,
                    "preallocate_space": 7,
                },
            },
        }

    return r_file.get("kedung")


def get_sock_path() -> str:
    """Menyediakan lokasi untuk socket."""
    read_file = _user_conf()
    default_path = "/tmp/kedung/"  # noqa: S108

    if not read_file:
        return default_path

    socket: str | dict[str, str | int] = read_file.get("location", default_path)
    return (
        socket
        if isinstance(socket, str)
        else cast(str, socket.get("socket", default_path))
    )


def get_log_path() -> str:
    """Menyediakan lokasi untuk log."""
    read_file = _user_conf()
    default_path = "/tmp/kedung/"  # noqa: S108

    if not read_file:
        return default_path

    socket: str | dict[str, str | int] = read_file.get("location", default_path)
    return (
        socket
        if isinstance(socket, str)
        else cast(str, socket.get("log", default_path))
    )


def get_preallocate_space() -> int:
    """Menyediakan panjang karakter yg dialokasikan untuk prefix."""
    read_file = _user_conf()
    default_space = 7

    if not read_file:
        return default_space

    runtime: int | dict[str, int | str] = read_file.get("runtime", default_space)
    return (
        runtime
        if isinstance(runtime, int)
        else cast(int, runtime.get("preallocate_space", default_space))
    )


def get_loging_level() -> int:
    """Menyediakan level untuk logging."""
    read_file = _user_conf()
    logging_levels = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50,
    }
    default_status = "INFO"

    if not read_file:
        return cast(int, logging_levels.get(default_status))

    runtime: str | dict[str, int | str] = read_file.get("runtime", default_status)
    level: str = (
        runtime
        if isinstance(runtime, str)
        else cast(str, runtime.get("logging", default_status))
    )

    return logging_levels.get(level.upper(), 20)


def get_cache_duration() -> int:
    """Menyediakan berapa panjang karakter yg dialokasikan untuk prefix."""
    read_file = _user_conf()
    default_space = 10

    if not read_file:
        return default_space

    duration: int | dict[str, int | str] = read_file.get("runtime", default_space)
    return (
        duration
        if isinstance(duration, int)
        else cast(int, duration.get("cache_duration", default_space))
    )
