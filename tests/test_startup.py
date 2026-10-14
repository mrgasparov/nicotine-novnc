"""Host-side startup regression tests; requires Bash, Python 3 and envsubst."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("envsubst"), "envsubst is required")
class StartupTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.directory = Path(self.scratch.name)
        self.config = self.directory / "supervisord.conf"
        self.template = ROOT / "etc/supervisord.conf.template"
        self.initial_template = self.template.read_bytes()
        self.bin = self.directory / "bin"
        self.bin.mkdir()
        self.env = {
            "PATH": f"{self.bin}:{os.environ['PATH']}",
            "PIPX_HOME": "/app",
        }
        self.mock("getent", 'echo "root:x:0:0:root:/root:/bin/bash"')
        self.mock("supervisord", 'cat "$2"')
        # Redirect only filesystem destinations; keep the actual startup logic.
        source = (ROOT / "scripts/init.sh").read_text()
        source = source.replace("/etc/supervisord.conf.template", str(self.template))
        source = source.replace("/tmp/supervisord.conf", str(self.config))
        source = source.replace("/etc/nicotine/gtk.css", str(ROOT / "etc/nicotine/gtk.css"))
        source = source.replace("/data", str(self.directory / "data"))
        self.init = self.directory / "init.sh"
        self.init.write_text(source)

    def mock(self, name, body):
        path = self.bin / name
        path.write_text(f"#!/bin/bash\n{body}\n")
        path.chmod(0o755)

    def run_init(self, **variables):
        return subprocess.run(
            ["bash", str(self.init)],
            env={**self.env, **variables},
            capture_output=True,
            text=True,
        )

    def test_default_resolution_and_port(self):
        result = self.run_init()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("-geometry 1280x720 -depth 24", result.stdout)
        self.assertIn("--listen 6080", result.stdout)

    def test_rerender_uses_updated_values_without_changing_template(self):
        self.assertEqual(self.run_init().returncode, 0)
        result = self.run_init(RESOLUTION="1920x1080", NOVNC_PORT="7080")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("-geometry 1920x1080 -depth 24", result.stdout)
        self.assertIn("--listen 7080", result.stdout)
        self.assertEqual(self.template.read_bytes(), self.initial_template)

    def test_render_failure_does_not_launch_supervisor(self):
        self.mock("envsubst", "exit 17")
        self.mock("supervisord", "echo supervisor-started")
        result = self.run_init()
        self.assertEqual(result.returncode, 17)
        self.assertNotIn("supervisor-started", result.stdout)

    def test_existing_gtk_stylesheet_is_preserved(self):
        stylesheet = self.directory / "data/.config/gtk-4.0/gtk.css"
        stylesheet.parent.mkdir(parents=True)
        stylesheet.write_text("/* custom GTK style */")
        result = self.run_init()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(stylesheet.read_text(), "/* custom GTK style */")

    def test_user_lookup_failure_does_not_launch_supervisor(self):
        self.mock("getent", "exit 2")
        self.mock("supervisord", "echo supervisor-started")
        result = self.run_init()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("supervisor-started", result.stdout)

    def test_integrated_display_is_supervised_and_vnc_is_loopback_only(self):
        result = self.run_init()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("command=/usr/bin/Xtigervnc :1", result.stdout)
        self.assertIn("-rfbport 5901 -localhost -SecurityTypes None -nolisten tcp", result.stdout)
        self.assertIn("-FrameRate 30", result.stdout)
        self.assertNotIn("Xvfb", result.stdout)
        self.assertNotIn("start-vnc.sh", result.stdout)


if __name__ == "__main__":
    unittest.main()
