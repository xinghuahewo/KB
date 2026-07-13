# syntax=docker/dockerfile:1.7
FROM python:3.11.15-slim-bookworm@sha256:961f57b66f6aee85ae11272cca9219123a860ab20e2a09a1238f57e0df495825 AS builder

ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cu128
ARG DEBIAN_MIRROR=
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH=/opt/venv/bin:$PATH

RUN if [ -n "$DEBIAN_MIRROR" ]; then \
      sed -i \
        -e "s|http://deb.debian.org/debian-security|${DEBIAN_MIRROR}/debian-security|g" \
        -e "s|http://deb.debian.org/debian|${DEBIAN_MIRROR}/debian|g" \
        /etc/apt/sources.list.d/debian.sources; \
    fi \
    && apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
COPY deploy/docling/requirements.lock /tmp/requirements.lock
RUN pip install --require-hashes -r /tmp/requirements.lock

COPY --from=model_assets / /opt/docling/models
COPY deploy/docling/model_manifest.json /opt/docling/model_manifest.json
COPY deploy/docling/verify_offline_runtime.py /opt/docling/verify_offline_runtime.py
RUN python /opt/docling/verify_offline_runtime.py \
      --manifest /opt/docling/model_manifest.json \
      --model-root /opt/docling/models \
      --skip-gpu \
      --skip-offline
RUN cyclonedx-py environment --output-format JSON --output-file /opt/docling/sbom.cdx.json \
    && pip-licenses --format=json --output-file=/opt/docling/python_licenses.json

FROM python:3.11.15-slim-bookworm@sha256:961f57b66f6aee85ae11272cca9219123a860ab20e2a09a1238f57e0df495825 AS runtime

ARG DEBIAN_MIRROR=

# 生产必须同时使用 Docker 参数 --network=none 启动。
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    DOCLING_ARTIFACTS_PATH=/opt/docling/models \
    DOCLING_DEVICE=cuda \
    PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1

RUN if [ -n "$DEBIAN_MIRROR" ]; then \
      sed -i \
        -e "s|http://deb.debian.org/debian-security|${DEBIAN_MIRROR}/debian-security|g" \
        -e "s|http://deb.debian.org/debian|${DEBIAN_MIRROR}/debian|g" \
        /etc/apt/sources.list.d/debian.sources; \
    fi \
    && apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*
RUN groupadd --system docling && useradd --system --create-home --gid docling --home /home/docling docling
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /opt/docling /opt/docling
RUN chown -R docling:docling /opt/docling /home/docling

USER docling
WORKDIR /workspace
ENTRYPOINT ["python", "/opt/docling/verify_offline_runtime.py"]
