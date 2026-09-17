"""
Regression tests for backend/common/validation.py.

validation.py used to define its own `ValidationError(Exception)`, a
completely separate class from backend.common.logging_utils.ValidationError
(ServiceError, status_code=400). validate_schema() raised the former, but
every service's Flask error handler checks `isinstance(e, ServiceError)` to
decide between returning the error's own status code and a generic 500 -
so every schema-validation failure across every route that uses
validate_schema (risk-metrics, stress-test, calculate-position, and any
future ones) surfaced as an unhandled 500 instead of a 400 with a useful
message. These tests would have caught that.
"""

import unittest

from backend.common import ServiceError
from backend.common.validation import (
    RiskMetricsRequest,
    ValidationError,
    validate_schema,
)


class TestValidationErrorIsServiceError(unittest.TestCase):
    """ValidationError must be a ServiceError subclass so Flask error
    handlers built around `isinstance(e, ServiceError)` recognise it."""

    def test_is_service_error_subclass(self) -> None:
        self.assertTrue(issubclass(ValidationError, ServiceError))

    def test_status_code_is_400(self) -> None:
        err = ValidationError("something went wrong")
        self.assertEqual(err.status_code, 400)
        self.assertIsInstance(err, ServiceError)

    def test_field_and_code_still_accessible(self) -> None:
        """Existing call sites throughout validation.py pass field=/code=;
        the fix must not break that constructor signature."""
        err = ValidationError("bad value", field="symbol", code="invalid")
        self.assertEqual(err.field, "symbol")
        self.assertEqual(err.code, "invalid")

    def test_to_dict_works(self) -> None:
        """Inherited from ServiceError - used by every app.py's error handler."""
        err = ValidationError("bad value")
        body = err.to_dict()
        self.assertEqual(body["status_code"], 400)
        self.assertEqual(body["error"], "bad value")


class TestValidateSchema(unittest.TestCase):
    """validate_schema() itself must raise the fixed ValidationError"""

    def test_raises_validation_error_on_bad_input(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_schema({}, RiskMetricsRequest)
        self.assertIsInstance(ctx.exception, ServiceError)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_raises_validation_error_on_non_dict_input(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_schema("not a dict", RiskMetricsRequest)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_valid_input_passes_through(self) -> None:
        result = validate_schema(
            {"portfolio": {"id": "p1", "cash": 100.0, "positions": []}},
            RiskMetricsRequest,
        )
        self.assertEqual(result["portfolio"]["id"], "p1")
        self.assertEqual(result["confidence_levels"], [0.95, 0.99])

    def test_would_be_caught_as_service_error_in_a_flask_route(self) -> None:
        """Simulates the exact pattern every app.py route handler uses."""
        try:
            validate_schema({}, RiskMetricsRequest)
            self.fail("expected validate_schema to raise")
        except Exception as e:
            if isinstance(e, ServiceError):
                status_code = e.status_code
            else:
                status_code = 500
        self.assertEqual(status_code, 400)


if __name__ == "__main__":
    unittest.main()
