import os
import requests
import helpers

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from constants import *
from main_menu.live import live


# START -----------------------------------------------------------------------------------------------
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


# MAIN MENU -----------------------------------------------------------------------------------------------
async def main_menu(update: Update, _) -> int:
    buttons = [
        ["🔍 SEARCH PRO PLAYERS", "📈 PLAYER'S STATS"],
        ["🔍 SEARCH MATCHES", "🔴 LIVE MATCHES"]
    ]
    keyboard = ReplyKeyboardMarkup(buttons)

    await update.message.reply_text(text="MAIN MENU", reply_markup=keyboard)
    return MAIN_MENU


# MAIN MENU -> MATCHES ------------------------------------------------------------------------------------
async def matches(update: Update, _) -> int:
    await update.message.reply_text(text="✍ write match id (e.g. 6720147701)", reply_markup=ReplyKeyboardRemove())

    return TYPING_MATCH_ID


async def get_match_id(update: Update, _) -> int:
    match_id = update.message.text
    buttons = [["WRITE OTHER ID"], ["MAIN MENU"]]
    keyboard = ReplyKeyboardMarkup(buttons)

    response = requests.get(f"https://api.opendota.com/api/matches/{match_id}")
    if response.status_code == 200:
        res_json = response.json()
        if "radiant_team" in response.json():
            teams = {
                "radiant": res_json["radiant_team"]["name"],
                "dire": res_json["dire_team"]["name"]
            }
        else:
            teams = {
                "radiant": "Radiant",
                "dire": "Dire"
            }
        text = teams["radiant"] + " vs " + teams["dire"]
        if res_json["radiant_win"]:
            text += "\nVictory: " + teams[helpers.who_won(res_json["radiant_win"])]
        if res_json["radiant_score"]:
            text += "\nKills: " + teams["radiant"] + " " + str(res_json["radiant_score"]) + ":" \
                    + str(res_json["dire_score"]) + " " + teams["radiant"]
        if res_json["duration"]:
            text += "\nDuration of match: " + helpers.seconds_to_minutes(res_json["duration"])
        if res_json["picks_bans"]:
            text += "\n\nPicks:\n" + helpers.get_picks(teams, res_json["picks_bans"])
        await update.message.reply_text(text=text)
        await update.message.reply_text(text="choose option:", reply_markup=keyboard)
    else:
        text = "wrong match id"
        await update.message.reply_text(text=text, reply_markup=keyboard)

    return MATCHES


# MAIN MENU -> PLAYERS MENU --------------------------------------------------------------------------------
async def check_account_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if ACCOUNT_ID in context.user_data:
        return await player_menu(update, context)
    else:
        return await type_account_id(update, context)


async def type_account_id(update: Update, _) -> int:
    await update.message.reply_text(text="✍ write player's id (e.g. 311360822)", reply_markup=ReplyKeyboardRemove())

    return TYPE_ACCOUNT_ID


async def save_account_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = update.message.text
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}")
    if response.status_code == 200 and "profile" in response.json():
        buttons = [["PLAYER'S MENU"], ["WRITE OTHER ID"], ["MAIN MENU"]]

        context.user_data[ACCOUNT_ID] = account_id
        res_json = response.json()
        context.user_data[PLAYER_NAME] = res_json["profile"]["personaname"]
        text = "Player's name: " + res_json["profile"]["personaname"]
    else:
        buttons = [["WRITE OTHER ID"], ["MAIN MENU"]]
        text = "wrong player's id"

    keyboard = ReplyKeyboardMarkup(buttons)
    await update.message.reply_text(text=text, reply_markup=keyboard)
    return PLAYERS


async def player_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    search_buttons = [
        ["WIN/LOSE", "RECENT MATCHES", "SORTED MATCHES"],
        ["MOST PICKED HEROES", "PEERS", "TOTALS"],
        ["LEAVER STATUS", "WORDCLOUD", "REFRESH"],
        ["FAVOURITE PLAYERS", "WRITE OTHER ID", "MAIN MENU"]
    ]
    keyboard = ReplyKeyboardMarkup(search_buttons)
    text = "account id: " + context.user_data[ACCOUNT_ID] + ", name: " + context.user_data[PLAYER_NAME]
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return PLAYERS


