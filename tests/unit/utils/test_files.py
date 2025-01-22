# noqa: D100
import shutil
from abc import abstractmethod
from collections.abc import Generator
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from kedung.utils.files import LogPath, SocketPath
from pytest_mock.plugin import MockerFixture


class _BaseTaseFiles:
    def setup_and_teardown(self) -> Generator[None]:
        yield
        junk_dirs = [
            *list(Path("/tmp/").glob("kedung*/")),
            Path("/tmp/kedung/"),
            Path.cwd() / "kedung_test_dir/",
        ]
        for folder in junk_dirs:
            if folder.is_dir():
                shutil.rmtree(folder)

    @pytest.fixture
    def tmp_user_dir(self) -> Generator[str]:
        with TemporaryDirectory(prefix="kedung_test_dir") as tmp:
            yield f"{tmp}/"

    @pytest.fixture
    def tmp_default_dir(self) -> str:
        return "/tmp/kedung/"

    @property
    @abstractmethod
    def file_type(self) -> str: ...

    def test_set_path(
        self,
        mocker: MockerFixture,
        path_obj: LogPath | SocketPath,
        tmp_user_dir: str,
    ) -> None:
        expected_path_file = f"{tmp_user_dir}kedung.{self.file_type}"

        mocker.patch.object(
            path_obj.__class__, "_create_dirs", return_value=tmp_user_dir
        )
        mock_create_file = mocker.patch.object(path_obj.__class__, "_create_file")

        path_obj.set_path(expected_path_file)

        assert path_obj._path == tmp_user_dir
        assert path_obj._path_file == expected_path_file
        mock_create_file.assert_called_once_with(expected_path_file)

    def test_get_path_file(
        self,
        mocker: MockerFixture,
        path_obj: LogPath | SocketPath,
        tmp_user_dir: str,
    ) -> None:
        max_created_files = 2
        max_files_checked = 4
        expected_path_file = f"{tmp_user_dir}kedung.{self.file_type}"

        mock_exists = mocker.patch(
            "pathlib.Path.exists", side_effect=[False, True, False, True]
        )
        mock_touch = mocker.patch("pathlib.Path.touch")
        mocker.patch("pathlib.Path.is_dir", side_effect=[True, True])

        # 2 tes teratas menguji dengan absolute path, 2 sisanya dengan
        # menggunakan absolute dir
        path_obj._create_file(expected_path_file)
        path_obj._create_file(expected_path_file)
        path_obj._create_file(tmp_user_dir)
        path_obj._create_file(tmp_user_dir)

        assert mock_touch.call_count == max_created_files
        assert mock_exists.call_count == max_files_checked
        assert path_obj._path_file == expected_path_file

    def test_get_path_file_wo_any_permissions(
        self,
        path_obj: SocketPath | LogPath,
        mocker: MockerFixture,
    ) -> None:
        exit_msg = f"Tidak punya akses ke `{path_obj._path}`, mengehentikan program..."

        mocker.patch.object(path_obj.__class__, "_has_rw_access", return_value=False)

        with pytest.raises(SystemExit) as se:
            path_obj.path_file  # noqa: B018

        assert str(se.value) == exit_msg

    def test_get_path_file_wo_permission(
        self,
        path_obj: SocketPath | LogPath,
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.object(path_obj.__class__, "_has_rw_access", return_value=True)
        mocker.patch.object(
            path_obj.__class__,
            "_is_path_exists",
            return_value=False,
        )
        mocker.patch("pathlib.Path.mkdir")
        mocker.patch("pathlib.Path.touch")

        result_path = path_obj.path_file

        assert result_path == path_obj._path_file

    def test_create_dir_with_user_path_permission(
        self,
        mocker: MockerFixture,
        path_obj: LogPath | SocketPath,
        tmp_user_dir: str,
        tmp_default_dir: str,
    ) -> None:
        """Menguji baris kode yg ada di dalam blok kode try."""
        mocker.patch("pathlib.Path.exists", side_effect=[True, False])
        mocker.patch.object(path_obj.__class__, "_raise_for_permission_error")
        mock_mkdir = mocker.patch("pathlib.Path.mkdir")

        # test dengan menggunakan direktori yg sudah atau belum ada.
        with_non_existing_user_path: str = path_obj._create_dirs(
            tmp_user_dir, tmp_default_dir
        )
        with_existing_user_path: str = path_obj._create_dirs(
            tmp_user_dir, tmp_default_dir
        )

        assert tmp_user_dir == with_non_existing_user_path
        assert tmp_user_dir == with_existing_user_path
        mock_mkdir.assert_called_once()

    def test_create_dir_wo_user_path_permission(
        self,
        mocker: MockerFixture,
        path_obj: LogPath | SocketPath,
        tmp_user_dir: str,
        tmp_default_dir: str,
    ) -> None:
        mocker.patch("pathlib.Path.exists", side_effect=[True, False])
        mock_mkdir = mocker.patch("pathlib.Path.mkdir")
        mocker.patch.object(
            path_obj.__class__,
            "_has_rw_access",
            return_value=True,
        )
        mocker.patch.object(
            path_obj.__class__,
            "_raise_for_permission_error",
            side_effect=[PermissionError, None],
        )
        result_path: str = path_obj._create_dirs(tmp_user_dir, tmp_default_dir)

        assert result_path == tmp_default_dir
        mock_mkdir.assert_called_once()

    def test_create_dir_wo_any_permission(
        self,
        mocker: MockerFixture,
        path_obj: SocketPath | LogPath,
        tmp_user_dir: str,
        tmp_default_dir: str,
    ) -> None:
        exit_msg = (
            f"Tidak punya akses ke `{tmp_user_dir}` atau "
            f"`{tmp_default_dir}`, mengehentikan program..."
        )

        mocker.patch("pathlib.Path.exists", return_value=False)
        mocker.patch("pathlib.Path.mkdir", side_effect=PermissionError)
        mocker.patch.object(
            path_obj.__class__,
            "_has_rw_access",
            return_value=False,
        )

        with pytest.raises(SystemExit) as se:
            path_obj._create_dirs(tmp_user_dir, tmp_default_dir)

        assert str(se.value) == exit_msg

    def test_create_files_with_supported_exts(
        self,
        mocker: MockerFixture,
        path_obj: LogPath | SocketPath,
        tmp_user_dir: str,
    ) -> None:
        excepted_path = f"{tmp_user_dir}test_file.{self.file_type}"

        mocker.patch("pathlib.Path.exists", side_effect=[False, True])
        mock_touch = mocker.patch("pathlib.Path.touch")

        path_obj._create_file(excepted_path)
        w_non_existing_file = path_obj._path_file
        path_obj._create_file(excepted_path)
        w_existing_file = path_obj._path_file

        assert excepted_path == w_non_existing_file
        assert excepted_path == w_existing_file
        mock_touch.assert_called_once()

    def test_create_files_with_unsupported_exts(
        self,
        mocker: MockerFixture,
        path_obj: LogPath | SocketPath,
        tmp_user_dir: str,
    ) -> None:
        max_created_file = 2
        file_name = f"kedung.{self.file_type}"
        target_path_1 = f"{tmp_user_dir}test_file.txt"
        target_path_2 = tmp_user_dir

        mocker.patch("pathlib.Path.exists", side_effect=[False, True, False, True])
        mocker.patch("pathlib.Path.is_dir", return_value=True)
        mock_touch = mocker.patch("pathlib.Path.touch")

        path_obj._create_file(target_path_1)
        w_non_existing_file_1 = path_obj._path_file
        path_obj._create_file(target_path_1)
        w_existing_file_1 = path_obj._path_file
        path_obj._create_file(target_path_2)
        w_non_existing_file_2 = path_obj._path_file
        path_obj._create_file(target_path_2)
        w_existing_file_2 = path_obj._path_file

        assert w_non_existing_file_1 == f"{target_path_1}/{file_name}"
        assert w_existing_file_1 == f"{target_path_1}/{file_name}"
        assert w_non_existing_file_2 == f"{target_path_2}{file_name}"
        assert w_existing_file_2 == f"{target_path_2}{file_name}"
        assert mock_touch.call_count == max_created_file

    def test_get_absolute_path(
        self, path_obj: LogPath | SocketPath, tmp_user_dir: str
    ) -> None:
        cwd = Path.cwd()
        file_nama = f"test_file.{self.file_type}"
        abs_path = f"{tmp_user_dir}{file_nama}"
        abs_dir = tmp_user_dir
        relative_file = f"foo/{file_nama}"
        ambiguous_file = "test_file"

        w_abs_path = path_obj._get_absolute_path(abs_path)
        w_abs_dir = path_obj._get_absolute_path(abs_dir)
        w_relative_file = path_obj._get_absolute_path(relative_file)
        w_file_name = path_obj._get_absolute_path(file_nama)
        w_ambiguous_file = path_obj._get_absolute_path(ambiguous_file)

        assert w_abs_path == tmp_user_dir[:-1]
        assert w_abs_dir == abs_dir
        assert w_relative_file == f"{cwd}/foo"
        assert w_file_name == str(cwd)
        assert w_ambiguous_file == str(cwd.joinpath(ambiguous_file))

    def test_rw_access(
        self,
        path_obj: LogPath | SocketPath,
        tmp_user_dir: str,
    ) -> None:
        assert isinstance(path_obj._has_rw_access(tmp_user_dir), bool)

    def test_get_path_dir(
        self,
        path_obj: LogPath | SocketPath,
        tmp_user_dir: str,
    ) -> None:
        default_file = f"{tmp_user_dir}/kedung.{self.file_type}"

        result_dir = path_obj._get_path_dir(default_file)

        assert result_dir == tmp_user_dir

    def test_path_existence(
        self,
        path_obj: SocketPath | LogPath,
        tmp_user_dir: str,
    ) -> None:
        assert isinstance(path_obj._is_path_exists(tmp_user_dir), bool)

    def test_raise_permission_error(
        self,
        mocker: MockerFixture,
        path_obj: SocketPath | LogPath,
        tmp_user_dir: str,
    ) -> None:
        mocker.patch("os.access", return_value=False)

        with pytest.raises(PermissionError):
            path_obj._raise_for_permission_error(tmp_user_dir)


class TestSocketPath(_BaseTaseFiles):
    @pytest.fixture
    def path_obj(self) -> SocketPath:
        return SocketPath()

    @property
    def file_type(self) -> str:
        return "sock"


class TestLogPath(_BaseTaseFiles):
    @pytest.fixture
    def path_obj(self) -> LogPath:
        return LogPath()

    @property
    def file_type(self) -> str:
        return "log"
