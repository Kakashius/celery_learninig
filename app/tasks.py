from app.celery_app import celery_app
from celery.exceptions import Retry, SoftTimeLimitExceeded

import time
import logging

# Получаем тот же логгер по имени
# logger = logging.getLogger("fastapi_app")
# Можно не использовать логгер, если для воркера запущен флаг --loglevel=info

@celery_app.task
def print_message(message: str):
    """
    Это обычная функция, но:
    1) обёрнута в @task
    2) теперь может жить в очереди
    3) может ничего не возвращать
    """
    print(f"Celery got message: {message}")
    #logger.info(f"Celery got message: {message}")


# RETRY задача
@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def risky_task(self, x):
    """
    bind=True → позволяет обращаться к self.retry, нужен параметр self
    max_retries → сколько раз пробуем
    default_retry_delay → сколько ждать между попытками
    self.retry() → повторяет задачу, сохраняет исключение в backend
    """
    try:
        # опасная операция
        result = 10 / x  # например, деление на ноль может быть
        return result
    except Exception as e:
        # повторяем задачу через 5 секунд, максимум 3 раза
        raise self.retry(exc=e)

# TIMEOUT задача - ограничить время выполнения задачи, чтобы worker не завис
@celery_app.task(time_limit=10, soft_time_limit=5)
def long_task():
    """
    soft_time_limit → воркер пытается корректно завершить задачу (можно поймать SoftTimeLimitExceeded)
    time_limit → принудительно убивает процесс, если soft_time_limit не сработал
    """
    # выполняется долго
    try:
        time.sleep(20)  # спит 20 секунд
        return "завершено"
    except SoftTimeLimitExceeded:
        # Перехватили, но игнорируем - продолжаем работу!
        time.sleep(20)  # продолжаем спать
        return "всё равно завершено"

# RATE LIMIT задача - Если лимит превышен, задачи ждут в очереди, но не падают
@celery_app.task(rate_limit="10/m")  # максимум 10 задач в минуту
def api_call_task():
    """
    Поддерживаются форматы: "10/s", "100/h", "50/m"
    """
    ...

from celery_once import QueueOnce
# celery_once позволяет гарантировать, что одна задача выполняется одновременно только один раз,
# даже при нескольких воркерах - задача становится атомарной, помогает избегать дублирование обработки
# Периодическая задача, см celery_app.py
@celery_app.task(base=QueueOnce, once={'graceful': True})
def say_hello(name):
    print(f"Hello, {name}!")
    # logger.info(f"Hello, {name}!")

@celery_app.task
def task1(x):
    """Умножает число на 2"""
    print(f"Task1: получил {x}")
    # logger.info(f"Task1: получил {x}")
    time.sleep(2)
    result = x * 2
    print(f"Task1: возвращает {result}")
    # logger.info(f"Task1: возвращает {result}")
    return result

@celery_app.task
def task2(x):
    """Прибавляет 10"""
    print(f"Task2: получил {x}")
    # logger.info(f"Task2: получил {x}")
    time.sleep(2)
    result = x + 10
    print(f"Task2: возвращает {result}")
    # logger.info(f"Task2: возвращает {result}")
    return result

@celery_app.task
def task3(x):
    """Возводит в квадрат"""
    print(f"Task3: получил {x}")
    # logger.info(f"Task3: получил {x}")
    time.sleep(2)
    result = x ** 2
    print(f"Task3: возвращает {result}")
    # logger.info(f"Task3: возвращает {result}")
    return result

@celery_app.task
def sum_results(results):
    """Суммирует список результатов"""
    print(f"Sum: получил {results}")
    # logger.info(f"Sum: получил {results}")
    total = sum(results)
    print(f"Sum: возвращает {total}")
    # logger.info(f"Sum: возвращает {total}")
    return total