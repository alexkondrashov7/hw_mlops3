#Учебный проект по MLOps (модуль 3 «Автоматизированное развертывание с помощью CI/CD»).
Учебный проект по MLOps (модуль 3 «Автоматизированное развертывание с помощью CI/CD»).  
Цель — упаковать ML-модель в сервис на FastAPI, реализовать стратегии деплоя Blue-Green / Canary c помощью Docker + Nginx и настроить базовый CI/CD-пайплайн на GitHub Actions.


## API эндпоинты (FastAPI)

Файл: `main.py`

- `GET /health`  
  Возвращает статус сервиса и версию модели:

  ```json
  {
    "status": "ok",
    "version": "v1.0.0"
  }
  ```

- `POST /predict`  
  На вход принимает JSON вида:

  ```json
  {
    "features": {
      "alcohol": 14.23,
      "malic_acid": 1.71,
      "ash": 2.43,
      "alcalinity_of_ash": 15.6,
      "magnesium": 127.0,
      "total_phenols": 2.8,
      "flavanoids": 3.06,
      "nonflavanoid_phenols": 0.28,
      "proanthocyanins": 2.29,
      "color_intensity": 5.64,
      "hue": 1.04,
      "od280/od315_of_diluted_wines": 3.92,
      "proline": 1065.0
    }
  }
  ```

  Ответ:

```json
  {
"predict" : int,
"prob" : float
"model_version" : str
}
  ```
## 2. Структура репозитория

```text
.
├── Dockerfile
├── inference.py          # класс ModelRunner (загрузка model.pkl, predict + predict_proba)
├── main.py               # FastAPI-приложение (/health, /predict)
├── model.pkl             # сохранённая ML-модель
├── nginx.conf            # конфигурация Nginx (canary 90/10)
├── requirements.txt
├── docker-compose.blue.yml
├── docker-compose.green.yml
├── docker-compose.nginx.yml
└── .github/
    └── workflows/
        └── deploy.yml    # CI/CD workflow (GitHub Actions)
```
## 3. Локальный запуск без Docker

```bash
# в виртуальном окружении
pip install -r requirements.txt

uvicorn main:app --host 0.0.0.0 --port 5070 --reload
```

Проверка:

```bash
curl http://localhost:5070/health
```

---

## 4. Docker-сервис

### Dockerfile

Сервис упакован в образ на базе `python:3.11-slim`, приложение стартует командой:

```bash
uvicorn main:app --host 0.0.0.0 --port 5070
```

### Локальная сборка и запуск одного сервиса

```bash
docker build -t ml_service:local .
docker run --rm -p 5070:5070 ml_service:local
```

Проверка:

```bash
curl http://localhost:5070/health
```

---

## 5. Blue / Green deployment через docker-compose

Используются два compose-файла:

### `docker-compose.blue.yml`

```yaml
version: "3.9"

services:
  mlservice_blue:
    build: .
    container_name: mlservice_blue
    environment:
      - MODEL_PATH=model.pkl
      - MODEL_VERSION=v1.0.0
    ports:
      - "5070:5070"
```

### `docker-compose.green.yml`

```yaml
version: "3.9"

services:
  mlservice_green:
    build: .
    container_name: mlservice_green
    environment:
      - MODEL_PATH=model.pkl
      - MODEL_VERSION=v1.1.0
    ports:
      - "5071:5070"
```

Запуск обеих версий:

```bash
docker compose -f docker-compose.blue.yml up -d --build
docker compose -f docker-compose.green.yml up -d --build
```

Проверка:

```bash
# Blue
curl http://localhost:5070/health   # → version: v1.0.0

# Green
curl http://localhost:5071/health   # → version: v1.1.0
```

## 6. Nginx + Canary deployment (90/10)

Для демонстрации canary deployment используется Nginx как reverse-proxy и балансировщик между blue и green версиями.

### `nginx.conf`

```nginx
worker_processes 1;

events {
    worker_connections 1024;
}

http {
    upstream ml_backend {
        server mlservice_blue:5070 weight=9;   # ~90% трафика
        server mlservice_green:5070 weight=1;  # ~10% трафика
    }

    server {
        listen 80;

        location / {
            proxy_pass http://ml_backend;

            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}
```

### `docker-compose.nginx.yml`

```yaml
version: "3.9"

services:
  nginx:
    image: nginx:latest
    container_name: ml_nginx
    ports:
      - "5086:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - mlservice_blue
      - mlservice_green
```

### Запуск всего стенда (blue + green + nginx)

```bash
docker compose   -f docker-compose.blue.yml   -f docker-compose.green.yml   -f docker-compose.nginx.yml   up -d --build
```

Проверка:

```bash
# прямой доступ
curl http://localhost:5070/health   # blue
curl http://localhost:5071/health   # green

# доступ через nginx (canary 90/10)
curl http://localhost:5086/health
```

















