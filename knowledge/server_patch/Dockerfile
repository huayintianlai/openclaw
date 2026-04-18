FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-impress \
    libreoffice-core \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    fastapi==0.109.0 \
    uvicorn==0.27.0 \
    pypdf==4.0.0 \
    python-pptx==0.6.23 \
    pymupdf==1.26.4 \
    qdrant-client==1.7.0 \
    httpx==0.27.0 \
    python-multipart==0.0.9 \
    Pillow==10.4.0

COPY app.py .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
