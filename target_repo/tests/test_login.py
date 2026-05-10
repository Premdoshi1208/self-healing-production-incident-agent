from services.auth.db import get_active_connections, reset_pool
from services.auth.login import login


def setup_function():
    reset_pool()


def test_successful_login_closes_connection():
    result = login("alice", "correct-password")

    assert result["ok"] is True
    assert get_active_connections() == 0


def test_unknown_user_closes_connection():
    result = login("missing-user", "whatever")

    assert result["ok"] is False
    assert get_active_connections() == 0


def test_bad_password_closes_connection():
    result = login("alice", "wrong-password")

    assert result["ok"] is False
    assert get_active_connections() == 0
