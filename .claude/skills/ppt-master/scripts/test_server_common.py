#!/usr/bin/env python3
"""Regression tests for local preview identity, permissions and child cleanup."""
import errno
import json
import os
import socket
import subprocess
import tempfile
import urllib.error
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import server_common as common


class ServerLifecycleTests(unittest.TestCase):
    def response(self, **overrides):
        data = dict(status='ok', project=str(Path('.').resolve()),
                    service='svg-editor', pid=123)
        data.update(overrides)
        response = MagicMock(status=200)
        response.read.return_value = json.dumps(data).encode()
        response.__enter__.return_value = response
        return response

    def test_identity_checks_project_service_and_child(self):
        for overrides, expected in [({}, True), ({'project': '/other'}, False),
                                    ({'service': 'confirm-ui'}, False),
                                    ({'pid': 456}, False), ({'status': 'bad'}, False),
                                    ({'project': ''}, False)]:
            with self.subTest(overrides=overrides), patch.object(
                    common, '_health_opener', return_value=MagicMock(
                        open=MagicMock(return_value=self.response(**overrides)))):
                self.assertEqual(common.probe_server(5050, Path('.'),
                                 'svg-editor', expected_pid=123), expected)

    def test_permission_error_is_not_a_timeout(self):
        with patch.object(common, '_health_opener') as opener:
            opener.return_value.open.side_effect = PermissionError(errno.EACCES, 'denied')
            with self.assertRaises(common.LocalServerPermissionError):
                common.probe_server(5050, Path('.'), 'svg-editor')

    def test_refused_connection_is_retryable(self):
        with patch.object(common, '_health_opener') as opener:
            opener.return_value.open.side_effect = ConnectionRefusedError()
            self.assertFalse(common.probe_server(5050, Path('.'), 'svg-editor'))

    def test_windows_permission_wrapped_by_urlopen(self):
        reason = OSError('socket blocked')
        reason.winerror = 10013
        with patch.object(common, '_health_opener') as opener:
            opener.return_value.open.side_effect = urllib.error.URLError(reason)
            with self.assertRaisesRegex(common.LocalServerPermissionError, 'LOCAL_SERVER_PERMISSION'):
                common.probe_server(5050, Path('.'), 'svg-editor')

    def test_permission_during_port_probe_stops_immediately(self):
        with patch.object(common.socket, 'socket') as factory:
            probe = factory.return_value.__enter__.return_value
            probe.connect.side_effect = PermissionError(errno.EACCES, 'denied')
            with self.assertRaises(common.LocalServerPermissionError):
                common.find_free_port(5050)
            self.assertEqual(probe.connect.call_count, 1)

    def test_cleanup_only_releases_own_lock(self):
        proc = MagicMock(pid=123)
        proc.poll.return_value = None
        with patch.object(common, 'read_lock', return_value={'pid': 456}), \
                patch.object(common, 'clear_lock') as clear:
            common.stop_started_child(proc, Path('lock.json'))
            proc.terminate.assert_called_once()
            proc.wait.assert_called_once()
            clear.assert_not_called()

    def test_exhausted_ports_do_not_return_busy_port(self):
        with patch.object(common, 'port_has_listener', return_value=True):
            with self.assertRaises(OSError):
                common.find_free_port(5050, span=2)

    def test_posix_detaches_session(self):
        with patch.object(common.os, 'name', 'posix'), \
                patch.object(common.subprocess, 'Popen') as spawn:
            common.popen_detached(['python', 'server.py'])
            self.assertTrue(spawn.call_args.kwargs['start_new_session'])

    def test_windows_fallback_preserves_detachment(self):
        with patch.object(common.os, 'name', 'nt'), \
                patch.object(subprocess, 'DETACHED_PROCESS', 8, create=True), \
                patch.object(subprocess, 'CREATE_NEW_PROCESS_GROUP', 512, create=True), \
                patch.object(common.subprocess, 'Popen') as spawn:
            spawn.side_effect = [PermissionError('job restriction'), MagicMock()]
            common.popen_detached(['python', 'server.py'])
            flags = spawn.call_args.kwargs['creationflags']
            self.assertTrue(flags & subprocess.DETACHED_PROCESS)
            self.assertTrue(flags & subprocess.CREATE_NEW_PROCESS_GROUP)

    def test_cleanup_kills_only_unresponsive_owned_child(self):
        proc = MagicMock(pid=123)
        proc.poll.return_value = None
        proc.wait.side_effect = [subprocess.TimeoutExpired('child', 3), None]
        with patch.object(common, 'read_lock', return_value={'pid': 123}), \
                patch.object(common, 'clear_lock') as clear:
            common.stop_started_child(proc, Path('lock.json'))
            proc.kill.assert_called_once()
            clear.assert_called_once()

    def test_wait_rejects_other_child_then_succeeds(self):
        proc = MagicMock(pid=123)
        proc.poll.return_value = None
        with patch.object(common, 'probe_server', side_effect=[False, True]) as probe, \
                patch.object(common.time, 'sleep'):
            self.assertTrue(common.wait_for_server(5050, proc, Path('.'), 'svg-editor', 2))
            self.assertEqual(probe.call_count, 2)
            self.assertEqual(probe.call_args.kwargs['expected_pid'], 123)

    @unittest.skipUnless(os.environ.get('PREVIEW_INTEGRATION') == '1', 'opt-in local sockets')
    def test_real_launch_reuse_and_shutdown(self):
        import sys
        from urllib.request import urlopen
        scripts = Path(__file__).resolve().parent
        for service in ('svg_editor', 'confirm_ui'):
            with self.subTest(service=service), \
                    tempfile.TemporaryDirectory(prefix='preview 한글 ') as tmp, \
                    socket.socket() as occupied:
                occupied.bind(('127.0.0.1', 0))
                occupied.listen()
                busy_port = occupied.getsockname()[1]
                project = Path(tmp)
                (project / 'svg_output').mkdir()
                (project / 'confirm_ui').mkdir()
                (project / 'confirm_ui/recommendations.json').write_text('{}')
                command = [sys.executable, str(scripts / service / 'server.py'),
                           str(project), '--port', str(busy_port)]
                try:
                    result = subprocess.run(command + ['--daemon', '--no-browser'],
                                            capture_output=True, text=True, encoding='utf-8', timeout=30)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    lock_path = (project / 'live_preview/lock.json' if service == 'svg_editor'
                                 else project / '.confirm_ui.lock')
                    lock = json.loads(lock_path.read_text())
                    self.assertNotEqual(lock['port'], busy_port)
                    with urlopen(f"http://127.0.0.1:{lock['port']}/api/health") as response:
                        health = json.load(response)
                    self.assertEqual(health['pid'], lock['pid'])
                    self.assertEqual(Path(health['project']), project)
                    if service == 'svg_editor':
                        reused = subprocess.run(command + ['--daemon', '--no-browser'],
                                                capture_output=True, text=True, encoding='utf-8', timeout=15)
                        self.assertEqual(reused.returncode, 0, reused.stderr)
                        self.assertEqual(json.loads(lock_path.read_text())['pid'], lock['pid'])
                finally:
                    subprocess.run(command + ['--shutdown'], capture_output=True, timeout=15)


if __name__ == '__main__':
    unittest.main()
