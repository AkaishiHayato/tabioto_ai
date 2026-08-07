FROM mcr.microsoft.com/playwright/python:v1.50.0-noble

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1

COPY backend/pyproject.toml .
COPY backend/app ./app
COPY backend/llm_core ./llm_core
RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
