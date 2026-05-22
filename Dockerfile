FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

COPY emergent/ emergent/
COPY config/ config/

CMD ["python", "-m", "emergent.cli.run"]
