FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy sensor scripts
COPY *.py ./

# Create non-root user for security
RUN groupadd -r sensor && useradd -r -g sensor sensor
USER sensor

# Default command (can be overridden)
CMD ["python", "temp_sensor.py"]