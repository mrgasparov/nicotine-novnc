FROM debian:trixie-slim

ARG NICOTINE_VERSION=3.3.11
ARG NOVNC_VERSION=1.7.0
ARG WEBSOCKIFY_VERSION=0.13.0

# Keep the existing application path used by the Supervisor template.
ENV PIPX_HOME=/app

# Use Debian's GTK bindings rather than compiling PyGObject and its dependencies.
# Install, download and clean up together to keep package caches and archives out of layers.
RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  gettext \
  gir1.2-adw-1 \
  gir1.2-gspell-1 \
  gir1.2-gtk-4.0 \
  librsvg2-common \
  net-tools \
  openbox \
  picom \
  python3 \
  python3-cairo \
  python3-gdbm \
  python3-gi \
  python3-gi-cairo \
  python3-venv \
  supervisor \
  tigervnc-scraping-server \
  x11-utils \
  xvfb && \
  mkdir /usr/share/novnc && \
  curl -fL# https://github.com/novnc/noVNC/archive/refs/tags/v${NOVNC_VERSION}.tar.gz -o /tmp/novnc.tar.gz && \
  tar -xf /tmp/novnc.tar.gz --strip-components=1 -C /usr/share/novnc && \
  mkdir /usr/share/novnc/utils/websockify && \
  curl -fL# https://github.com/novnc/websockify/archive/refs/tags/v${WEBSOCKIFY_VERSION}.tar.gz -o /tmp/websockify.tar.gz && \
  tar -xf /tmp/websockify.tar.gz --strip-components=1 -C /usr/share/novnc/utils/websockify && \
  python3 -m venv --system-site-packages /app/venvs/nicotine-plus && \
  /app/venvs/nicotine-plus/bin/pip install --no-cache-dir nicotine-plus==${NICOTINE_VERSION} && \
  apt-get purge -y --auto-remove curl && \
  apt-get clean && \
  rm -rf /tmp/* /var/lib/apt/lists/* /var/tmp/*

RUN useradd -u 1000 -U -d /data -s /bin/false nicotine && \
  usermod -G users nicotine && \
  mkdir /downloads && \
  chown nicotine:nicotine /downloads && \
  chown -R nicotine:nicotine /app

COPY ./etc /etc
COPY ./usr /usr
COPY ./scripts /usr/local/bin
RUN chmod +x /usr/local/bin/init.sh /usr/local/bin/start-vnc.sh

EXPOSE 6080/tcp
VOLUME ["/data","/downloads"]

CMD ["/usr/local/bin/init.sh"]
