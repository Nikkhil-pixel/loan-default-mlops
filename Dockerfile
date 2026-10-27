FROM python:3.11-slim

ARG APP_DIR=/app
ENV APP_DIR=${APP_DIR} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    API_HOST=0.0.0.0 \
    API_PORT=8000
WORKDIR ${APP_DIR}
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 appuser \
    && mkdir -p "${APP_DIR}/logs" "${APP_DIR}/reports" "${APP_DIR}/artifacts" "${APP_DIR}/mlflow" \
    && chown -R appuser:appuser "${APP_DIR}"
COPY --chown=appuser:appuser . .
USER appuser
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; from src.config import load_config; urllib.request.urlopen(load_config()['api']['healthcheck_url'], timeout=3)" || exit 1
CMD ["sh", "-c", "uvicorn app.main:app --host ${API_HOST} --port ${API_PORT}"]
