# Настройки для разработки
import os

# Django настройки
DEBUG = True
SECRET_KEY = 'django-insecure-your-secret-key-here-change-in-production'

# База данных PostgreSQL (для Docker)
DATABASE_CONFIG = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': os.getenv('DB_NAME', 'school_schedule'),
    'USER': os.getenv('DB_USER', 'postgres'),
    'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
    'HOST': os.getenv('DB_HOST', 'db'),  # имя сервиса в docker-compose
    'PORT': os.getenv('DB_PORT', '5432'),
}

# Настройки CORS
CORS_ALLOW_ALL_ORIGINS = True

# Языковые настройки
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow' 