# MAIN MENU -> PLAYERS MENU -> PLAYERS WL -------------------------------------------------------------------
async def wl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    button = [["BACK"]]
    keyboard = ReplyKeyboardMarkup(button)

    account_id = context.user_data[ACCOUNT_ID]
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/wl")
    if response.status_code == 200:
        res_json = response.json()
        text = "Won: " + str(res_json["win"]) + "\nLost: " + str(res_json["lose"])
        text += "\nWinrate: " + helpers.count_winrate(res_json["win"] + res_json["lose"], res_json["win"])
    else:
        text = "Error"
    await update.message.reply_text(text=text, reply_markup=keyboard)
    return WL


# MAIN MENU -> PLAYERS MENU -> RECENT_MATCHES --------------------------------------------------------------
async def recent_matches(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/recentMatches")
    res_json = response.json()
    text = helpers.matches_to_str(res_json)

    button = [["BACK"]]
    keyboard = ReplyKeyboardMarkup(button)
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return RECENT_MATCHES


# MAIN MENU -> PLAYERS MENU -> PLAYERS MATCHES -------------------------------------------------------------
async def player_matches(update: Update, _) -> int:
    text = "Sort by..."
    search_buttons = [
        ["KILLS", "DEATHS", "ASSISTS"],
        ["WIN", "LOSE", "HERO", ],
        ["BACK TO PLAYER'S MENU"]
    ]
    keyboard = ReplyKeyboardMarkup(search_buttons)
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return PLAYER_MATCHES


# MAIN MENU -> PLAYERS MENU -> PLAYERS MATCHES -> SORT BY KDA ---------------------------------------------
async def sort_by_kda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    sort = kda_obj[update.message.text]
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/matches",
                            params={"limit": 10, "sort": sort})
    res_json = response.json()
    text = helpers.matches_to_str(res_json)

    button = [["BACK"]]
    keyboard = ReplyKeyboardMarkup(button)
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return PLAYER_MATCHES


# MAIN MENU -> PLAYERS MENU -> PLAYERS MATCHES -> SORT BY WL ---------------------------------------------
async def sort_by_wl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    int_wl = wl_obj[update.message.text]
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/matches",
                            params={"limit": 10, "win": int_wl})
    res_json = response.json()
    text = helpers.matches_to_str(res_json)

    button = [["BACK"]]
    keyboard = ReplyKeyboardMarkup(button)
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return PLAYER_MATCHES


# MAIN MENU -> PLAYERS MENU -> PLAYERS MATCHES -> SORT BY HERO ---------------------------------------------
async def choose_hero_to_sort(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if SKIP_HEROES not in context.user_data:
        context.user_data[SKIP_HEROES] = False
    if context.user_data[SKIP_HEROES]:
        offset = 70
    else:
        offset = 0

    heroes = heroes_col.find().skip(offset).limit(70)
    buttons = []
    row = []
    counter = 0
    for hero in heroes:
        row.append(hero["localized_name"])
        counter += 1
        if counter == 4:
            buttons.append(row)
            row = []
            counter = 0
    buttons.append(row)

    back_button = ["NEXT LIST", "BACK TO SORT MENU"]
    buttons.append(back_button)
    keyboard = ReplyKeyboardMarkup(buttons)
    await update.message.reply_text(text="choose hero to sort", reply_markup=keyboard)

    return SORT_BY_HERO


async def next_hero_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data[SKIP_HEROES]:
        context.user_data[SKIP_HEROES] = False
    else:
        context.user_data[SKIP_HEROES] = True
    return await choose_hero_to_sort(update, context)


async def sort_by_hero(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    hero = heroes_col.find_one({"localized_name": update.message.text})
    hero_id = hero.get("id")
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/matches",
                            params={"limit": 10, "hero_id": hero_id})
    res_json = response.json()
    if res_json:
        text = helpers.matches_to_str(res_json)
    else:
        text = "matches not found"
    button = [["BACK"]]
    keyboard = ReplyKeyboardMarkup(button)
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return SORT_BY_HERO


# MAIN MENU -> PLAYERS MENU -> HEROES -----------------------------------------------------------------------
async def player_heroes_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/heroes",
                            params={"sort": "games"})
    res_json = response.json()
    text = helpers.hero_stats(res_json)
    button = [["BACK"]]
    keyboard = ReplyKeyboardMarkup(button)
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return PLAYER_HEROES


