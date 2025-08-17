import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command, StateFilter
from apps.key import main_kb, categories, items
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import apps.database.requests as rq
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from apps.database.models import SupportTicket, BonusTicket, ResponseTickets, User, async_session
from sqlalchemy import select

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    try:
        await rq.set_user(message.from_user.id)
        await message.answer(
            '🌟 Добро пожаловать в наш бонусный бот! 🌟\n\n'
            'Здесь вы можете получить вознаграждение за выполнение заданий и приглашение друзей.',
            reply_markup=main_kb
        )
        await message.answer(
            'Выберите действие в меню ниже 👇',
            reply_markup=main_kb
        )
    except Exception as e:
        print(f"Ошибка в cmd_start: {e}")
        await message.answer("❌ Ошибка при запуске бота.")

@router.message(Command("cancel"), ~StateFilter(None))
async def cancel_support(message: Message, state: FSMContext):
    try:
        current_state = await state.get_state()
        if current_state in [SupportState.waiting_for_support_message, BonusState.waiting_for_bonus_message]:
            await state.clear()
            await message.answer(
                "❌ Запрос отменен.\n"
                "Вы можете создать новый запрос в любое время.",
                reply_markup=await categories()
            )
        else:
            await message.answer(
                "ℹ️ Сейчас нет активных действий для отмены.",
                reply_markup=await categories()
            )
    except Exception as e:
        print(f"Ошибка в cancel_support: {e}")
        await message.answer("❌ Ошибка при отмене запроса.")

@router.message(F.text == 'Каталог')
async def catalog(message: Message):
    try:
        await message.answer(
            '🎁 Выберите категорию товара из нашего каталога:',
            reply_markup=await categories()
        )
    except Exception as e:
        print(f"Ошибка в catalog: {e}")
        await message.answer("❌ Ошибка при загрузке каталога.")

@router.callback_query(F.data.startswith('category_'))
async def category(callback: CallbackQuery):
    try:
        await callback.answer('✅ Категория выбрана')
        category_id = callback.data.split('_')[1]
        await callback.message.answer(
            '📦 Выберите товар из доступных:',
            reply_markup=await items(category_id)
        )
    except Exception as e:
        print(f"Ошибка в category: {e}")
        await callback.message.answer("❌ Ошибка при выборе категории.")

@router.callback_query(F.data.startswith('item_'))
async def show_item(callback: CallbackQuery):
    try:
        item_id = callback.data.split('_')[1]
        item_data = await rq.get_item(item_id)
        if not item_data:
            await callback.message.answer("❌ Товар не найден.")
            return
        
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(
            text='⬅️ Назад к товарам', 
            callback_data=f'category_{item_data.category}'
        ))
        keyboard.add(InlineKeyboardButton(
            text='📂 Категории', 
            callback_data='back_to_categories'
        ))
        keyboard.add(InlineKeyboardButton(
            text='🏠 Главное меню', 
            callback_data='to_main'
        ))
        
        await callback.message.answer(
            f'🎁 {item_data.name}\n\n'
            f'💰 Награда: {item_data.reward}\n\n'
            f'📝 Описание: {item_data.description}\n\n'
            'Выберите действие ниже 👇',
            reply_markup=keyboard.adjust(2).as_markup()
        )
        await callback.answer()
    except Exception as e:
        print(f"Ошибка в show_item: {e}")
        await callback.message.answer("❌ Ошибка при отображении товара.")

@router.callback_query(F.data == 'to_main')
async def back_to_main(callback: CallbackQuery):
    try:
        await callback.message.delete()
        await callback.message.answer(
            "🏠 Вы вернулись в главное меню\n\n"
            "Здесь вы можете:\n"
            "• Выбрать товары из каталога 🛍\n"
            "• Обратиться в поддержку 🆘\n"
            "• Получить бонусы за рефералов 💰",
            reply_markup=main_kb
        )
        await callback.answer()
    except Exception as e:
        print(f"Ошибка в back_to_main: {e}")
        await callback.message.answer("❌ Ошибка при возврате в главное меню.")

@router.callback_query(F.data == 'back_to_categories')
async def back_to_categories(callback: CallbackQuery):
    try:
        await callback.message.delete()
        await callback.message.answer(
            "📂 Выберите интересующую категорию:",
            reply_markup=await categories()
        )
        await callback.answer()
    except Exception as e:
        print(f"Ошибка в back_to_categories: {e}")
        await callback.message.answer("❌ Ошибка при возврате к категориям.")

class SupportState(StatesGroup):
    waiting_for_support_message = State()

