FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ /app/src/

# Create directories for input/output
RUN mkdir -p /input /output /logs

# Set Python to run in unbuffered mode for better logging
ENV PYTHONUNBUFFERED=1

# Run the main script
ENTRYPOINT ["python", "/app/src/refresh_cookie.py"]
