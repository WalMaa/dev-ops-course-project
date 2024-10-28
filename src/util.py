from enum import Enum


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


def log_and_print(logger, level, msg):
    print(msg)

    if level == LogLevel.DEBUG:
        logger.debug(msg)
    elif level == LogLevel.WARNING:
        logger.warning(msg)
    elif level == LogLevel.ERROR:
        logger.error(msg)
    else:
        logger.info(msg)
