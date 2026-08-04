FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости, включая сборщику для компиляции пакетов
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Обновляем pip до актуальной версии внутри контейнера
RUN pip install --no-cache-dir --upgrade pip

# Сначала копируем только requirements.txt, чтобы Docker кэшировал зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код проекта
COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]



