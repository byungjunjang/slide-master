#!/usr/bin/env python3
"""
PPT Master - Local Preview Server Helpers

Shared per-project mutual-exclusion (lock) and liveness helpers for the local
Flask preview servers (`svg_editor/server.py`, `confirm_ui/server.py`). Each
server keeps its own lock filename and Flask app; this module owns only the
cross-platform process-liveness check and the claim/read/release lock logic so
the two servers cannot drift apart.

Usage:
    from server_common import process_alive, read_lock, lock_pid, claim_lock, release_lock, clear_lock, find_free_port

Dependencies:
    None (only uses standard library)
"""

import json
import errno
import logging
import os
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional


class LocalServerPermissionError(PermissionError):
    """The host denied local sockets; retry through the host permission flow."""


def _permission_denied(exc: BaseException) -> bool:
    reason = getattr(exc, 'reason', exc)
    return (isinstance(reason, PermissionError)
            or getattr(reason, 'errno', None) in (errno.EACCES, errno.EPERM)
            or getattr(reason, 'winerror', None) in (5, 10013))


def _permission_error(exc: BaseException) -> LocalServerPermissionError:
    return LocalServerPermissionError(
        'LOCAL_SERVER_PERMISSION: local sockets are blocked. Use the host\'s '
        'authorized execution/approval flow; do not change firewall settings. '
        f'Original error: {exc}')


def _health_opener():
    # Loopback must not depend on the user's HTTP proxy configuration.
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def probe_server(port: int, project: Path, service: str,
                 expected_pid: Optional[int] = None) -> bool:
    """Verify server identity, not just a listening PID or HTTP status."""
    try:
        with _health_opener().open(
                f'http://127.0.0.1:{port}/api/health', timeout=1) as response:
            if response.status != 200:
                return False
            data = json.loads(response.read())
        if (not isinstance(data, dict) or not isinstance(data.get('project'), str)
                or not data['project']):
            return False
        # Existing pre-upgrade sessions may omit service and pid.
        legacy_service = 'svg-editor' if 'svg_output' in data else 'confirm-ui'
        return (data.get('status') == 'ok'
                and data.get('service', legacy_service) == service
                and Path(data.get('project', '')).resolve() == project.resolve()
                and (expected_pid is None or data.get('pid') == expected_pid))
    except (OSError, urllib.error.URLError) as exc:
        if _permission_denied(exc):
            raise _permission_error(exc) from exc
        return False
    except (ValueError, TypeError):
        return False


def wait_for_server(port: int, proc: subprocess.Popen, project: Path,
                    service: str, timeout: float) -> bool:
    """Wait for this child; permission failures terminate the wait immediately."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return False
        if probe_server(port, project, service, expected_pid=proc.pid):
            return True
        time.sleep(0.2)
    return False


def stop_started_child(proc: subprocess.Popen, lock_file: Path) -> None:
    """Clean up only the child owned by this failed launch, never a reused PID."""
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)
    if lock_pid(read_lock(lock_file)) == proc.pid:
        clear_lock(lock_file)


def port_has_listener(host: str, port: int, timeout: float = 0.3) -> bool:
    """Return True if a server is actively accepting connections on host:port.

    A bind probe alone is unreliable on Windows: with ``SO_REUSEADDR`` set, the
    OS lets a second socket bind a port that another process is *actively
    listening* on, so a successful bind does NOT prove the port is free. A
    successful TCP connect, by contrast, proves something is already serving
    there. ``find_free_port`` uses this to skip such ports so a fresh launch
    (a new project, or a relaunch) never silently collides with a preview /
    confirm server left running from an earlier session.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(timeout)
        try:
            probe.connect((host, port))
            return True
        except OSError as exc:
            if _permission_denied(exc):
                raise _permission_error(exc) from exc
            return False


def find_free_port(preferred: int, host: str = '127.0.0.1', span: int = 50) -> int:
    """Return ``preferred`` if it is genuinely free, else the next free port
    within ``span``. Lets a new project's UI server coexist with another
    project's server already holding the default port, instead of crashing on
    bind or — worse, on Windows — binding the same port a stale server is still
    serving. A port is "free" only when nothing is actively listening on it
    (connect probe) AND it is bindable. Falls back to ``preferred`` if the whole
    span is taken (let the caller's bind surface it).
    """
    for port in range(preferred, preferred + span):
        # Windows SO_REUSEADDR makes bind() succeed on an actively-served port,
        # so an explicit connect probe is what actually detects a live server.
        if port_has_listener(host, port):
            continue
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind((host, port))
                return port
            except OSError as exc:
                if _permission_denied(exc):
                    raise _permission_error(exc) from exc
                continue
    raise OSError(f'No available loopback port in {preferred}..{preferred + span - 1}')


