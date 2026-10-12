"""Run with NICOTINE_TEST_IMAGE=<built-image> to check VNC and GTK rendering."""

import json
import os
import subprocess
import time
import unittest
import uuid


STATE_SCRIPT = """
import json, os, socket
from pathlib import Path
os.environ['DISPLAY'] = ':1'
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
Gtk.init()
assert Gdk.Display.get_default().is_composited(), 'GTK popup transparency needs a compositor'
icon = next(Path('/usr/share/icons/Adwaita').rglob('dialog-warning-symbolic.svg'))
assert GdkPixbuf.Pixbuf.new_from_file(str(icon)), 'GTK SVG icon could not be decoded'
server = next(path.parent for path in Path('/proc').glob('[0-9]*/comm')
              if path.read_text().strip() == 'X0tigervnc')
def parent(path):
    return next(line.split()[1] for line in (path / 'status').read_text().splitlines()
                if line.startswith('PPid:'))
wrapper = Path('/proc') / parent(server)
assert (wrapper / 'comm').read_text().strip() == 'x0vncserver'
assert parent(wrapper) == '1', 'VNC wrapper detached from Supervisor'
assert b'supervisord' in Path('/proc/1/cmdline').read_bytes()
assert 'FATAL' not in Path('/tmp/supervisord.log').read_text()
with socket.create_connection(('127.0.0.1', 5901), timeout=2) as connection:
    assert connection.recv(12).startswith(b'RFB ')
print(json.dumps({'pid': int(server.name)}))
"""


@unittest.skipUnless(os.environ.get("NICOTINE_TEST_IMAGE"), "Set NICOTINE_TEST_IMAGE to run")
class ContainerRuntimeTests(unittest.TestCase):
    def docker(self, *args, check=True):
        return subprocess.run(
            ["docker", *args], check=check, capture_output=True, text=True, timeout=30,
        )

    def wait_for_server(self, previous_pid=None):
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            result = self.docker("exec", self.container, "python3", "-c", STATE_SCRIPT, check=False)
            if result.returncode == 0:
                state = json.loads(result.stdout)
                if state["pid"] != previous_pid:
                    return state
            time.sleep(1)
        self.fail(f"VNC did not become supervised and reachable: {result.stderr}")

    def test_real_vnc_server_stays_supervised_and_recovers(self):
        self.container = f"nicotine-vnc-test-{uuid.uuid4().hex[:12]}"
        self.docker(
            "run", "-d", "--name", self.container, "-e", "PUID=1000", "-e", "PGID=1000",
            os.environ["NICOTINE_TEST_IMAGE"],
        )
        self.addCleanup(self.docker, "rm", "-fv", self.container)
        initial = self.wait_for_server()
        # Give a detaching wrapper time to exit rather than checking only startup.
        time.sleep(3)
        self.assertEqual(self.wait_for_server()["pid"], initial["pid"])
        self.docker(
            "exec", self.container, "python3", "-c",
            f"import os, signal; os.kill({initial['pid']}, signal.SIGTERM)",
        )
        replacement = self.wait_for_server(previous_pid=initial["pid"])
        time.sleep(3)
        self.assertEqual(self.wait_for_server()["pid"], replacement["pid"])


if __name__ == "__main__":
    unittest.main()
