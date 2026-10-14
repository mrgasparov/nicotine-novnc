"""Run with NICOTINE_TEST_IMAGE=<built-image> to check VNC and GTK rendering."""

import json
import os
import subprocess
import time
import unittest
import uuid


STATE_SCRIPT = """
import json, os, socket, urllib.request
from pathlib import Path
os.environ['DISPLAY'] = ':1'
os.environ['HOME'] = '/data'
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
Gtk.init()
assert Gdk.Display.get_default().is_composited(), 'GTK popup transparency needs a compositor'
icon = next(Path('/usr/share/icons/Adwaita').rglob('dialog-warning-symbolic.svg'))
assert GdkPixbuf.Pixbuf.new_from_file(str(icon)), 'GTK SVG icon could not be decoded'
dialog = Gtk.Window()
dialog.set_titlebar(Gtk.HeaderBar())
dialog.realize()
border = dialog.get_style_context().get_border()
assert min(border.top, border.right, border.bottom, border.left) > 0, 'GTK window border missing'
dialog.destroy()
server = next(path.parent for path in Path('/proc').glob('[0-9]*/comm')
              if path.read_text().strip() == 'Xtigervnc')
def parent(path):
    return next(line.split()[1] for line in (path / 'status').read_text().splitlines()
                if line.startswith('PPid:'))
assert parent(server) == '1', 'Integrated display detached from Supervisor'
assert not any(path.read_text().strip() in ('Xvfb', 'X0tigervnc', 'x0vncserver')
               for path in Path('/proc').glob('[0-9]*/comm')), 'Separate screen capture is still running'
nicotine = next(path.parent for path in Path('/proc').glob('[0-9]*/comm')
                if path.read_text().strip() == 'nicotine')
assert b'supervisord' in Path('/proc/1/cmdline').read_bytes()
assert 'FATAL' not in Path('/tmp/supervisord.log').read_text()
listeners = []
for table in ('tcp', 'tcp6'):
    for line in (Path('/proc/net') / table).read_text().splitlines()[1:]:
        fields = line.split()
        if fields[3] == '0A':
            address, port = fields[1].split(':')
            listeners.append((address, int(port, 16)))
vnc_addresses = [address for address, port in listeners if port == 5901]
assert vnc_addresses and all(address in ('0100007F', '00000000000000000000000001000000')
                             for address in vnc_addresses), 'VNC exposed beyond loopback'
assert not any(port == 6001 for address, port in listeners), 'X11 TCP listening is enabled'
with socket.create_connection(('127.0.0.1', 5901), timeout=2) as connection:
    assert connection.recv(12).startswith(b'RFB ')
with urllib.request.urlopen('http://127.0.0.1:6080/vnc.html', timeout=2) as response:
    assert response.status == 200 and b'noVNC' in response.read(), 'Browser client unavailable'
print(json.dumps({'pid': int(server.name), 'nicotine_pid': int(nicotine.name)}))
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
        self.assertNotEqual(replacement["nicotine_pid"], initial["nicotine_pid"])
        time.sleep(3)
        self.assertEqual(self.wait_for_server()["pid"], replacement["pid"])


if __name__ == "__main__":
    unittest.main()
