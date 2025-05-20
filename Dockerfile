FROM python:3.10-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Create logs directory and set permissions
RUN mkdir -p /app/logs && \
    chmod 777 /app/logs

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set proper permissions for all files
RUN chown -R 1000:1000 /app && \
    chmod -R 755 /app && \
    chmod -R 777 /app/logs

EXPOSE 5000

CMD ["python", "monitorr.py", "--web-only", "--host", "0.0.0.0", "--port", "5000"] 