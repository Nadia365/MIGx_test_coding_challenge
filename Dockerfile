FROM python:3.12-slim

WORKDIR /app

# Keep image small; no pandas needed at runtime (not used in src/)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV MAX_STUDIES=500

RUN chmod +x docker/entrypoint.sh

ENTRYPOINT ["docker/entrypoint.sh"]
