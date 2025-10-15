FROM python:3.9.18-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    default-mysql-client \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir cryptography && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "backend.py"]