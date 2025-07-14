# Kraken Trading Bot Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs models data

# Create non-root user for security
RUN useradd -m -u 1000 tradingbot && \
    chown -R tradingbot:tradingbot /app

# Switch to non-root user
USER tradingbot

# Expose ports
EXPOSE 8050 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8050/ || exit 1

# Default command
CMD ["python", "main.py", "--mode", "bot"]