# Сборка и публикация (dev, с --reload):
#   docker build -f Dockerfile -t lapiki/backend:dev ./backend
# Локально из корня репозитория:
#   docker compose up backend   # использует этот Dockerfile

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
