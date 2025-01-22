import os
import sys
from contextlib import suppress
from pathlib import Path
from typing import TypeVar

from kedung.utils.userconf import get_log_path, get_sock_path

SP = TypeVar("SP", bound="SocketPath")
LP = TypeVar("LP", bound="LogPath")


class _BasePath:
    _path: str = ""
    _path_file: str = ""
    _extension: str = ""
    _supported_extensions: tuple[str, str] = (".sock", ".log")

    @classmethod
    def set_path(cls, location: str) -> None:
        """Mensetel lokasi folder yg akan digunakan untuk socket/log.

        Jika `location` tidak memiliki suffix `.log` atau `.sock`,
        maka `location` akan dianggap sebagai sebauh folder.

        :param location: lokasi file socket.
        :type location: str
        """
        if not location.endswith((".sock", ".log", "/")):
            location = f"{location}/"

        working_dir: str = cls._create_dirs(user_path=location, default_path=cls._path)
        path_file: str = (
            f"{working_dir}/{location.split('/')[-1]}"
            if location.endswith(cls._supported_extensions)
            else working_dir
        )

        cls._path = f"{working_dir}/" if not working_dir.endswith("/") else working_dir
        cls._path_file = cls._remove_slash_duplicate(path_file)

        cls._create_file(cls._path_file)

    @property
    def path_file(self) -> str:
        """Mengembalikan lokasi socket/log.

        Jika akses ke default path, yakni `/tmp/`, tidak dimiliki, maka
        program diberhentikan.

        :return: string lokasi socket yg digunakan oleh kedung
        :rtype: str
        """
        if not self._has_rw_access(self._path):
            sys.exit(f"Tidak punya akses ke `{self._path}`, mengehentikan program...")
        if not self._is_path_exists(self._path, self._path_file):
            self.__class__._create_dirs(self._path, self._path)  # noqa: SLF001
            self.__class__._create_file(self._path_file)  # noqa: SLF001
        return self._path_file

    @classmethod
    def _create_dirs(cls, user_path: str, default_path: str) -> str:
        """Membuat direktori yang diperlukan untuk operasional program.

        `user_path` lebih diprioritaskan alih-alih `default_path` untuk
        oprasional program. Jika akses ke kedua lokasi tsb tidak ada,
        maka program diberhentikan.

        :param user_path: lokasi yg diberikan oleh user untuk
            kegiatan operasional program.
        :type user_path: str
        :param default_path: lokasi alternatif yg akan digunakan jika
            akses ke `user_path` tidak tersedia.
        :type default_path: str
        :return: direktori yg bisa digunakan untuk operasional program
        :rtype: str
        """
        user_path = cls._get_path_dir(user_path)
        default_path = cls._get_path_dir(default_path)

        user_abs_path: str = cls._get_absolute_path(user_path)
        user_path_obj = Path(user_abs_path)
        normalized_path: str

        try:
            if not user_path_obj.exists():
                user_path_obj.mkdir(parents=True, exist_ok=True)
            else:
                cls._raise_for_permission_error(user_abs_path)
        except PermissionError:
            default_instance = Path(default_path)
            with suppress(PermissionError):
                if not default_instance.exists():
                    default_instance.mkdir(parents=True, exist_ok=True)

            if not cls._has_rw_access(default_path):
                msg = (
                    f"Tidak punya akses ke `{user_abs_path}` atau "
                    f"`{default_path}`, mengehentikan program..."
                )
                sys.exit(msg)

            normalized_path = default_path

        else:
            normalized_path = user_abs_path

        return normalized_path

    @classmethod
    def _create_file(cls, user_file: str) -> None:
        """Membuat file, sock atau log, untuk operasional program.

        :param user_file: lokasi dari file yg akan dibuat.
        :type user_file: str
        """
        end_with_supported_exts = user_file.endswith(cls._supported_extensions)
        user_path_obj: Path = Path(user_file)

        if end_with_supported_exts:
            # absolute path. contoh, `/tmp/foo/t.sock`
            if not user_path_obj.exists():
                user_path_obj.touch()
            cls._path_file = user_file

        elif user_path_obj.is_dir() and not end_with_supported_exts:
            # absolute dir. contoh, `/tmp/foo/`
            path_file = user_path_obj.joinpath(f"kedung.{cls._extension}")
            if not user_path_obj.exists():
                path_file.touch()
            cls._path_file = str(path_file)

    @staticmethod
    def _get_absolute_path(user_path: str) -> str:
        """Menambahakan `cwd` jika `user_path` bukanlah absolute path."""
        minimum_path_component = 2
        extensions = _BasePath._supported_extensions

        user_path_obj = Path(user_path)
        cwd = Path.cwd()
        split_user_path: list[str] = user_path.split("/")
        user_path_is_absolute: bool = user_path_obj.is_absolute()
        end_with_supported_exts = user_path.endswith(extensions)

        normalized_path: str

        if user_path_is_absolute:
            if end_with_supported_exts:
                # user input berupa absolute path. contoh, `/tmp/foo/t.sock`.
                normalized_path = str(user_path_obj.parent)
            else:
                # user input berupa absolute dir. contoh, `/tmp/foo/`.
                normalized_path = user_path

        elif not user_path_is_absolute:
            if end_with_supported_exts:
                if len(split_user_path) >= minimum_path_component:
                    # user input berupa child dir dan file.
                    # contoh, `foo/foo/t.sock`
                    normalized_path = str(cwd.joinpath(user_path_obj.parent))
                else:
                    # user input hanya berupa file. contoh, `t.sock`
                    normalized_path = str(cwd)
            else:
                # user input kurang jelas. contoh, `t1`.
                # `t1` bisa diasumsikan sebagai file atau folder.
                # sebaagai tanggapan, pendekatan yg diambil dengan
                # mengasumsikan `t1` adalah  child dir.
                normalized_path = str(cwd.joinpath(user_path_obj))

        return normalized_path

    @staticmethod
    def _has_rw_access(path_dir: str) -> bool:
        """Memerika akses baca tulis ke lokasi yg diberikan."""
        return os.access(path_dir, os.R_OK) and os.access(path_dir, os.W_OK)

    @staticmethod
    def _get_path_dir(path: str) -> str:
        """Mengambil path direktori dari sebuah path file."""
        extensions = _BasePath._supported_extensions
        result: str = path

        if path.endswith(extensions):
            result = f"{Path(path).parent}/"

        return result

    @staticmethod
    def _is_path_exists(*paths: str) -> bool:
        """Memerika keberadaan semua `*paths` yg diberikan."""
        return all(Path(path).exists() for path in paths)

    @staticmethod
    def _raise_for_permission_error(path: str) -> None:
        """Menaikan `PermissionError` jika akses ke `path` tidak ada."""
        if not _BasePath._has_rw_access(path):
            raise PermissionError

    @staticmethod
    def _remove_slash_duplicate(path: str) -> str:
        normalized = "/".join(filter(None, path.split("/")))
        return normalized if not path.startswith("/") else f"/{normalized}"


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
            location = get_sock_path()
            cls._extension = "sock"
            cls._instance = super().__new__(cls)

            if location.endswith(".sock"):
                cls._path = cls._get_path_dir(location)
                cls._path_file = location
            else:
                # default nama socket file yg akan digunakan jika
                # end-user hanya menyediakan lokasi socket saja.
                cls._path = location
                cls._path_file = (
                    f"{location}kedung.sock"
                    if location.endswith("/")
                    else f"{location}/kedung.sock"
                )

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

            if location.startswith("/") and location.endswith(".log"):
                split_path = location.split("/")
                cls._path = "/".join(split_path[:-1]) + "/"
                cls._path_file = location
            else:
                # default nama log file yg akan digunakan jika end-user
                # hanya menyediakan lokasi log saja.
                cls._path = location
                cls._path_file = (
                    f"{location}kedung.log"
                    if location.endswith("/")
                    else f"{location}/kedung.log"
                )

        return cls._instance
