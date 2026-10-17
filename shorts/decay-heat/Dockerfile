# syntax=docker/dockerfile:1
FROM manimcommunity/manim@sha256:f18f53f2e4eaf2ea41713437d34363fb3f5cc6008b03fd798676ac0359396c3b
USER root
RUN --mount=type=secret,id=proxy_ca,required=true \
    apt-get -o Acquire::https::CaInfo=/run/secrets/proxy_ca update \
    && DEBIAN_FRONTEND=noninteractive apt-get -o Acquire::https::CaInfo=/run/secrets/proxy_ca install -y --no-install-recommends ffmpeg \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
USER manimuser
WORKDIR /manim
