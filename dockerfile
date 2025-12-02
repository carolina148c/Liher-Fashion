FROM python:3.13-alpine

WORKDIR /app

RUN apk update && \
    apk add --no-cache \
        postgresql-dev \
        gcc \
        python3-dev \
        musl-dev \
        libffi-dev \
        openssl-dev

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --break-system-packages --root-user-action=ignore --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
EXPOSE 8000