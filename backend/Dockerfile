# Build context is the project root (see docker-compose.yml) because scraping.py
# imports pipeline.py from one directory above backend/.
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY pipeline.py ./pipeline.py
COPY backend/ ./backend/

WORKDIR /app/backend

EXPOSE 8000

# Un seul worker: scheduler.py demarre une boucle de fond en singleton par process,
# plusieurs workers gunicorn dupliqueraient les envois d'emails.
CMD ["gunicorn", "--workers", "1", "--threads", "4", "--bind", "0.0.0.0:8000", "--timeout", "120", "app:app"]
