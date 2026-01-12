# 1️⃣ Базовый образ
FROM python:3.11-slim

# 2️⃣ Обновление утилит и установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 3️⃣ Определяем рабочую директорию
WORKDIR /app

# 4️⃣ Копируем файл зависимостей и устанавливаем библиотеки
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5️⃣ Копируем исходный код проекта
COPY app/ ./app/

# 6️⃣ Expose порт FastAPI
EXPOSE 8000

# 7️⃣ Команда запуска по умолчанию (переопределяется в docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
