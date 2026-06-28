import os
from pathlib import Path
from datetime import timedelta

# Базовые пути проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Секретный ключ - в реальном проекте выносим в переменные окружения
SECRET_KEY = 'django-insecure-your-secret-key-here-change-in-production'

# Режим разработки
DEBUG = True

# Разрешаем все хосты для тестирования
ALLOWED_HOSTS = ['*']

# Подключаем все необходимые приложения
INSTALLED_APPS = [
    # Стандартные приложения Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Сторонние библиотеки
    'rest_framework',  # DRF для создания API
    'rest_framework_simplejwt',  # JWT для аутентификации
    'corsheaders',  # Для кросс-доменных запросов

    # Наши приложения
    'users',  # Модель пользователя
    'auth_system',  # Кастомная система авторизации
    'api',  # API эндпоинты
]

# Промежуточные слои для обработки запросов
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS должен быть как можно выше
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Корневой URL конфиг
ROOT_URLCONF = 'config.urls'

# Настройки шаблонов
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# НАСТРОЙКА БАЗЫ ДАННЫХ POSTGRESQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'pass',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Валидаторы паролей (стандартные)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Говорим Django использовать нашу модель User вместо стандартной
AUTH_USER_MODEL = 'users.User'


# Используем свой бэкенд, а не стандартный ModelBackend
AUTHENTICATION_BACKENDS = [
    'auth_system.backends.CustomAuthBackend',
]

# НАСТРОЙКИ DRF
REST_FRAMEWORK = {
    # Классы аутентификации
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Классы разрешений - используем свою кастомную систему
    'DEFAULT_PERMISSION_CLASSES': (
        'auth_system.permissions.CustomPermission',
    ),
    # Отдаем только JSON
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
}

# НАСТРОЙКИ JWT ТОКЕНОВ
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),  # Access токен живет час
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  # Refresh токен живет неделю
    'ROTATE_REFRESH_TOKENS': True,  # Обновляем при использовании
    'BLACKLIST_AFTER_ROTATION': True,  # Добавляем старые в черный список
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ
# Разрешаем CORS для всех источников (для разработки)
CORS_ALLOW_ALL_ORIGINS = True

# Локализация
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Статика
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'