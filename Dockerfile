FROM debian:sid-slim

ARG NICOTINE_VERSION=3.3.10
ARG NOVNC_VERSION=1.6.0
ARG WEBSOCKIFY_VERSION=0.13.0

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
  mkdir /downloads && \
  chown nicotine:nicotine /downloads

ENV PIPX_HOME=/app

RUN apt-get install -y \
  gir1.2-adw-1 \
  gir1.2-gspell-1 \
  gir1.2-gtk-4.0 \
  libcairo2-dev \
  libgirepository-2.0-dev \
  libglib2.0-dev \
  libgtk-4-dev \
  python3 \
  python3-dev \
  python3-gdbm \
  python3-gi \
  meson \
  pipx

# install ninja-build using apt because pipx fails to build the package on ARM

RUN pipx install nicotine-plus==${NICOTINE_VERSION}

RUN chown -R nicotine:nicotine /app

RUN apt-get --purge remove -y \
  curl \
  libcairo2-dev \
  libgirepository-2.0-dev \
  libglib2.0-dev \
  libgtk-4-dev \
  python3-dev \
  meson \
  pipx && \
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
VOLUME ["/data","/downloads"]

CMD ["/bin/bash", "-c", "/tmp/init.sh;/usr/bin/supervisord -c /etc/supervisord.conf"]