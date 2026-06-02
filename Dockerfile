FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Build essentials are required by some ML/vector dependencies.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r /app/requirements.txt

COPY src /app/src
COPY config /app/config

# Runs one full agent workflow and exits (batch style).
CMD ["python", "-m", "src.multi_agent_supply_chain"]
