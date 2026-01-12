from fastapi import FastAPI
from app.tasks import print_message

from app.tasks import task1, task2, task3, sum_results
from celery import group, chord, chain

import logging

# Создание логгера
logger = logging.getLogger("fastapi_app")
logger.setLevel(logging.INFO)
# Форматирование
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Хендлер для вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

app = FastAPI()

@app.post("/send")
def send_message():
    print_message.delay("Hello from FastAPI")
    #print_message.apply_async(args=["Hello from FastAPI",])
    return {"status": "sent"}

@app.get("/chain")
async def do_chain_tasks():
    # Chain: последовательное выполнение
    """
    .s() = signature, нужен для передачи аргументов
    Порядок выполнения: task1 → task2 → task3
    Результат task1 автоматически передаётся task2 и дальше
    """
    workflow = chain(
        task1.s(5),  # 5 * 2 = 10
        task2.s(),  # 10 + 10 = 20
        task3.s()  # 20 ** 2 = 400
    )
    # Тот же chain, но через оператор |
    # workflow = task1.s(5) | task2.s() | task3.s()
    #result = workflow.apply_async(queue="chain_tasks") # Запускает задачи в очереди chain_tasks и возвращает данные о workflow.
    # Для ее обработки надо указать воркеру эту слушать очередь
    result = workflow.apply_async() # Запускает задачи в очереди celery и возвращает данные о workflow

    # Ждём результат
    # final = result.get()
    # print(f"Финальный результат: {final}")  # 400

    return {"task_id": result.id, "status": "processing"}

@app.get("/group")
async def do_group_tasks():
    # Запускаем task1 параллельно с разными аргументами
    """
    Несколько задач выполняются параллельно, и можно дождаться их всех
    Все задачи стартуют одновременно
    Можно собрать результаты после завершения
    """
    job = group(
task1.s(1),   # 1 * 2 = 2
    task1.s(2),   # 2 * 2 = 4
    task1.s(3),   # 3 * 2 = 6
    task1.s(4),   # 4 * 2 = 8
    task1.s(5)    # 5 * 2 = 10
    )
    result = job.apply_async() # Запускает задачи и возвращает данные о workflow

    # Получаем все результаты
    # results = result.get()
    # print(f"Результаты: {results}")  # [2, 4, 6, 8, 10]

    return {"Group group_id": result.id, "status": "processing"}

@app.get("/chord")
async def do_chord_tasks():
    # Параллельно выполняем task1, затем суммируем результаты
    """
    Chord = Group + Callback
    После того как все задачи группы завершены, вызывается callback
    """
    workflow = chord(
        group(
            task1.s(1),  # 1 * 2 = 2
            task1.s(2),  # 2 * 2 = 4
            task1.s(3),  # 3 * 2 = 6
            task1.s(4),  # 4 * 2 = 8
            task1.s(5)  # 5 * 2 = 10
        ),
        sum_results.s()   # sum([2, 4, 6, 8, 10]) = 30
    )
    
    result = workflow.apply_async()

    # Получаем финальный результат
    # final = result.get()
    # print(f"Сумма всех результатов: {final}")  # 30

    return {"Group task_id": result.id, "status": "processing"}