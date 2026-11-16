# Base image: a full Debian system with Python 3.13 already installed.
FROM python:3.13

# Every following instruction runs inside /app in the image.
WORKDIR /app

# Install uv
RUN pip install uv==0.12.17

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Copy only required folders/files
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini README.md ./

# Install the project itself.
RUN uv sync --frozen --no-dev

# Documentation only: the app listens on 8000. Publishing happens at `docker run -p`.
EXPOSE 8000

ENV PATH="/app/.venv/bin:$PATH"
# 0.0.0.0 = accept connections on every network interface of the container.
# 127.0.0.1 would accept only connections from inside the container itself.
CMD ["uvicorn", "payments.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
