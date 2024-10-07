import os
from pathlib import Path
from typing import TypeVar

from kedung.utils.userconf import get_log_path

SP = TypeVar("SP", bound="SocketPath")
LP = TypeVar("LP", bound="LogPath")


class _BasePath:
    _path = ""
    _path_file = ""
    _extension = ""

    def set_path(self, location: str) -> None:
        """Mensetel lokasi folder yg akan digunakan untuk socket/log.

        :param socket_location: lokasi file socket.
        :type socket_location: str
        """
        location = location if location.endswith("/") else f"{location}/"
        self.__class__._create_dirs(location, self._path)  # noqa: SLF001
        self.__class__._create_file(location)  # noqa: SLF001

    @property
    def path_file(self) -> str:
        """Mengembalikan lokasi socket/log.

        :return: string lokasi socket yg digunakan oleh kedung
        :rtype: str
        """
        self.__class__._create_dirs(self._path, self._path)  # noqa: SLF001
        self.__class__._create_file(self._path_file)  # noqa: SLF001
        return self._path_file

    @classmethod
    def _create_dirs(cls, user_path: str, default_path: str) -> None:
        user_instance = user_path if isinstance(user_path, Path) else Path(user_path)
        dp_instance = (
            default_path if isinstance(default_path, Path) else Path(default_path)
        )

        try:
            user_instance.exists()
        except PermissionError:
            dp_instance.mkdir(parents=True, exist_ok=True)
            cls._path = str(dp_instance)
            return

        _user_path: Path = (
            user_instance
            if user_instance.is_absolute()
            else Path.cwd() / str(user_instance)
        )

        if not _user_path.exists():
            _user_path.mkdir(parents=True, exist_ok=True)

        if cls._has_rw_access(str(_user_path)):
            cls._path = str(_user_path)
            return

    @staticmethod
    def _has_rw_access(path_dir: str) -> bool:
        dir_read_status = os.access(path_dir, os.R_OK)
        dir_write_status = os.access(path_dir, os.W_OK)
        return all([dir_read_status, dir_write_status])

    @classmethod
    def _create_file(cls, path_file: Path | str) -> None:
        path_instance = path_file if isinstance(path_file, Path) else Path(path_file)
        str_path = str(path_file)

        if str_path.endswith((".sock", ".log")) and not path_instance.exists():
            path_instance.touch()
            cls._path_file = str(path_instance.resolve())

        elif path_instance.is_dir():
            file = "kedung.sock" if cls._extension == "sock" else "kedung.log"
            path_file = path_instance / file
            path_file.touch()
            cls._path_file = str(path_file.resolve())

        else:
            path_file = Path(cls._path_file)
            if not path_file.exists():
                path_file.touch()
            cls._path_file = str(path_file.resolve())


class SocketPath(_BasePath):
    """Membuat path dan socket file.

    **Contoh Penggunaan**:
    .. highlight:: python
    .. code-block:: python
        >>> # menggunakan default path
        >>> socket_path = SocketPath()
        >>> socket_path.path_file
        "/tmp/kedung/kedung.sock"
        >>>
        >>> # menggunakan path yg spesifik.
        >>> path_location = str(Path().cwd() / "configured_path/")
        >>> socket_path = SocketPath()
        >>> socket_path.set_path(path_location)
        >>> socket_path.path_file
        >>> # Output yg seharusnya dihasilkan seperti berikut,
        >>> # /<current_dir>/configured_path/kedung.sock
    """

    _instance = None

    def __new__(cls: type[SP]) -> SP:  # noqa: D102
        if cls._instance is None:
            location = get_log_path()
            cls._extension = "sock"
            cls._instance = super().__new__(cls)
            cls._path = f"{location}/"
            cls._path_file = f"{location}/kedung.sock"
        return cls._instance


class LogPath(_BasePath):
    """Membuat path dan log file.

    **Contoh Penggunaan**:
    .. highlight:: python
    .. code-block:: python
        >>> # menggunakan default path yg sudah disediakan.
        >>> log_path = LogPath()
        "/tmp/kedung/kedung.log"
        >>>
        >>> # menggunakan path yg spesifik.
        >>> path_location = str(Path().cwd() / "configured_path/")
        >>> log_path = SocketPath()
        >>> log_path.set_path(path_location)
        >>> log_path.path_file
        >>> # Output yg seharusnya dihasilkan seperti berikut,
        >>> # /<current_dir>/configured_path/kedung.log
    """

    _instance = None

    def __new__(cls: type[LP]) -> LP:  # noqa: D102
        if cls._instance is None:
            location = get_log_path()
            cls._extension = "log"
            cls._instance = super().__new__(cls)
            cls._path = f"{location}/"
            cls._path_file = f"{location}/kedung.log"
        return cls._instance