@router.callback_query(F.data == 'TP_room')
async def TP_room(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.answer(
            "🆘 Техническая поддержка\n\n"
            "Напишите ваш вопрос, и мы ответим в ближайшее время.\n"
            "Постарайтесь описать проблему максимально подробно.\n\n"
            "❌ Для отмены используйте /cancel"
        )
        await state.set_state(SupportState.waiting_for_support_message)
        await callback.answer()
    except Exception as e:
        print(f"Ошибка в TP_room: {e}")
        await callback.message.answer("❌ Ошибка при открытии техподдержки.")

@router.message(SupportState.waiting_for_support_message)
async def process_support_message(message: Message, state: FSMContext, bot: Bot):
    if message.text.startswith('/'):
        return
        
    SUPPORT_CHAT_ID = 7268834861
    
    try:
        user = await rq.get_user_by_tg_id(message.from_user.id)
        if not user:
            await message.answer("❌ Ошибка: пользователь не найден.")
            await state.clear()
            return

        ticket = await rq.create_support_ticket(user.id, message.text)
        if not ticket:
            await message.answer("❌ Не удалось создать обращение.")
            await state.clear()
            return

        user_info = f"👤 ID: {message.from_user.id}\nИмя: {message.from_user.full_name}"
        if message.from_user.username:
            user_info += f"\n🔗 @{message.from_user.username}"
        
        await bot.send_message(
            SUPPORT_CHAT_ID,
            f"🆘 НОВЫЙ ЗАПРОС #{ticket.id}\n\n"
            f"{user_info}\n"
            f"🕒 {ticket.created_at}\n\n"
            f"📄 Сообщение:\n{message.text}"
        )
        
        await message.answer(
            "✅ Ваш запрос принят!\n\n"
            f"🔢 Номер обращения: #{ticket.id}\n"
            "⏳ Ожидайте ответа в ближайшее время.",
            reply_markup=await categories()
        )
    except Exception as e:
        print(f"Ошибка в process_support_message: {e}")
        await message.answer(
            "❌ Произошла ошибка при отправке запроса.\n"
            "Попробуйте позже или свяжитесь с нами другим способом.",
            reply_markup=await categories()
        )
    finally:
        await state.clear()

class BonusState(StatesGroup):
    waiting_for_bonus_message = State()

@router.callback_query(F.data == 'dop_bonus')
async def dop_bonus(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.answer(
            "💰 ДОПОЛНИТЕЛЬНЫЕ БОНУСЫ 💰\n\n"
            "Приглашайте друзей и получайте бонусы:\n\n"
            "🔹 3+ реферала = +10% к выплате\n"
            "🔹 5+ рефералов = +15% к выплате\n"
            "🔹 15+ рефералов = +30% к выплате\n\n"
            "📌 Для получения бонуса отправьте:\n"
            "1. Скриншоты выполненных заданий\n"
            "2. Номер карты для выплаты\n"
            "3. Ваш контакт для связи\n\n"
            "❌ Для отмены используйте /cancel"
        )
        await state.set_state(BonusState.waiting_for_bonus_message)
        await callback.answer()
    except Exception as e:
        print(f"Ошибка в dop_bonus: {e}")
        await callback.message.answer("❌ Ошибка при открытии бонусов.")

@router.message(BonusState.waiting_for_bonus_message)
async def process_bonus_message(message: Message, state: FSMContext, bot: Bot):
    if message.text.startswith('/'):
        return
        
    BONUS_CHAT_ID = 7268834861
    
    try:
        user = await rq.get_user_by_tg_id(message.from_user.id)
        if not user:
            await message.answer("❌ Ошибка: пользователь не найден.")
            await state.clear()
            return

        ticket = await rq.create_bonus_ticket(user.id, message.text)
        if not ticket:
            await message.answer("❌ Не удалось создать запрос на бонус.")
            await state.clear()
            return
        
        user_info = f"👤 ID: {message.from_user.id}\nИмя: {message.from_user.full_name}"
        if message.from_user.username:
            user_info += f"\n🔗 @{message.from_user.username}"
        
        await bot.send_message(
            BONUS_CHAT_ID,
            f"💰 ЗАПРОС НА БОНУС #{ticket.id}\n\n"
            f"{user_info}\n"
            f"🕒 {ticket.created_at}\n\n"
            f"📄 Данные:\n{message.text}"
        )
        
        await message.answer(
            "🎉 Запрос на бонус принят!\n\n"
            f"🔢 Номер заявки: #{ticket.id}\n"
            "⏳ Ожидайте проверки и выплаты в течение 24 часов.",
            reply_markup=await categories()
        )
    except Exception as e:
        print(f"Ошибка в process_bonus_message: {e}")
        await message.answer(
            "❌ Произошла ошибка при отправке запроса.\n"
            "Попробуйте позже или свяжитесь с поддержкой.",
            reply_markup=await categories()
        )
    finally:
        await state.clear()

@router.message(Command('ticketsup'))
async def list_support_tickets(message: Message):
    try:
        async with async_session() as session:
            tickets = await session.scalars(select(SupportTicket).order_by(SupportTicket.id))
            tickets = list(tickets)
            if not tickets:
                await message.answer("❌ Нет активных тикетов поддержки.")
                return
            
            response = "🆘 Список тикетов поддержки:\n\n"
            for ticket in tickets:
                user = await session.scalar(select(User).where(User.id == ticket.user_id))
                user_info = f"👤 TG ID: {user.tg_id if user else 'Не найден'}"
                response += (
                    f"🔢 Тикет #{ticket.id}\n"
                    f"{user_info}\n"
                    f"🕒 {ticket.created_at}\n"
                    f"📄 Сообщение: {ticket.message}\n"
                    f"📊 Статус: {ticket.status}\n\n"
                )
            
            await message.answer(response)
    except Exception as e:
        print(f"Ошибка в ticketsup: {e}")
        await message.answer("❌ Ошибка при получении тикетов поддержки.")

@router.message(Command('ticketbon'))
async def list_bonus_tickets(message: Message):
    try:
        async with async_session() as session:
            tickets = await session.scalars(select(BonusTicket).order_by(BonusTicket.id))
            tickets = list(tickets)
            if not tickets:
                await message.answer("❌ Нет активных бонусных тикетов.")
                return
            
            response = "💰 Список бонусных тикетов:\n\n"
            for ticket in tickets:
                user = await session.scalar(select(User).where(User.id == ticket.user_id))
                user_info = f"👤 TG ID: {user.tg_id if user else 'Не найден'}"
                response += (
                    f"🔢 Тикет #{ticket.id}\n"
                    f"{user_info}\n"
                    f"🕒 {ticket.created_at}\n"
                    f"📄 Сообщение: {ticket.message}\n"
                    f"📊 Статус: {ticket.status}\n\n"
                )
            
            await message.answer(response)
    except Exception as e:
        print(f"Ошибка в ticketbon: {e}")
        await message.answer("❌ Ошибка при получении бонусных тикетов.")

class AnswerState(StatesGroup):
    waiting_for_answer_message = State()

@router.message(Command('answer'))
async def answer_ticket_command(message: Message, state: FSMContext, bot: Bot):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("❌ Используйте формат: /answer <номер_тикета> <текст_ответа>")
        return
    
    try:
        ticket_id = int(args[1])
        answer_text = args[2]
    except ValueError:
        await message.answer("❌ Номер тикета должен быть числом.")
        return

    try:
        async with async_session() as session:
            # Проверяем наличие тикета
            support_ticket = await session.scalar(select(SupportTicket).where(SupportTicket.id == ticket_id))
            bonus_ticket = await session.scalar(select(BonusTicket).where(BonusTicket.id == ticket_id))
            
            if not support_ticket and not bonus_ticket:
                await message.answer(f"❌ Тикет #{ticket_id} не найден.")
                return
            
            ticket = support_ticket or bonus_ticket
            user = await session.scalar(select(User).where(User.id == ticket.user_id))
            
            if not user:
                await message.answer("❌ Пользователь не найден.")
                return

            # Сохраняем tg_id до закрытия сессии
            user_tg_id = user.tg_id
            if not user_tg_id:
                await message.answer("❌ У пользователя отсутствует TG ID.")
                return

            # Создаём ответ
            response = ResponseTickets(
                user_id=user.id,
                message=answer_text
            )
            ticket.status = 'closed'
            session.add(response)
            
            # Сохраняем в базу
            try:
                await session.commit()
                print(f"Успешно сохранён ответ для тикета #{ticket_id}")
            except Exception as commit_error:
                print(f"Ошибка при коммите в answer: {commit_error}")
                await session.rollback()
                await message.answer("❌ Ошибка при сохранении ответа в базе.")
                return

        # Отправляем сообщение пользователю вне сессии
        try:
            print(f"Попытка отправки сообщения пользователю {user_tg_id} для тикета #{ticket_id}")
            await bot.send_message(
                user_tg_id,
                f"📬 Ответ на тикет #{ticket_id}:\n\n{answer_text}"
            )
            await message.answer(f"✅ Ответ на тикет #{ticket_id} отправлен пользователю, тикет закрыт.")
        except Exception as send_error:
            print(f"Ошибка при отправке сообщения пользователю {user_tg_id}: {send_error}")
            await message.answer(f"❌ Ошибка при отправке сообщения пользователю (TG ID: {user_tg_id}), но ответ сохранён в базе.")
    except Exception as e:
        print(f"Общая ошибка в answer: {e}")
        await message.answer("❌ Ошибка при обработке ответа на тикет.")