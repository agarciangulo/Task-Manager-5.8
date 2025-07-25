# Use Python 3.9 slim as the base image
FROM python:3.9-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Final stage
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install dependencies
RUN pip install --no-cache /wheels/*

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs cache chroma_db email_storage

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=src.api.app_auth
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0

# Expose port (standardized to 5000 for Google Cloud)
EXPOSE 5000

# Run the application
CMD ["python", "-m", "src.api.app_auth"] 