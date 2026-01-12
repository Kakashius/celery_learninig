<h4> Структура проекта с Celery в FastAPI </h4>

```
project/
│
├── app/
│   ├── __init__.py
│   ├── main.py        ← FastAPI
│   ├── celery_app.py  ← Celery instance
│   └── tasks.py       ← Celery tasks
│
├── requirements.txt
├── Dockerfile
└── docker-compose.yml

```

<h4>Роли файлов: </h4>

- main.py — HTTP
- celery_app.py — инициализация и настройка Celery, подключение Redis
- tasks.py — фоновые функции для обработки

<h4>Самая важная строка в Celery</h4>

1) Просто:
`some_task.delay(arg1, arg2)`
2) Гибко:
```
some_task.apply_async(
    args=[arg1, arg2],
    queue='priority',  # ← явное указание очереди, где будет выполнятся задача (воркер нужно запусить для этой очереди, по умолчанию очередь = 'celery')
    countdown=60,  # запустится через 60 секунд,
    priority=0,  # 0 = highest, 9 = lowest
    link=log_result.s(),  # callback функция, запустится после успеха
    link_error=handle_error.s(),  # callback функция, запустится при ошибке
    countdown=600   # запустится через 10 минут
    eta=datetime.utcnow() + timedelta(minutes=10)   # через конкретное время

)
```

<h4>Запуск процесса Celery воркера</h4>

```angular2html
celery -A app.celery_app worker
│      │  │           │
│      │  │           └─ команда (запустить воркер)
│      │  └─ имя приложения Celery
│      └─ флаг --app (сокращённо -A)
└─ CLI утилита Celery
```

<h4>Запуск Celery воркера для отдельной очереди</h4>

```angular2html
celery -A myapp worker -Q emails -n worker_emails@%h (необязательно)
                                │  └─────┬──────┘
                                │        └─ hostname
                                └─ флаг --hostname (сокращённо -n)
worker_emails — название воркера (любое имя на ваш выбор)
@ — разделитель
%h — переменная, которая заменяется на hostname машины
```

<h4>Celery плох в:</h4>

- тяжёлые CPU-bound задачи (воркеры заняты на 100% CPU). Лучше отдельные сервисы (C++, Go, Rust)
- простой асинхронный код. Лучше BackgroundTasks FastAPI или asyncio.create_task

<h4>Доступные команды Celery:</h4>

```angular2html
# Основные команды
celery -A celery_app worker     # Запустить воркер
celery -A celery_app beat       # Запустить планировщик периодических задач
celery -A celery_app flower     # Запустить веб-мониторинг (требует flower)
celery -A celery_app events     # Мониторинг событий
celery -A celery_app shell      # Интерактивная оболочка
celery -A celery_app inspect    # Инспектирование воркеров
celery -A celery_app control    # Управление воркерами
celery -A celery_app purge      # Очистить все задачи из очередей
celery -A celery_app call       # Вызвать задачу из командной строки
celery -A celery_app result     # Показать результат задачи по ID
celery -A celery_app migrate    # Миграция задач между брокерами
celery -A celery_app graph      # Генерация графа задач
celery -A celery_app upgrade    # Обновление настроек/кода
celery -A celery_app logtool    # Утилиты для логов
celery -A celery_app amqp       # AMQP утилиты
```

<h4>Статус задач, извлеченные из очереди и закинутые в backend result:</h4>

| Поведение                 | Статус задачи в backend |
| ------------------------- | ----------------------- |
| В очереди                 | `PENDING`               |
| Выполняется               | `STARTED`               |
| Повторяется               | `RETRY`                 |
| Неудача после max_retries | `FAILURE`               |
| Успешно                   | `SUCCESS`               |

<h4>Как получить результат задачи запросом клиента?</h4>

ОБЯЗАТЕЛЬНО: нужен result_backend для сохранения результата задачи!\
Шаги:

1) при запуске фоновой задачи:
`result = my_task.delay(data)`
или
`result = my_task.apply_async(args=[*data])`
возвращается task_id задачи. Его нужно вернуть клиенту

2) При запросе клиент должен указать этот id и вызывать:
```
from celery.result import AsyncResult, GroupResult

res = AsyncResult(task_id, app=celery_app)
или res = AsyncResult(task_id, app=celery_app) для результата групповых задач
```

<H3>Celery Beat</H3>
**Celery Beat** — **отдельный процесс**, который ставит задачи в очередь по расписанию.

Архитектура:
```angular2html
Periodic task schedule
         ↓
     Celery Beat
         ↓
      Broker (Redis)
         ↓
     Celery Worker
         ↓
   Выполнение задачи

```

Celery Beat **не предназначен** для периодической/отложенной обработки задачи конкретных пользователей:

