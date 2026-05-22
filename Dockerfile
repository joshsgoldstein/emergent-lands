FROM python:3.11-slim

RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml .
RUN pip install --no-cache-dir ".[dev]"

COPY emergent/ emergent/
COPY config/ config/

RUN chown -R app:app /app
USER app

CMD ["python", "-m", "emergent.cli.run"]