# MAIN MENU -> PLAYERS MENU -> PEERS -----------------------------------------------------------------------
async def peers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/peers",
                            params={"sort": "games"})
    res_json = response.json()
    text = helpers.peers_to_text(res_json)
    button = [["BACK"]]
    keyboard = ReplyKeyboardMarkup(button)
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return PEERS


# MAIN MENU -> PLAYERS MENU -> TOTALS -----------------------------------------------------------------------
async def totals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/totals")
    res_json = response.json()
    text = helpers.totals_to_text(res_json)
    button = [["BACK"]]
    keyboard = ReplyKeyboardMarkup(button)
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return TOTALS


# MAIN MENU -> PLAYERS MENU -> LEAVER_STATUS -----------------------------------------------------------------------
async def leaver_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/counts")
    res_json = response.json()
    text = helpers.leaver_status_to_text(res_json)
    button = [["BACK"]]
    keyboard = ReplyKeyboardMarkup(button)
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return LEAVER_STATUS


# MAIN MENU -> PLAYERS MENU -> WORDCLOUD -----------------------------------------------------------------------
async def wordcloud(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/wordcloud")
    res_json = response.json()
    text = helpers.wordcloud_to_text(res_json)
    button = [["BACK"]]
    keyboard = ReplyKeyboardMarkup(button)
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return WORDCLOUD


# MAIN MENU -> PLAYERS MENU -> REFRESH -----------------------------------------------------------------------
async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.post(f"https://api.opendota.com/api/players/{account_id}/refresh")
    if response.status_code == 200:
        text = "account refreshed"
    else:
        text = "wrong request"
    button = [["BACK"]]
    keyboard = ReplyKeyboardMarkup(button)
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return REFRESH


# MAIN MENU -> PLAYERS MENU -> FAVOURITE PLAYERS --------------------------------------------------------------
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


# MAIN MENU -> PRO_PLAYER -----------------------------------------------------------------------
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

    await update.message.reply_text(text=text, reply_markup=keyboard)

    return PRO_PLAYER


# MAIN MENU -> LIVE -----------------------------------------------------------------------
# async def live(update: Update, _) -> int:
#     response = requests.get(f"https://api.opendota.com/api/live")
#     res_json = response.json()
#     text = helpers.get_pro_matches(res_json)
#     if not text:
#         text = "no pro matches\n\n"
#     text += helpers.get_public_matches(res_json)
#
#     button = [["MAIN MENU"]]
#     keyboard = ReplyKeyboardMarkup(button)
#
#     while len(text) > 4096:
#         last_pos = text[0:4096].rfind("\n\n")
#         await update.message.reply_html(text=text[0:last_pos])
#         text = text[last_pos:len(text)]
#
#     await update.message.reply_html(text=text, reply_markup=keyboard)
#
#     return LIVE


# UNKNOWN COMMAND  -----------------------------------------------------------------------
async def unknown(update: Update, _) -> int:
    await update.message.reply_text(text="unknown command, please type /menu", reply_markup=ReplyKeyboardRemove())
    return UNKNOWN


# ADMIN  -------------------------------------------------------------------------------
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


def main() -> None:
    app = Application.builder().token(os.environ['TOKEN']).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.Regex("^🔍 SEARCH MATCHES$"), matches),
                MessageHandler(filters.Regex("^📈 PLAYER'S STATS$"), check_account_id),
                MessageHandler(filters.Regex("^🔍 SEARCH PRO PLAYERS$"), type_pro_player),
                MessageHandler(filters.Regex("^🔴 LIVE MATCHES$"), live)
            ],
            LIVE: [
                MessageHandler(filters.Regex("^MAIN MENU$"), main_menu)
            ],
            TYPING_MATCH_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_match_id)],
            TYPE_PRO_PLAYER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pro_player_name)],
            ADD_NEW_PLAYER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_new_player)],
            DELETE_PLAYER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_players_order)],
            MATCHES: [
                MessageHandler(filters.Regex("^WRITE OTHER ID$"), matches),
            ],
            PRO_PLAYER: [
                MessageHandler(filters.Regex("^WRITE OTHER PLAYER$"), type_pro_player),
            ],
            TYPE_ACCOUNT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_account_id)],
            WL: [MessageHandler(filters.Regex("^BACK$"), check_account_id)],
            RECENT_MATCHES: [MessageHandler(filters.Regex("^BACK$"), check_account_id)],
            SORT_BY_HERO: [
                MessageHandler(filters.Regex("^NEXT LIST$"), next_hero_list),
                MessageHandler(filters.Regex("^BACK$"), choose_hero_to_sort),
                MessageHandler(filters.Regex("^BACK TO SORT MENU$"), player_matches),
                MessageHandler(filters.TEXT & ~filters.COMMAND, sort_by_hero),

            ],
            PLAYER_MATCHES: [
                MessageHandler(filters.Regex("^KILLS$"), sort_by_kda),
                MessageHandler(filters.Regex("^DEATHS$"), sort_by_kda),
                MessageHandler(filters.Regex("^ASSISTS$"), sort_by_kda),
                MessageHandler(filters.Regex("^WIN$"), sort_by_wl),
                MessageHandler(filters.Regex("^LOSE$"), sort_by_wl),
                MessageHandler(filters.Regex("^HERO$"), choose_hero_to_sort),
                MessageHandler(filters.Regex("^BACK$"), player_matches),
                MessageHandler(filters.Regex("^BACK TO PLAYER'S MENU$"), player_menu),
            ],
            PLAYER_HEROES: [
                MessageHandler(filters.Regex("^BACK$"), player_menu),
            ],
            PEERS: [
                MessageHandler(filters.Regex("^BACK$"), player_menu),
            ],
            TOTALS: [
                MessageHandler(filters.Regex("^BACK$"), player_menu),
            ],
            LEAVER_STATUS: [
                MessageHandler(filters.Regex("^BACK$"), player_menu),
            ],
            WORDCLOUD: [
                MessageHandler(filters.Regex("^BACK$"), player_menu),
            ],
            REFRESH: [
                MessageHandler(filters.Regex("^BACK$"), player_menu),
            ],
            FAVOURITE_PLAYERS: [
                MessageHandler(filters.Regex("^ADD NEW PLAYER$"), add_new_player),
                MessageHandler(filters.Regex("^DELETE PLAYER$"), type_delete_number),
                MessageHandler(filters.Regex("^BACK$"), player_menu),
            ],
            PLAYERS: [
                MessageHandler(filters.Regex("^WRITE OTHER ID$"), type_account_id),
                MessageHandler(filters.Regex("^PLAYER'S MENU$"), player_menu),
                MessageHandler(filters.Regex("^MAIN MENU$"), main_menu),
                MessageHandler(filters.Regex("^WIN/LOSE$"), wl),
                MessageHandler(filters.Regex("^RECENT MATCHES$"), recent_matches),
                MessageHandler(filters.Regex("^SORTED MATCHES$"), player_matches),
                MessageHandler(filters.Regex("^MOST PICKED HEROES$"), player_heroes_stats),
                MessageHandler(filters.Regex("^PEERS$"), peers),
                MessageHandler(filters.Regex("^TOTALS$"), totals),
                MessageHandler(filters.Regex("^LEAVER STATUS$"), leaver_status),
                MessageHandler(filters.Regex("^REFRESH$"), refresh),
                MessageHandler(filters.Regex("^WORDCLOUD$"), wordcloud),
                MessageHandler(filters.Regex("^FAVOURITE PLAYERS"), favourite_players)
            ],
            UNKNOWN: [
                CommandHandler("menu", start)
            ],
            TYPE_ADMIN_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, send_admin_message)
            ],
            ADMIN: [
                MessageHandler(filters.Regex("^GOT IT$"), main_menu),
            ]
        },
        fallbacks=[
            CommandHandler("admin", admin),
            CommandHandler("menu", start),
            MessageHandler(filters.Regex("^🔴 LIVE MATCHES$"), live),
            MessageHandler(filters.Regex("^MAIN MENU$"), main_menu)
        ]
    )
    app.add_handler(conv_handler)

    helpers.mongodb_heroes_init()
    helpers.mongodb_pro_players_init()

    app.run_polling()


if __name__ == "__main__":
    main()
