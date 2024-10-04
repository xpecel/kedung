import asyncio
import sys
from pathlib import Path
from time import perf_counter
from typing import cast

import structlog

sys.path.append(str(Path.cwd()))

from kedung.client import Client
from kedung.utils.custom_types import Data
from kedung.utils.logging import default_strouctlog_config

client = Client()
REQUESTS = 1000
DATA_SIZE = 1024
CYCLES = 4
logger = structlog.get_logger()


async def main() -> None:  # noqa: D103
    time_start = perf_counter()

    default_strouctlog_config()
    await client.create_connection()

    times = []

    for cycle in range(CYCLES):
        cycle_start = perf_counter()
        tasks = []
        for number in range(REQUESTS):
            single_op = {
                "SET": {f"key_{number}": "x" * DATA_SIZE},
                "GET": {f"key_{number}": None},
                "EXIST": {f"key_{number}": None},
                "DEL": {f"key_{number}": None},
            }
            multi_op = {
                "BSET": {
                    f"key_{number}_1": "x" * DATA_SIZE,
                    f"key_{number}_2": "x" * DATA_SIZE,
                },
                "BGET": {f"key_{number}_1": None, f"key_{number}_2": None},
                "BEXISTS": {f"key_{number}_1": None, f"key_{number}_2": None},
                "BDEL": {f"key_{number}_1": None, f"key_{number}_2": None},
            }
            for key, value in {**single_op, **multi_op}.items():
                tasks.append(
                    client.send(
                        key, cast(Data, value),
                    ),
                )

        tasks.append(client.send("FLUSH", {}))

        await asyncio.gather(*tasks)
        cycle_end = perf_counter() - cycle_start
        times.append(cycle_end)

        await logger.ainfo(
            f"Siklus ke-{cycle + 1} selesai dalam {cycle_end:.3f} detik",
        )

    await client.send("FLUSH")
    execution_time = perf_counter() - time_start

    await logger.ainfo(f"Total siklus: {CYCLES}")
    await logger.ainfo(f"Total request persiklus: {REQUESTS * 8}")
    await logger.ainfo(f"Ukuran data terikirim per-request: {DATA_SIZE}")
    await logger.ainfo(
        f"Rata-rata waktu eksekusi siklus: {sum(times) / CYCLES:.3f} detik",
    )
    await logger.ainfo(f"Total waktu eksekusi: {execution_time:.3f} detik")
    await logger.ainfo(
        f"Throughput: {int(REQUESTS / execution_time)} request/detik",
    )


try:
    import uvloop
except ModuleNotFoundError:
    asyncio.run(main())
else:
    with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
        runner.run(main())
