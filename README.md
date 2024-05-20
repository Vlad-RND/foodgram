# Проект Foodgram
[![Main Foodgram workflow](https://github.com/Vlad-RND/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/Vlad-RND/foodgram/actions/workflows/main.yml)

### Описание проекта:
Проект Foodgram - сайт для публикации рецептов. В проекте равлизована регистрация, подписки,
избранное рецептов и формирование списка покупок.
Бэкенд реализован с помощью Django и DRF (Api).
Фронтенд реализован с помощью React.
Проект упакован в контейнеры и настроен CI/CD.

#### Адрес сайта: 
```
https://foodgram-vladrnd.myftp.org/recipes.
```

### Используемые библиотеки:
asgiref==3.8.1, certifi==2024.2.2, cffi==1.16.0, charset-normalizer==3.3.2, 
cryptography==42.0.5, defusedxml==0.8.0rc2, Django==4.2, django-filter==24.2,
django-templated-mail==1.1.1, djangorestframework==3.15.1,
djangorestframework-simplejwt==5.3.1, djoser==2.2.2, flake8==6.0.0, flake8-isort==6.0.0,
idna==3.7, isort==5.13.2, mccabe==0.7.0, oauthlib==3.2.2, pillow==10.3.0,
psycopg2-binary==2.9.9, python-dotenv==1.0.1, pycodestyle==2.10.0, pycparser==2.22,
pyflakes==3.0.1, PyJWT==2.8.0, python3-openid==3.2.0, requests==2.31.0,
requests-oauthlib==2.0.0, setuptools==69.5.1, social-auth-app-django==5.4.0,
social-auth-core==4.5.3, sqlparse==0.4.4, tzdata==2024.1, urllib3==2.2.1, webcolors==1.13

### Как запустить проект:
Клонировать репозиторий и перейти в него в командной строке:
```
git clone https://github.com/Vlad-RND/foodgram.git
```
```
cd foodgram
```

### Создать в директории проекта и заполнить .env:
```
POSTGRES_DB=***
POSTGRES_USER=***
POSTGRES_PASSWORD=***
DB_HOST=***
DB_PORT=***
SECRET_KEY=***
ALLOWED_HOSTS=***
DEBUG_MODE=***
```

### Подтянуть последнюю версию проекта:
```
docker compose -f docker-compose.production.yml pull
```

### Запустить инструкцию с автоматическим запуском контейнеров проекта:
```
docker compose -f docker-compose.production.yml up
```

### Создать миграции в БД проекта:
```
docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```

### Собрать статику бекэнда и скопировать в нужную директорию:
```
docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
```
```
docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```

### Функционал:
- Регистрация;
- Создание/редактирование/удаление рецепта с фото, категориями и ингредиентами;
- Подписка на автором рецептов;
- Добавление рецептов в избранное;
- Создание/редактирование и скачивание списка покупок;
- Реализован широкий функционал админ-панели django.

Автор - Vlad-RND, GIT - https://github.com/Vlad-RND