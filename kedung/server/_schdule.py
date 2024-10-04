import asyncio
from collections.abc import MutableMapping
from datetime import datetime
from typing import cast

import structlog

from kedung.utils.dateandtime import get_localzone

from ._storage import DataHolder

CLEANER_DURATION: float = 5.0
logger = structlog.get_logger()


async def schedule_task() -> None:
    event_loop = asyncio.get_event_loop()
    await logger.ainfo("Memulai schedule ...")

    while event_loop.is_running():
        await asyncio.sleep(CLEANER_DURATION)

        await _remove_expired_items()


async def _remove_expired_items() -> None:
    storage = DataHolder()

    all_items = storage.all_items()
    if not all_items:
        return

    try:
        for key, value in all_items.items():
            if _is_expired(value):
                storage.clear(key)
    except RuntimeError as RE:
        msg = RE.args[0]
        if "dictionary changed" in msg:
            await logger.adebug("Data dibersihkan dari penyimpanan!!")


def _is_expired(value: MutableMapping[str, float | object]) -> bool:
    local_timezone = get_localzone()
    now: float = datetime.now(tz=local_timezone).timestamp()
    expired: float = cast(float, value.get("expired"))

    return now > expired
