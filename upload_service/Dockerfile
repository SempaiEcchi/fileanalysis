# Use official Python 3.12.2 slim image
FROM python:3.12.2-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for common Python libs and file handling)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency list first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Environment (Flask will listen on all interfaces inside container)
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_DEBUG=1
# Expose port (overridden in docker-compose)
EXPOSE 5000

# Default command for Flask apps
CMD ["flask", "--app", "app.py", "run", "--host=0.0.0.0", "--port=5000", "--reload"]