import unittest
from unittest.mock import MagicMock

import requests
from backend.api.ai_gateway import (
    AIEngineClient,
    create_ai_gateway_blueprint,
    is_write,
    resolve_upstream,
)
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token


class FakeSession:
    def __init__(self, status=200, payload=None, error=None):
        self.status = status
        self.payload = {"ok": True} if payload is None else payload
        self.error = error
        self.calls = []

    def request(self, method, url, params=None, json=None, headers=None, timeout=None):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "params": params,
                "json": json,
                "headers": headers,
                "timeout": timeout,
            }
        )
        if self.error:
            raise self.error
        response = MagicMock()
        response.status_code = self.status
        response.json.return_value = self.payload
        return response


def build_app(session, **kwargs):
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-secret-key-with-sufficient-length-32"
    JWTManager(app)
    client = AIEngineClient("http://ai:8080", "k", session)
    app.register_blueprint(create_ai_gateway_blueprint(client=client, **kwargs))
    return app


class TestResolveUpstream(unittest.TestCase):
    def test_allowlist(self):
        self.assertEqual(resolve_upstream("models"), "/api/models")
        self.assertEqual(resolve_upstream("predict/m1/AAPL"), "/api/predict/m1/AAPL")
        self.assertEqual(resolve_upstream("signals/generate"), "/api/generate-signals")
        self.assertEqual(resolve_upstream("rl/act"), "/api/rl/act")
        self.assertEqual(resolve_upstream("health"), "/health")
        self.assertEqual(
            resolve_upstream("models/m1/versions/2/promote"),
            "/api/models/m1/versions/2/promote",
        )

    def test_blocked(self):
        for path in (
            "metrics",
            "admin",
            "models/../../etc",
            "train-model",
            "models/m1/unknown",
        ):
            self.assertIsNone(resolve_upstream(path), path)

    def test_write_classification(self):
        self.assertFalse(is_write("GET", "models"))
        self.assertFalse(is_write("POST", "predict"))
        self.assertFalse(is_write("POST", "signals/generate"))
        self.assertTrue(is_write("POST", "models"))
        self.assertTrue(is_write("DELETE", "models/m1"))
        self.assertTrue(is_write("POST", "models/m1/train"))


class TestGatewayProxy(unittest.TestCase):
    def test_forwards_query_body_and_key(self):
        session = FakeSession(payload={"id": "m1"})
        http = build_app(session).test_client()
        resp = http.post(
            "/api/ai/predict",
            json={"model_id": "m1", "symbol": "AAPL"},
            headers={"X-Request-ID": "r1"},
        )
        self.assertEqual(resp.status_code, 200)
        call = session.calls[0]
        self.assertEqual(call["url"], "http://ai:8080/api/predict")
        self.assertEqual(call["json"], {"model_id": "m1", "symbol": "AAPL"})
        self.assertEqual(call["headers"]["X-Internal-Key"], "k")
        self.assertEqual(call["headers"]["X-Request-ID"], "r1")
        http.get("/api/ai/models?status=trained")
        self.assertEqual(session.calls[1]["params"], {"status": "trained"})

    def test_single_symbol_signal_body_is_normalised(self):
        session = FakeSession()
        build_app(session).test_client().post(
            "/api/ai/signals/generate", json={"symbol": "AAPL", "strategy": "technical"}
        )
        self.assertEqual(session.calls[0]["json"]["symbols"], ["AAPL"])

    def test_upstream_status_and_errors(self):
        http = build_app(
            FakeSession(status=404, payload={"error": "nope", "code": "NOT_FOUND"})
        ).test_client()
        self.assertEqual(http.get("/api/ai/models/x").status_code, 404)
        self.assertEqual(
            build_app(FakeSession(error=requests.ConnectionError()))
            .test_client()
            .get("/api/ai/models")
            .status_code,
            503,
        )
        self.assertEqual(
            build_app(FakeSession(error=requests.Timeout()))
            .test_client()
            .get("/api/ai/models")
            .status_code,
            504,
        )
        self.assertEqual(
            build_app(FakeSession()).test_client().get("/api/ai/secret").status_code,
            404,
        )
        bad = (
            build_app(FakeSession())
            .test_client()
            .post("/api/ai/predict", data="{bad", content_type="application/json")
        )
        self.assertEqual(bad.status_code, 400)

    def test_long_operations_use_long_timeout_unless_async(self):
        session = FakeSession()
        http = build_app(session).test_client()
        http.post("/api/ai/models/m1/train", json={"symbol": "AAPL"})
        http.post("/api/ai/models/m1/train", json={"symbol": "AAPL", "async": True})
        http.get("/api/ai/models")
        self.assertGreater(session.calls[0]["timeout"], session.calls[1]["timeout"])
        self.assertEqual(session.calls[1]["timeout"], session.calls[2]["timeout"])

    def test_envelope_mode(self):
        http = build_app(FakeSession(payload=[1, 2]), envelope=True).test_client()
        body = http.get("/api/ai/models").get_json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"], [1, 2])
        failure = (
            build_app(
                FakeSession(status=409, payload={"error": "busy", "code": "CONFLICT"}),
                envelope=True,
            )
            .test_client()
            .get("/api/ai/models")
            .get_json()
        )
        self.assertFalse(failure["success"])
        self.assertEqual(failure["error"], "busy")


class TestGatewayAuth(unittest.TestCase):
    def setUp(self):
        from flask_jwt_extended import jwt_required

        self.session = FakeSession()
        self.app = build_app(
            self.session, auth_decorator=lambda f: jwt_required()(f), enforce_roles=True
        )

    def _headers(self, roles):
        with self.app.app_context():
            token = create_access_token("u1", additional_claims={"roles": roles})
        return {"Authorization": f"Bearer {token}"}

    def test_requires_token(self):
        self.assertEqual(self.app.test_client().get("/api/ai/models").status_code, 401)
        self.assertEqual(self.app.test_client().get("/api/ai/health").status_code, 200)

    def test_viewer_can_read_and_predict_but_not_write(self):
        http = self.app.test_client()
        headers = self._headers(["viewer"])
        self.assertEqual(http.get("/api/ai/models", headers=headers).status_code, 200)
        self.assertEqual(
            http.post("/api/ai/predict", json={}, headers=headers).status_code, 200
        )
        self.assertEqual(
            http.post("/api/ai/models", json={}, headers=headers).status_code, 403
        )
        self.assertEqual(
            http.delete("/api/ai/models/m1", headers=headers).status_code, 403
        )

    def test_analyst_can_write(self):
        resp = self.app.test_client().post(
            "/api/ai/models", json={"name": "x"}, headers=self._headers(["analyst"])
        )
        self.assertEqual(resp.status_code, 200)


class TestPeriodContract(unittest.TestCase):
    def test_market_data_request_accepts_aliases_and_generic_periods(self):
        from backend.common.validation import MarketDataRequest

        schema = MarketDataRequest()
        for period in ("1d", "30d", "1mo", "3m", "1y", "1wk", "max"):
            data = schema.load({"symbol": "AAPL", "timeframe": "1d", "period": period})
            self.assertEqual(data["period"], period)
        with self.assertRaises(Exception):
            schema.load({"symbol": "AAPL", "period": "forever"})

    def test_parse_period_covers_validated_values(self):
        from backend.common.utils import parse_period

        for period in ("1d", "30d", "1mo", "3m", "1y", "1wk", "max", "2y"):
            parse_period(period)
        with self.assertRaises(ValueError):
            parse_period("forever")


if __name__ == "__main__":
    unittest.main()
