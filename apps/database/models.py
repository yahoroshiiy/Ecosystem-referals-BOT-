from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase , Mapped , mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from datetime import datetime
from sqlalchemy import DateTime


engine = create_async_engine(url='postgresql+asyncpg://cco:Rahagatop1@localhost/ref')

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs,DeclarativeBase):
    pass
class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
class Category(Base):
    __tablename__ = 'categories'
    id: Mapped[int] = mapped_column(primary_key = True)
    name: Mapped[str] = mapped_column(String(25))

class Item(Base):
    __tablename__ = 'items'
    id: Mapped[int] = mapped_column(primary_key = True)
    name: Mapped[str] = mapped_column(String(25))
    reward: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column(String(5000))
    category: Mapped[int] = mapped_column(ForeignKey('categories.id'))

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
class SupportTicket(Base):
    __tablename__ = 'support_tickets'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    message: Mapped[str] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(20), default='open')  # open, answered, closed
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,  # Автоматически подставит текущее время при создании
        nullable=False
    )
class BonusTicket(Base):
    __tablename__ = 'bonus_tickets'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    message: Mapped[str] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(20), default='open')  # open, answered, closed
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,  # Автоматически подставит текущее время при создании
        nullable=False
    )
class ResponseTickets(Base):
    __tablename__ = 'response_tickets'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    message: Mapped[str] = mapped_column(String(1000))

