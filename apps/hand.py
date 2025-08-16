import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from apps.key import main_kb, categories, items
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import apps.database.requests as rq
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from apps.database.requests import create_support_ticket, get_user_by_tg_id
from aiogram.filters import StateFilter
from apps.database.requests import create_bonus_ticket

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
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

@router.message(F.text == 'Каталог')
async def catalog(message: Message):
    await message.answer(
        '🎁 Выберите категорию товара из нашего каталога:',
        reply_markup=await categories()
    )

@router.callback_query(F.data.startswith('category_'))
async def category(callback: CallbackQuery):
    await callback.answer('✅ Категория выбрана')
    category_id = callback.data.split('_')[1]
    await callback.message.answer(
        '📦 Выберите товар из доступных:',
        reply_markup=await items(category_id)
    )

@router.callback_query(F.data.startswith('item_'))
async def show_item(callback: CallbackQuery):
    item_id = callback.data.split('_')[1]
    item_data = await rq.get_item(item_id)
    
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

@router.callback_query(F.data == 'to_main')
async def back_to_main(callback: CallbackQuery):
    await callback.message.delete()  
    await callback.message.answer(
        "🏠 Вы вернулись в главное меню\n\n"
        "Здесь вы можете:\n"
        "• Выбрать товары из каталога 🛍️\n"
        "• Обратиться в поддержку 🆘\n"
        "• Получить бонусы за рефералов 💰",
        reply_markup=main_kb
    )
    await callback.answer()

@router.callback_query(F.data == 'back_to_categories')
async def back_to_categories(callback: CallbackQuery):
    await callback.message.delete()  
    await callback.message.answer(
        "📂 Выберите интересующую категорию:",
        reply_markup=await categories()
    )
    await callback.answer()

class SupportState(StatesGroup):
    waiting_for_support_message = State()

@router.callback_query(F.data == 'TP_room')
async def TP_room(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🆘 Техническая поддержка\n\n"
        "Напишите ваш вопрос, и мы ответим в ближайшее время.\n"
        "Постарайтесь описать проблему максимально подробно.\n\n"
        "❌ Для отмены используйте /cancel"
    )
    await state.set_state(SupportState.waiting_for_support_message)
    await callback.answer()

@router.message(Command("cancel"), ~StateFilter(None))
async def cancel_support(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == SupportState.waiting_for_support_message:
        await state.clear()
        await message.answer(
            "❌ Запрос в поддержку отменен.\n"
            "Вы можете создать новый запрос в любое время.",
            reply_markup=await categories()
        )
    else:
        await message.answer(
            "ℹ️ Сейчас нет активных действий для отмены.",
            reply_markup=await categories()
        )

@router.message(SupportState.waiting_for_support_message)
async def process_support_message(message: Message, state: FSMContext, bot: Bot):
    if message.text.startswith('/'):
        return
        
    SUPPORT_CHAT_ID = 7268834861
    
    try:
        user = await get_user_by_tg_id(message.from_user.id)
        if not user:
            await message.answer("❌ Ошибка: пользователь не найден.")
            await state.clear()
            return

        ticket = await create_support_ticket(user.id, message.text)
        
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
        print(f"Ошибка: {e}")
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

@router.message(BonusState.waiting_for_bonus_message)
async def process_bonus_message(message: Message, state: FSMContext, bot: Bot):
    if message.text.startswith('/'):
        return
        
    BONUS_CHAT_ID = 7268834861
    
    try:
        user = await get_user_by_tg_id(message.from_user.id)
        if not user:
            await message.answer("❌ Ошибка: пользователь не найден.")
            await state.clear()
            return

        ticket = await create_bonus_ticket(user.id, message.text)
        
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
        print(f"Ошибка: {e}")
        await message.answer(
            "❌ Произошла ошибка при отправке запроса.\n"
            "Попробуйте позже или свяжитесь с поддержкой.",
            reply_markup=await categories()
        )
    
    finally:
        await state.clear()