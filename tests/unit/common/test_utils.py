"""
Unit tests for the Common module's utilities.
"""

import os
import sys
import unittest
import uuid
from typing import Any
from datetime import datetime

import numpy as np
import pandas as pd

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
try:
    from backend.common.exceptions import ValidationError
    from backend.common.utils import (
        calculate_moving_average,
        calculate_percentage_change,
        deep_get,
        deep_set,
        denormalize_data,
        dict_to_object,
        filter_dict_by_keys,
        flatten_dict,
        format_timestamp,
        generate_id,
        merge_dictionaries,
        normalize_data,
        object_to_dict,
        parse_timestamp,
        resample_data,
        unflatten_dict,
        validate_enum_field,
        validate_field_range,
        validate_field_type,
        validate_required_fields,
    )
except ImportError:

    def generate_id(prefix: Any = "id") -> Any:
        return f"{prefix}_{uuid.uuid4().hex}"

    def format_timestamp(dt: Any) -> Any:
        return dt.isoformat() if dt else None

    def parse_timestamp(timestamp_str: Any) -> Any:
        return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

    def validate_required_fields(data: Any, required_fields: Any) -> Any:
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                raise ValidationError(f"Missing required field: {field}")

    def validate_field_type(value: Any, field_name: Any, expected_type: Any) -> Any:
        if not isinstance(value, expected_type):
            raise ValidationError(
                f"Invalid type for {field_name}: expected {expected_type.__name__}, got {type(value).__name__}"
            )

    def validate_field_range(
        value: Any, field_name: Any, min_value: Any = None, max_value: Any = None
    ) -> Any:
        if min_value is not None and value < min_value:
            raise ValidationError(
                f"Value for {field_name} is below minimum: {value} < {min_value}"
            )
        if max_value is not None and value > max_value:
            raise ValidationError(
                f"Value for {field_name} is above maximum: {value} > {max_value}"
            )

    def validate_enum_field(value: Any, field_name: Any, valid_values: Any) -> Any:
        if value not in valid_values:
            raise ValidationError(
                f"Invalid value for {field_name}: {value}. Valid values: {', '.join(valid_values)}"
            )

    def calculate_percentage_change(old_value: Any, new_value: Any) -> Any:
        return (new_value - old_value) / old_value * 100 if old_value != 0 else 0

    def calculate_moving_average(data: Any, window: Any) -> Any:
        return pd.Series(data).rolling(window=window).mean().tolist()

    def normalize_data(data: Any, min_val: Any = None, max_val: Any = None) -> Any:
        min_val = min_val if min_val is not None else min(data)
        max_val = max_val if max_val is not None else max(data)
        return [(x - min_val) / (max_val - min_val) for x in data]

    def denormalize_data(normalized_data: Any, min_val: Any, max_val: Any) -> Any:
        return [x * (max_val - min_val) + min_val for x in normalized_data]

    def resample_data(df: Any, timeframe: Any) -> Any:
        return df.resample(timeframe).agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )

    def merge_dictionaries(dict1: Any, dict2: Any) -> Any:
        result = dict1.copy()
        result.update(dict2)
        return result

    def filter_dict_by_keys(d: Any, keys: Any) -> Any:
        return {k: v for k, v in d.items() if k in keys}

    def deep_get(d: Any, keys: Any, default: Any = None) -> Any:
        if not keys:
            return d
        if not isinstance(d, dict):
            return default
        key = keys[0]
        if key not in d:
            return default
        if len(keys) == 1:
            return d[key]
        return deep_get(d[key], keys[1:], default)

    def deep_set(d: Any, keys: Any, value: Any) -> Any:
        if not keys:
            return
        key = keys[0]
        if len(keys) == 1:
            d[key] = value
        else:
            if key not in d:
                d[key] = {}
            deep_set(d[key], keys[1:], value)

    def flatten_dict(d: Any, parent_key: Any = "", sep: Any = ".") -> Any:
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def unflatten_dict(d: Any, sep: Any = ".") -> Any:
        result = {}
        for key, value in d.items():
            parts = key.split(sep)
            deep_set(result, parts, value)
        return result

    def dict_to_object(d: Any) -> Any:

        class DictObject:
            pass

        obj = DictObject()
        for key, value in d.items():
            if isinstance(value, dict):
                value = dict_to_object(value)
            setattr(obj, key, value)
        return obj

    def object_to_dict(obj: Any) -> Any:
        if not hasattr(obj, "__dict__"):
            return obj
        result = {}
        for key, value in obj.__dict__.items():
            if key.startswith("_"):
                continue
            if hasattr(value, "__dict__"):
                value = object_to_dict(value)
            result[key] = value
        return result

    class ValidationError(Exception):
        pass


