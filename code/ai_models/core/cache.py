import threading
import time
from collections import OrderedDict
from typing import Any, Callable, Optional


class TTLCache:
    def __init__(self, max_size: int = 256, ttl: float = 60.0) -> None:
        self.max_size = max_size
        self.ttl = ttl
        self._data: "OrderedDict[Any, tuple]" = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: Any) -> Optional[Any]:
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            expires, value = item
            if expires < time.monotonic():
                del self._data[key]
                return None
            self._data.move_to_end(key)
            return value

    def set(self, key: Any, value: Any) -> None:
        if self.ttl <= 0:
            return
        with self._lock:
            self._data[key] = (time.monotonic() + self.ttl, value)
            self._data.move_to_end(key)
            while len(self._data) > self.max_size:
                self._data.popitem(last=False)

    def get_or_set(self, key: Any, factory: Callable[[], Any]) -> Any:
        value = self.get(key)
        if value is None:
            value = factory()
            self.set(key, value)
        return value

    def invalidate(self, prefix: Optional[str] = None) -> None:
        with self._lock:
            if prefix is None:
                self._data.clear()
                return
            for key in [k for k in self._data if str(k).startswith(prefix)]:
                del self._data[key]

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)
