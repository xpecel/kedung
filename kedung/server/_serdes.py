import json

from kedung.utils.custom_types import Data


def deserializer(raw_data: str | bytes) -> Data:
    data = raw_data if isinstance(raw_data, str) else raw_data.decode()
    result: Data = json.loads(data)
    return result


def serilizer(data: Data) -> str:
    return json.dumps(data)
