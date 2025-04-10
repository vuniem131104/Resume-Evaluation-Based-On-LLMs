FROM python:3.12-slim

WORKDIR /app 

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    redis-tools \
    libportaudio2 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

COPY ./app/requirements.txt /app/
RUN pip install --upgrade pip && \
pip config set global.timeout 120 && \
pip install --no-cache-dir --default-timeout=100 -r requirements.txt || \
pip install --no-cache-dir --default-timeout=100 -r requirements.txt

COPY ./app /app  

RUN mkdir -p /app/uploads && chmod -R 777 /app/uploads
RUN mkdir -p /app/temp_images && chmod -R 777 /app/temp_images