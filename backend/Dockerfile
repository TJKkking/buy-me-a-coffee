# Use Python 3.12 slim base
FROM --platform=linux/amd64 python:3.12-slim

# Build-time args to allow overriding mirrors
ARG PIP_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"
ARG APT_MIRROR="mirrors.tuna.tsinghua.edu.cn"

ENV PYTHONUNBUFFERED=1
ENV PIP_INDEX_URL=${PIP_INDEX_URL}

WORKDIR /app

# Try to switch apt sources to a China mirror (best-effort), then install build deps
RUN set -eux; \
    sed -i "s|deb.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources || true; \
    sed -i "s|security.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources || true; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       libpq-dev \
       ca-certificates \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps first for better caching (use China PyPI by default)
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -i "$PIP_INDEX_URL" -r /app/requirements.txt
    
# 探针
RUN pip3 config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip3 config set install.trusted-host mirrors.aliyun.com
RUN pip3 install aliyun-bootstrap
RUN aliyun-bootstrap -a install

# Copy project
COPY . /app

# Labels
LABEL org.opencontainers.image.title="buy-me-a-coffee"

