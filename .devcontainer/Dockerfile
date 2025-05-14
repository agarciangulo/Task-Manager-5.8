FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONPATH=/workspace
ENV FLASK_APP=app_flask.py
ENV FLASK_ENV=development

# Expose port
EXPOSE 5000

# Command to run when container starts
CMD ["flask", "run", "--host=0.0.0.0"] 