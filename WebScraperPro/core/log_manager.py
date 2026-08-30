r"""
WebScraper Pro - Structured Log Manager
=======================================
Provides centralized, structured logging with:
  - Console handler (ColoredFormatter-like output)
  - File handler with rotation (time + size based)
  - Log export to JSON/CSV
  - In-memory ring buffer for UI display
  - Per-module verbosity control
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import deque


# ---------------------------------------------------------------------------
# Log levels
# ---------------------------------------------------------------------------
VERBOSE = 5
logging.addLevelName(VERBOSE, "VERBOSE")


def _verbose(self, msg, *args, **kwargs):
    if self.isEnabledFor(VERBOSE):
        self._log(VERBOSE, msg, args, **kwargs)

logging.Logger.verbose = _verbose


# ---------------------------------------------------------------------------
# Ring Buffer Handler — keeps last N records in memory for UI
# ---------------------------------------------------------------------------

class RingBufferHandler(logging.Handler):
    """Logging handler that keeps the last *capacity* log records in memory."""

    def __init__(self, capacity: int = 500):
        super().__init__()
        self._buffer: deque = deque(maxlen=capacity)
        self._lock = None  # logging module handles thread safety

    def emit(self, record: logging.LogRecord) -> None:
        try:
            entry = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "module": record.module,
                "message": self.format(record),
            }
            self._buffer.append(entry)
        except Exception:
            self.handleError(record)

    def get_entries(self, limit: int = 100, level: Optional[str] = None) -> List[Dict]:
        """Return recent log entries, optionally filtered by level."""
        entries = list(self._buffer)
        if level:
            entries = [e for e in entries if e["level"] == level.upper()]
        return entries[-limit:]

    def get_all_entries(self) -> List[Dict]:
        """Return all buffered entries."""
        return list(self._buffer)

    def clear(self) -> None:
        """Clear the buffer."""
        self._buffer.clear()

    @property
    def count(self) -> int:
        return len(self._buffer)


# ---------------------------------------------------------------------------
# Structured JSON Formatter
# ---------------------------------------------------------------------------

class StructuredFormatter(logging.Formatter):
    """JSON-structured log formatter for file output."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "ts": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
            "msg": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """Colored console formatter.

    Colors: DEBUG=cyan, INFO=green, WARNING=yellow, ERROR=red, CRITICAL=red bold.
    """

    _COLORS = {
        "DEBUG": "\033[36m",     # cyan
        "VERBOSE": "\033[35m",   # magenta
        "INFO": "\033[32m",      # green
        "WARNING": "\033[33m",   # yellow
        "ERROR": "\033[31m",     # red
        "CRITICAL": "\033[1;31m", # bold red
    }
    _RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self._COLORS.get(record.levelname, self._RESET)
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        lvl = record.levelname.ljust(8)
        name = record.name[:20].ljust(20) if len(record.name) > 20 else record.name.ljust(20)
        msg = record.getMessage()
        formatted = f"{color}{ts} {lvl} {name}{self._RESET} {msg}"
        if record.exc_info and record.exc_info[1]:
            formatted += "\n" + self.formatException(record.exc_info)
        return formatted


# ---------------------------------------------------------------------------
# Main Log Manager
# ---------------------------------------------------------------------------

