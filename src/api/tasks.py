from fastapi import APIRouter, Depends, Request
from arq.jobs import Job, JobStatus
from src.api.deps import get_current_user
from src.models.user import User
from loguru import logger

router = APIRouter(prefix="/tasks", tags=["Background Tasks"])

@router.post("/submit")
async def submit_background_task(
    task_name: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Отправляет тяжелую задачу в фоновый воркер и сразу возвращает ID задачи."""
    arq_pool = request.app.state.arq_pool
    
    # Отправляем задачу в очередь Redis
    job = await arq_pool.enqueue_job(
        "process_heavy_ai_task",
        task_name,
        current_user.id
    )
    
    logger.info(f"Юзер {current_user.email} поставил задачу {job.job_id} в очередь.")
    
    return {
        "message": "Задача принята в обработку.",
        "task_id": job.job_id,
        "status": "queued"
    }


@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Проверяет статус исполнения фоновой задачи по ее ID."""
    arq_pool = request.app.state.arq_pool
    
    # Инициализируем объект задачи по её ID
    job = Job(task_id, redis=arq_pool)
    
    # Запрашиваем актуальный статус у Redis
    status = await job.status()
    
    # Если задача вообще не найдена в Redis
    if status == JobStatus.not_found:
        return {
            "task_id": task_id,
            "status": "not_found",
            "result": None
        }
    
    # Если задача еще в очереди или выполняется
    if status != JobStatus.complete:
        return {
            "task_id": task_id,
            "status": status.value,  # вернет "queued" или "in_progress"
            "result": None
        }
        
    # Если задача успешно завершена, забираем результат
    job_info = await job.result_info()
    
    return {
        "task_id": task_id,
        "status": "completed",
        "result": job_info.result if job_info else None
    }
