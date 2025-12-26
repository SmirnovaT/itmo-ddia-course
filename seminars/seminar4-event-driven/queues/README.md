# Семинар 4: Event-Driven система с очередями

## Цель
Построить асинхронную систему обработки изображений с использованием message queue

## Архитектура системы

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Client    │─────>│  API Service │─────>│  RabbitMQ   │
└─────────────┘      └──────────────┘      └──────┬──────┘
                            │                      │
                            v                      v
                     ┌──────────────┐      ┌─────────────┐
                     │  MinIO (S3)  │<─────│   Workers   │
                     └──────────────┘      └──────┬──────┘
                                                   │
                                                   v
                                            ┌─────────────┐
                                            │ Notification│
                                            │  Service    │
                                            └─────────────┘
```

### Компоненты:
1. **API Service** - принимает загрузку изображений (FastAPI)
2. **RabbitMQ** - очередь задач на обработку
3. **Worker Services** - обработка изображений (resize, watermark, filter)
4. **MinIO** - S3-compatible хранилище для изображений
5. **Notification Service** - уведомления о готовности

## Быстрый старт

### 1. Запуск всей системы
```bash
docker-compose up -d
```

### 2. Проверка статуса
```bash
docker-compose ps
```

### 3. Доступ к компонентам
- **API Service**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

## Задачи семинара

### Задача 1: Загрузка изображений
```bash
# Загрузить одно изображение
curl -X POST "http://localhost:8000/upload" \
  -F "file=@test_image.jpg" \
  -F "operations=resize,watermark"

# Проверить статус
curl "http://localhost:8000/status/{job_id}"
```

### Задача 2: Масштабирование workers
```bash
# Увеличить количество workers до 3
docker-compose up -d --scale worker=3

# До 5
docker-compose up -d --scale worker=5
```

### Задача 3: Мониторинг очереди
```bash
# Запустить мониторинг
python monitoring/queue_monitor.py

# Метрики очереди
curl http://localhost:8000/metrics
```

### Задача 4: Нагрузочное тестирование
```bash
# Загрузка 100 изображений
python load_test/bulk_upload.py --count 100 --workers 1

# С разным количеством workers
python load_test/bulk_upload.py --count 100 --workers 3
python load_test/bulk_upload.py --count 100 --workers 5

# Анализ результатов
python load_test/analyze_results.py
```

## Эксперименты

### Эксперимент 1: Отказоустойчивость
```bash
# Остановить один worker во время обработки
docker-compose stop worker

# Наблюдать за перераспределением задач
docker-compose logs -f worker

# Перезапустить
docker-compose start worker
```

### Эксперимент 2: Пиковая нагрузка
```bash
# Создать burst нагрузки
python load_test/burst_test.py --burst-size 50 --interval 5

# Мониторить throughput и latency
python monitoring/performance_monitor.py
```

### Эксперимент 3: Dead Letter Queue
```bash
# Загрузить поврежденное изображение
curl -X POST "http://localhost:8000/upload" \
  -F "file=@corrupted.jpg"

# Проверить DLQ
curl http://localhost:8000/dlq/stats
```

## Метрики для измерения

1. **Throughput**: изображений/секунду
2. **Latency**: время от загрузки до результата
3. **Queue Size**: размер очереди в RabbitMQ
4. **Worker Utilization**: загрузка workers
5. **Failed Tasks**: количество ошибок

## Структура проекта

```
queues/
├── docker-compose.yml
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── config.py
├── worker/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── worker.py
│   └── processors/
│       ├── resize.py
│       ├── watermark.py
│       └── filter.py
├── notification/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── notifier.py
├── monitoring/
│   ├── queue_monitor.py
│   └── performance_monitor.py
├── load_test/
│   ├── bulk_upload.py
│   ├── burst_test.py
│   └── analyze_results.py
└── test_images/
    └── sample.jpg
```

## Очистка

```bash
# Остановить все сервисы
docker-compose down

# Удалить volumes (данные)
docker-compose down -v
```

## Troubleshooting

### RabbitMQ недоступен
```bash
docker-compose logs rabbitmq
docker-compose restart rabbitmq
```

### Worker не обрабатывает задачи
```bash
docker-compose logs worker
# Проверить подключение к RabbitMQ и MinIO
```

### Нет свободного места
```bash
# Очистить старые образы
docker system prune -a

# Очистить volumes
docker volume prune
```