class LogManager:
    """Centralized log manager for the entire application.

    Parameters
    ----------
    log_dir : str
        Directory for log files.
    app_name : str
        Application name (used in log filenames).
    console_level : int
        Minimum level for console output.
    file_level : int
        Minimum level for file output.
    file_max_bytes : int
        Max file size before rotation (bytes).
    backup_count : int
        Number of rotated backup files to keep.
    ring_capacity : int
        Number of in-memory log entries to keep.
    """

    _instance: Optional[LogManager] = None

    def __init__(
        self,
        log_dir: str = "",
        app_name: str = "WebScraperPro",
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        file_max_bytes: int = 5 * 1024 * 1024,  # 5 MB
        backup_count: int = 5,
        ring_capacity: int = 500,
    ) -> None:
        self._app_name = app_name
        self._console_level = console_level
        self._file_level = file_level

        # Ensure log directory exists
        if not log_dir:
            log_dir = os.path.join(os.path.expanduser("~"), ".webscraperpro", "logs")
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)

        # Ring buffer for UI
        self._ring = RingBufferHandler(capacity=ring_capacity)

        # Configure root logger
        self._root_logger = logging.getLogger(app_name)
        self._root_logger.setLevel(logging.DEBUG)
        self._root_logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(ConsoleFormatter())
        self._root_logger.addHandler(console_handler)

        # File handler (rotating)
        log_file = self._log_dir / f"{app_name.lower()}.log"
        file_handler = RotatingFileHandler(
            str(log_file),
            maxBytes=file_max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(file_level)
        file_handler.setFormatter(StructuredFormatter())
        self._root_logger.addHandler(file_handler)

        # Ring buffer handler
        self._ring.setLevel(logging.DEBUG)
        self._root_logger.addHandler(self._ring)

        # Suppress noisy third-party loggers
        for noisy in ["urllib3", "requests", "matplotlib", "parso", "asyncio"]:
            logging.getLogger(noisy).setLevel(logging.WARNING)

        self._root_logger.info("LogManager initialized. Log dir: %s", self._log_dir)

    @classmethod
    def get_instance(cls, **kwargs) -> LogManager:
        """Get or create the singleton LogManager instance."""
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (for testing)."""
        cls._instance = None

    @property
    def logger(self) -> logging.Logger:
        """The root application logger."""
        return self._root_logger

    @property
    def ring_buffer(self) -> RingBufferHandler:
        """The in-memory ring buffer handler."""
        return self._ring

    def get_recent(self, limit: int = 100, level: Optional[str] = None) -> List[Dict]:
        """Get recent log entries from the ring buffer."""
        return self._ring.get_entries(limit=limit, level=level)

    def get_log_files(self) -> List[Dict[str, Any]]:
        """List all log files with metadata."""
        files = []
        for p in sorted(self._log_dir.glob("*.log*"), reverse=True):
            stat = p.stat()
            files.append({
                "name": p.name,
                "path": str(p),
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        return files

    def export_logs(self, output_path: str, format: str = "json") -> Dict[str, Any]:
        """Export all ring buffer logs to a file.

        Parameters
        ----------
        output_path : str
            Output file path.
        format : str
            ``"json"`` or ``"csv"``.

        Returns
        -------
        dict with status, path, entries_exported.
        """
        entries = self._ring.get_all_entries()
        if not entries:
            return {"error": "No log entries to export"}

        try:
            if format == "csv":
                import csv
                with open(output_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=["timestamp", "level", "module", "message"])
                    writer.writeheader()
                    writer.writerows(entries)
            else:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(entries, f, indent=2, ensure_ascii=False)

            return {
                "status": "ok",
                "path": output_path,
                "entries_exported": len(entries),
                "format": format,
            }
        except Exception as e:
            return {"error": str(e)}

    def clear_logs(self) -> None:
        """Clear the in-memory ring buffer."""
        self._ring.clear()
        self._root_logger.info("Log buffer cleared.")

    def set_level(self, level: str) -> None:
        """Set the console log level.

        Parameters
        ----------
        level : str
            One of: DEBUG, VERBOSE, INFO, WARNING, ERROR, CRITICAL.
        """
        level_map = {
            "DEBUG": logging.DEBUG,
            "VERBOSE": VERBOSE,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        lvl = level_map.get(level.upper(), logging.INFO)
        self._console_level = lvl
        for handler in self._root_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RingBufferHandler):
                handler.setLevel(lvl)
        self._root_logger.info("Console log level set to %s", level.upper())

    def get_log_stats(self) -> Dict[str, Any]:
        """Return statistics about the log buffer."""
        entries = self._ring.get_all_entries()
        level_counts = {}
        for e in entries:
            lvl = e["level"]
            level_counts[lvl] = level_counts.get(lvl, 0) + 1
        return {
            "total_entries": len(entries),
            "buffer_capacity": self._ring._buffer.maxlen,
            "level_counts": level_counts,
            "log_dir": str(self._log_dir),
            "log_files": len(self.get_log_files()),
        }
