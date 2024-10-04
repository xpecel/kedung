import sys

import structlog

from kedung.utils.userconf import get_loging_level

LOG_LEVEL: int = get_loging_level()


_is_log_already_configured = False


def default_strouctlog_config() -> None:
    """Konfigurasi default untuk strucklog."""
    if _is_log_already_configured:
        return

    if sys.stderr.isatty():
        processors = [
            structlog.processors.TimeStamper(
                fmt="[%Y/%b/%d - %H:%M:%S]",
                utc=False,
            ),
            structlog.processors.add_log_level,
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),
        ]
    else:
        processors = [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    log_level = LOG_LEVEL
    structlog.configure(
        cache_logger_on_first_use=True,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        processors=processors,  # type: ignore[arg-type]
    )
