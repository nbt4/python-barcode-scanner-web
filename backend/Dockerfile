FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libc6-dev \
    zlib1g-dev \
    libjpeg-dev \
    libfreetype6-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    cmake \
    pkg-config \
    libffi-dev \
    cargo \
    rustc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Upgrade pip and install requirements
RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir wheel setuptools && \
    python -m pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=run.py
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]
