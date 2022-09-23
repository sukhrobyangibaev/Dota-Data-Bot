from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove

from constants import PRO_PLAYER, TYPE_PRO_PLAYER, pro_players_col
from helpers import helpers


async def type_pro_player(update: Update, _) -> int:
    await update.message.reply_text(text="✍ write player's nickname (e.g. ammar)", reply_markup=ReplyKeyboardRemove())
    return TYPE_PRO_PLAYER


async def get_pro_player_name(update: Update, _) -> int:
    player_name = update.message.text
    buttons = [["WRITE OTHER PLAYER"], ["MAIN MENU"]]
    keyboard = ReplyKeyboardMarkup(buttons)

    found_players = pro_players_col.find({"name": {"$regex": "^(?i)" + player_name}}).limit(10)
    text = helpers.pro_players_to_text(found_players)
    if len(text) == 0:
        text += "player not found"

    await update.message.reply_html(text=text, reply_markup=keyboard)

    return PRO_PLAYER
