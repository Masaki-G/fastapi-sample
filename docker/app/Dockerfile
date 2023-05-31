FROM python:3.11.1-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./app/ .



CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8080"]
