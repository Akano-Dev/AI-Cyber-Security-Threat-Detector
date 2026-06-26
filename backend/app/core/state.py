"""Shared in-memory runtime state (singletons)."""

# IPs blocked across this process. Loaded from the DB at startup and kept in sync.
# NOTE: in-memory only — Phase 5 moves this to Redis so multiple workers share it.
blocklist: set[str] = set()
