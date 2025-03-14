import os
import logging
from logging.handlers import RotatingFileHandler
from . import __version__

def setup_logger(config:dict):
    verbose = config.get("VERBOSE", False)
    log_file = config.get("LOG_FILE", "ai_service.log")
    log_format = f"%(asctime)s [{__version__}] [%(levelname)s] %(filename)s:%(lineno)d: %(message)s"
    date_format = "[%Y-%m-%d %H:%M:%S]"
    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
    logging.basicConfig(
        format=log_format,
        datefmt=date_format,
    )
    if os.path.exists(log_file):
        os.remove(log_file)
    handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=1, encoding="utf-8"
    )
    handler.stream.flush()
    handler.setFormatter(formatter)
    log = logging.getLogger("ai_service")
    log.addHandler(handler)
    log.setLevel(logging.DEBUG if verbose else logging.INFO)
    return log