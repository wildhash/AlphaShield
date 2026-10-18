# High-Performance Runtime for AlphaShield Multi-Agent Framework
FROM python:3.11-slim

# Install system dependencies required for technical analysis libraries and pandas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libatlas-base-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency specifications
COPY requirements.txt .

# Install dependencies with optimization flags
RUN pip install --no-cache-dir -r requirements.txt

# Copy application layer source code
COPY . .

# Expose target deployment port for Google Cloud Run (defaults to 8080)
EXPOSE 8080

# Launch application via high-performance ASGI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
