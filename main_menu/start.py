from telegram import Update
from telegram.ext import ContextTypes

from constants import chats_col, logger, users_col
from main_menu.main_menu import main_menu


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_found = chats_col.find_one({"id": update.message.chat.id})
    if not chat_found:
        chat = update.message.chat
        chat_dict = {
            "id": chat.id,
            "type": chat.type,
            "last_name": chat.last_name,
            "first_name": chat.first_name
        }
        chats_col.insert_one(chat_dict)
        logger.info("added new chat: " + str(chat_dict))
        user = update.message.from_user
        user_dict = {
            "is_bot": user.is_bot,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "id": user.id,
            "language_code": user.language_code
        }
        users_col.insert_one(user_dict)
        logger.info("added new user: " + str(user_dict))

    return await main_menu(update, context)
