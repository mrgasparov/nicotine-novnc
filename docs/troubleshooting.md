# Troubleshooting

## Browser access

Open `http://<docker-host>:6080`, or the host port you selected in your deployment. `NOVNC_PORT` controls the port inside the container. For example, `7080:6080` exposes the default internal port at `http://<docker-host>:7080`.

If the page cannot connect, check the container and its logs:

```bash
docker ps
docker logs nicotine
```

The example uses the Compose container name; substitute `nicotine-novnc` for the README's Docker CLI deployment. The integrated TigerVNC server provides both the virtual display and VNC endpoint, and Supervisor restarts failed desktop services. Persistent failures need investigation in the logs.

The browser endpoint has no authentication or TLS by default. Restrict access to a trusted network or use an authenticated HTTPS reverse proxy.

## Icons, menus, and black blocks

The image includes the SVG loader for GTK icons, a 24-bit virtual display, and Picom compositing for transparent menus. Picom retains full-frame repainting to address black blocks left behind by popup windows. TigerVNC provides the display and VNC endpoint directly, avoiding a separate screen-capture process. VNC updates are capped at 30 per second. Full-frame compositing still favors reliable rendering and may use more CPU than incremental repainting.

After updating, recreate the container and reload the browser page. If artifacts remain, check `docker logs` for errors from `picom` or `vncserver`. Include your image tag, browser, desktop resolution, and a screenshot when reporting a problem.

## Slow UI on a NAS

The image uses an integrated TigerVNC display rather than Xvfb plus a separate VNC capture process. This removes the separate screen-reading stage; the actual improvement depends on the NAS, workload, and network. Keep `RESOLUTION=1280x720` when testing responsiveness on lower-powered devices.

Compare CPU and memory use with `docker stats nicotine` while scrolling the same list or opening the same menus. If accessing the UI over a fast local network, try `http://<docker-host>:6080/vnc.html?compression=1&quality=6` to reduce VNC compression work at the cost of more network traffic.

Restarting the integrated display also disconnects the graphical application and restarts its UI. Reconnect the browser if needed. Avoid restarting the display during active transfers when testing.

## Dialog placement, closing, and borders

The main window fills the desktop. Openbox centers dialog windows and provides decorations with a mouse-operated close button. GTK dialogs may use their own title bars. Open About to check placement and closing.

The default GTK stylesheet adds a 2-pixel border to windows with GTK client-side decorations outside fullscreen mode. Picom also adds soft shadows. Startup copies the stylesheet to `/data/.config/gtk-4.0/gtk.css` only if no file or symlink already exists there.

If you have a custom stylesheet, merge the following rule into it and restart the container:

```css
window.csd:not(.fullscreen) {
  border: 2px solid alpha(currentColor, 0.4);
}
```

You can also edit that file to customize the border. Keep a backup of your styles before changing them.

## Download permissions

Set both `PUID` and `PGID` to match a host user with write access to your mounted directories. Startup remaps the container user's IDs and changes ownership of `/data` only when both IDs are nonzero. It leaves the mounted `/downloads` ownership unchanged. The default `PUID=0` runs the desktop as root.

Choose folders under `/downloads` in Nicotine+ preferences. Paths inside the container must use the container mount path, rather than the host directory name.

## Incoming Soulseek connections

Choose a listening port within the published TCP range (`2234-2239` in the README examples). For incoming connections across your router, forward the chosen port to the Docker host and allow it through the host firewall. Nicotine+ 3.3.11 disables automatic router port forwarding in Docker.

The browser port and the Soulseek listening port serve different purposes; publishing port 6080 alone does not enable incoming Soulseek connections.

[Back to README](../README.md)
