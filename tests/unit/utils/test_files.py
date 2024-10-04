# noqa: D100
import shutil
from collections.abc import Generator
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from kedung.utils.files import LogPath, SocketPath


class _BaseTaseFiles:
    @pytest.fixture(scope="session", autouse=True)
    def setup_and_teardown(self) -> Generator[None]:
        yield

        for folder in Path("/tmp/").glob("kedung*/"):
            if folder.is_dir():
                shutil.rmtree(folder)

    @pytest.fixture
    def tmp_absolute_dir(self) -> Generator[str]:
        with TemporaryDirectory(prefix="kedung_test_dir") as tmp:
            yield tmp
            shutil.rmtree(str(tmp))

    @pytest.fixture
    def tmp_relative_dir(self) -> Generator[str]:
        relative_dir = "kedung_test_dir"
        yield relative_dir
        targfet_dir = Path.cwd() / relative_dir
        shutil.rmtree(str(targfet_dir))

    def test_create_dir_wo_rw_permission(
        self,
        path_obj: LogPath | SocketPath,
        tmp_relative_dir: str,
        tmp_absolute_dir: Generator[str],
    ) -> None:
        user_dir = Path.cwd() / tmp_relative_dir
        user_dir.mkdir(parents=True, exist_ok=True)
        user_dir.chmod(0o000)

        path_obj._create_dirs(
            str(user_dir / "child_dir/"),
            str(tmp_absolute_dir),
        )
        user_dir.chmod(0o700)

        assert str(tmp_absolute_dir) in path_obj._path

    def test_create_dir_with_configured_path(
        self,
        path_obj: LogPath | SocketPath,
        tmp_absolute_dir: Generator[str],
        tmp_relative_dir: str,
    ) -> None:
        file_type = "kedung.sock" if isinstance(path_obj, SocketPath) else "kedung.log"
        for user_dir in (tmp_relative_dir, str(tmp_absolute_dir)):
            path_obj.set_path(f"{user_dir}/")
            result = Path(user_dir).resolve()
            assert path_obj.path_file == f"{result!s}/{file_type}"

    def test_create_dir_with_default_path(self, path_obj: LogPath | SocketPath) -> None:
        _path_obj = Path(path_obj.path_file)

        assert _path_obj.exists()
        assert _path_obj.is_file()


class TestSocketPath(_BaseTaseFiles):
    @pytest.fixture
    def path_obj(self) -> SocketPath:
        return SocketPath()

    def file_type(self) -> str:
        return "kedung.sock"


class TestLogPath(_BaseTaseFiles):
    @pytest.fixture
    def path_obj(self) -> LogPath:
        return LogPath()

    def file_type(self) -> str:
        return "kedung.log"
