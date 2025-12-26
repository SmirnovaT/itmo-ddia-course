# Семинар 4: Quick Reference

## Быстрый старт (5 минут)

```bash
# 1. Запустить систему
./start.sh

# 2. Проверить готовность
python verify_setup.py

# 3. Создать тестовое изображение
cd test_images && python generate_sample.py && cd ..

# 4. Загрузить изображение
curl -X POST "http://localhost:8000/upload" \
  -F "file=@test_images/sample.jpg" \
  -F "operations=resize,watermark"
```

## Основные команды

### Управление системой
```bash
./start.sh              # Запустить все сервисы
./stop.sh               # Остановить сервисы
./stop.sh --clean       # Остановить и удалить данные
./scale_workers.sh 5    # Масштабировать до 5 workers
```

### Мониторинг
```bash
# Логи всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f worker
docker-compose logs -f api

# Мониторинг очередей
cd monitoring && python queue_monitor.py

# Метрики производительности
cd monitoring && python performance_monitor.py

# Статус через API
curl http://localhost:8000/metrics
```

### Нагрузочное тестирование
```bash
cd load_test

# Массовая загрузка
python bulk_upload.py --count 100 --concurrency 10

# Burst тест
python burst_test.py --burst-size 50 --burst-count 3

# Анализ результатов
python analyze_results.py
```

## Эксперименты

### 1. Масштабирование workers
```bash
# Тест с 1 worker
./scale_workers.sh 1
cd load_test && python bulk_upload.py --count 50

# Тест с 5 workers
./scale_workers.sh 5
cd load_test && python bulk_upload.py --count 50

# Сравнить результаты
cd load_test && python analyze_results.py
```

### 2. Отказоустойчивость
```bash
# Запустить нагрузку
cd load_test && python bulk_upload.py --count 100 &

# Убить worker во время обработки
docker stop $(docker ps -q -f name=worker)

# Наблюдать за recovery
docker-compose logs -f
```

### 3. Dead Letter Queue
```bash
# Создать невалидный файл
echo "not an image" > corrupted.jpg

# Загрузить его
curl -X POST "http://localhost:8000/upload" \
  -F "file=@corrupted.jpg"

# Проверить DLQ
curl http://localhost:8000/dlq/stats
```

## Веб-интерфейсы

- **API Docs**: http://localhost:8000/docs
- **RabbitMQ**: http://localhost:15672 (guest/guest)
- **MinIO**: http://localhost:9001 (minioadmin/minioadmin)

## Метрики для измерения

1. **Throughput**: images/second
   ```bash
   curl http://localhost:8000/metrics | jq '.queues.task_queue'
   ```

2. **Latency**: время обработки одного изображения
   ```bash
   docker-compose logs notification | grep "Processing Time"
   ```

3. **Queue Size**: размер очереди
   ```bash
   cd monitoring && python queue_monitor.py
   ```

4. **Worker Utilization**: загрузка workers
   ```bash
   docker-compose ps worker
   ```

## Архитектура

```
Client → API → RabbitMQ → Workers → MinIO
                  ↓
            Notification Service
```

### Компоненты:
- **API** (FastAPI): прием изображений, публикация в очередь
- **RabbitMQ**: очередь задач с DLQ
- **Workers**: обработка (resize, watermark, filter)
- **MinIO**: S3-compatible хранилище
- **Notification**: уведомления о завершении

## Troubleshooting

### Сервисы не запускаются
```bash
docker-compose down -v
docker-compose up -d
docker-compose logs
```

### Workers не обрабатывают задачи
```bash
# Проверить подключение к RabbitMQ
docker-compose logs worker

# Перезапустить workers
docker-compose restart worker
```

### Очередь растет, но ничего не обрабатывается
```bash
# Увеличить workers
./scale_workers.sh 5

# Проверить логи
docker-compose logs -f worker
```

### Проверить, что все работает
```bash
python verify_setup.py
```

## Очистка

```bash
# Остановить и удалить все данные
./stop.sh --clean

# Удалить все Docker ресурсы (опционально)
docker system prune -a
```

## Задачи на семинар

- [ ] Запустить систему и проверить базовую функциональность
- [ ] Провести load test с разным количеством workers (1, 3, 5)
- [ ] Измерить throughput и latency
- [ ] Протестировать отказоустойчивость (kill worker)
- [ ] Проверить Dead Letter Queue на невалидных файлах
- [ ] Провести burst test и проанализировать результаты
- [ ] Задокументировать результаты и выводы
