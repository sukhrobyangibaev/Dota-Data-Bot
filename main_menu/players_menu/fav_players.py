from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes

from constants import ACCOUNT_ID, fav_players_col, FAVOURITE_PLAYERS, ADD_NEW_PLAYER, DELETE_PLAYER


async def favourite_players(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    fav_players = fav_players_col.find_one({"account_id": account_id})
    text = ""
    if fav_players and fav_players["players"]:
        for i, player in enumerate(fav_players["players"]):
            text += "{}. {} {} \n".format(i + 1, player["id"], player["name"])
    else:
        text = "list is empty"

    buttons = [["ADD NEW PLAYER"],
               ["DELETE PLAYER"],
               ["BACK"]]
    keyboard = ReplyKeyboardMarkup(buttons)
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return FAVOURITE_PLAYERS


async def add_new_player(update: Update, _) -> int:
    await update.message.reply_text(text="✍ write player's id and name (e.g. \"311360822 ana\")",
                                    reply_markup=ReplyKeyboardRemove())
    return ADD_NEW_PLAYER


async def type_delete_number(update: Update, _) -> int:
    await update.message.reply_text(text="✍ write player's order in list (e.g. \"1\" or \"2\")",
                                    reply_markup=ReplyKeyboardRemove())
    return DELETE_PLAYER


async def get_new_player(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        player_id, player_name = update.message.text.split()
        account_id = context.user_data.get(ACCOUNT_ID)
        fav_players = fav_players_col.find_one({"account_id": account_id})
        if not fav_players:
            fav_players_col.insert_one({
                "account_id": account_id,
                "players": [{
                    "id": player_id,
                    "name": player_name
                }]
            })
        else:
            fav_players["players"].append({
                "id": player_id,
                "name": player_name
            })
            fav_players_col.update_one({"_id": fav_players["_id"]}, {"$set": fav_players})
        return await favourite_players(update, context)
    except ValueError:
        await update.message.reply_text("error, please check spelling")
        return await add_new_player(update, context)


async def get_players_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    order = update.message.text
    account_id = context.user_data.get(ACCOUNT_ID)
    print(order)
    if order.isnumeric():
        idx = int(order)
        fav_players = fav_players_col.find_one({"account_id": account_id})
        try:
            del fav_players["players"][idx - 1]
            fav_players_col.update_one({"_id": fav_players["_id"]}, {"$set": fav_players})
            text = "player successfully deleted"
            await update.message.reply_text(text)
            return await favourite_players(update, context)
        except TypeError:
            text = "order must be integer"
        except IndexError:
            text = "order is out of range"
        await update.message.reply_text(text)
        return await type_delete_number(update, context)
    else:
        text = "order must be digit"
        await update.message.reply_text(text)
        return await type_delete_number(update, context)
