# Unit Converter — DevOps-проєкт

Вебзастосунок для конвертації одиниць вимірювання (довжина, маса, температура), який автоматично тестується, пакується в Docker-образ, публікується в Docker Hub і розгортається на сервері AWS EC2, створеному Terraform.

## Зміст

- [Призначення застосунку](#призначення-застосунку)
- [Структура проєкту](#структура-проєкту)
- [Як працює пайплайн](#як-працює-пайплайн)
- [Локальний запуск](#локальний-запуск)
- [Змінні середовища](#змінні-середовища)
- [GitHub Secrets](#github-secrets)
- [Деплой](#деплой)
- [Видалення інфраструктури](#видалення-інфраструктури)
- [Робота з гілками](#робота-з-гілками)

## Призначення застосунку

Користувач обирає категорію, вводить значення та одиниці, а застосунок повертає результат конвертації.

| Маршрут | Опис |
| --- | --- |
| `GET /` | Вебсторінка з формою конвертера |
| `GET /api/convert?category=length&value=10&from=km&to=m` | Конвертація, відповідь у JSON |
| `GET /api/units` | Список категорій і одиниць |
| `GET /health` | Стан застосунку, версія та середовище (для перевірки після деплою) |

Підтримувані одиниці:

- `length` — mm, cm, m, km, in, ft, mi
- `mass` — g, kg, t, lb, oz
- `temperature` — C, F, K

Приклад відповіді:

```json
{"category": "temperature", "from_unit": "C", "to_unit": "F", "value": 100.0, "result": 212.0}
```

Стек: Python 3.12, Flask, Gunicorn, Docker, Terraform, AWS EC2, GitHub Actions.

## Структура проєкту

```
students/hrassh/
├── src/
│   ├── app.py               Flask-застосунок і маршрути
│   ├── converter.py         логіка конвертації
│   └── templates/index.html вебсторінка
├── tests/test_app.py        тести (pytest)
├── infra/                   Terraform: EC2, Security Group, Key Pair
│   ├── versions.tf          провайдер AWS і бекенд S3 для state
│   ├── variables.tf
│   ├── main.tf
│   ├── outputs.tf
│   ├── user_data.sh         встановлення Docker на сервер
│   └── terraform.tfvars.example
├── .github/workflows/       копія воркфлоу (див. примітку нижче)
├── Dockerfile
├── .dockerignore
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
└── pytest.ini
```

> **Примітка.** GitHub Actions запускає воркфлоу лише з папки `.github/workflows/` у корені репозиторію. Тому робочі файли лежать у `/.github/workflows/hrassh-cicd.yml` і `/.github/workflows/hrassh-destroy.yml`, а в `students/hrassh/.github/workflows/` знаходиться їхня копія відповідно до структури шаблону.

## Як працює пайплайн

Воркфлоу `hrassh-cicd.yml` запускається при пуші в `main`, якщо змінилися файли в `students/hrassh/`, а також при pull request у `main`.

```
push у main
   │
   ▼
1. Tests          встановлення залежностей і запуск pytest
   │
   ▼
2. Build & push   збірка Docker-образу (Buildx + кеш GitHub Actions)
   │              і пуш у Docker Hub з тегами <sha> та latest
   ▼
3. Terraform      створення S3-бакета для state (якщо його ще немає),
   │              terraform init / validate / apply → EC2 + Security Group + Key Pair
   ▼
4. Deploy         SSH на EC2 → docker pull → перезапуск контейнера на порту 80
                  → перевірка http://<ip>/health
```

| Етап | Що робить | При pull request |
| --- | --- | --- |
| Tests | Запускає тести застосунку | так |
| Build & push | Збирає образ; пушить у Docker Hub | лише збірка, без пушу |
| Terraform | Створює або оновлює інфраструктуру | ні |
| Deploy | Розгортає новий образ на EC2 | ні |

Особливості:

- **State Terraform** зберігається в S3-бакеті (`TF_STATE_BUCKET`), тому кожен запуск оновлює ту саму інфраструктуру, а не створює новий сервер. Блокування state — через `use_lockfile` (Terraform 1.10+).
- **SSH-ключ** зберігається лише в секреті `EC2_SSH_KEY_B64`. Публічний ключ для `aws_key_pair` генерується з нього в пайплайні, тому окремо його ніде вказувати не треба.
- **Сервер** — Ubuntu 24.04, `t3.micro` (Free Tier), регіон `eu-central-1` (Франкфурт). Docker встановлюється скриптом `user_data.sh` при першому запуску.
- **Образ** тегується хешем коміту, тому на сервері завжди відомо, яка версія працює (поле `version` у `/health`).

## Локальний запуск

### У Docker

```bash
cd students/hrassh
docker build -t unit-converter .
docker run -d --name unit-converter -p 8000:8000 -e APP_ENV=local unit-converter
```

Відкрийте http://localhost:8000. Перевірка стану:

```bash
curl http://localhost:8000/health
docker ps
```

Колонка `STATUS` має показувати `(healthy)` — у Dockerfile налаштовано `HEALTHCHECK`.

Зупинка:

```bash
docker rm -f unit-converter
```

### Без Docker (для розробки)

```bash
cd students/hrassh
pip install -r requirements-dev.txt
pytest -v
python src/app.py
```

### Особливості Dockerfile

- **Multi-stage build**: залежності встановлюються у віртуальне оточення на етапі `builder`, у фінальний образ копіюється лише воно — без кешу pip і проміжних файлів.
- **Кеш шарів**: `requirements.txt` копіюється окремо від коду, тому при зміні лише коду залежності не перевстановлюються.
- **Безпека**: застосунок працює від користувача `appuser`, а не від root.
- **`.dockerignore`** виключає тести, інфраструктуру, документацію та секрети з контексту збірки.
- **Gunicorn** замість вбудованого сервера Flask для продакшн-запуску.

## Змінні середовища

| Змінна | За замовчуванням | Опис |
| --- | --- | --- |
| `APP_ENV` | `development` | Назва середовища; у продакшні — `production` |
| `APP_VERSION` | `local` | Версія застосунку; у пайплайні — короткий хеш коміту |
| `PORT` | `8000` | Порт при запуску через `python src/app.py` |

Змінні Terraform (`infra/variables.tf`):

| Змінна | За замовчуванням | Опис |
| --- | --- | --- |
| `aws_region` | `eu-central-1` | Регіон AWS |
| `project_name` | `unit-converter` | Префікс назв ресурсів |
| `instance_type` | `t3.micro` | Тип інстансу EC2 |
| `public_key` | — | Публічний SSH-ключ (у пайплайні формується автоматично) |
| `ssh_cidr` | `0.0.0.0/0` | Звідки дозволений SSH (GitHub Actions не має фіксованих IP) |

## GitHub Secrets

Settings → Secrets and variables → Actions → New repository secret:

| Секрет | Опис |
| --- | --- |
| `DOCKER_USERNAME` | Логін Docker Hub |
| `DOCKER_TOKEN` | Access Token Docker Hub (Account settings → Personal access tokens, права Read & Write) |
| `AWS_ACCESS_KEY_ID` | Ключ доступу IAM-користувача AWS |
| `AWS_SECRET_ACCESS_KEY` | Секретний ключ IAM-користувача AWS |
| `EC2_SSH_KEY_B64` | Приватний SSH-ключ у Base64 |
| `TF_STATE_BUCKET` | Унікальна назва S3-бакета для state Terraform, наприклад `hrassh-tfstate-2026` |

Створення SSH-ключа і його Base64 (PowerShell):

```powershell
ssh-keygen -t ed25519 -f $HOME\.ssh\unit-converter -N '""'
[Convert]::ToBase64String([IO.File]::ReadAllBytes("$HOME\.ssh\unit-converter"))
```

Linux / macOS:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/unit-converter -N ""
base64 -w 0 ~/.ssh/unit-converter
```

Отриманий рядок вставте в секрет `EC2_SSH_KEY_B64`. Сам файл ключа в репозиторій не додається (`*.pem`, `*.key`, `id_*` є в `.gitignore`).

IAM-користувачу AWS для навчального проєкту достатньо політик `AmazonEC2FullAccess` і `AmazonS3FullAccess`.

## Деплой

Деплой повністю автоматичний: будь-який пуш у `main`, що змінює `students/hrassh/`, запускає пайплайн. Також його можна запустити вручну: Actions → **hrassh CI/CD** → Run workflow.

Після успішного запуску адреса застосунку з'являється в кроці **Health check** та в посиланні середовища `production` на сторінці запуску. Перевірка:

```bash
curl http://<public_ip>/health
```

Підключення до сервера вручну:

```bash
ssh -i ~/.ssh/unit-converter ubuntu@<public_ip>
sudo docker ps
sudo docker logs unit-converter
```

### Ручний запуск Terraform (необов'язково)

```bash
cd students/hrassh/infra
terraform init -backend-config="bucket=<TF_STATE_BUCKET>" -backend-config="region=eu-central-1"
terraform plan -var="public_key=$(cat ~/.ssh/unit-converter.pub)"
```

## Видалення інфраструктури

AWS тарифікує ресурси, тому після перевірки роботу треба зупинити: Actions → **hrassh Terraform destroy** → Run workflow → введіть `DESTROY`. Воркфлоу виконає `terraform destroy` і видалить EC2, Security Group і Key Pair. S3-бакет зі state залишається, він майже нічого не коштує; його можна видалити вручну в консолі AWS.

## Робота з гілками

- `main` — стабільна гілка, з неї виконується деплой.
- Нові зміни робляться в окремих гілках (`feature/...`, `fix/...`, `docs/...`) і потрапляють у `main` через pull request.
- Для кожного pull request автоматично запускаються тести і пробна збірка образу, тому в `main` потрапляє лише перевірений код.
- Повідомлення комітів — короткі, у наказовому способі: `Add unit converter API`, `Add Terraform infrastructure`.
