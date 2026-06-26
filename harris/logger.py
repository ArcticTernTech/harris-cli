import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_logger(name: str = "harris") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    log_dir = Path.home() / ".harris" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        log_dir / "harris.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
