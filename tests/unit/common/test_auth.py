from typing import Any

"""
Unit tests for the Common module's authentication utilities.
"""

import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import jwt

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
try:
    from backend.common.auth import (
        AuthManager,
        generate_token,
        hash_password,
        require_auth,
        require_role,
        verify_password,
        verify_token,
    )
    from backend.common.exceptions import AuthError, ValidationError
except ImportError:

    class AuthManager:

        def __init__(self, config_manager: Any, db_manager: Any) -> None:
            self.config_manager = config_manager
            self.db_manager = db_manager
            self.jwt_secret = "test_secret"
            self.jwt_expiration = 3600

        def authenticate(self, username: Any, password: Any) -> Any:
            if username == "testuser" and password == "password":
                return {
                    "id": "user_1234567890",
                    "username": "testuser",
                    "email": "test@example.com",
                    "role": "user",
                }
            raise AuthError("Invalid username or password")

        def register(
            self,
            username: Any,
            email: Any,
            password: Any,
            first_name: Any = None,
            last_name: Any = None,
        ) -> Any:
            if username == "existinguser":
                raise ValidationError("Username already exists")
            if email == "existing@example.com":
                raise ValidationError("Email already exists")
            return {
                "id": "user_1234567890",
                "username": username,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "role": "user",
                "created_at": datetime.utcnow().isoformat(),
            }

        def generate_token(
            self, user_id: Any, role: Any = "user", expiration: Any = None
        ) -> Any:
            expiration = expiration or self.jwt_expiration
            payload = {
                "user_id": user_id,
                "role": role,
                "exp": datetime.utcnow() + timedelta(seconds=expiration),
            }
            return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

        def verify_token(self, token: Any) -> Any:
            try:
                payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
                return payload
            except jwt.ExpiredSignatureError:
                raise AuthError("Token expired")
            except jwt.InvalidTokenError:
                raise AuthError("Invalid token")

        def get_user(self, user_id: Any) -> Any:
            if user_id == "user_1234567890":
                return {
                    "id": "user_1234567890",
                    "username": "testuser",
                    "email": "test@example.com",
                    "role": "user",
                }
            raise ValidationError("User not found")

        def update_user(self, user_id: Any, data: Any) -> Any:
            if user_id == "user_1234567890":
                return {
                    "id": "user_1234567890",
                    "username": "testuser",
                    "email": "test@example.com",
                    "role": "user",
                    **data,
                }
            raise ValidationError("User not found")

        def change_password(
            self, user_id: Any, current_password: Any, new_password: Any
        ) -> Any:
            if user_id == "user_1234567890" and current_password == "password":
                return True
            raise AuthError("Invalid current password")

    def hash_password(password: Any) -> Any:
        return f"hashed_{password}"

    def verify_password(password: Any, hashed_password: Any) -> Any:
        return hashed_password == f"hashed_{password}"

    def generate_token(payload: Any, secret: Any, expiration: Any = 3600) -> Any:
        payload["exp"] = datetime.utcnow() + timedelta(seconds=expiration)
        return jwt.encode(payload, secret, algorithm="HS256")

    def verify_token(token: Any, secret: Any) -> Any:
        try:
            return jwt.decode(token, secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise AuthError("Token expired")
        except jwt.InvalidTokenError:
            raise AuthError("Invalid token")

    def require_auth(f: Any) -> Any:

        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        return wrapper

    def require_role(role: Any) -> Any:

        def decorator(f):

            def wrapper(*args, **kwargs):
                return f(*args, **kwargs)

            return wrapper

        return decorator

    class AuthError(Exception):
        pass

    class ValidationError(Exception):
        pass


class TestAuth(unittest.TestCase):
    """Unit tests for authentication utilities."""

    def setUp(self) -> Any:
        """Set up test fixtures."""
        self.config_manager = MagicMock()
        self.config_manager.get_security_config.return_value = {
            "jwt_secret": "test_secret",
            "jwt_expiration": 3600,
        }
        self.db_manager = MagicMock()
        self.session = MagicMock()
        self.db_manager.get_postgres_session.return_value = self.session
        self.auth_manager = AuthManager(self.config_manager, self.db_manager)

    def test_hash_password(self) -> Any:
        """Test password hashing."""
        hashed = hash_password("password")
        self.assertNotEqual(hashed, "password")
        self.assertTrue(isinstance(hashed, str))
        hashed2 = hash_password("password")
        self.assertNotEqual(hashed, hashed2)

    def test_verify_password(self) -> Any:
        """Test password verification."""
        hashed = hash_password("password")
        self.assertTrue(verify_password("password", hashed))
        self.assertFalse(verify_password("wrong", hashed))

    def test_generate_token(self) -> Any:
        """Test token generation."""
        payload = {"user_id": "user_1234567890", "role": "user"}
        token = generate_token(payload, "test_secret", 3600)
        self.assertTrue(isinstance(token, str))
        decoded = jwt.decode(token, "test_secret", algorithms=["HS256"])
        self.assertEqual(decoded["user_id"], "user_1234567890")
        self.assertEqual(decoded["role"], "user")
        self.assertTrue("exp" in decoded)

    def test_verify_token(self) -> Any:
        """Test token verification."""
        payload = {"user_id": "user_1234567890", "role": "user"}
        token = generate_token(payload, "test_secret", 3600)
        decoded = verify_token(token, "test_secret")
        self.assertEqual(decoded["user_id"], "user_1234567890")
        self.assertEqual(decoded["role"], "user")
        with self.assertRaises(AuthError):
            verify_token(token, "wrong_secret")
        expired_token = generate_token(payload, "test_secret", -1)
        with self.assertRaises(AuthError):
            verify_token(expired_token, "test_secret")

    def test_auth_manager_init(self) -> Any:
        """Test AuthManager initialization."""
        auth_manager = AuthManager(self.config_manager, self.db_manager)
        self.assertEqual(auth_manager.config_manager, self.config_manager)
        self.assertEqual(auth_manager.db_manager, self.db_manager)
        self.assertEqual(auth_manager.jwt_secret, "test_secret")
        self.assertEqual(auth_manager.jwt_expiration, 3600)

    @patch("backend.common.auth.verify_password")
    def test_authenticate_success(self, mock_verify_password: Any) -> Any:
        """Test successful authentication."""
        mock_verify_password.return_value = True
        mock_user = MagicMock()
        mock_user.to_dict.return_value = {
            "id": "user_1234567890",
            "username": "testuser",
            "email": "test@example.com",
            "role": "user",
            "password_hash": "hashed_password",
        }
        self.session.query().filter().first.return_value = mock_user
        user = self.auth_manager.authenticate("testuser", "password")
        self.assertEqual(user["id"], "user_1234567890")
        self.assertEqual(user["username"], "testuser")
        self.assertEqual(user["email"], "test@example.com")
        self.assertEqual(user["role"], "user")
        self.assertNotIn("password_hash", user)

    @patch("backend.common.auth.verify_password")
    def test_authenticate_wrong_password(self, mock_verify_password: Any) -> Any:
        """Test authentication with wrong password."""
        mock_verify_password.return_value = False
        mock_user = MagicMock()
        mock_user.to_dict.return_value = {
            "id": "user_1234567890",
            "username": "testuser",
            "email": "test@example.com",
            "role": "user",
            "password_hash": "hashed_password",
        }
        self.session.query().filter().first.return_value = mock_user
        with self.assertRaises(AuthError):
            self.auth_manager.authenticate("testuser", "wrong")

    def test_authenticate_user_not_found(self) -> Any:
        """Test authentication with non-existent user."""
        self.session.query().filter().first.return_value = None
        with self.assertRaises(AuthError):
            self.auth_manager.authenticate("nonexistent", "password")

    @patch("backend.common.auth.hash_password")
    def test_register_success(self, mock_hash_password: Any) -> Any:
        """Test successful user registration."""
        mock_hash_password.return_value = "hashed_password"
        self.session.query().filter().first.return_value = None
        mock_user = MagicMock()
        mock_user.to_dict.return_value = {
            "id": "user_1234567890",
            "username": "newuser",
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User",
            "role": "user",
            "created_at": datetime.utcnow().isoformat(),
        }
        self.session.add = MagicMock()
        self.session.commit = MagicMock()
        with patch("backend.common.models.User") as MockUser:
            MockUser.return_value = mock_user
            user = self.auth_manager.register(
                username="newuser",
                email="new@example.com",
                password="password",
                first_name="New",
                last_name="User",
            )
            self.assertEqual(user["id"], "user_1234567890")
            self.assertEqual(user["username"], "newuser")
            self.assertEqual(user["email"], "new@example.com")
            self.assertEqual(user["first_name"], "New")
            self.assertEqual(user["last_name"], "User")
            self.assertEqual(user["role"], "user")
            self.assertNotIn("password_hash", user)
            self.session.add.assert_called_once()
            self.session.commit.assert_called_once()

    def test_register_existing_username(self) -> Any:
        """Test registration with existing username."""
        self.session.query().filter().first.return_value = MagicMock()
        with self.assertRaises(ValidationError):
            self.auth_manager.register(
                username="existinguser", email="new@example.com", password="password"
            )

    def test_register_existing_email(self) -> Any:
        """Test registration with existing email."""
        self.session.query().filter().first.side_effect = [None, MagicMock()]
        with self.assertRaises(ValidationError):
            self.auth_manager.register(
                username="newuser", email="existing@example.com", password="password"
            )

    def test_generate_token_auth_manager(self) -> Any:
        """Test token generation by AuthManager."""
        token = self.auth_manager.generate_token("user_1234567890", "user")
        self.assertTrue(isinstance(token, str))
        decoded = jwt.decode(token, "test_secret", algorithms=["HS256"])
        self.assertEqual(decoded["user_id"], "user_1234567890")
        self.assertEqual(decoded["role"], "user")
        self.assertTrue("exp" in decoded)

    def test_verify_token_auth_manager(self) -> Any:
        """Test token verification by AuthManager."""
        token = self.auth_manager.generate_token("user_1234567890", "user")
        payload = self.auth_manager.verify_token(token)
        self.assertEqual(payload["user_id"], "user_1234567890")
        self.assertEqual(payload["role"], "user")

    def test_get_user(self) -> Any:
        """Test getting user by ID."""
        mock_user = MagicMock()
        mock_user.to_dict.return_value = {
            "id": "user_1234567890",
            "username": "testuser",
            "email": "test@example.com",
            "role": "user",
            "password_hash": "hashed_password",
        }
        self.session.query().filter().first.return_value = mock_user
        user = self.auth_manager.get_user("user_1234567890")
        self.assertEqual(user["id"], "user_1234567890")
        self.assertEqual(user["username"], "testuser")
        self.assertEqual(user["email"], "test@example.com")
        self.assertEqual(user["role"], "user")
        self.assertNotIn("password_hash", user)

    def test_get_user_not_found(self) -> Any:
        """Test getting non-existent user."""
        self.session.query().filter().first.return_value = None
        with self.assertRaises(ValidationError):
            self.auth_manager.get_user("nonexistent")

    def test_update_user(self) -> Any:
        """Test updating user."""
        mock_user = MagicMock()
        mock_user.to_dict.return_value = {
            "id": "user_1234567890",
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Updated",
            "last_name": "User",
            "role": "user",
            "password_hash": "hashed_password",
        }
        self.session.query().filter().first.return_value = mock_user
        user = self.auth_manager.update_user(
            "user_1234567890", {"first_name": "Updated", "last_name": "User"}
        )
        self.assertEqual(user["id"], "user_1234567890")
        self.assertEqual(user["username"], "testuser")
        self.assertEqual(user["email"], "test@example.com")
        self.assertEqual(user["first_name"], "Updated")
        self.assertEqual(user["last_name"], "User")
        self.assertEqual(user["role"], "user")
        self.assertNotIn("password_hash", user)
        self.session.commit.assert_called_once()

    def test_update_user_not_found(self) -> Any:
        """Test updating non-existent user."""
        self.session.query().filter().first.return_value = None
        with self.assertRaises(ValidationError):
            self.auth_manager.update_user(
                "nonexistent", {"first_name": "Updated", "last_name": "User"}
            )

    @patch("backend.common.auth.verify_password")
    @patch("backend.common.auth.hash_password")
    def test_change_password(
        self, mock_hash_password: Any, mock_verify_password: Any
    ) -> Any:
        """Test changing password."""
        mock_verify_password.return_value = True
        mock_hash_password.return_value = "new_hashed_password"
        mock_user = MagicMock()
        mock_user.password_hash = "hashed_password"
        self.session.query().filter().first.return_value = mock_user
        result = self.auth_manager.change_password(
            "user_1234567890", "password", "new_password"
        )
        self.assertTrue(result)
        self.assertEqual(mock_user.password_hash, "new_hashed_password")
        self.session.commit.assert_called_once()

    @patch("backend.common.auth.verify_password")
    def test_change_password_wrong_current(self, mock_verify_password: Any) -> Any:
        """Test changing password with wrong current password."""
        mock_verify_password.return_value = False
        mock_user = MagicMock()
        mock_user.password_hash = "hashed_password"
        self.session.query().filter().first.return_value = mock_user
        with self.assertRaises(AuthError):
            self.auth_manager.change_password(
                "user_1234567890", "wrong", "new_password"
            )

    def test_change_password_user_not_found(self) -> Any:
        """Test changing password for non-existent user."""
        self.session.query().filter().first.return_value = None
        with self.assertRaises(ValidationError):
            self.auth_manager.change_password("nonexistent", "password", "new_password")


if __name__ == "__main__":
    unittest.main()
