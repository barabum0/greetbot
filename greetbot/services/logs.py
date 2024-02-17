import sys

import logging
from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record):
        level = logger.level(record.levelname).name
        logger.log(level, record.getMessage())


def configure_logger() -> None:
    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level> {exception}\n"

    logger.remove()
    logger.add(sys.stdout, colorize=True, format=log_format, diagnose=True, backtrace=True)
    logger.add(
        f"logs/log.log",
        format=log_format,
        rotation="1 week",
        diagnose=True,
        enqueue=True,
        colorize=True,
        backtrace=True,
    )
    logger.level("DEBUG", color="<fg #7f7f7f>")
    logger.level("INFO", color="<white>")
    logger.level("SUCCESS", color="<green>")
    logger.level("WARNING", color="<yellow>")
    logger.level("ERROR", color="<red>")
    logger.level("CRITICAL", color="<bold><white><RED>")

    logging.getLogger('aiogram').setLevel(logging.DEBUG)
    logging.getLogger('aiogram').addHandler(InterceptHandler())
    logging.getLogger('asyncio').setLevel(logging.DEBUG)
    logging.getLogger('asyncio').addHandler(InterceptHandler())
