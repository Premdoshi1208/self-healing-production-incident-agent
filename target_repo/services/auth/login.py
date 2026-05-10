from services.auth.db import get_connection


def login(username, password):
    conn = get_connection()
    user = conn.query_user(username)

    if not user:
        return {"ok": False, "reason": "invalid credentials"}

    if user["password"] != password:
        return {"ok": False, "reason": "invalid credentials"}

    conn.close()
    return {"ok": True, "user_id": user["id"]}
