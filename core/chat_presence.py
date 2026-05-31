import time
from threading import Lock


STALE_AFTER_SECONDS = 35

_lock = Lock()
_online_connections = {}


def _now():
    return time.time()


def _prune_locked():
    cutoff = _now() - STALE_AFTER_SECONDS
    stale_users = []
    for uid, connections in list(_online_connections.items()):
        fresh = {conn_id: seen_at for conn_id, seen_at in connections.items() if float(seen_at or 0) >= cutoff}
        if fresh:
            _online_connections[uid] = fresh
            continue
        stale_users.append(uid)
    for uid in stale_users:
        _online_connections.pop(uid, None)


def mark_user_connected(user_id, connection_id):
    uid = int(user_id or 0)
    conn_id = str(connection_id or "").strip()
    if uid <= 0 or not conn_id:
        return 0
    with _lock:
        _prune_locked()
        connections = dict(_online_connections.get(uid) or {})
        connections[conn_id] = _now()
        _online_connections[uid] = connections
        return len(connections)


def touch_user_connection(user_id, connection_id):
    uid = int(user_id or 0)
    conn_id = str(connection_id or "").strip()
    if uid <= 0 or not conn_id:
        return 0
    with _lock:
        _prune_locked()
        connections = dict(_online_connections.get(uid) or {})
        if not connections or conn_id not in connections:
            connections[conn_id] = _now()
        else:
            connections[conn_id] = _now()
        _online_connections[uid] = connections
        return len(connections)


def mark_user_disconnected(user_id, connection_id):
    uid = int(user_id or 0)
    conn_id = str(connection_id or "").strip()
    if uid <= 0 or not conn_id:
        return 0
    with _lock:
        _prune_locked()
        connections = dict(_online_connections.get(uid) or {})
        connections.pop(conn_id, None)
        if connections:
            _online_connections[uid] = connections
            return len(connections)
        _online_connections.pop(uid, None)
        return 0


def is_user_online(user_id):
    uid = int(user_id or 0)
    if uid <= 0:
        return False
    with _lock:
        _prune_locked()
        return bool(_online_connections.get(uid))


def get_online_user_ids():
    with _lock:
        _prune_locked()
        return sorted(_online_connections.keys())
