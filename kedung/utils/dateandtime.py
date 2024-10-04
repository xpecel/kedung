import time
from datetime import timedelta, timezone


def get_localzone() -> timezone:
    """Mengembalikan objek timezone yang mewakili zona waktu sistem.

    :return: Objek timezone yang mewakili zona waktu lokal saat ini.
    :rtype: timezone
    """
    local_tz_name = time.tzname[time.localtime().tm_isdst]
    offset = -time.timezone if time.localtime().tm_isdst == 0 else -time.altzone
    return timezone(timedelta(seconds=offset), name=local_tz_name)
