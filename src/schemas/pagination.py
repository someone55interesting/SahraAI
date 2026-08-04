import math
from typing import Generic, TypeVar, List
from pydantic import BaseModel

# Объявляем generic-тип (обобщенный тип), который будем подставлять
T = TypeVar('T')

class Page(BaseModel, Generic[T]):
    """
    Универсальная схема для пагинации.
    Подходит для любых моделей. Пример использования: Page[MessageResponse], Page[UserResponse].
    """
    items: List[T]       # Сами элементы страницы
    total: int           # Общее количество элементов в БД
    page: int            # Текущая страница
    size: int            # Количество элементов на странице (limit)
    total_pages: int     # Общее количество страниц
    has_next: bool       # Есть ли следующая страница
    has_prev: bool       # Есть ли предыдущая страница

    @classmethod
    def create(cls, items: List[T], total: int, page: int, size: int):
        """Фабричный метод для автоматического расчета всех полей."""
        total_pages = math.ceil(total / size) if size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


