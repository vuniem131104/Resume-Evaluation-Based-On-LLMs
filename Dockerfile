FROM python:3.11-slim

WORKDIR /app 

COPY ./app/requirements.txt /app/
RUN pip install -r requirements.txt 

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    redis-tools \
    libportaudio2 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

COPY ./app /app  