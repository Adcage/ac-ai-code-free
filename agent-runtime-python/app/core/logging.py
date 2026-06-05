import logging


def setup_logging(log_level: str = "INFO") -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    if not root_logger.handlers:
        logging.basicConfig(level=level, format=log_format)
        return

    root_logger.setLevel(level)
    formatter = logging.Formatter(log_format)
    for handler in root_logger.handlers:
        handler.setLevel(level)
        if handler.formatter is None:
            handler.setFormatter(formatter)


def get_logger(name: str = "app") -> logging.Logger:
    return logging.getLogger(name)
