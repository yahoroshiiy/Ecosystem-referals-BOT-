from apps.database.models import async_session
from apps.database.models import User, Category, Item, SupportTicket, BonusTicket
from sqlalchemy import select
from datetime import datetime

async def set_user(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            user = User(tg_id=tg_id)
            session.add(user)
            await session.commit()
        return user

async def get_categories():
    async with async_session() as session:
        return await session.scalars(select(Category))

async def get_category_item(category_id):
    async with async_session() as session:
        return await session.scalars(select(Item).where(Item.category == int(category_id)))

async def get_item(item_id):
    async with async_session() as session:
        return await session.scalar(select(Item).where(Item.id == int(item_id)))

async def get_user_by_tg_id(tg_id: int):
    async with async_session() as session:
        return await session.scalar(select(User).where(User.tg_id == tg_id))

async def create_support_ticket(user_id: int, message: str):
    async with async_session() as session:
        try:
            user = await session.scalar(select(User).where(User.id == user_id))
            if not user:
                print(f"Ошибка: пользователь с id {user_id} не найден")
                return None
            ticket = SupportTicket(
                user_id=user_id,
                message=message,
                created_at=datetime.utcnow()
            )
            session.add(ticket)
            await session.commit()
            await session.refresh(ticket)
            return ticket
        except Exception as e:
            print(f"Ошибка при создании тикета поддержки: {e}")
            await session.rollback()
            return None

async def create_bonus_ticket(user_id: int, message: str):
    async with async_session() as session:
        try:
            user = await session.scalar(select(User).where(User.id == user_id))
            if not user:
                print(f"Ошибка: пользователь с id {user_id} не найден")
                return None
            ticket = BonusTicket(
                user_id=user_id,
                message=message,
                created_at=datetime.utcnow()
            )
            session.add(ticket)
            await session.commit()
            await session.refresh(ticket)
            return ticket
        except Exception as e:
            print(f"Ошибка при создании бонусного тикета: {e}")
            await session.rollback()
            return None