FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin farmwise \
    && chown farmwise:farmwise /app
COPY --chown=farmwise:farmwise app ./app
COPY --chown=farmwise:farmwise scripts ./scripts
COPY --chown=farmwise:farmwise alembic.ini ./alembic.ini
COPY --chown=farmwise:farmwise alembic ./alembic
EXPOSE 8000
USER farmwise
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
