import pytest
from kedung.server._commands import Command
from kedung.utils.custom_types import Data, DataValue

DummyData = dict[str, str | dict[str, str]]


@pytest.fixture
def command() -> Command:
    return Command()


def inject_injected_data(data: Data) -> Data:
    data["data"]["injected_data"] = "dummy_injected_1"  # type: ignore[index]
    return data


class TestSingleOperation:
    @pytest.fixture
    def dummy_data(self) -> DataValue:
        return {
            "key_1": "value_1",
            "injected_data": "dummy_injected_1",
        }

    @pytest.fixture
    def dummy_data_get(self, dummy_data: DataValue) -> Data:
        return {
            "command": "GET",
            "data": dummy_data,
        }

    @pytest.fixture()
    def dummy_data_set(self, dummy_data: DataValue) -> Data:
        return {
            "command": "SET",
            "data": dummy_data,
        }

    def test_set_item(
        self,
        command: Command,
        dummy_data_set: Data,
    ) -> None:
        result = command.set_(dummy_data_set)

        assert result.values()

    def test_existence_item_with_existing_key(
        self,
        command: Command,
        dummy_data_get: Data,
        dummy_data_set: Data,
    ) -> None:
        command.set_(dummy_data_set)

        result = command.exist(inject_injected_data(dummy_data_get))

        assert result.get("key_1")

    def test_get_item_with_existing_key(
        self,
        command: Command,
        dummy_data_get: Data,
        dummy_data_set: Data,
    ) -> None:
        command.set_(dummy_data_set)
        result = command.get(inject_injected_data(dummy_data_get))

        assert result.get("key_1")

    def test_delete_item_with_existing_key(
        self,
        command: Command,
        dummy_data_get: Data,
        dummy_data_set: Data,
    ) -> None:
        command.set_(dummy_data_set)
        result = command.del_(inject_injected_data(dummy_data_get))

        assert result.get("key_1")

    def test_get_non_existent_item(
        self,
        command: Command,
        dummy_data_get: Data,
    ) -> None:
        result = command.get(dummy_data_get)

        assert not result.get("key_1")

    def test_delete_non_existent_item(
        self,
        command: Command,
        dummy_data_get: Data,
    ) -> None:
        result = command.del_(dummy_data_get)

        assert not result.get("key_1")

    def test_existence_item_with_non_existing_key(
        self,
        command: Command,
        dummy_data_get: Data,
    ) -> None:
        result = command.exist(dummy_data_get)

        assert not result.get("key_1")


class TestBulkOperations:
    @pytest.fixture
    def dummy_data(self) -> DataValue:
        return {
            "key_1": "value_1",
            "key_2": "value_2",
            "injected_data": "dummy_injected_1",
        }

    @pytest.fixture
    def dummy_data_bget(self, dummy_data: DataValue) -> Data:
        return {
            "command": "BGET",
            "data": dummy_data,
        }

    @pytest.fixture
    def dummy_data_bset(self, dummy_data: DataValue) -> Data:
        return {
            "command": "BSET",
            "data": dummy_data,
        }

    def test_bset_items(
        self,
        dummy_data_bset: Data,
        command: Command,
    ) -> None:
        result = command.bulk_set(dummy_data_bset)

        assert result.get("key_1") is True
        assert result.get("key_2") is True

    def test_existence_items_with_existing_keys(
        self,
        dummy_data_bget: Data,
        dummy_data_bset: Data,
        command: Command,
    ) -> None:
        command.bulk_set(dummy_data_bset)
        result = command.bulk_exists(inject_injected_data(dummy_data_bget))

        assert result.get("key_1")
        assert result.get("key_2")

    def test_bget_items_with_existing_keys(
        self,
        command: Command,
        dummy_data_bget: Data,
        dummy_data_bset: Data,
    ) -> None:
        command.bulk_set(dummy_data_bset)
        result = command.bulk_get(inject_injected_data(dummy_data_bget))

        assert result.get("key_1") == "value_1"
        assert result.get("key_2") == "value_2"

    def test_bdel_items_with_existing_keys(
        self,
        command: Command,
        dummy_data_bget: Data,
        dummy_data_bset: Data,
    ) -> None:
        command.bulk_set(dummy_data_bset)
        del_result = command.bulk_del(inject_injected_data(dummy_data_bget))

        assert del_result.get("key_1")
        assert del_result.get("key_2")

    def test_bget_non_existent_item(
        self,
        command: Command,
        dummy_data_bget: Data,
    ) -> None:
        result = command.bulk_get(dummy_data_bget)

        assert not result.get("key_1")
        assert not result.get("key_2")

    def test_delete_non_existent_item(
        self,
        command: Command,
        dummy_data_bget: Data,
    ) -> None:
        result = command.bulk_del(dummy_data_bget)

        assert not result.get("key_1")
        assert not result.get("key_2")

    def test_existence_items_with_non_existing_keys(
        self,
        command: Command,
        dummy_data_bget: Data,
    ) -> None:
        result = command.bulk_exists(dummy_data_bget)

        assert not result.get("key_1")
        assert not result.get("key_2")

def test_flush(command: Command) -> None:
    dummy: Data = {
        "command": "SET",
        "data": {
            "key_1": "value_1",
            "key_2": "value_2",
            "key_3": "value_3",
            "injected_data": "dummy_injected_1",
        },
    }
    command.bulk_set(dummy)

    result: Data = command.flush_(inject_injected_data(dummy))
    assert all(result.values())
