FROM debian:bookworm-slim

ARG NICOTINE_VERSION=3.2.9
ARG NOVNC_VERSION=1.4.0
ARG WEBSOCKIFY_VERSION=0.11.0

RUN apt-get update && apt-get install -y --no-install-recommends \
  curl \
  gettext \
  net-tools \
  openbox \
  software-properties-common \
  supervisor \
  tigervnc-scraping-server \
  xvfb

RUN mkdir /usr/share/novnc && \
  curl -fL# https://github.com/novnc/noVNC/archive/refs/tags/v${NOVNC_VERSION}.tar.gz -o /tmp/novnc.tar.gz && \
  tar -xf /tmp/novnc.tar.gz --strip-components=1 -C /usr/share/novnc && \
  mkdir /usr/share/novnc/utils/websockify && \
  curl -fL# https://github.com/novnc/websockify/archive/refs/tags/v${WEBSOCKIFY_VERSION}.tar.gz -o /tmp/websockify.tar.gz && \
  tar -xf /tmp/websockify.tar.gz --strip-components=1 -C /usr/share/novnc/utils/websockify

RUN useradd -u 1000 -U -d /data -s /bin/false nicotine && \
  usermod -G users nicotine && \
  mkdir -p /data/.config/nicotine /downloads && \
  chown nicotine:nicotine /downloads && \
  ln -s /data/.config/nicotine /config

ENV PIPX_HOME=/app

RUN apt-get install -y \
  gir1.2-adw-1 \
  gir1.2-gspell-1 \
  gir1.2-gtk-4.0\
  libcairo2-dev \
  libgirepository1.0-dev \
  pipx \
  python3 \
  python3-dev \
  python3-gdbm \
  python3-gi && \
  pipx install nicotine-plus==${NICOTINE_VERSION}

RUN chown -R nicotine:nicotine /app

RUN apt-get --purge remove -y \
  curl \
  libcairo2-dev \
  libgirepository1.0-dev \
  pipx \
  python3-dev && \
  apt autoremove -y && \
  apt-get clean && \
  rm -rf \
  /tmp/* \
  /var/lib/apt/lists/* \
  /var/tmp/*

COPY ./etc /etc
COPY ./usr /usr
COPY ./scripts/init.sh /tmp/init.sh

EXPOSE 6080/tcp
VOLUME ["/config","/downloads"]

CMD ["/bin/bash", "-c", "/tmp/init.sh;/usr/bin/supervisord -c /etc/supervisord.conf"]