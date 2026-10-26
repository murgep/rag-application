FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install the system dependency required for OCR.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies separately to improve build caching.
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

# Copy application source and scripts.
COPY app/ ./app/
COPY scripts/ ./scripts/

EXPOSE 8000

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]