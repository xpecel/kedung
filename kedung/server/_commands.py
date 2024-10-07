from typing import cast

from kedung.utils.custom_types import Data, DataValue

from ._storage import DataHolder
from ._types import CommandCall


class Command:
    """Utilitas untuk berinteraksi dengan kelas `DataHolder`."""

    def __init__(self) -> None:
        self._storage = DataHolder()

    def get_command(self, command: str) -> None | CommandCall:
        list_command: dict[str, CommandCall] = {
            "GET": self.get,
            "SET": self.set_,
            "DEL": self.del_,
            "EXIST": self.exist,
            "BGET": self.bulk_get,
            "BSET": self.bulk_set,
            "BDEL": self.bulk_del,
            "BEXISTS": self.bulk_exists,
            "FLUSH": self.flush_,
        }

        return list_command.get(command)

    def _split_data(self, data: Data) -> tuple[str, DataValue, str]:
        actual_data = cast(dict[str, DataValue], data.get("data"))

        # bagian penting dari sisi client.
        injected_data = cast(str, actual_data.pop("injected_data"))
        # nilai dari variabel key nantinya digunakan sebagai id
        # untuk membedakan data yg disimpan di `DataHolder`.
        key: str = next(iter(actual_data.keys()))
        # Data sebenarnya yg akan disimpan
        value: DataValue = next(iter(actual_data.values()))

        return (key, value, injected_data)

    def _bulk_split_data(
        self,
        data: Data,
    ) -> tuple[dict[str, DataValue], str]:
        actual_data = cast(dict[str, DataValue], data.get("data"))
        injected_data = cast(str, actual_data.pop("injected_data"))

        return (actual_data, injected_data)

    def get(self, data: Data) -> Data:
        key, _, injected_data = self._split_data(data)
        operation_result: dict[str, object] = self._storage.get(key)

        result = {**operation_result, "injected_data": injected_data}
        return cast(Data, result)

    def set_(self, data: Data) -> Data:
        key, value, injected_data = self._split_data(data)
        operation_result: dict[str, bool] = self._storage.set_(key, value)

        result = {**operation_result, "injected_data": injected_data}
        return cast(Data, result)

    def del_(self, data: Data) -> Data:
        key, _, injected_data = self._split_data(data)
        operation_result: dict[str, bool] = {key: self._storage.clear(key)}

        result = {**operation_result, "injected_data": injected_data}
        return cast(Data, result)

    def exist(self, data: Data) -> Data:
        key, _, injected_data = self._split_data(data)

        status = self._storage.get(key)
        operation_result: dict[str, bool] = {key: bool(status.get(key))}

        result = {**operation_result, "injected_data": injected_data}
        return cast(Data, result)

    def bulk_get(self, data: Data) -> Data:
        actual_data, injected_data = self._bulk_split_data(data)

        operation_result: dict[str, object] = {}
        for key in actual_data:
            chunk = self._storage.get(key)
            operation_result[key] = chunk.pop(key)

        result = {**operation_result, "injected_data": injected_data}
        return cast(Data, result)

    def bulk_set(self, data: Data) -> Data:
        actual_data, injected_data = self._bulk_split_data(data)

        operation_result: dict[str, bool] = {}
        for key, value in actual_data.items():
            chunk = self._storage.set_(key, value)
            operation_result[key] = chunk.pop(key)

        result = {**operation_result, "injected_data": injected_data}
        return cast(Data, result)

    def bulk_del(self, data: Data) -> Data:
        actual_data, injected_data = self._bulk_split_data(data)

        operation_result: dict[str, bool] = {}
        for key in actual_data:
            operation_result[key] = self._storage.clear(key)

        result = {**operation_result, "injected_data": injected_data}
        return cast(Data, result)

    def bulk_exists(self, data: Data) -> Data:
        actual_data, injected_data = self._bulk_split_data(data)

        operation_result: dict[str, bool] = {}
        for key in actual_data:
            chunk = self._storage.get(key)
            operation_result[key] = bool(chunk.get(key))

        result = {**operation_result, "injected_data": injected_data}
        return cast(Data, result)

    def flush_(self, data: Data) -> Data:
        actual_data = cast(dict[str, DataValue], data.get("data"))
        injected_data = cast(str, actual_data.pop("injected_data"))
        operation_result: dict[str, bool] = {"flush": self._storage.clear_all()}

        result = {**operation_result, "injected_data": injected_data}
        return cast(Data, result)
