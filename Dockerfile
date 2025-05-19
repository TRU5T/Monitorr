FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 6000

CMD ["python", "monitorr.py", "--web-only", "--host", "0.0.0.0", "--port", "6000"] 