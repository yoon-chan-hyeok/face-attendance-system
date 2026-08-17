import logging
import sys
import threading
from collections import deque
from datetime import datetime
from typing import Deque, Dict, List, Optional


class LogStore:
    def __init__(self, maxlen: int = 3000):
        self._items: Deque[Dict[str, str]] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def add(self, level: str, source: str, message: str):
        msg = (message or "").strip()
        if not msg:
            return
        item = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "level": level,
            "source": source,
            "message": msg,
        }
        with self._lock:
            self._items.append(item)

    def recent(self, limit: int = 200) -> List[Dict[str, str]]:
        with self._lock:
            data = list(self._items)
        return data[-limit:]

    def clear(self):
        with self._lock:
            self._items.clear()


class LogStoreHandler(logging.Handler):
    def __init__(self, store: LogStore):
        super().__init__()
        self.store = store
        self.setFormatter(logging.Formatter("%(name)s | %(message)s"))

    def emit(self, record: logging.LogRecord):
        try:
            message = self.format(record)
            self.store.add(record.levelname, "logging", message)
        except Exception:
            pass


class StreamTee:
    def __init__(self, stream, store: LogStore, source: str, level: str):
        self.stream = stream
        self.store = store
        self.source = source
        self.level = level
        self._buffer = ""
        self._lock = threading.Lock()

    def write(self, s):
        if not isinstance(s, str):
            s = str(s)
        with self._lock:
            self.stream.write(s)
            self._buffer += s
            while "\n" in self._buffer:
                line, self._buffer = self._buffer.split("\n", 1)
                self.store.add(self.level, self.source, line)
        return len(s)

    def flush(self):
        with self._lock:
            if self._buffer.strip():
                self.store.add(self.level, self.source, self._buffer.strip())
            self._buffer = ""
            self.stream.flush()

    def isatty(self):
        return getattr(self.stream, "isatty", lambda: False)()


log_store = LogStore()
_initialized = False


def setup_log_capture():
    global _initialized
    if _initialized:
        return
    _initialized = True

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    has_store_handler = any(isinstance(h, LogStoreHandler) for h in root.handlers)
    if not has_store_handler:
        root.addHandler(LogStoreHandler(log_store))

    if not isinstance(sys.stdout, StreamTee):
        sys.stdout = StreamTee(sys.stdout, log_store, source="stdout", level="INFO")
    if not isinstance(sys.stderr, StreamTee):
        sys.stderr = StreamTee(sys.stderr, log_store, source="stderr", level="ERROR")

    log_store.add("INFO", "system", "Log capture initialized.")
