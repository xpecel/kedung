# Kedung
Implementasi sederhana dari in-memory database dengan orientasi key-value.

## Persyaratan
- Linux
- Python 3.11+
- Git

## Instalasi
```bash
# dengan asumsi sudah menyiapkan virtual environment
pip install git+https://github.com/xpecel/kedung
```

## Contoh penggunaan
```python
# server.py
import asyncio  # noqa: D100
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
```
```python
# client.py
import asyncio

from kedung import Client


async def main() -> None:
    client = Client()

    await client.create_connection()

    data = {"key_1": "value_1"}
    await client.send("SET", data)
    await client.send("GET", {"key_1": None})


try:
    import uvloop
except ModuleNotFoundError:
    asyncio.run(main())
else:
    with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
        runner.run(main())
```

## Konfigurasi
File konfigurasi bisa ditaruh di bawah project directory dengan nama file sebagai `config.toml`.  
Berikut adalah default konfigurasi yg digunakan:

```toml
[kedung.runtime]
# durasi data akan disimpan sebelum dibersihkan.
# default-nya adalah 10 menit.
cache_duration = 10
# jumlah karakter yg dapat diproses dalam satu kali request.
# default-nya hingga 9 juta karakter.
preallocate_space = 7

[kedung.location]
# lokasi folder untuk file socket dan log.
socket = "/tmp/kedung/"
log = "/tmp/kedung/"
```

## Lisensi
GPLv3+
