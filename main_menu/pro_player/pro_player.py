from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes

from constants import PRO_PLAYER, TYPE_PRO_PLAYER, pro_players_col
from helpers import helpers
from main_menu import main_menu


async def type_pro_player(update: Update, _) -> int:
    await update.message.reply_text(text="✍ write player's nickname (e.g. ammar)", reply_markup=ReplyKeyboardRemove())
    return TYPE_PRO_PLAYER


async def get_pro_player_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    player_name = update.message.text
    found_players = pro_players_col.find({"name": {"$regex": "^(?i)" + player_name}}).limit(10)
    text = helpers.pro_players_to_text(found_players)
    if len(text) == 0:
        text += "player not found"

    await update.message.reply_html(text=text)

    return await main_menu(update, context)
