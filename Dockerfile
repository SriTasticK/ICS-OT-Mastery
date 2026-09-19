FROM ghcr.io/astral-sh/uv:0.10.12 AS uv
FROM python:3.13-slim-bookworm
COPY --from=uv /uv /uvx /bin/
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never LAB_DATA=/data
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache \
    && groupadd --gid 10001 lab \
    && useradd --uid 10001 --gid 10001 --no-create-home lab \
    && mkdir /data && chown 10001:10001 /data
COPY lab ./lab
USER 10001:10001
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD ["/app/.venv/bin/python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3)"]
CMD ["/app/.venv/bin/gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "120", "--worker-tmp-dir", "/tmp", "lab.app:create_app()"]
