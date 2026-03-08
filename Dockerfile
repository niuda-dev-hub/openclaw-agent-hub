FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    AGENT_HUB_DATA_DIR=/data \
    AGENT_HUB_PORT=8000

WORKDIR /app

# Runtime dependencies (if any extra system libs are needed later, add here)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip \
    && pip install .

EXPOSE 8000
VOLUME ["/data"]

CMD ["sh", "-c", "uvicorn agent_hub.main:app --host 0.0.0.0 --port ${AGENT_HUB_PORT:-8000}"]
