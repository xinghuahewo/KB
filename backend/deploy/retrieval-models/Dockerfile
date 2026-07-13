FROM python:3.11.13-slim

ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock /app/requirements.lock
RUN python -m pip install --no-cache-dir --requirement /app/requirements.lock \
    --extra-index-url https://download.pytorch.org/whl/cu128
COPY service.py /app/service.py
USER 65532:65532
