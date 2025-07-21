-- Инициализация базы данных для School Schedule
-- Файл выполняется при первом запуске PostgreSQL контейнера

-- Создание базы данных (если не существует)
SELECT 'CREATE DATABASE school_schedule'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'school_schedule')\gexec

-- Подключение к базе данных
\c school_schedule

-- Установка кодировки
SET client_encoding = 'UTF8';

-- Создание расширений (если нужны в будущем)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- для UUID полей
-- CREATE EXTENSION IF NOT EXISTS "pg_trgm";    -- для полнотекстового поиска

-- Комментарий к базе данных
COMMENT ON DATABASE school_schedule IS 'База данных системы управления школьным расписанием'; 