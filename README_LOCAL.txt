==============================
LOКАЛЬНЫЙ ЗАПУСК ПРОЕКТА
(Flask + PostgreSQL)
==============================

📌 Требования:
- Python 3.8+
- PostgreSQL установлен и запущен

------------------------------
🔧 УСТАНОВКА ЛОКАЛЬНО если проект на gitHub
------------------------------

1. Установите PostgreSQL:
   https://www.postgresql.org/download/

   ✅ Проверьте запуск PostgreSQL и создайте базу:
   - База данных: postgres
   - Пользователь: postgres
   - Пароль: postgres

2. Скачайте проект:
   > git clone https://github.com/yourusername/flask_postgres_app.git
   > cd flask_postgres_app
3. Создайте виртуальное окружение:
   > python -m venv venv
   > venv\Scripts\activate   (Windows)
   > source venv/bin/activate (Linux/macOS)

4. Установите зависимости:
   > pip install -r requirements.txt

5. Запустите приложение:
   > python app.py

6. Откройте в браузере:
   http://localhost:5000

------------------------------
🔧 УСТАНОВКА ЛОКАЛЬНО если проект в папке на флешке
------------------------------

1. Установите PostgreSQL:
   https://www.postgresql.org/download/

   ✅ Проверьте запуск PostgreSQL и создайте базу:
   - База данных: postgres
   - Пользователь: postgres
   - Пароль: postgres
   Установите PyCharm:
   https://www.jetbrains.com/pycharm/download/
2. Скачайте проект:
   Перенесите с флешки на локальный стол
3. Создайте виртуальное окружение:
   Откройте app.py в приложени PyCharm и создайте проект.

4. Установите зависимости:
   > pip install -r requirements.txt

5. Запустите приложение:
   > python app.py

6. Откройте в браузере:
   http://localhost:5000

------------------------------
💡 ПРОВЕРКА
------------------------------

Запустите проект и перейдите в приложении по ссылке, появляющейся после запуска. Откроется главная страница сайта. Пройдитесь по навигационному меню. Должны работать все ссылки.