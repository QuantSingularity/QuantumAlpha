import json
import os
import threading

import pytest
from ai_models.core.cache import TTLCache
from ai_models.core.exceptions import ConflictError, NotFoundError
from ai_models.core.jobs import JobManager
from ai_models.registry.store import ModelRegistry


def test_registry_lifecycle_and_versions(tmp_path):
    registry = ModelRegistry(str(tmp_path))
    info = registry.create("alpha", "ridge", features=["sma_20"])
    model_id = info["id"]
    assert registry.list()[0]["id"] == model_id
    registry.begin_training(model_id)
    with pytest.raises(ConflictError):
        registry.begin_training(model_id)
    with pytest.raises(ConflictError):
        registry.delete(model_id)
    registry.add_version(model_id, 1, {"mse": 1.0}, {"symbol": "AAPL"}, {})
    registry.add_version(
        model_id, 2, {"mse": 0.5}, {"symbol": "AAPL"}, {}, activate=False
    )
    assert registry.get(model_id)["active_version"] == 1
    registry.promote(model_id, 2)
    assert registry.get(model_id)["metrics"] == {"mse": 0.5}
    with pytest.raises(ConflictError):
        registry.delete_version(model_id, 2)
    registry.delete_version(model_id, 1)
    registry.delete(model_id)
    with pytest.raises(NotFoundError):
        registry.get(model_id)


def test_registry_persists_and_handles_legacy_records(tmp_path):
    legacy = {
        "models": {
            "m1": {
                "name": "legacy",
                "type": "lstm",
                "status": "created",
                "created_at": "2026-01-01",
            }
        }
    }
    os.makedirs(tmp_path, exist_ok=True)
    with open(tmp_path / "registry.json", "w") as handle:
        json.dump(legacy, handle)
    registry = ModelRegistry(str(tmp_path))
    assert registry.get("m1")["versions"] == []
    reopened = ModelRegistry(str(tmp_path))
    assert reopened.list()[0]["name"] == "legacy"


def test_registry_sees_changes_from_other_instances(tmp_path):
    first, second = ModelRegistry(str(tmp_path)), ModelRegistry(str(tmp_path))
    model_id = first.create("shared", "ridge")["id"]
    assert second.get(model_id)["name"] == "shared"
    second.update(model_id, {"name": "renamed"})
    assert first.get(model_id)["name"] == "renamed"


def test_registry_concurrent_creates(tmp_path):
    registry = ModelRegistry(str(tmp_path))
    errors = []

    def create(i):
        try:
            registry.create(f"m{i}", "ridge")
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=create, args=(i,)) for i in range(20)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert not errors
    assert len(registry.list()) == 20


def test_recover_stuck_training(tmp_path):
    registry = ModelRegistry(str(tmp_path))
    model_id = registry.create("x", "ridge")["id"]
    registry.begin_training(model_id)
    assert registry.recover_stuck() == 1
    assert registry.get(model_id)["status"] == "error"


def test_cache_ttl_and_eviction():
    cache = TTLCache(max_size=2, ttl=60)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    assert cache.get("a") is None and cache.get("c") == 3
    assert TTLCache(ttl=0).get_or_set("k", lambda: 5) == 5


def test_job_manager_success_and_failure():
    jobs = JobManager(max_workers=1, history=5)
    ok = jobs.submit("t", lambda: {"v": 1})
    bad = jobs.submit("t", lambda: 1 / 0)
    import time

    for _ in range(50):
        if (
            jobs.get(bad["id"])["status"] == "failed"
            and jobs.get(ok["id"])["status"] == "succeeded"
        ):
            break
        time.sleep(0.05)
    assert jobs.get(ok["id"])["result"] == {"v": 1}
    assert jobs.get(bad["id"])["error"]["code"] == "JOB_FAILED"
    with pytest.raises(NotFoundError):
        jobs.get("missing")
    jobs.shutdown()
