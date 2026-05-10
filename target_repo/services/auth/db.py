_active_connections = 0


class FakeConnection:
    def __init__(self):
        self.closed = False

    def query_user(self, username):
        users = {
            "alice": {"id": 1, "username": "alice", "password": "correct-password"},
        }
        return users.get(username)

    def close(self):
        global _active_connections

        if not self.closed:
            self.closed = True
            _active_connections = max(_active_connections - 1, 0)


def get_connection():
    global _active_connections
    _active_connections += 1
    return FakeConnection()


def get_active_connections():
    return _active_connections


def reset_pool():
    global _active_connections
    _active_connections = 0
