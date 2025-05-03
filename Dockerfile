# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12.3
FROM python:${PYTHON_VERSION}-alpine as base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN pip install "psycopg[binary]"

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/migrations/versions && \
    chmod -R 755 /app/migrations

# Create uploads directory with root ownership
RUN mkdir -p /var/www/html/uploads && \
    chown root:root /var/www/html/uploads && \
    chmod 777 /var/www/html/uploads

EXPOSE 5000
CMD python3 run.py
