"""Ensure the two-worker adapters stop cleanly and fail if a worker exits."""
from pathlib import Path
import os
import selectors
import shutil
import signal
import subprocess
import time
import unittest

PHP = shutil.which('php')
SUPPORTED = bool(PHP) and os.name == 'posix' and subprocess.run(
    [PHP, '-r', 'exit(extension_loaded("pcntl") && extension_loaded("posix") ? 0 : 1);'],
    capture_output=True,
).returncode == 0
COMMON = Path(__file__).resolve().parents[1] / 'common' / 'async.php'


@unittest.skipUnless(SUPPORTED, 'Requires PHP CLI with pcntl and posix')
class WorkerTest(unittest.TestCase):
    def launch(self, body):
        code = 'require ' + repr(str(COMMON)) + '; benchWorkers(static function (): void {' + body + '});'
        process = subprocess.Popen([PHP, '-r', code], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True, bufsize=0)
        self.addCleanup(self.cleanup, process)
        return process

    @staticmethod
    def cleanup(process):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate(timeout=3)
        process.stdout.close()
        process.stderr.close()

    @unittest.skipUnless(Path('/proc/self/status').exists(), 'Signal-handler readiness check requires Linux procfs')
    def test_signals_interrupt_parent_wait_and_stop_both_workers(self):
        for sig in [signal.SIGTERM, signal.SIGINT]:
            with self.subTest(signal=sig):
                process = self.launch('echo "ready\\n"; while (true) { usleep(10000); }')
                deadline = time.monotonic() + 3
                ready = b''
                with selectors.DefaultSelector() as selector:
                    selector.register(process.stdout, selectors.EVENT_READ)
                    while ready.count(b'\n') < 2 and time.monotonic() < deadline:
                        if selector.select(timeout=max(0, deadline - time.monotonic())):
                            data = os.read(process.stdout.fileno(), 1000)
                            if not data:
                                break
                            ready += data
                self.assertEqual(ready.count(b'\n'), 2, 'Both workers must start')
                # Children can print before the parent installs handlers; don't signal that startup gap.
                expected = (1 << (signal.SIGTERM - 1)) | (1 << (signal.SIGINT - 1))
                caught = 0
                while time.monotonic() < deadline:
                    status = Path(f'/proc/{process.pid}/status').read_text()
                    caught = int(next(line.split()[1] for line in status.splitlines() if line.startswith('SigCgt:')), 16)
                    if caught & expected == expected:
                        break
                    time.sleep(.001)
                self.assertEqual(caught & expected, expected, 'Parent signal handlers must be ready')
                process.send_signal(sig)
                self.assertEqual(process.wait(timeout=3), 0)

    def test_unexpected_worker_exit_fails_the_application(self):
        process = self.launch('return;')
        self.assertEqual(process.wait(timeout=3), 1)


if __name__ == '__main__':
    unittest.main()
