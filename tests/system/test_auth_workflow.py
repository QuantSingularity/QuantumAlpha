"""
System tests for user authentication and authorization workflow.
"""

import os
import sys
import unittest
from typing import Any
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import requests

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
try:
    from backend.common.auth import AuthManager
    from backend.common.exceptions import AuthError, ValidationError
except ImportError:

    class AuthManager:
        pass

    class AuthError(Exception):
        pass

    class ValidationError(Exception):
        pass


class TestAuthWorkflow(unittest.TestCase):
    """System tests for user authentication and authorization workflow."""

    def setUp(self) -> Any:
        """Set up test fixtures."""
        self.config_manager = MagicMock()
        self.config_manager.get_security_config.return_value = {
            "jwt_secret": "test_secret",
            "jwt_expiration": 3600,
            "refresh_token_expiration": 86400,
        }
        self.db_manager = MagicMock()
        self.auth_manager = AuthManager(self.config_manager, self.db_manager)
        self.api_base_url = "http://localhost:8080/api"

    @patch("requests.post")
    def test_user_registration_login_workflow(self, mock_post: Any) -> Any:
        """Test user registration and login workflow."""
        register_url = f"{self.api_base_url}/auth/register"
        register_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Password123!",
            "first_name": "Test",
            "last_name": "User",
        }
        mock_register_response = MagicMock()
        mock_register_response.status_code = 201
        mock_register_response.json.return_value = {
            "id": "user_1234567890",
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "role": "user",
            "created_at": datetime.utcnow().isoformat(),
        }
        mock_post.return_value = mock_register_response
        response = requests.post(register_url, json=register_data)
        self.assertEqual(response.status_code, 201)
        user = response.json()
        self.assertEqual(user["username"], "testuser")
        self.assertEqual(user["email"], "test@example.com")
        self.assertEqual(user["role"], "user")
        login_url = f"{self.api_base_url}/auth/login"
        login_data = {"username": "testuser", "password": "Password123!"}
        mock_login_response = MagicMock()
        mock_login_response.status_code = 200
        mock_login_response.json.return_value = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl8xMjM0NTY3ODkwIiwicm9sZSI6InVzZXIiLCJleHAiOjE3MTY5MjMwMDB9.6J6vEwrKqZUF9aQQIkxHhOLvK6XnJJEj6xn2d-0g5Yk",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl8xMjM0NTY3ODkwIiwicm9sZSI6InVzZXIiLCJleHAiOjE3MTcwMDk0MDB9.8J8vEwrKqZUF9aQQIkxHhOLvK6XnJJEj6xn2d-0g5Yk",
            "user": {
                "id": "user_1234567890",
                "username": "testuser",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "role": "user",
            },
        }
        mock_post.return_value = mock_login_response
        response = requests.post(login_url, json=login_data)
        self.assertEqual(response.status_code, 200)
        auth_data = response.json()
        self.assertIn("access_token", auth_data)
        self.assertIn("refresh_token", auth_data)
        self.assertIn("user", auth_data)
        self.assertEqual(auth_data["user"]["username"], "testuser")
        access_token = auth_data["access_token"]
        with patch.object(self.auth_manager, "verify_token") as mock_verify:
            mock_verify.return_value = {
                "user_id": "user_1234567890",
                "role": "user",
                "exp": datetime.utcnow() + timedelta(hours=1),
            }
            payload = self.auth_manager.verify_token(access_token)
            self.assertEqual(payload["user_id"], "user_1234567890")
            self.assertEqual(payload["role"], "user")
            self.assertIn("exp", payload)

    @patch("requests.post")
    @patch("requests.get")
    def test_authenticated_api_access_workflow(
        self, mock_get: Any, mock_post: Any
    ) -> Any:
        """Test authenticated API access workflow."""
        login_url = f"{self.api_base_url}/auth/login"
        login_data = {"username": "testuser", "password": "Password123!"}
        mock_login_response = MagicMock()
        mock_login_response.status_code = 200
        mock_login_response.json.return_value = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl8xMjM0NTY3ODkwIiwicm9sZSI6InVzZXIiLCJleHAiOjE3MTY5MjMwMDB9.6J6vEwrKqZUF9aQQIkxHhOLvK6XnJJEj6xn2d-0g5Yk",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl8xMjM0NTY3ODkwIiwicm9sZSI6InVzZXIiLCJleHAiOjE3MTcwMDk0MDB9.8J8vEwrKqZUF9aQQIkxHhOLvK6XnJJEj6xn2d-0g5Yk",
            "user": {
                "id": "user_1234567890",
                "username": "testuser",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "role": "user",
            },
        }
        mock_post.return_value = mock_login_response
        response = requests.post(login_url, json=login_data)
        self.assertEqual(response.status_code, 200)
        auth_data = response.json()
        access_token = auth_data["access_token"]
        profile_url = f"{self.api_base_url}/users/profile"
        headers = {"Authorization": f"Bearer {access_token}"}
        mock_profile_response = MagicMock()
        mock_profile_response.status_code = 200
        mock_profile_response.json.return_value = {
            "id": "user_1234567890",
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "role": "user",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "preferences": {"theme": "light", "notifications_enabled": True},
        }
        mock_get.return_value = mock_profile_response
        response = requests.get(profile_url, headers=headers)
        self.assertEqual(response.status_code, 200)
        profile = response.json()
        self.assertEqual(profile["id"], "user_1234567890")
        self.assertEqual(profile["username"], "testuser")
        self.assertEqual(profile["email"], "test@example.com")
        self.assertIn("preferences", profile)
        mock_unauthorized_response = MagicMock()
        mock_unauthorized_response.status_code = 401
        mock_unauthorized_response.json.return_value = {
            "error": "Unauthorized",
            "message": "Authentication token is missing or invalid",
        }
        mock_get.return_value = mock_unauthorized_response
        response = requests.get(profile_url)
        self.assertEqual(response.status_code, 401)
        error = response.json()
        self.assertEqual(error["error"], "Unauthorized")

    @patch("requests.post")
    def test_token_refresh_workflow(self, mock_post: Any) -> Any:
        """Test token refresh workflow."""
        login_url = f"{self.api_base_url}/auth/login"
        login_data = {"username": "testuser", "password": "Password123!"}
        mock_login_response = MagicMock()
        mock_login_response.status_code = 200
        mock_login_response.json.return_value = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl8xMjM0NTY3ODkwIiwicm9sZSI6InVzZXIiLCJleHAiOjE3MTY5MjMwMDB9.6J6vEwrKqZUF9aQQIkxHhOLvK6XnJJEj6xn2d-0g5Yk",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl8xMjM0NTY3ODkwIiwicm9sZSI6InVzZXIiLCJleHAiOjE3MTcwMDk0MDB9.8J8vEwrKqZUF9aQQIkxHhOLvK6XnJJEj6xn2d-0g5Yk",
            "user": {
                "id": "user_1234567890",
                "username": "testuser",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "role": "user",
            },
        }
        mock_post.return_value = mock_login_response
        response = requests.post(login_url, json=login_data)
        self.assertEqual(response.status_code, 200)
        auth_data = response.json()
        refresh_token = auth_data["refresh_token"]
        refresh_url = f"{self.api_base_url}/auth/refresh"
        refresh_data = {"refresh_token": refresh_token}
        mock_refresh_response = MagicMock()
        mock_refresh_response.status_code = 200
        mock_refresh_response.json.return_value = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl8xMjM0NTY3ODkwIiwicm9sZSI6InVzZXIiLCJleHAiOjE3MTY5MjY2MDB9.7K7vFwrLqZUF9aQQIkxHhOLvK6XnJJEj6xn2d-0g5Yk",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl8xMjM0NTY3ODkwIiwicm9sZSI6InVzZXIiLCJleHAiOjE3MTcwMTMwMDB9.9K9vFwrLqZUF9aQQIkxHhOLvK6XnJJEj6xn2d-0g5Yk",
        }
        mock_post.return_value = mock_refresh_response
        response = requests.post(refresh_url, json=refresh_data)
        self.assertEqual(response.status_code, 200)
        refresh_data = response.json()
        self.assertIn("access_token", refresh_data)
        self.assertIn("refresh_token", refresh_data)
        new_access_token = refresh_data["access_token"]
        with patch.object(self.auth_manager, "verify_token") as mock_verify:
            mock_verify.return_value = {
                "user_id": "user_1234567890",
                "role": "user",
                "exp": datetime.utcnow() + timedelta(hours=1),
            }
            payload = self.auth_manager.verify_token(new_access_token)
            self.assertEqual(payload["user_id"], "user_1234567890")
            self.assertEqual(payload["role"], "user")
            self.assertIn("exp", payload)

    @patch("requests.post")
    @patch("requests.get")
    def test_role_based_access_control_workflow(
        self, mock_get: Any, mock_post: Any
    ) -> Any:
        """Test role-based access control workflow."""
        login_url = f"{self.api_base_url}/auth/login"
        login_data = {"username": "adminuser", "password": "AdminPass123!"}
        mock_admin_login_response = MagicMock()
        mock_admin_login_response.status_code = 200
        mock_admin_login_response.json.return_value = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl9hZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTcxNjkyMzAwMH0.7J7vEwrKqZUF9aQQIkxHhOLvK6XnJJEj6xn2d-0g5Yk",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl9hZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTcxNzAwOTQwMH0.9J9vEwrKqZUF9aQQIkxHhOLvK6XnJJEj6xn2d-0g5Yk",
            "user": {
                "id": "user_admin",
                "username": "adminuser",
                "email": "admin@example.com",
                "first_name": "Admin",
                "last_name": "User",
                "role": "admin",
            },
        }
        mock_post.return_value = mock_admin_login_response
        response = requests.post(login_url, json=login_data)
        self.assertEqual(response.status_code, 200)
        admin_auth_data = response.json()
        admin_token = admin_auth_data["access_token"]
        admin_url = f"{self.api_base_url}/admin/users"
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        mock_admin_response = MagicMock()
        mock_admin_response.status_code = 200
        mock_admin_response.json.return_value = {
            "users": [
                {
                    "id": "user_1234567890",
                    "username": "testuser",
                    "email": "test@example.com",
                    "role": "user",
                },
                {
                    "id": "user_admin",
                    "username": "adminuser",
                    "email": "admin@example.com",
                    "role": "admin",
                },
            ],
            "total": 2,
        }
        mock_get.return_value = mock_admin_response
        response = requests.get(admin_url, headers=admin_headers)
        self.assertEqual(response.status_code, 200)
        users_data = response.json()
        self.assertIn("users", users_data)
        self.assertEqual(users_data["total"], 2)
        login_data = {"username": "testuser", "password": "Password123!"}
        mock_user_login_response = MagicMock()
        mock_user_login_response.status_code = 200
        mock_user_login_response.json.return_value = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl8xMjM0NTY3ODkwIiwicm9sZSI6InVzZXIiLCJleHAiOjE3MTY5MjMwMDB9.6J6vEwrKqZUF9aQQIkxHhOLvK6XnJJEj6xn2d-0g5Yk",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl8xMjM0NTY3ODkwIiwicm9sZSI6InVzZXIiLCJleHAiOjE3MTcwMDk0MDB9.8J8vEwrKqZUF9aQQIkxHhOLvK6XnJJEj6xn2d-0g5Yk",
            "user": {
                "id": "user_1234567890",
                "username": "testuser",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "role": "user",
            },
        }
        mock_post.return_value = mock_user_login_response
        response = requests.post(login_url, json=login_data)
        self.assertEqual(response.status_code, 200)
        user_auth_data = response.json()
        user_token = user_auth_data["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        mock_forbidden_response = MagicMock()
        mock_forbidden_response.status_code = 403
        mock_forbidden_response.json.return_value = {
            "error": "Forbidden",
            "message": "Insufficient permissions to access this resource",
        }
        mock_get.return_value = mock_forbidden_response
        response = requests.get(admin_url, headers=user_headers)
        self.assertEqual(response.status_code, 403)
        error = response.json()
        self.assertEqual(error["error"], "Forbidden")

    @patch("requests.post")
    def test_password_change_workflow(self, mock_post: Any) -> Any:
        """Test password change workflow."""
        login_url = f"{self.api_base_url}/auth/login"
        login_data = {"username": "testuser", "password": "Password123!"}
        mock_login_response = MagicMock()
        mock_login_response.status_code = 200
        mock_login_response.json.return_value = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl8xMjM0NTY3ODkwIiwicm9sZSI6InVzZXIiLCJleHAiOjE3MTY5MjMwMDB9.6J6vEwrKqZUF9aQQIkxHhOLvK6XnJJEj6xn2d-0g5Yk",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl8xMjM0NTY3ODkwIiwicm9sZSI6InVzZXIiLCJleHAiOjE3MTcwMDk0MDB9.8J8vEwrKqZUF9aQQIkxHhOLvK6XnJJEj6xn2d-0g5Yk",
            "user": {
                "id": "user_1234567890",
                "username": "testuser",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "role": "user",
            },
        }
        mock_post.return_value = mock_login_response
        response = requests.post(login_url, json=login_data)
        self.assertEqual(response.status_code, 200)
        auth_data = response.json()
        access_token = auth_data["access_token"]
        change_password_url = f"{self.api_base_url}/auth/change-password"
        change_password_data = {
            "current_password": "Password123!",
            "new_password": "NewPassword456!",
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        mock_change_password_response = MagicMock()
        mock_change_password_response.status_code = 200
        mock_change_password_response.json.return_value = {
            "success": True,
            "message": "Password changed successfully",
        }
        mock_post.return_value = mock_change_password_response
        response = requests.post(
            change_password_url, json=change_password_data, headers=headers
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["success"])
        login_data = {"username": "testuser", "password": "NewPassword456!"}
        mock_new_login_response = MagicMock()
        mock_new_login_response.status_code = 200
        mock_new_login_response.json.return_value = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl8xMjM0NTY3ODkwIiwicm9sZSI6InVzZXIiLCJleHAiOjE3MTY5MjMwMDB9.6J6vEwrKqZUF9aQQIkxHhOLvK6XnJJEj6xn2d-0g5Yk",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl8xMjM0NTY3ODkwIiwicm9sZSI6InVzZXIiLCJleHAiOjE3MTcwMDk0MDB9.8J8vEwrKqZUF9aQQIkxHhOLvK6XnJJEj6xn2d-0g5Yk",
            "user": {
                "id": "user_1234567890",
                "username": "testuser",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "role": "user",
            },
        }
        mock_post.return_value = mock_new_login_response
        response = requests.post(login_url, json=login_data)
        self.assertEqual(response.status_code, 200)
        new_auth_data = response.json()
        self.assertIn("access_token", new_auth_data)
        self.assertIn("refresh_token", new_auth_data)
        self.assertIn("user", new_auth_data)


if __name__ == "__main__":
    unittest.main()
