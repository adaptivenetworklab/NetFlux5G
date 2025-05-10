#!/bin/bash
# Real-world application deployment test for Docker, Containerd, Podman, and LXD

set -e

echo "=== Containerized Application Deployment Comparison ==="

mkdir -p container-app-test
cd container-app-test

# Create Flask app
cat > app.py << 'EOF'
from flask import Flask, request, jsonify
import os
import psycopg2
import time

app = Flask(__name__)

def get_db_connection():
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            conn = psycopg2.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                database=os.environ.get('DB_NAME', 'testdb'),
                user=os.environ.get('DB_USER', 'user'),
                password=os.environ.get('DB_PASSWORD', 'password')
            )
            return conn
        except psycopg2.OperationalError:
            if attempt < max_attempts - 1:
                time.sleep(1)
                continue
            raise

@app.route('/')
def hello():
    return jsonify({"message": "Hello, World!"})

@app.route('/init-db')
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS counter (id SERIAL PRIMARY KEY, count INTEGER);')
    cursor.execute('INSERT INTO counter (count) VALUES (0) ON CONFLICT DO NOTHING;')
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Database initialized"})

@app.route('/increment')
def increment():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE counter SET count = count + 1 WHERE id = 1 RETURNING count;')
    count = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"count": count})

@app.route('/count')
def get_count():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT count FROM counter WHERE id = 1;')
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return jsonify({"count": count})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF

# Create requirements
cat > requirements.txt << 'EOF'
flask==2.0.1
psycopg2-binary==2.9.1
EOF

# Create Dockerfile
cat > Dockerfile.app << 'EOF'
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
ENV FLASK_APP=app.py
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
EOF

# Create docker-compose
cat > docker-compose.yml << 'EOF'
version: '3'
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.app
    ports:
      - "5000:5000"
    environment:
      DB_HOST: db
      DB_NAME: testdb
      DB_USER: user
      DB_PASSWORD: password
    depends_on:
      - db
  db:
    image: postgres:13-alpine
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_USER: user
      POSTGRES_DB: testdb
    volumes:
      - postgres_data:/var/lib/postgresql/data
volumes:
  postgres_data:
EOF

# Create Podman pod YAML
cat > pod.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: flask-app
spec:
  containers:
  - name: web
    image: localhost/flask-app:latest
    ports:
    - containerPort: 5000
      hostPort: 5001
    env:
    - name: DB_HOST
      value: localhost
    - name: DB_NAME
      value: testdb
    - name: DB_USER
      value: user
    - name: DB_PASSWORD
      value: password
  - name: db
    image: postgres:13-alpine
    env:
    - name: POSTGRES_PASSWORD
      value: password
    - name: POSTGRES_USER
      value: user
    - name: POSTGRES_DB
      value: testdb
    volumeMounts:
    - mountPath: /var/lib/postgresql/data
      name: postgres-data
  volumes:
  - name: postgres-data
    emptyDir: {}
EOF

# Create LXD profile
cat > lxd-web-profile.yaml << 'EOF'
name: flask-app-profile
config:
  environment.DB_HOST: 10.0.0.2
  environment.DB_NAME: testdb
  environment.DB_USER: user
  environment.DB_PASSWORD: password
description: Flask application profile
devices:
  web:
    bind: tcp:0.0.0.0:5003
    connect: tcp:127.0.0.1:5000
    listen: tcp:0.0.0.0:5003
    type: proxy
EOF

# Function to test deployment
test_deployment() {
  local platform=$1
  local port=$2
  echo "Testing $platform deployment on port $port"
  echo "Testing / endpoint:"
  curl -s "http://localhost:$port/" | jq .
  echo "Initializing database:"
  curl -s "http://localhost:$port/init-db" | jq .
  echo "Testing /increment endpoint:"
  curl -s "http://localhost:$port/increment" | jq .
  echo "Testing /count endpoint:"
  curl -s "http://localhost:$port/count" | jq .
  echo "$platform test completed"
  echo "-----------------------------------"
}

# Docker deployment
echo "Deploying with Docker Compose:"
time docker-compose up -d --build
sleep 10
test_deployment "Docker" 5000
time docker-compose down -v

# Containerd deployment
echo "Deploying with Nerdctl Compose:"
time nerdctl compose up -d --build
sleep 10
test_deployment "Containerd" 5000
time nerdctl compose down -v

# Podman deployment
echo "Building image with Podman:"
time podman build -t localhost/flask-app:latest -f Dockerfile.app .
echo "Deploying with Podman pod:"
time podman play kube pod.yaml
sleep 10
test_deployment "Podman" 5001
time podman pod rm -f flask-app

# LXD deployment
echo "Deploying with LXD:"
lxc profile create flask-app-profile >/dev/null 2>&1 || true
cat lxd-web-profile.yaml | lxc profile edit flask-app-profile
lxc network create flasknet >/dev/null 2>&1 || true
time lxc launch ubuntu:22.04 flask-db --network flasknet
lxc exec flask-db -- apt-get update
lxc exec flask-db -- apt-get install -y postgresql postgresql-contrib
lxc exec flask-db -- su - postgres -c "psql -c \"CREATE USER user WITH PASSWORD 'password';\""
lxc exec flask-db -- su - postgres -c "psql -c \"CREATE DATABASE testdb OWNER user;\""
lxc exec flask-db -- sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/14/main/postgresql.conf
lxc exec flask-db -- bash -c 'echo "host    all             all             0.0.0.0/0               md5" >> /etc/postgresql/14/main/pg_hba.conf'
lxc exec flask-db -- systemctl restart postgresql
time lxc launch ubuntu:22.04 flask-web --network flasknet --profile flask-app-profile
lxc exec flask-web -- apt-get update
lxc exec flask-web -- apt-get install -y python3-pip
lxc file push app.py flask-web/app/
lxc file push requirements.txt flask-web/app/
lxc exec flask-web -- pip3 install -r /app/requirements.txt
lxc exec flask-web -- bash -c 'cd /app && FLASK_APP=app.py python3 -m flask run --host=0.0.0.0 &'
sleep 15
test_deployment "LXD" 5003
lxc delete -f flask-web flask-db
lxc profile delete flask-app-profile
lxc network delete flasknet

# Clean up
cd ..
rm -rf container-app-test
