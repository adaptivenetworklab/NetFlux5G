FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY open5gs_exporter.py .

EXPOSE 9090

CMD ["python", "open5gs_exporter.py"]
