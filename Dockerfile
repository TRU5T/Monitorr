FROM python:3.10-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the web server port
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "monitorr.py", "--web-only", "--host", "0.0.0.0", "--port", "5000"] 