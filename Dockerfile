FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create logs directory and set permissions
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Expose port
EXPOSE 5000

# Run the application with both monitoring and web interface
CMD ["python", "monitorr.py", "--web", "--host", "0.0.0.0", "--port", "5000"] 