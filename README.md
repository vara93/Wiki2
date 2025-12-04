# Internal Wiki (FastAPI + Markdown)

Простой wiki-сервис на FastAPI с хранением документов в файловой системе.

## Структура проекта

```
project_root/
  app/
    main.py
    config.py
    deps.py
    services/
      docs_service.py
      search_service.py
      upload_service.py
    templates/
      base.html
      index.html
      view_doc.html
      edit_doc.html
      new_doc.html
      search_results.html
      upload_image.html
    static/
  data/
    docs/
    uploads/
  requirements.txt
  run.sh
  README.md
```

## Запуск в dev-режиме

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./run.sh
```

## systemd-юнит (пример)

```
[Unit]
Description=Internal Wiki (FastAPI)
After=network.target

[Service]
WorkingDirectory=/opt/wiki
Environment="PATH=/opt/wiki/venv/bin"
ExecStart=/opt/wiki/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 80
Restart=always
User=www-data
Group=www-data

[Install]
WantedBy=multi-user.target
```

## Nginx-прокси (пример)

```
server {
    listen 80;
    server_name _;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Инструкция по запуску на Debian 12 (под root, без sudo)

1. Установка Python и зависимостей:

```bash
apt-get update
apt-get install -y python3 python3-venv python3-pip
cd /opt/wiki
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Тестовый запуск в dev-режиме:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. Вариант А: uvicorn слушает 80 порт напрямую

```bash
setcap 'cap_net_bind_service=+ep' $(readlink -f $(which python3))
uvicorn app.main:app --host 0.0.0.0 --port 80
```

systemd-юнит:

```
[Unit]
Description=Internal Wiki (FastAPI)
After=network.target

[Service]
WorkingDirectory=/opt/wiki
Environment="PATH=/opt/wiki/venv/bin"
ExecStart=/opt/wiki/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 80
Restart=always
User=www-data
Group=www-data

[Install]
WantedBy=multi-user.target
```

4. Вариант Б: Nginx на 80 порту, uvicorn на 8000

- uvicorn слушает 127.0.0.1:8000
- Nginx-конфиг:

```
server {
    listen 80;
    server_name _;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
