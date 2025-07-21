# Makefile для управления School Schedule проектом

# Переменные
DOCKER_COMPOSE = docker compose
DJANGO_SERVICE = web
DB_SERVICE = db

# Цвета для вывода
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

.PHONY: help build up down restart logs shell migrate makemigrations superuser test clean

# Помощь
help:
	@echo "$(GREEN)School Schedule - Команды для разработки:$(NC)"
	@echo ""
	@echo "$(YELLOW)Основные команды:$(NC)"
	@echo "  build          - Собрать Docker образы"
	@echo "  up             - Запустить все сервисы"
	@echo "  down           - Остановить все сервисы"
	@echo "  restart        - Перезапустить сервисы"
	@echo "  logs           - Показать логи всех сервисов"
	@echo "  logs-web       - Показать логи Django"
	@echo "  logs-db        - Показать логи PostgreSQL"
	@echo ""
	@echo "$(YELLOW)Django команды:$(NC)"
	@echo "  shell          - Войти в Django shell"
	@echo "  bash           - Войти в bash контейнера"
	@echo "  migrate        - Выполнить миграции"
	@echo "  makemigrations - Создать миграции"
	@echo "  superuser      - Создать суперпользователя"
	@echo "  collectstatic  - Собрать статические файлы"
	@echo ""
	@echo "$(YELLOW)Разработка:$(NC)"
	@echo "  test           - Запустить тесты"
	@echo "  check          - Проверить конфигурацию Django"
	@echo "  clean          - Очистить Docker данные"
	@echo "  reset-db       - Пересоздать базу данных"

# Сборка образов
build:
	@echo "$(GREEN)Сборка Docker образов...$(NC)"
	$(DOCKER_COMPOSE) build

# Запуск всех сервисов
up:
	@echo "$(GREEN)Запуск всех сервисов...$(NC)"
	$(DOCKER_COMPOSE) up -d

# Запуск с выводом логов
up-logs:
	@echo "$(GREEN)Запуск всех сервисов с выводом логов...$(NC)"
	$(DOCKER_COMPOSE) up

# Остановка всех сервисов
down:
	@echo "$(YELLOW)Остановка всех сервисов...$(NC)"
	$(DOCKER_COMPOSE) down

# Перезапуск сервисов
restart:
	@echo "$(YELLOW)Перезапуск сервисов...$(NC)"
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) up -d

# Просмотр логов
logs:
	$(DOCKER_COMPOSE) logs -f

logs-web:
	$(DOCKER_COMPOSE) logs -f $(DJANGO_SERVICE)

logs-db:
	$(DOCKER_COMPOSE) logs -f $(DB_SERVICE)

# Django shell
shell:
	$(DOCKER_COMPOSE) exec $(DJANGO_SERVICE) python manage.py shell

# Bash в контейнере
bash:
	$(DOCKER_COMPOSE) exec $(DJANGO_SERVICE) bash

# Миграции
migrate:
	@echo "$(GREEN)Выполнение миграций...$(NC)"
	$(DOCKER_COMPOSE) exec $(DJANGO_SERVICE) python manage.py migrate

makemigrations:
	@echo "$(GREEN)Создание миграций...$(NC)"
	$(DOCKER_COMPOSE) exec $(DJANGO_SERVICE) python manage.py makemigrations

# Создание суперпользователя
superuser:
	$(DOCKER_COMPOSE) exec $(DJANGO_SERVICE) python manage.py createsuperuser

# Сборка статических файлов
collectstatic:
	$(DOCKER_COMPOSE) exec $(DJANGO_SERVICE) python manage.py collectstatic --noinput

# Проверка конфигурации
check:
	$(DOCKER_COMPOSE) exec $(DJANGO_SERVICE) python manage.py check

# Тесты
test:
	$(DOCKER_COMPOSE) exec $(DJANGO_SERVICE) python manage.py test

# Pytest
pytest:
	$(DOCKER_COMPOSE) exec $(DJANGO_SERVICE) pytest

# Очистка Docker данных
clean:
	@echo "$(RED)Очистка Docker данных...$(NC)"
	$(DOCKER_COMPOSE) down -v --remove-orphans
	docker system prune -f

# Пересоздание базы данных
reset-db:
	@echo "$(RED)Пересоздание базы данных...$(NC)"
	$(DOCKER_COMPOSE) down
	docker volume rm $$(docker volume ls -q | grep postgres_data) || true
	$(DOCKER_COMPOSE) up -d $(DB_SERVICE)
	@echo "$(YELLOW)Ожидание запуска PostgreSQL...$(NC)"
	sleep 10
	$(DOCKER_COMPOSE) up -d $(DJANGO_SERVICE)

# Первый запуск проекта
first-run: build up migrate superuser
	@echo "$(GREEN)Проект готов! Переходите на http://localhost:8000$(NC)" 