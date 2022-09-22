from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove

from constants import MAIN_MENU, UNKNOWN


async def main_menu(update: Update, _) -> int:
    buttons = [
        ["🔍 SEARCH PRO PLAYERS", "📈 PLAYER'S STATS"],
        ["🔍 SEARCH MATCHES", "🔴 LIVE MATCHES"]
    ]
    keyboard = ReplyKeyboardMarkup(buttons)

    await update.message.reply_text(text="MAIN MENU", reply_markup=keyboard)
    return MAIN_MENU


# UNKNOWN COMMAND  -----------------------------------------------------------------------
async def unknown(update: Update, _) -> int:
    await update.message.reply_text(text="unknown command, please type /menu", reply_markup=ReplyKeyboardRemove())
    return UNKNOWN
