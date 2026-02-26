# Build from repo root: docker compose build payer_psp (context .)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl git \
    && rm -rf /var/lib/apt/lists/*

COPY payer_psp/requirements.txt .
COPY requirements_phase2.txt ./phase2_requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r phase2_requirements.txt

# Phase 2: Agent infrastructure
COPY agents/ ./agents/
COPY manifest.py a2a_protocol.py code_updater.py llm.py docker_manager.py ./

COPY payer_psp/app.py ./payer_psp/
COPY payer_psp/db ./payer_psp/db

ENV PORT=5000
EXPOSE 5000

CMD ["python3", "payer_psp/app.py"]
