import contextlib
import json
import os
import shutil
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional

from ai_models.core.exceptions import ConflictError, NotFoundError, ValidationError
from ai_models.core.logging import get_logger

try:
    import fcntl
except ImportError:
    fcntl = None

logger = get_logger("registry")

STATUSES = ("created", "training", "trained", "error")
SUMMARY_FIELDS = (
    "id",
    "name",
    "description",
    "type",
    "status",
    "created_at",
    "updated_at",
    "metrics",
    "active_version",
    "tags",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ModelRegistry:
    def __init__(self, base_dir: str, id_prefix: str = "model") -> None:
        self.base_dir = base_dir
        self.id_prefix = id_prefix
        self.artifact_root = os.path.join(base_dir, "artifacts")
        self.registry_file = os.path.join(base_dir, "registry.json")
        self._lock_file = os.path.join(base_dir, ".registry.lock")
        self._thread_lock = threading.RLock()
        self._state: Dict[str, Any] = {"models": {}}
        self._signature: Optional[tuple] = None
        os.makedirs(self.artifact_root, exist_ok=True)
        with self._locked(write=False):
            pass

    def _file_signature(self) -> Optional[tuple]:
        try:
            stat = os.stat(self.registry_file)
            return (stat.st_mtime_ns, stat.st_size)
        except FileNotFoundError:
            return None

    def _load(self) -> None:
        signature = self._file_signature()
        if signature is None:
            self._state = {"models": {}}
            self._signature = None
            return
        if signature == self._signature:
            return
        try:
            with open(self.registry_file, "r") as handle:
                state = json.load(handle)
            if not isinstance(state, dict) or not isinstance(state.get("models"), dict):
                raise ValueError("invalid registry structure")
            for record in state["models"].values():
                record.setdefault("versions", [])
                record.setdefault("active_version", None)
                record.setdefault("metrics", {})
                record.setdefault("tags", [])
                record.setdefault("parameters", {})
                record.setdefault("features", [])
            self._state = state
        except (OSError, ValueError) as exc:
            logger.error("Registry unreadable, starting empty: %s", exc)
            self._state = {"models": {}}
        self._signature = signature

    def _save(self) -> None:
        temp = f"{self.registry_file}.{uuid.uuid4().hex}.tmp"
        with open(temp, "w") as handle:
            json.dump(self._state, handle, indent=2, default=str)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, self.registry_file)
        self._signature = self._file_signature()

    @contextlib.contextmanager
    def _locked(self, write: bool) -> Iterator[None]:
        with self._thread_lock:
            handle = None
            if fcntl is not None:
                os.makedirs(self.base_dir, exist_ok=True)
                handle = open(self._lock_file, "a+")
                fcntl.flock(handle, fcntl.LOCK_EX if write else fcntl.LOCK_SH)
            try:
                self._load()
                yield
                if write:
                    self._save()
            finally:
                if handle is not None:
                    fcntl.flock(handle, fcntl.LOCK_UN)
                    handle.close()

    def _require(self, model_id: str) -> Dict[str, Any]:
        info = self._state["models"].get(model_id)
        if info is None:
            raise NotFoundError(f"Model not found: {model_id}")
        return info

    @staticmethod
    def summary(info: Dict[str, Any]) -> Dict[str, Any]:
        out = {key: info.get(key) for key in SUMMARY_FIELDS}
        out["metrics"] = info.get("metrics") or {}
        out["tags"] = info.get("tags") or []
        return out

    @staticmethod
    def detail(info: Dict[str, Any]) -> Dict[str, Any]:
        out = ModelRegistry.summary(info)
        out["parameters"] = info.get("parameters") or {}
        out["features"] = info.get("features") or []
        out["training_data"] = info.get("training_data")
        out["versions"] = [
            {k: v for k, v in version.items() if k != "path"}
            for version in info.get("versions", [])
        ]
        return out

    def list(
        self, status: Optional[str] = None, model_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        with self._locked(write=False):
            infos = list(self._state["models"].values())
        infos = [
            i
            for i in infos
            if (status is None or i.get("status") == status)
            and (model_type is None or i.get("type") == model_type)
        ]
        infos.sort(key=lambda i: i.get("created_at", ""), reverse=True)
        return [self.summary(i) for i in infos]

    def get(self, model_id: str) -> Dict[str, Any]:
        with self._locked(write=False):
            return json.loads(json.dumps(self._require(model_id)))

    def create(
        self,
        name: str,
        model_type: str,
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None,
        features: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if not name or not isinstance(name, str) or len(name) > 120:
            raise ValidationError("Model name is required (max 120 characters)")
        model_id = f"{self.id_prefix}_{uuid.uuid4().hex}"
        now = _now()
        info = {
            "id": model_id,
            "name": name.strip(),
            "description": description or "",
            "type": model_type,
            "status": "created",
            "created_at": now,
            "updated_at": now,
            "parameters": parameters or {},
            "features": features or [],
            "tags": tags or [],
            "metrics": {},
            "training_data": None,
            "active_version": None,
            "versions": [],
        }
        with self._locked(write=True):
            self._state["models"][model_id] = info
        return json.loads(json.dumps(info))

    def update(self, model_id: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        allowed = {"name", "description", "parameters", "features", "tags"}
        with self._locked(write=True):
            info = self._require(model_id)
            for key, value in changes.items():
                if key in allowed:
                    info[key] = value
            info["updated_at"] = _now()
            return json.loads(json.dumps(info))

    def set_status(self, model_id: str, status: str) -> Dict[str, Any]:
        if status not in STATUSES:
            raise ValidationError(f"Invalid status: {status}")
        with self._locked(write=True):
            info = self._require(model_id)
            info["status"] = status
            info["updated_at"] = _now()
            return json.loads(json.dumps(info))

    def begin_training(self, model_id: str) -> Dict[str, Any]:
        with self._locked(write=True):
            info = self._require(model_id)
            if info["status"] == "training":
                raise ConflictError(f"Model is already training: {model_id}")
            info["status"] = "training"
            info["updated_at"] = _now()
            return json.loads(json.dumps(info))

    def version_dir(self, model_id: str, version: int) -> str:
        return os.path.join(self.artifact_root, model_id, f"v{version}")

    def next_version(self, model_id: str) -> int:
        with self._locked(write=False):
            info = self._require(model_id)
            return max((v["version"] for v in info.get("versions", [])), default=0) + 1

    def add_version(
        self,
        model_id: str,
        version: int,
        metrics: Dict[str, Any],
        training_data: Dict[str, Any],
        parameters: Dict[str, Any],
        activate: bool = True,
    ) -> Dict[str, Any]:
        with self._locked(write=True):
            info = self._require(model_id)
            if any(v["version"] == version for v in info["versions"]):
                raise ConflictError(f"Version already exists: {version}")
            info["versions"].append(
                {
                    "version": version,
                    "created_at": _now(),
                    "metrics": metrics,
                    "training_data": training_data,
                    "parameters": parameters,
                    "path": self.version_dir(model_id, version),
                }
            )
            if activate or info["active_version"] is None:
                info["active_version"] = version
                info["metrics"] = metrics
                info["training_data"] = training_data
            info["status"] = "trained"
            info["updated_at"] = _now()
            return json.loads(json.dumps(info))

    def promote(self, model_id: str, version: int) -> Dict[str, Any]:
        with self._locked(write=True):
            info = self._require(model_id)
            match = next((v for v in info["versions"] if v["version"] == version), None)
            if match is None:
                raise NotFoundError(f"Version not found: {version}")
            info["active_version"] = version
            info["metrics"] = match["metrics"]
            info["training_data"] = match["training_data"]
            info["updated_at"] = _now()
            return json.loads(json.dumps(info))

    def active_path(self, model_id: str, version: Optional[int] = None) -> tuple:
        with self._locked(write=False):
            info = self._require(model_id)
            if info["status"] == "training" and not info["versions"]:
                raise ConflictError(f"Model is still training: {model_id}")
            target = version if version is not None else info.get("active_version")
            if target is None:
                return info, None, None
            match = next((v for v in info["versions"] if v["version"] == target), None)
            if match is None:
                raise NotFoundError(f"Version not found: {target}")
            return json.loads(json.dumps(info)), target, match["path"]

    def delete(self, model_id: str) -> Dict[str, Any]:
        with self._locked(write=True):
            info = self._require(model_id)
            if info["status"] == "training":
                raise ConflictError("Cannot delete a model while it is training")
            del self._state["models"][model_id]
        shutil.rmtree(os.path.join(self.artifact_root, model_id), ignore_errors=True)
        return {"id": model_id, "name": info["name"], "deleted": True}

    def delete_version(self, model_id: str, version: int) -> Dict[str, Any]:
        with self._locked(write=True):
            info = self._require(model_id)
            if info.get("active_version") == version:
                raise ConflictError("Cannot delete the active version")
            before = len(info["versions"])
            info["versions"] = [v for v in info["versions"] if v["version"] != version]
            if len(info["versions"]) == before:
                raise NotFoundError(f"Version not found: {version}")
            info["updated_at"] = _now()
        shutil.rmtree(self.version_dir(model_id, version), ignore_errors=True)
        return {"id": model_id, "version": version, "deleted": True}

    def recover_stuck(self) -> int:
        count = 0
        with self._locked(write=True):
            for info in self._state["models"].values():
                if info.get("status") == "training":
                    info["status"] = "trained" if info.get("versions") else "error"
                    count += 1
        return count