def popen_detached(
    args: list[str],
    *,
    logger: Optional[logging.Logger] = None,
    **kwargs: object,
) -> subprocess.Popen:
    """Start a long-running child process detached from the caller.

    Windows hosts such as terminal sandboxes may place child processes in the
    caller's Job Object. ``CREATE_BREAKAWAY_FROM_JOB`` lets the local UI server
    survive after the launcher command returns; when that flag is forbidden, the
    function falls back to the previous detached-process flags.
    """
    if os.name != 'nt':
        return subprocess.Popen(args, start_new_session=True, **kwargs)

    base_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    breakaway_flag = getattr(subprocess, 'CREATE_BREAKAWAY_FROM_JOB', 0x01000000)
    try:
        return subprocess.Popen(
            args,
            creationflags=base_flags | breakaway_flag,
            **kwargs,
        )
    except OSError as exc:
        if logger is not None:
            logger.warning(
                'Windows process breakaway failed; falling back to detached '
                'process-group launch (%s)',
                exc,
            )
        return subprocess.Popen(args, creationflags=base_flags, **kwargs)


def process_alive(pid: object) -> bool:
    """Return True if a process with this pid is reachable.

    On POSIX, ``os.kill(pid, 0)`` succeeds when the process exists even without
    permission to signal it; ``PermissionError`` therefore still counts as
    alive. On Windows there is no ``os.kill(pid, 0)`` equivalent, so probe via
    ``OpenProcess`` + ``WaitForSingleObject``.
    """
    try:
        pid_int = int(pid)
    except (TypeError, ValueError):
        return False
    if pid_int <= 0:
        return False
    if os.name == 'nt':
        import ctypes
        import ctypes.wintypes

        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel32.OpenProcess.argtypes = [
            ctypes.wintypes.DWORD,
            ctypes.wintypes.BOOL,
            ctypes.wintypes.DWORD,
        ]
        kernel32.OpenProcess.restype = ctypes.wintypes.HANDLE
        kernel32.WaitForSingleObject.argtypes = [
            ctypes.wintypes.HANDLE,
            ctypes.wintypes.DWORD,
        ]
        kernel32.WaitForSingleObject.restype = ctypes.wintypes.DWORD
        kernel32.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
        kernel32.CloseHandle.restype = ctypes.wintypes.BOOL

        process_query_limited_information = 0x1000
        synchronize = 0x00100000
        wait_timeout = 0x00000102
        wait_object_0 = 0x00000000
        wait_failed = 0xFFFFFFFF

        handle = kernel32.OpenProcess(
            process_query_limited_information | synchronize,
            False,
            pid_int,
        )
        if not handle:
            return ctypes.get_last_error() == 5  # ERROR_ACCESS_DENIED
        try:
            result = kernel32.WaitForSingleObject(handle, 0)
            if result == wait_timeout:
                return True
            if result in (wait_object_0, wait_failed):
                return False
            return False
        finally:
            kernel32.CloseHandle(handle)

    try:
        os.kill(pid_int, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def read_lock(lock_file: Path) -> Optional[dict]:
    """Read a lock file, returning the lock dict or None if absent/corrupt."""
    try:
        data = json.loads(lock_file.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def lock_pid(lock: Optional[dict]) -> int:
    """Return a valid pid from a lock dict, or 0 if absent/corrupt."""
    if not lock:
        return 0
    raw_pid = lock.get('pid', 0)
    if isinstance(raw_pid, bool):
        return 0
    if isinstance(raw_pid, int):
        return raw_pid if raw_pid > 0 else 0
    if isinstance(raw_pid, str) and raw_pid.strip().isdigit():
        return int(raw_pid.strip())
    return 0


def claim_lock(lock_file: Path, port: int) -> Optional[dict]:
    """Try to claim the per-project preview slot.

    Returns ``None`` on success. If another live process already holds the
    slot, returns the existing lock dict (caller surfaces it as an error).
    A stale lock (pointing at a dead pid) is silently overwritten.
    """
    existing = read_lock(lock_file)
    if existing and process_alive(lock_pid(existing)):
        return existing
    lock_file.write_text(
        json.dumps({'pid': os.getpid(), 'port': port}),
        encoding='utf-8',
    )
    return None


def release_lock(lock_file: Path) -> None:
    """Best-effort cleanup: only delete the lock if it still names *us*."""
    try:
        current = read_lock(lock_file)
        if lock_pid(current) == os.getpid():
            lock_file.unlink(missing_ok=True)
    except OSError:
        pass


def clear_lock(lock_file: Path) -> None:
    """Best-effort cleanup for a lock already proven stale by the caller."""
    try:
        lock_file.unlink(missing_ok=True)
    except OSError:
        pass
