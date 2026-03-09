FROM python:3.11-slim

# Install uv and curl (required for healthcheck)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files first
COPY pyproject.toml uv.lock ./

# Install dependencies directly to system Python (faster and simpler)
RUN uv pip install --system --no-cache .

# Copy application code
COPY config.py ./
COPY src/ ./src/

# Copy model files
COPY ./model/ ./model

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthcheck || exit 1

CMD ["python", "-m", "uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
