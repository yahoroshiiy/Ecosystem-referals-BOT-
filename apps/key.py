from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from apps.database.requests import get_categories
from aiogram.utils.keyboard import InlineKeyboardBuilder
from apps.database.requests import get_category_item


main_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='Каталог')]],
    input_field_placeholder='Выберите пункт меню...',
    resize_keyboard=True
)

async def categories():
    all_categories = await get_categories()
    keyboard = InlineKeyboardBuilder()

    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name, callback_data=f"category_{category.id}"))
    
    keyboard.row(InlineKeyboardButton(text='Тех поддержка', callback_data='TP_room'))
    keyboard.row(InlineKeyboardButton(text='Дополнительные бонусы', callback_data='dop_bonus'))

    return keyboard.adjust(2).as_markup()

async def items(category_id):
    all_items = await get_category_item(category_id)
    keyboard = InlineKeyboardBuilder()

    for item in all_items:
        keyboard.add(InlineKeyboardButton(text=item.name, callback_data=f"item_{item.id}"))
    
    keyboard.adjust(2)
    
    keyboard.row(InlineKeyboardButton(text='Категории', callback_data='back_to_categories'))
    keyboard.row(InlineKeyboardButton(text='Тех поддержка', callback_data='TP_room'))
    keyboard.row(InlineKeyboardButton(text='Дополнительные бонусы', callback_data='dop_bonus'))
    keyboard.row(InlineKeyboardButton(text='❌ Отмена', callback_data='to_main'))
    
    return keyboard.as_markup()