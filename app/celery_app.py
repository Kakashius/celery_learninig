from celery import Celery

from celery.schedules import crontab

import os

"""
По умолчанию у каждого сервера redis-server по 16 баз данных (0 - 15)
"""
celery_app = Celery(
    "worker",
    # broker="redis://localhost:6379/0",  # В базу 0 - отправка фоновых задач для celery worker
    # backend="redis://localhost:6379/1", # В базу 1 - отправка результатов от celery worker
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND"),
)

celery_app.autodiscover_tasks(["app"])  # Ищи в папке (пакет) app модуль tasks.py
# Время хранения результатов задач в backend_result (секунды)
celery_app.conf.result_expires = 3600  # 1 час

# Повторное подключение к брокеру при разрыве
celery_app.conf.broker_connection_retry = True
celery_app.conf.broker_connection_retry_on_startup = True

# Максимальное количество попыток (None = бесконечно)
celery_app.conf.broker_connection_max_retries = None

# ВАЖНО: Настройки для celery-once
celery_app.conf.update(
    # Настройки ONCE
    ONCE={
        'backend': 'celery_once.backends.Redis',
        'settings': {
            'url': os.getenv("CELERY_BROKER_URL"),
            'default_timeout': 60 * 60  # максимум 1 час на блокировку задачи при ее выполнении
        }
    },
    # Настройки Flower, чтобы Flower видел воркера
    worker_send_task_events=True,  # для Flower
    task_send_sent_event=True      # чтобы видеть отправленные задачи

)


# Периодическая задача
"""
beat_schedule — словарь с задачами и расписанием
"task" — путь к задаче (app.tasks.say_hello)
"schedule" — интервал (секунды) или crontab для более сложных расписаний
"args" — аргументы задачи
"""
celery_app.conf.beat_schedule = {
    "say-hello-every-10-seconds": {
        "task": "app.tasks.say_hello",
        "schedule": 10.0,  # каждые 10 секунд
        "args": ("world",),
        "options": {"queue": "celery"}  # <- явно отправит задачу в очередь celery для воркера
    },
    "say-hello-every-morning": {
        "task": "app.tasks.say_hello",
        "schedule": crontab(hour=8, minute=30, day_of_week="sat,sun"),  # Выполнится в 08:30 в субботу и воскр
        "args": ("world",),
        "options": {"queue": "celery"}
    },
}
celery_app.conf.timezone = "UTC"

# Late ACK (по умолчанию, РЕКОМЕНДУЕТСЯ)
celery_app.conf.task_acks_late = True

# Early ACK (НЕ РЕКОМЕНДУЕТСЯ - задачи могут потеряться)
# celery_app.conf.task_acks_late = False
