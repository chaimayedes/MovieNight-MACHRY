FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir grpcio grpcio-tools "passlib[bcrypt]" "bcrypt<4.0"

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 50051

ENTRYPOINT ["/entrypoint.sh"]
