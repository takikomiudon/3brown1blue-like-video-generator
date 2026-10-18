ARG MANIM_BASE_IMAGE=manimcommunity/manim:v0.20.1
FROM ${MANIM_BASE_IMAGE}

USER root

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER manimuser
WORKDIR /manim
