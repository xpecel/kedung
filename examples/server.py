import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path.cwd()))

from kedung import Server

server = Server()

try:
    import uvloop
except ModuleNotFoundError:
    asyncio.run(server.run())
else:
    with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
        runner.run(server.run())
