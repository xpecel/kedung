from collections.abc import Callable

from kedung.utils.custom_types import Data

CommandCall = Callable[..., Data]
