# Используем легковесный образ Python на Alpine Linux
FROM python:3.11-alpine

# Устанавливаем системные зависимости для сборки библиотек, если потребуются
RUN apk add --no-cache gcc musl-dev libffi-dev

WORKDIR /app

# Копируем список зависимостей
COPY requirements.txt .

# Устанавливаем библиотеки без сохранения кэша для уменьшения веса образа
RUN pip install --no-cache-dir -r requirements.txt

# Создаем непривилегированного пользователя для безопасности (защита от root-хакинга)
RUN adduser --disabled-password --gecos "" botuser

# Копируем весь остальной код проекта в контейнер
COPY . .

# Назначаем права пользователю botuser на рабочую директорию
RUN chown -R botuser:botuser /app

# Переключаемся на безопасного пользователя
USER botuser

# Запуск бота
CMD ["python", "main.py"]
