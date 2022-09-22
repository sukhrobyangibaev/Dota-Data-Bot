# ADMIN  -------------------------------------------------------------------------------
import os

from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from constants import TYPE_ADMIN_MESSAGE, logger, chats_col, ADMIN
from main_menu.start import start


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("/admin command by user with id " + str(update.effective_user.id))
    if str(update.effective_user.id) == os.environ['ADMIN_ID']:
        await update.message.reply_text(text="welcome admin", reply_markup=ReplyKeyboardRemove())
        return await type_admin_message(update, context)
    else:
        await update.message.reply_text(text="sorry, you are not admin")
        return await start(update, context)


async def type_admin_message(update: Update, _) -> int:
    await update.message.reply_text(text="✍ write admin message to all chats")
    return TYPE_ADMIN_MESSAGE


async def send_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    all_chats = chats_col.find()
    button = [["GOT IT"]]
    keyboard = ReplyKeyboardMarkup(button)
    for chat in all_chats:
        await context.bot.sendMessage(chat_id=chat["id"], text=text, reply_markup=keyboard)
    return ADMIN