# Image for the Hospital Management System API.
# Build:  docker build -t hospital-api .
# Usually started together with PostgreSQL through docker-compose.yml.
FROM docker.io/library/python:3.14-slim

# Print logs right away and don't write .pyc files.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /code

# Install packages first, so this layer is reused when only the code changes.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY frontend ./frontend
COPY tests ./tests
COPY pytest.ini .

# Run as a normal user, not root.
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# Marks the container unhealthy if the API or its database stops answering.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
