from collections.abc import Iterable, Mapping, MutableMapping

PrimitiveData = str | int | float | bool | None
Key = str

# Storage
UnixTime = float
Storage = MutableMapping[Key, MutableMapping[Key, UnixTime | object]]

# Serdes
StrCommand = str
UserData = Mapping[str | None, object | None]
Deserializer = Mapping[Key, StrCommand | UserData]
Serializer = bytes

# data
DataKey = str | None
DataValue = PrimitiveData | Iterable[object] | MutableMapping[object, object]
Data = MutableMapping[DataKey, DataValue]
