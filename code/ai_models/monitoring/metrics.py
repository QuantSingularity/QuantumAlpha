import threading
from collections import defaultdict
from typing import Dict, Tuple

LabelKey = Tuple[Tuple[str, str], ...]


def _key(labels: Dict[str, str]) -> LabelKey:
    return tuple(sorted((k, str(v)) for k, v in labels.items()))


def _render_labels(key: LabelKey) -> str:
    if not key:
        return ""
    return "{" + ",".join(f'{k}="{v}"' for k, v in key) + "}"


class MetricsRegistry:
    def __init__(self) -> None:
        self._counters: Dict[str, Dict[LabelKey, float]] = defaultdict(dict)
        self._sums: Dict[str, Dict[LabelKey, float]] = defaultdict(dict)
        self._counts: Dict[str, Dict[LabelKey, int]] = defaultdict(dict)
        self._lock = threading.Lock()

    def inc(self, name: str, value: float = 1.0, **labels: str) -> None:
        key = _key(labels)
        with self._lock:
            self._counters[name][key] = self._counters[name].get(key, 0.0) + value

    def observe(self, name: str, value: float, **labels: str) -> None:
        key = _key(labels)
        with self._lock:
            self._sums[name][key] = self._sums[name].get(key, 0.0) + value
            self._counts[name][key] = self._counts[name].get(key, 0) + 1

    def render(self) -> str:
        lines = []
        with self._lock:
            for name, series in sorted(self._counters.items()):
                lines.append(f"# TYPE {name} counter")
                for key, value in sorted(series.items()):
                    lines.append(f"{name}{_render_labels(key)} {value}")
            for name, series in sorted(self._sums.items()):
                lines.append(f"# TYPE {name} summary")
                for key, value in sorted(series.items()):
                    labels = _render_labels(key)
                    lines.append(f"{name}_sum{labels} {value}")
                    lines.append(f"{name}_count{labels} {self._counts[name][key]}")
        return "\n".join(lines) + "\n"
