# Development

## Build locally

Use a running Docker-compatible engine. On macOS with Colima, start it with `colima start` before building.

```bash
docker build -t nicotine-novnc:test .
docker run -d \
  --name nicotine-test \
  -e PUID=1000 \
  -e PGID=1000 \
  -p 127.0.0.1:6080:6080 \
  nicotine-novnc:test
```

Open `http://localhost:6080`. This preview uses Docker-managed volumes for `/data` and `/downloads`; mount host directories as shown in the [README](../README.md) for your regular deployment. Publish a Soulseek listening port as well if testing incoming connections.

The Dockerfile pins Nicotine+ 3.3.11, noVNC 1.7.0, and websockify 0.13.0. Override `NICOTINE_VERSION`, `NOVNC_VERSION`, or `WEBSOCKIFY_VERSION` with `docker build --build-arg NAME=VERSION` to test another release. Update the README version table whenever the default pins change.

The base is Debian trixie-slim. GTK and Python bindings come from Debian packages; Nicotine+ runs in a virtual environment that can access those system packages. Downloads and package cleanup happen in the same build layer.

## Desktop components

| Component | Responsibility |
| --- | --- |
| `scripts/init.sh` | Initialize user settings and GTK CSS, render the Supervisor template, and run Supervisor as PID 1 |
| `etc/supervisord.conf.template` | Start and restart the display, VNC server, window manager, compositor, browser proxy, and Nicotine+ |
| `scripts/start-vnc.sh` | Wait for the display and run VNC in the foreground on loopback port 5901 with shared-memory capture disabled |
| Xvfb | Provide the virtual desktop at the configured resolution and 24-bit depth |
| Openbox / `etc/xdg/openbox/rc.xml` | Keep the main window fullscreen and center dialogs with close controls |
| Picom | Composite transparent popups with software XRender, full-frame repainting, and soft shadows |
| `etc/nicotine/gtk.css` | Supply the default GTK dialog border without overwriting saved user styles |
| noVNC / websockify | Serve the browser client and bridge WebSocket connections to VNC |

Nicotine+ uses GTK4 with the Cairo renderer. The VNC wrapper must retain `-fg`: without it, Debian's wrapper detaches and Supervisor loses control of the server process. Supervisor stops the whole VNC process group during shutdown.

## Verification

The host startup tests require Python 3, Bash, and `envsubst` (provided by gettext). Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

This runs seven startup tests and skips the container test. To include the container test against a built image, run:

```bash
NICOTINE_TEST_IMAGE=nicotine-novnc:test \
  PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

The container test starts a disposable container, checks SVG icon decoding, GTK compositing and borders, verifies VNC remains supervised and speaks RFB, and checks recovery after terminating the actual VNC server. It removes its test container and anonymous volumes afterward.

For browser verification, open menus and About, check icons and transparent backgrounds, close dialogs with the mouse, and look for repaint artifacts after overlapping windows. Soulseek login and file transfers require separate checks with an account; the automated tests do not cover them.

Release builds run from `v*` Git tags via `.github/workflows/docker-build.yml` and publish `linux/amd64`, `linux/arm64`, and `linux/arm/v7` images. The workflow does not currently run these tests on pull requests. Validate the supported architectures when changing runtime dependencies.

## Screenshots

The README references `docs/nicotine-novnc-welcome.png` and `docs/nicotine-novnc-setup-1.png` through `docs/nicotine-novnc-setup-4.png`. Replace those files to refresh the screenshots without changing links. Capture the desktop, opening Preferences, account/port settings, download paths, and shared folders respectively. Hide credentials and private file names before committing screenshots.

[Back to README](../README.md)
