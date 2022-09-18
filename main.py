import logging
import os
import requests
import pymongo

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

(
    MATCHES,
    PLAYERS,
    PRO_PLAYER,
    PRO_MATCHES,
    PUBLIC_MATCHES,
    PARSED_MATCHES,
    EXPLORER,
    METADATA,
    DISTRIBUTIONS,
    SEARCH,
    RANKINGS,
    BENCHMARKS,
    STATUS,
    HEALTH,
    REQUEST,
    FINDMATCHES,
    HEROES,
    HERO_STAT,
    LEAGUE,
    TEAMS,
    REPLAYS,
    RECORDS,
    LIVE,
    SCENARIOS,
    SCHEMA,
    CONSTANTS,
    MAIN_MENU,
    TYPING_MATCH_ID,
    BACK,
    FROM_CALLBACK_QUERY,
    ACCOUNT_ID,
    # players
    WL,
    RECENT_MATCHES,
    PLAYER_MATCHES,
    PLAYER_HEROES,
    PEERS,
    TOTALS,
    LEAVER_STATUS,
    HISTOGRAMS,
    WARDMAP,
    WORDCLOUD,
    RATINGS,
    PLAYER_RANKINGS,
    REFRESH,
    WRITE_ANOTHER_ID,
    BACK_TO_PLAYERS_MENU,
    ACCOUNT_ID_EXISTS,
    ACCOUNT_ID_NOT_EXISTS,
    TYPE_ACCOUNT_ID,
    SORT_BY_KILLS,
    SORT_BY_DEATHS,
    SORT_BY_ASSISTS,
    SORT_BY_WIN,
    SORT_BY_HERO,
    BACK_TO_PLAYERS_MATCHES,
    SORT_BY_LOSE,
    NEXT_HERO_LIST,
    SKIP_HEROES,
    BACK_TO_HERO_LIST,
    PLAYER_NAME,
    TYPE_PRO_PLAYER,
    WRITE_OTHER_PLAYER,
    UNKNOWN,
    ADMIN,
    TYPE_ADMIN_MESSAGE
) = range(65)

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["opendotabot"]
heroes_col = mydb["heroes"]
pro_players_col = mydb["proplayers"]
users_col = mydb["users"]
chats_col = mydb["chats"]


# HELPERS --------------------------------------------------------------------------------------
def mongodb_heroes_init() -> None:
    list_of_cols = mydb.list_collection_names()
    if "heroes" not in list_of_cols:
        response = requests.get("https://api.opendota.com/api/heroes")
        res_json = response.json()
        for hero in res_json:
            heroes_col.insert_one(hero)
        logger.info("added heroes to db")


def mongodb_pro_players_init() -> None:
    list_of_cols = mydb.list_collection_names()
    if "proplayers" not in list_of_cols:
        response = requests.get("https://api.opendota.com/api/proPlayers")
        res_json = response.json()
        for player in res_json:
            pro_players_col.insert_one(player)
        logger.info("added pro players to db")


def seconds_to_minutes(duration) -> str:
    text = str(int(duration / 60)) + ":" + str(duration % 60)
    return text


def who_won(radiant_won) -> str:
    return "radiant" if radiant_won else "dire"


def get_picks(teams, picks_bans) -> str:
    radiant_picks = teams["radiant"] + ": "
    dire_picks = teams["dire"] + ": "
    for picks in picks_bans:
        # logger.info(heroes_col.find_one({"id": picks["hero_id"]}).get("localized_name"))
        if picks["is_pick"]:
            if picks["team"]:
                dire_picks += heroes_col.find_one({"id": picks["hero_id"]}).get("localized_name") + ", "
            else:
                radiant_picks += heroes_col.find_one({"id": picks["hero_id"]}).get("localized_name") + ", "
    return radiant_picks[:-2] + "\n" + dire_picks[:-2]


def get_hero_name(hero_id) -> str:
    return heroes_col.find_one({"id": hero_id}).get("localized_name")


