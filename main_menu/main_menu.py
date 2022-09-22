from telegram import ReplyKeyboardMarkup, Update

from constants import MAIN_MENU


async def main_menu(update: Update, _) -> int:
    buttons = [
        ["🔍 SEARCH PRO PLAYERS", "📈 PLAYER'S STATS"],
        ["🔍 SEARCH MATCHES", "🔴 LIVE MATCHES"]
    ]
    keyboard = ReplyKeyboardMarkup(buttons)

    await update.message.reply_text(text="MAIN MENU", reply_markup=keyboard)
    return MAIN_MENU
