import html
import json
import traceback

from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from constants import MAIN_MENU, UNKNOWN, logger, DEVELOPER_CHAT_ID


async def main_menu(update: Update, _) -> int:
    buttons = [
        ["🔍 SEARCH PRO PLAYERS", "🔍 SEARCH MATCHES"],
        ["⭐ FAVOURITE PLAYERS", "📈 PLAYER'S STATS"],
        ["🔴 LIVE MATCHES", "🔵 LIVE LEAGUE MATCHES"]
    ]
    keyboard = ReplyKeyboardMarkup(buttons)

    await update.message.reply_text(text="MAIN MENU", reply_markup=keyboard)
    return MAIN_MENU


# UNKNOWN COMMAND  -----------------------------------------------------------------------
async def unknown(update: Update, _) -> int:
    await update.message.reply_text(text="unknown command, please type /menu", reply_markup=ReplyKeyboardRemove())
    return UNKNOWN


# ERROR HANDLER --------------------------------------------------------------------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    await context.bot.send_message(
        chat_id=DEVELOPER_CHAT_ID, text=message[0:4090], parse_mode=ParseMode.HTML
    )