- НЕ слушает HTTP
- НЕ реагирует на пользователя
- НЕ смотрит в очередь

Для этих целей используются воркеры Celery для отложенных задач.

<h4>Запуск процесса Celery Beat:</h4>

`celery -A celery_app beat --concurrency=4 --loglevel=info`
--concurrency=4 - до 4 задач извлекаются параллельно

<H3>Celery Flower</H3>

Flower — веб-интерфейс для мониторинга Celery
`pip install flower`
Запуск Flower - как отдельный процесс:
`celery -A celery_app flower --port=5555`
- -A celery_app → указываем объект Celery
- --port=5555 → веб-интерфейс будет доступен по http://localhost:5555

<H3>Chain / Group / Chord</H3>

- Chain (цепочка задач)
- Group (параллельные задачи)
- Chord (группировка результатов + колбэк (опционально))

Для Chain / Group / Chord **нужен backend redis**, чтобы хранить результаты промежуточных задач.
```
Внутри задач можно вызывать свой Chain / Group / Chord:
Chain(task1, chord(group(...), task3))
```

<H4>Объект result = workflow.apply_async()</H4>

result:
1) AsyncResult - если chain, chord
2) GroupResult - если group
Основные операции с результатом:
```angular2html
# Получить ID задачи
task_id = result.id
# Проверить готовность
if result.ready():
    print("Задача завершена!")
else:
    print("Задача ещё выполняется...")

# Проверить успешность
if result.successful():
    print("Задача выполнена успешно!")
else:
    print("Задача провалилась или ещё выполняется")

# Проверить неудачу
if result.failed():
    print("Задача провалилась с ошибкой")

# Получить текущий статус
status = result.status
# Возможные значения: 'PENDING', 'STARTED', 'SUCCESS', 'FAILURE', 
#                      'RETRY', 'REVOKED'
# Блокирующее ожидание результата (с таймаутом)
try:
    final_result = result.get(timeout=30)  # ждёт до 30 секунд
    print(f"Результат: {final_result}")
except TimeoutError:
    print("Задача не завершилась за 30 секунд")
# Получить текущую информацию (полезно для прогресс-баров)
info = result.info

# Отменить задачу
result.revoke()

# Отменить с убийством процесса (если задача уже выполняется)
result.revoke(terminate=True)

# Отменить с сигналом
result.revoke(terminate=True, signal='SIGKILL')

# Удалить результат из Redis/БД
result.forget()
# После forget() повторный get() вернёт None
```

<H3>Надежность при потере задач Celery</H3>
1) По умолчанию Celery использует "late acknowledgement" — задача помечается как выполненная ПОСЛЕ успешного завершения, а не при получении.

```angular2html
# celery_config.py

# Late ACK (по умолчанию, РЕКОМЕНДУЕТСЯ)
celery_app.conf.task_acks_late = True

# Early ACK (НЕ РЕКОМЕНДУЕТСЯ - задачи могут потеряться)
# celery_app.conf.task_acks_late = False
```

**Как это работает:**
```
Late ACK (task_acks_late=True):
1. Воркер получает задачу из очереди
2. Задача остаётся в очереди (не удаляется)
3. Воркер выполняет задачу
4. ✅ Если успех → задача удаляется из очереди
5. ❌ Если воркер падает → задача остаётся в очереди
6. Другой воркер подхватит задачу

Early ACK (task_acks_late=False):
1. Воркер получает задачу
2. ❌ Задача СРАЗУ удаляется из очереди
3. Воркер начинает выполнение
4. ❌ Если воркер падает → задача ПОТЕРЯНА навсегда!
```
2) Prefetch Limit (ограничение предзагрузки)
```angular2html
# Ограничить количество задач, которые воркер берёт заранее
celery_app.conf.worker_prefetch_multiplier = 1

# По умолчанию = 4, что означает:
# - Воркер с concurrency=4 предзагрузит 16 задач (4 * 4)
# - Если воркер упадёт, все 16 задач потеряются (при early ACK)

# При prefetch_multiplier=1:
# - Воркер берёт ровно 1 задачу
# - Меньше риск потери при падении
```

<H3>Масштабируемость Celery и Redis:</H3>

- Для broker_url и result_backend *всегда* указывается мастер-нода redis!
- Каждую задачу можно поместить в отдельную очередь, чтобы отдельный воркер слушал её.
- Можно запускать несколько контейнеров одного ворекра, но нужно настроить celery_once и prefetch_multiplier=1 для ищбежания дублирования обработки задач.
- Celery Beat и Flower масштабировать не нужно, т.к. Beat всего лишь планировщик (не выполняет задачи), Flower - инструмеент мониторнинга

