import logging
from pathlib import Path

from app.core.context import get_trace_id

_LOG_FILE_NAME = "agent-python.log"


class TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id() or "-"
        return True


def _get_log_dir() -> Path:
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    return project_root / "logs"


def _has_file_handler(root_logger: logging.Logger, log_path: Path) -> bool:
    for h in root_logger.handlers:
        if isinstance(h, logging.FileHandler):
            try:
                if Path(h.baseFilename) == log_path:
                    return True
            except (AttributeError, ValueError):
                pass
    return False


def setup_logging(log_level: str = "INFO") -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    log_format = "%(asctime)s | %(levelname)s | %(name)s | trace_id=%(trace_id)s | %(message)s"
    formatter = logging.Formatter(log_format)
    trace_filter = TraceIdFilter()

    root_logger.setLevel(level)

    if not root_logger.handlers:
        logging.basicConfig(level=level, format=log_format)

    for handler in root_logger.handlers:
        handler.setLevel(level)
        if handler.formatter is None:
            handler.setFormatter(formatter)
        if not any(isinstance(f, TraceIdFilter) for f in handler.filters):
            handler.addFilter(trace_filter)

    log_dir = _get_log_dir()
    log_path = log_dir / _LOG_FILE_NAME
    if not _has_file_handler(root_logger, log_path):
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(trace_filter)
        root_logger.addHandler(file_handler)


def get_logger(name: str = "app") -> logging.Logger:
    return logging.getLogger(name)
