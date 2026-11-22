# Unit Converter

Простий вебзастосунок на Python (Flask) для конвертації одиниць: довжина, маса, температура.

Маршрути:

- `/` — сторінка з формою конвертера
- `/api/convert?category=length&value=10&from=km&to=m` — конвертація (JSON)
- `/api/units` — список одиниць
- `/health` — перевірка стану застосунку

## Структура

```
students/hrassh/
├── src/          код застосунку
├── tests/        тести (pytest)
├── infra/        Terraform (EC2, Security Group, Key Pair)
├── .github/      копія воркфлоу
├── Dockerfile
├── .dockerignore
└── .gitignore
```

GitHub Actions бачить воркфлоу лише в корені репозиторію, тому робочі файли лежать у `/.github/workflows/`, а в цій папці їхня копія.

## Локальний запуск

```bash
cd students/hrassh
docker build -t unit-converter .
docker run -d -p 8000:8000 unit-converter
```

Відкрити http://localhost:8000.

Тести без Docker:

```bash
pip install -r requirements-dev.txt
pytest
```

## Як працює CI/CD

Пайплайн `hrassh-cicd.yml` запускається при пуші в `main`:

1. **Tests** — запуск тестів.
2. **Build and push** — збірка Docker-образу і пуш у Docker Hub (теги: хеш коміту і `latest`).
3. **Terraform apply** — створення сервера EC2 в AWS. State зберігається в S3.
4. **Deploy** — підключення до EC2 по SSH, `docker pull` і запуск контейнера на порту 80, перевірка `/health`.

Для pull request виконуються лише тести і збірка образу.

Щоб видалити сервер: Actions → **hrassh Terraform destroy** → Run workflow → ввести `DESTROY`.

## Змінні середовища

| Змінна | Опис |
| --- | --- |
| `APP_ENV` | середовище (`development` / `production`) |
| `APP_VERSION` | версія застосунку, у пайплайні — хеш коміту |

## Секрети GitHub

| Секрет | Опис |
| --- | --- |
| `DOCKER_USERNAME` | логін Docker Hub |
| `DOCKER_TOKEN` | токен Docker Hub |
| `AWS_ACCESS_KEY_ID` | ключ доступу AWS |
| `AWS_SECRET_ACCESS_KEY` | секретний ключ AWS |
| `EC2_SSH_KEY_B64` | приватний SSH-ключ у Base64 |
| `TF_STATE_BUCKET` | назва S3-бакета для state Terraform |