def win_or_loose(player_slot, radiant_win) -> str:
    if radiant_win and player_slot < 128:
        return "WON"
    elif not radiant_win and player_slot > 127:
        return "WON"
    else:
        return "LOST"


def matches_to_str(res_json) -> str:
    text = ""
    for match in res_json:
        text += win_or_loose(match["player_slot"], match["radiant_win"]) + " with "
        text += get_hero_name(match["hero_id"]) + ", "
        text += "K/D/A - " + "/".join([str(match["kills"]), str(match["deaths"]), str(match["assists"])]) + "\n"
    return text


def count_winrate(games, wins) -> str:
    return str(int((wins * 100) / games)) + "%"


def hero_stats(res_json) -> str:
    text = ""
    for i in range(10):
        hero = res_json[i]
        games = hero["games"]
        wins = hero["win"]
        winrate = count_winrate(games, wins)
        text += str(i + 1) + ". " + get_hero_name(int(hero["hero_id"]))
        text += " - games: " + str(games) + ", winrate: " + winrate + "\n"
    return text


def peers_to_text(res_json) -> str:
    text = ""
    counter = 0
    for peer in res_json:
        counter += 1
        games = peer["games"]
        winrate = count_winrate(games, peer["win"])
        text += peer["personaname"] + " - games " + str(games) + ", winrate " + winrate + "\n"
        if counter == 10:
            break
    return text


def totals_to_text(res_json) -> str:
    text = f"K/D/A - {res_json[0]['sum']}/{res_json[1]['sum']}/{res_json[2]['sum']}\n" \
           f"Last hits - {res_json[6]['sum']}\n" \
           f"Denies - {res_json[7]['sum']}\n" \
           f"Hours played - {int(res_json[9]['sum'] / 3600)}\n" \
           f"Courier kills - {res_json[17]['sum']}"
    return text


def leaver_status_to_text(res_json) -> str:
    text = ""
    ls = res_json["leaver_status"]
    if "2" in ls:
        text += "Disconnect: " + str(ls["2"]["games"])
    if "3" in ls:
        text += "\nAbandoned: " + str(ls["3"]["games"])
    if "4" in ls:
        text += "\nAFK: " + str(ls["4"]["games"])
    return text


def wordcloud_to_text(res_json) -> str:
    words = res_json["my_word_counts"] | res_json["all_word_counts"]
    sorted_words = dict(sorted(words.items(), key=lambda item: item[1], reverse=True))
    counter = 0
    text = ""
    for word, num in sorted_words.items():
        counter += 1
        text += word + " - " + str(num) + "\n"
        if counter == 10:
            break
    return text


def pro_players_to_text(players) -> str:
    text = ""
    for player in players:
        text += "\n\nname: " + player["name"]
        if player["team_name"]:
            text += "\nteam: " + player["team_name"]
        if player["country_code"]:
            text += "\ncountry code: " + player["country_code"]
        if player["account_id"]:
            text += "\naccount id: " + str(player["account_id"])
    return text


def get_pro_matches(res_json) -> str:
    text = ""
    for match in res_json:
        if match["league_id"] and not match["deactivate_time"]:
            text += match["team_name_radiant"] + " " + str(match["radiant_score"])
            text += " vs " + str(match["dire_score"]) + " " + match["team_name_dire"] + "\n"
    return text


kda_obj = {
    "KILLS": "kills",
    "DEATHS": "deaths",
    "ASSISTS": "assists"
}

wl_obj = {
    "WIN": 1,
    "LOSE": 0
}


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
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
        text += "\nVictory: " + teams[who_won(res_json["radiant_win"])]
        text += "\nKills: " + teams["radiant"] + " " + str(res_json["radiant_score"]) + ":" \
                + str(res_json["dire_score"]) + " " + teams["radiant"]
        text += "\nDuration of match: " + seconds_to_minutes(res_json["duration"])
        text += "\n\nPicks:\n" + get_picks(teams, res_json["picks_bans"])
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
        ["WRITE OTHER ID", "MAIN MENU"]
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
        text += "\nWinrate: " + count_winrate(res_json["win"] + res_json["lose"], res_json["win"])
    else:
        text = "Error"
    await update.message.reply_text(text=text, reply_markup=keyboard)
    return WL


