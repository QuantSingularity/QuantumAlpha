import threading
import traceback
import uuid
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from ai_models.core.exceptions import AIEngineError, NotFoundError
from ai_models.core.logging import get_logger

logger = get_logger("jobs")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobManager:
    def __init__(self, max_workers: int = 2, history: int = 200) -> None:
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="ai-job"
        )
        self._jobs: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
        self._lock = threading.Lock()
        self._history = history

    def submit(
        self,
        kind: str,
        fn: Callable[..., Any],
        *args: Any,
        meta: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        job_id = f"job_{uuid.uuid4().hex[:16]}"
        record = {
            "id": job_id,
            "kind": kind,
            "status": "queued",
            "meta": meta or {},
            "result": None,
            "error": None,
            "created_at": _now(),
            "started_at": None,
            "finished_at": None,
        }
        with self._lock:
            self._jobs[job_id] = record
            self._trim()
        self._executor.submit(self._run, job_id, fn, args, kwargs)
        return self.get(job_id)

    def _trim(self) -> None:
        while len(self._jobs) > self._history:
            for key, job in self._jobs.items():
                if job["status"] in ("succeeded", "failed"):
                    del self._jobs[key]
                    break
            else:
                break

    def _update(self, job_id: str, **changes: Any) -> None:
        with self._lock:
            self._jobs[job_id].update(changes)

    def _run(
        self, job_id: str, fn: Callable[..., Any], args: tuple, kwargs: dict
    ) -> None:
        self._update(job_id, status="running", started_at=_now())
        try:
            result = fn(*args, **kwargs)
            self._update(job_id, status="succeeded", result=result, finished_at=_now())
        except AIEngineError as exc:
            self._update(
                job_id, status="failed", error=exc.to_dict(), finished_at=_now()
            )
        except Exception as exc:
            logger.error("Job %s failed: %s\n%s", job_id, exc, traceback.format_exc())
            self._update(
                job_id,
                status="failed",
                error={"error": str(exc), "code": "JOB_FAILED"},
                finished_at=_now(),
            )

    def get(self, job_id: str) -> Dict[str, Any]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise NotFoundError(f"Job not found: {job_id}")
            return dict(job)

    def list(self, kind: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            jobs = [dict(j) for j in self._jobs.values() if kind in (None, j["kind"])]
        return list(reversed(jobs))[:limit]

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
