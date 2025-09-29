## Подготовка окружения

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Миграция базы данных

При первом запуске таблицы будут созданы автоматически в файле `app.db` (SQLite).

## Запуск апки

```bash
uvicorn app.main:app --reload
```

Апка будет доступна по адресу `http://127.0.0.1:8000`. Swagger: `http://127.0.0.1:8000/docs`.