# MAIN MENU -> PLAYERS MENU -> RECENT_MATCHES --------------------------------------------------------------
async def recent_matches(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/recentMatches")
    res_json = response.json()
    text = matches_to_str(res_json)

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
    text = matches_to_str(res_json)

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
    text = matches_to_str(res_json)

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
        text = matches_to_str(res_json)
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
    text = hero_stats(res_json)
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
    text = peers_to_text(res_json)
    button = [["BACK"]]
    keyboard = ReplyKeyboardMarkup(button)
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return PEERS


# MAIN MENU -> PLAYERS MENU -> TOTALS -----------------------------------------------------------------------
async def totals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/totals")
    res_json = response.json()
    text = totals_to_text(res_json)
    button = [["BACK"]]
    keyboard = ReplyKeyboardMarkup(button)
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return TOTALS


# MAIN MENU -> PLAYERS MENU -> LEAVER_STATUS -----------------------------------------------------------------------
async def leaver_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/counts")
    res_json = response.json()
    text = leaver_status_to_text(res_json)
    button = [["BACK"]]
    keyboard = ReplyKeyboardMarkup(button)
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return LEAVER_STATUS


# MAIN MENU -> PLAYERS MENU -> WORDCLOUD -----------------------------------------------------------------------
async def wordcloud(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/wordcloud")
    res_json = response.json()
    text = wordcloud_to_text(res_json)
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


# MAIN MENU -> PRO_PLAYER -----------------------------------------------------------------------
async def type_pro_player(update: Update, _) -> int:
    await update.message.reply_text(text="✍ write player's nickname (e.g. ammar)", reply_markup=ReplyKeyboardRemove())
    return TYPE_PRO_PLAYER


async def get_pro_player_name(update: Update, _) -> int:
    player_name = update.message.text
    buttons = [["WRITE OTHER PLAYER"], ["MAIN MENU"]]
    keyboard = ReplyKeyboardMarkup(buttons)

    found_players = pro_players_col.find({"name": {"$regex": "^(?i)" + player_name}}).limit(10)
    text = pro_players_to_text(found_players)
    if len(text) == 0:
        text += "player not found"

    await update.message.reply_text(text=text, reply_markup=keyboard)

    return PRO_PLAYER


# MAIN MENU -> LIVE -----------------------------------------------------------------------
async def live(update: Update, _) -> int:
    # await update.callback_query.answer()
    response = requests.get(f"https://api.opendota.com/api/live")
    res_json = response.json()
    text = get_pro_matches(res_json)
    if not text:
        text = "no live matches"
    button = [["MAIN MENU"]]
    keyboard = ReplyKeyboardMarkup(button)
    await update.message.reply_text(text=text, reply_markup=keyboard)

    return LIVE


# UNKNOWN COMMAND  -----------------------------------------------------------------------
async def unknown(update: Update, _) -> int:
    await update.message.reply_text(text="unknown command, please type /menu")
    return UNKNOWN


# ADMIN  -------------------------------------------------------------------------------
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("/admin command by user with id " + str(update.effective_user.id))
    if str(update.effective_user.id) == os.environ['ADMIN_ID']:
        await update.message.reply_text(text="welcome admin")
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
            TYPING_MATCH_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_match_id)],
            TYPE_PRO_PLAYER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pro_player_name)],
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
                MessageHandler(filters.Regex("^WORDCLOUD$"), wordcloud)
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

    mongodb_heroes_init()
    mongodb_pro_players_init()

    app.run_polling()


if __name__ == "__main__":
    main()
