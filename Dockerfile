FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы Poetry
COPY pyproject.toml poetry.lock ./

# Устанавливаем Poetry
RUN pip install poetry

# Конфигурируем Poetry
RUN poetry config virtualenvs.create false

# Устанавливаем зависимости
RUN poetry install --only=main --no-root

# Копируем код приложения
COPY . .

# Устанавливаем текущий проект без root пакета
RUN poetry install --only=main --no-root

# Открываем порт
EXPOSE 8002

# Команда запуска
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