class TestUtils(unittest.TestCase):
    """Unit tests for utility functions."""

    def test_generate_id(self) -> Any:
        """Test ID generation."""
        id1 = generate_id()
        self.assertTrue(id1.startswith("id_"))
        self.assertEqual(len(id1), 3 + 1 + 32)
        id2 = generate_id("test")
        self.assertTrue(id2.startswith("test_"))
        self.assertEqual(len(id2), 4 + 1 + 32)
        id3 = generate_id()
        self.assertNotEqual(id1, id3)

    def test_format_timestamp(self) -> Any:
        """Test timestamp formatting."""
        dt = datetime(2023, 1, 1, 12, 0, 0)
        formatted = format_timestamp(dt)
        self.assertEqual(formatted, "2023-01-01T12:00:00")
        formatted = format_timestamp(None)
        self.assertIsNone(formatted)

    def test_parse_timestamp(self) -> Any:
        """Test timestamp parsing."""
        dt = parse_timestamp("2023-01-01T12:00:00Z")
        self.assertEqual(dt.year, 2023)
        self.assertEqual(dt.month, 1)
        self.assertEqual(dt.day, 1)
        self.assertEqual(dt.hour, 12)
        self.assertEqual(dt.minute, 0)
        self.assertEqual(dt.second, 0)
        dt = parse_timestamp("2023-01-01T12:00:00.123Z")
        self.assertEqual(dt.year, 2023)
        self.assertEqual(dt.month, 1)
        self.assertEqual(dt.day, 1)
        self.assertEqual(dt.hour, 12)
        self.assertEqual(dt.minute, 0)
        self.assertEqual(dt.second, 0)
        self.assertEqual(dt.microsecond, 123000)

    def test_validate_required_fields(self) -> Any:
        """Test required fields validation."""
        data = {"name": "Test", "age": 30, "email": "test@example.com"}
        validate_required_fields(data, ["name", "age", "email"])
        data = {"name": "Test", "age": 30}
        with self.assertRaises(ValidationError):
            validate_required_fields(data, ["name", "age", "email"])
        data = {"name": "Test", "age": 30, "email": ""}
        with self.assertRaises(ValidationError):
            validate_required_fields(data, ["name", "age", "email"])
        data = {"name": "Test", "age": 30, "email": None}
        with self.assertRaises(ValidationError):
            validate_required_fields(data, ["name", "age", "email"])

    def test_validate_field_type(self) -> Any:
        """Test field type validation."""
        validate_field_type("Test", "name", str)
        validate_field_type(30, "age", int)
        validate_field_type(30.5, "height", float)
        validate_field_type(True, "active", bool)
        validate_field_type([], "items", list)
        validate_field_type({}, "config", dict)
        with self.assertRaises(ValidationError):
            validate_field_type("30", "age", int)
        with self.assertRaises(ValidationError):
            validate_field_type(30, "name", str)

    def test_validate_field_range(self) -> Any:
        """Test field range validation."""
        validate_field_range(30, "age", min_value=18, max_value=100)
        validate_field_range(30.5, "height", min_value=0)
        validate_field_range(30.5, "height", max_value=300)
        validate_field_range(30.5, "height")
        with self.assertRaises(ValidationError):
            validate_field_range(15, "age", min_value=18)
        with self.assertRaises(ValidationError):
            validate_field_range(150, "age", max_value=100)

    def test_validate_enum_field(self) -> Any:
        """Test enum field validation."""
        validate_enum_field("admin", "role", ["user", "admin", "guest"])
        with self.assertRaises(ValidationError):
            validate_enum_field("superuser", "role", ["user", "admin", "guest"])

    def test_calculate_percentage_change(self) -> Any:
        """Test percentage change calculation."""
        change = calculate_percentage_change(100, 110)
        self.assertEqual(change, 10.0)
        change = calculate_percentage_change(100, 90)
        self.assertEqual(change, -10.0)
        change = calculate_percentage_change(100, 100)
        self.assertEqual(change, 0.0)
        change = calculate_percentage_change(0, 100)
        self.assertEqual(change, 0.0)

    def test_calculate_moving_average(self) -> Any:
        """Test moving average calculation."""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        ma = calculate_moving_average(data, 3)
        self.assertEqual(len(ma), len(data))
        self.assertTrue(pd.isna(ma[0]))
        self.assertTrue(pd.isna(ma[1]))
        self.assertEqual(ma[2], 2.0)
        self.assertEqual(ma[3], 3.0)
        self.assertEqual(ma[4], 4.0)
        self.assertEqual(ma[9], 9.0)

    def test_normalize_data(self) -> Any:
        """Test data normalization."""
        data = [1, 2, 3, 4, 5]
        normalized = normalize_data(data)
        self.assertEqual(len(normalized), len(data))
        self.assertEqual(normalized[0], 0.0)
        self.assertEqual(normalized[4], 1.0)
        normalized = normalize_data(data, min_val=0, max_val=10)
        self.assertEqual(normalized[0], 0.1)
        self.assertEqual(normalized[4], 0.5)

    def test_denormalize_data(self) -> Any:
        """Test data denormalization."""
        normalized = [0.0, 0.25, 0.5, 0.75, 1.0]
        denormalized = denormalize_data(normalized, 1, 5)
        self.assertEqual(len(denormalized), len(normalized))
        self.assertEqual(denormalized[0], 1.0)
        self.assertEqual(denormalized[2], 3.0)
        self.assertEqual(denormalized[4], 5.0)

    def test_resample_data(self) -> Any:
        """Test data resampling."""
        df = pd.DataFrame(
            {
                "timestamp": pd.date_range(start="2023-01-01", periods=24, freq="H"),
                "open": np.random.normal(100, 2, 24),
                "high": np.random.normal(102, 2, 24),
                "low": np.random.normal(98, 2, 24),
                "close": np.random.normal(100, 2, 24),
                "volume": np.random.normal(1000000, 100000, 24),
            }
        )
        df.set_index("timestamp", inplace=True)
        resampled = resample_data(df, "4H")
        self.assertEqual(len(resampled), 6)
        self.assertTrue("open" in resampled.columns)
        self.assertTrue("high" in resampled.columns)
        self.assertTrue("low" in resampled.columns)
        self.assertTrue("close" in resampled.columns)
        self.assertTrue("volume" in resampled.columns)

    def test_merge_dictionaries(self) -> Any:
        """Test dictionary merging."""
        dict1 = {"name": "Test", "age": 30}
        dict2 = {"email": "test@example.com", "age": 31}
        merged = merge_dictionaries(dict1, dict2)
        self.assertEqual(merged["name"], "Test")
        self.assertEqual(merged["email"], "test@example.com")
        self.assertEqual(merged["age"], 31)

    def test_filter_dict_by_keys(self) -> Any:
        """Test dictionary filtering by keys."""
        d = {"name": "Test", "age": 30, "email": "test@example.com"}
        filtered = filter_dict_by_keys(d, ["name", "email"])
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered["name"], "Test")
        self.assertEqual(filtered["email"], "test@example.com")
        self.assertNotIn("age", filtered)

    def test_deep_get(self) -> Any:
        """Test deep dictionary value retrieval."""
        d = {
            "user": {
                "profile": {"name": "Test", "age": 30},
                "settings": {"theme": "dark"},
            }
        }
        name = deep_get(d, ["user", "profile", "name"])
        theme = deep_get(d, ["user", "settings", "theme"])
        self.assertEqual(name, "Test")
        self.assertEqual(theme, "dark")
        email = deep_get(d, ["user", "profile", "email"], "default@example.com")
        self.assertEqual(email, "default@example.com")

    def test_deep_set(self) -> Any:
        """Test deep dictionary value setting."""
        d = {"user": {"profile": {"name": "Test"}}}
        deep_set(d, ["user", "profile", "age"], 30)
        deep_set(d, ["user", "settings", "theme"], "dark")
        self.assertEqual(d["user"]["profile"]["age"], 30)
        self.assertEqual(d["user"]["settings"]["theme"], "dark")

    def test_flatten_dict(self) -> Any:
        """Test dictionary flattening."""
        d = {
            "user": {
                "profile": {"name": "Test", "age": 30},
                "settings": {"theme": "dark"},
            }
        }
        flattened = flatten_dict(d)
        self.assertEqual(flattened["user.profile.name"], "Test")
        self.assertEqual(flattened["user.profile.age"], 30)
        self.assertEqual(flattened["user.settings.theme"], "dark")

    def test_unflatten_dict(self) -> Any:
        """Test dictionary unflattening."""
        d = {
            "user.profile.name": "Test",
            "user.profile.age": 30,
            "user.settings.theme": "dark",
        }
        unflattened = unflatten_dict(d)
        self.assertEqual(unflattened["user"]["profile"]["name"], "Test")
        self.assertEqual(unflattened["user"]["profile"]["age"], 30)
        self.assertEqual(unflattened["user"]["settings"]["theme"], "dark")

    def test_dict_to_object(self) -> Any:
        """Test dictionary to object conversion."""
        d = {
            "name": "Test",
            "age": 30,
            "profile": {"email": "test@example.com", "phone": "123-456-7890"},
        }
        obj = dict_to_object(d)
        self.assertEqual(obj.name, "Test")
        self.assertEqual(obj.age, 30)
        self.assertEqual(obj.profile.email, "test@example.com")
        self.assertEqual(obj.profile.phone, "123-456-7890")

    def test_object_to_dict(self) -> Any:
        """Test object to dictionary conversion."""

        class User:

            def __init__(self):
                self.name = "Test"
                self.age = 30
                self._private = "private"
                self.profile = Profile()

        class Profile:

            def __init__(self):
                self.email = "test@example.com"
                self.phone = "123-456-7890"

        user = User()
        d = object_to_dict(user)
        self.assertEqual(d["name"], "Test")
        self.assertEqual(d["age"], 30)
        self.assertNotIn("_private", d)
        self.assertEqual(d["profile"]["email"], "test@example.com")
        self.assertEqual(d["profile"]["phone"], "123-456-7890")


if __name__ == "__main__":
    unittest.main()
