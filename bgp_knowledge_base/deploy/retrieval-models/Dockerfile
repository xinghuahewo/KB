FROM pytorch/pytorch:2.10.0-cuda12.8-cudnn9-runtime

ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock /app/requirements.lock
RUN python -m pip install --no-cache-dir --requirement /app/requirements.lock
COPY service.py /app/service.py
USER 65532:65532
