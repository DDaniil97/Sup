from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def start_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✍️ Написать обращение")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
