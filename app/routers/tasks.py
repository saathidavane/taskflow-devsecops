import logging
import uuid

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select

from app.deps import CurrentUser, DbSession
from app.models import Task, TaskStatus
from app.schemas import TaskCreate, TaskRead, TaskUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_owned_task(db: DbSession, user: CurrentUser, task_id: uuid.UUID) -> Task:
    task = db.scalar(select(Task).where(Task.id == task_id, Task.owner_id == user.id))
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return task


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: DbSession, user: CurrentUser) -> Task:
    task = Task(**payload.model_dump(mode="json"), owner_id=user.id)
    db.add(task)
    db.commit()
    logger.info("task_created", extra={"task_id": str(task.id), "user_id": str(user.id)})
    return task


@router.get("", response_model=list[TaskRead])
def list_tasks(
    db: DbSession,
    user: CurrentUser,
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[Task]:
    stmt = select(Task).where(Task.owner_id == user.id)
    if status_filter:
        stmt = stmt.where(Task.status == status_filter.value)
    stmt = stmt.order_by(Task.created_at.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt).all())


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: uuid.UUID, db: DbSession, user: CurrentUser) -> Task:
    return _get_owned_task(db, user, task_id)


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(task_id: uuid.UUID, payload: TaskUpdate, db: DbSession, user: CurrentUser) -> Task:
    task = _get_owned_task(db, user, task_id)
    data = payload.model_dump(exclude_unset=True, mode="json")
    for required_field in ("title", "status"):
        if required_field in data and data[required_field] is None:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, f"{required_field} cannot be null"
            )
    for key, value in data.items():
        setattr(task, key, value)
    db.commit()
    logger.info("task_updated", extra={"task_id": str(task.id), "user_id": str(user.id)})
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: uuid.UUID, db: DbSession, user: CurrentUser) -> Response:
    task = _get_owned_task(db, user, task_id)
    db.delete(task)
    db.commit()
    logger.info("task_deleted", extra={"task_id": str(task_id), "user_id": str(user.id)})
    return Response(status_code=status.HTTP_204_NO_CONTENT)
