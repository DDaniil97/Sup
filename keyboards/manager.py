from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def take_ticket_kb(ticket_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🟢 Взяти в роботу",
                    callback_data=f"take_ticket:{ticket_id}"
                )
            ]
        ]
    )
