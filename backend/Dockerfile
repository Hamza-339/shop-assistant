FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app

RUN pip install --no-cache-dir -e .

# Bakes the embedding model into the image so the API doesn't pay a
# first-request download/latency hit (ADR-0003).
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
