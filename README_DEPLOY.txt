=========================================
РАЗВЁРТЫВАНИЕ FLASK + POSTGRESQL В ИНТЕРНЕТЕ
(через Render.com)
=========================================

🔹 Что нужно:
- Аккаунт GitHub
- Аккаунт на https://render.com

------------------------------
🚀 ШАГ 1: Подготовка репозитория
------------------------------

1. Загрузите проект на GitHub:
   > git init  
   > git add .  
   > git commit -m "Initial commit"  
   > git remote add origin https://github.com/yourusername/flask_postgres_app.git  
   > git push -u origin master

2. Убедитесь, что в репозитории есть:
   - app.py
   - requirements.txt
   - Procfile
   - templates/
   - static/

------------------------------
🌐 ШАГ 2: Создание PostgreSQL на Render
------------------------------

1. Зайдите в https://dashboard.render.com
2. Нажмите "New → PostgreSQL"
3. Задайте имя (например: flaskdb)
4. После создания Render покажет:
   - DATABASE URL: `postgres://user:pass@host:port/dbname`

Скопируйте эту строку.

------------------------------
🛠️ ШАГ 3: Деплой Flask-приложения
------------------------------

1. Нажмите "New → Web Service"
2. Подключите ваш GitHub-репозиторий
3. Настройки:
   - Name: flask-postgres-app
   - Root Directory: /
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
   - Environment: Python 3

4. Добавьте переменную окружения:
   - `DATABASE_URL` = <ваш postgres url из шага 2>

5. Нажмите "Create Web Service"

Через 1–2 минуты приложение будет доступно по адресу:
> https://flask-postgres-app.onrender.com

------------------------------
💡 ПРОВЕРКА
------------------------------

На главной странице должен быть список пользователей (пустой).
Добавьте данные через psql или pgAdmin.

Готово!
