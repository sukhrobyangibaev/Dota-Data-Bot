import logging
import requests
import pymongo

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
    COUNTS,
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
    BACK_TO_HERO_LIST
) = range(59)

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["opendotabot"]
heroes_col = mydb["heroes"]


# HELPERS --------------------------------------------------------------------------------------
def mongodb_init() -> None:
    list_of_cols = mydb.list_collection_names()
    if "heroes" not in list_of_cols:
        response = requests.get("https://api.opendota.com/api/heroes")
        res_json = response.json()
        for hero in res_json:
            heroes_col.insert_one(hero)
        logger.info("added heroes to db")


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
    for peer in res_json:
        games = peer["games"]
        winrate = count_winrate(games, peer["win"])
        text += peer["personaname"] + " - games " + str(games) + ", winrate " + winrate + "\n"
    return text


def totals_to_text(res_json) -> str:
    text = f"K/D/A - {res_json[0]['sum']}/{res_json[1]['sum']}/{res_json[2]['sum']}\n" \
           f"Last hits - {res_json[6]['sum']}\n" \
           f"Denies - {res_json[7]['sum']}\n" \
           f"Hours played - {int(res_json[9]['sum'] / 3600)}\n" \
           f"Courier kills - {res_json[17]['sum']}"
    return text


kda_obj = {
    SORT_BY_KILLS: "kills",
    SORT_BY_DEATHS: "deaths",
    SORT_BY_ASSISTS: "assists"
}

wl_obj = {
    SORT_BY_WIN: 1,
    SORT_BY_LOSE: 0
}


# MAIN MENU -----------------------------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    buttons = [
        [
            InlineKeyboardButton(text="MATCHES", callback_data=MATCHES),
            InlineKeyboardButton(text="PALYERS", callback_data=PLAYERS),
            InlineKeyboardButton(text="PRO_PLAYER", callback_data=PRO_PLAYER)
        ],
        [
            InlineKeyboardButton(text="PRO_MATCHES", callback_data=PRO_MATCHES),
            InlineKeyboardButton(text="PUBLIC_MATCHES", callback_data=PUBLIC_MATCHES),
            InlineKeyboardButton(text="PARSED_MATCHES", callback_data=PARSED_MATCHES)
        ],
        [
            InlineKeyboardButton(text="EXPLORER", callback_data=EXPLORER),
            InlineKeyboardButton(text="METADATA", callback_data=METADATA),
            InlineKeyboardButton(text="SEARCH", callback_data=SEARCH)
        ],
        [
            InlineKeyboardButton(text="RANKINGS", callback_data=RANKINGS),
            InlineKeyboardButton(text="BENCHMARKS", callback_data=BENCHMARKS),
            InlineKeyboardButton(text="STATUS", callback_data=STATUS)
        ],
        [
            InlineKeyboardButton(text="HEALTH", callback_data=HEALTH),
            InlineKeyboardButton(text="REQUEST", callback_data=REQUEST),
            InlineKeyboardButton(text="FINDMATCHES", callback_data=FINDMATCHES)
        ],
        [
            InlineKeyboardButton(text="HEROES", callback_data=HEROES),
            InlineKeyboardButton(text="HERO_STAT", callback_data=HERO_STAT),
            InlineKeyboardButton(text="LEAGUE", callback_data=LEAGUE)
        ],
        [
            InlineKeyboardButton(text="TEAMS", callback_data=TEAMS),
            InlineKeyboardButton(text="REPLAYS", callback_data=REPLAYS),
            InlineKeyboardButton(text="RECORDS", callback_data=RECORDS)
        ],
        [
            InlineKeyboardButton(text="LIVE", callback_data=LIVE),
            InlineKeyboardButton(text="SCENARIOS", callback_data=SCENARIOS),
            InlineKeyboardButton(text="SCHEMA", callback_data=SCHEMA)
        ],
        [
            InlineKeyboardButton(text="CONSTANTS", callback_data=CONSTANTS)
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    if context.user_data.get(FROM_CALLBACK_QUERY):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text="Choose category", reply_markup=keyboard)
    else:
        await update.message.reply_text(text="Choose category", reply_markup=keyboard)
        context.user_data[FROM_CALLBACK_QUERY] = True
    return MAIN_MENU


# MAIN MENU -> MATCHES ------------------------------------------------------------------------------------
async def matches(update: Update, _) -> int:
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text="write match id")
    return TYPING_MATCH_ID


async def get_match_id(update: Update, _) -> int:
    match_id = update.message.text
    buttons = [
        [
            InlineKeyboardButton(text="WRITE OTHER ID", callback_data=WRITE_ANOTHER_ID),
            InlineKeyboardButton(text="MAIN MENU", callback_data=MAIN_MENU)
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    response = requests.get(f"https://api.opendota.com/api/matches/{match_id}")
    if response.status_code == 200 and "radiant_team" in response.json():
        res_json = response.json()
        teams = {
            "radiant": res_json["radiant_team"]["name"],
            "dire": res_json["dire_team"]["name"]
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
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text="write player's id")

    return TYPE_ACCOUNT_ID


async def save_account_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account_id = update.message.text
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}")
    if response.status_code == 200 and "profile" in response.json():
        buttons = [
            [
                InlineKeyboardButton(text="WRITE OTHER ID", callback_data=WRITE_ANOTHER_ID),
                InlineKeyboardButton(text="PLAYER'S MENU", callback_data=BACK_TO_PLAYERS_MENU),
                InlineKeyboardButton(text="MAIN MENU", callback_data=MAIN_MENU),
            ]
        ]
        keyboard = InlineKeyboardMarkup(buttons)

        context.user_data[ACCOUNT_ID] = account_id
        res_json = response.json()
        text = "Player's name: " + res_json["profile"]["personaname"]
        await update.message.reply_text(text=text, reply_markup=keyboard)
        return PLAYERS
    else:
        buttons = [
            [
                InlineKeyboardButton(text="WRITE OTHER ID", callback_data=WRITE_ANOTHER_ID),
                InlineKeyboardButton(text="MAIN MENU", callback_data=MAIN_MENU),
            ]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(text="wrong player's id", reply_markup=keyboard)
        return PLAYERS


async def player_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    search_buttons = [[
        InlineKeyboardButton(text="WIN/LOSE", callback_data=WL),
        InlineKeyboardButton(text="RECENT MATCHES", callback_data=RECENT_MATCHES),
        InlineKeyboardButton(text="MATCHES", callback_data=PLAYER_MATCHES)
    ], [
        InlineKeyboardButton(text="HEROES", callback_data=PLAYER_HEROES),
        InlineKeyboardButton(text="PEERS", callback_data=PEERS),
        InlineKeyboardButton(text="TOTALS", callback_data=TOTALS)
    ], [
        InlineKeyboardButton(text="COUNTS", callback_data=COUNTS),
        InlineKeyboardButton(text="HISTOGRAMS", callback_data=HISTOGRAMS),
        InlineKeyboardButton(text="WARDMAP", callback_data=WARDMAP)
    ], [
        InlineKeyboardButton(text="WORDCLOUD", callback_data=WORDCLOUD),
        InlineKeyboardButton(text="RATINGS", callback_data=RATINGS),
        InlineKeyboardButton(text="RANKINGS", callback_data=RANKINGS)
    ], [
        InlineKeyboardButton(text="REFRESH", callback_data=REFRESH),
        InlineKeyboardButton(text="WRITE OTHER ID", callback_data=WRITE_ANOTHER_ID),
        InlineKeyboardButton(text="MAIN MENU", callback_data=MAIN_MENU)
    ]]
    keyboard = InlineKeyboardMarkup(search_buttons)
    text = "account id: " + context.user_data[ACCOUNT_ID]
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return PLAYERS


# MAIN MENU -> PLAYERS MENU -> PLAYERS WL -------------------------------------------------------------------
async def wl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    button = InlineKeyboardButton(text="BACK", callback_data=BACK_TO_PLAYERS_MENU)
    keyboard = InlineKeyboardMarkup.from_button(button)

    account_id = context.user_data[ACCOUNT_ID]
    await update.callback_query.answer()
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/wl")
    if response.status_code == 200:
        res_json = response.json()
        text = "Won: " + str(res_json["win"]) + "\nLost: " + str(res_json["lose"])
        text += "\nWinrate: " + count_winrate(res_json["win"] + res_json["lose"], res_json["win"])
    else:
        text = "Error"
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return WL


# MAIN MENU -> PLAYERS MENU -> RECENT_MATCHES --------------------------------------------------------------
async def recent_matches(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/recentMatches")
    res_json = response.json()
    text = matches_to_str(res_json)

    button = InlineKeyboardButton(text="BACK", callback_data=BACK_TO_PLAYERS_MENU)
    keyboard = InlineKeyboardMarkup.from_button(button)
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return RECENT_MATCHES


# MAIN MENU -> PLAYERS MENU -> PLAYERS MATCHES -------------------------------------------------------------
async def player_matches(update: Update, _) -> int:
    await update.callback_query.answer()
    text = "Sort by..."
    search_buttons = [[
        InlineKeyboardButton(text="KILLS", callback_data=SORT_BY_KILLS),
        InlineKeyboardButton(text="DEATHS", callback_data=SORT_BY_DEATHS),
        InlineKeyboardButton(text="ASSISTS", callback_data=SORT_BY_ASSISTS)
    ], [
        InlineKeyboardButton(text="WIN", callback_data=SORT_BY_WIN),
        InlineKeyboardButton(text="LOSE", callback_data=SORT_BY_LOSE),
        InlineKeyboardButton(text="HERO", callback_data=SORT_BY_HERO),
    ], [
        InlineKeyboardButton(text="BACK", callback_data=BACK_TO_PLAYERS_MENU)
    ]]
    keyboard = InlineKeyboardMarkup(search_buttons)
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return PLAYER_MATCHES


# MAIN MENU -> PLAYERS MENU -> PLAYERS MATCHES -> SORT BY KDA ---------------------------------------------
async def sort_by_kda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()

    account_id = context.user_data.get(ACCOUNT_ID)
    sort = kda_obj[int(update.callback_query.data)]
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/matches",
                            params={"limit": 10, "sort": sort})
    res_json = response.json()
    text = matches_to_str(res_json)

    button = InlineKeyboardButton(text="BACK", callback_data=BACK_TO_PLAYERS_MATCHES)
    keyboard = InlineKeyboardMarkup.from_button(button)
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return PLAYER_MATCHES


# MAIN MENU -> PLAYERS MENU -> PLAYERS MATCHES -> SORT BY WL ---------------------------------------------
async def sort_by_wl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    int_wl = wl_obj[int(update.callback_query.data)]
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/matches",
                            params={"limit": 10, "win": int_wl})
    res_json = response.json()
    text = matches_to_str(res_json)

    button = InlineKeyboardButton(text="BACK", callback_data=BACK_TO_PLAYERS_MATCHES)
    keyboard = InlineKeyboardMarkup.from_button(button)
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return PLAYER_MATCHES


# MAIN MENU -> PLAYERS MENU -> PLAYERS MATCHES -> SORT BY HERO ---------------------------------------------
async def choose_hero_to_sort(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()

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
        row.append(InlineKeyboardButton(text=hero["localized_name"], callback_data=hero["id"]))
        counter += 1
        if counter == 4:
            buttons.append(row)
            row = []
            counter = 0
    buttons.append(row)

    back_button = [
        InlineKeyboardButton(text="NEXT LIST", callback_data="NEXT_HERO_LIST"),
        InlineKeyboardButton(text="BACK", callback_data="BACK_TO_PLAYERS_MATCHES")
    ]
    buttons.append(back_button)
    keyboard = InlineKeyboardMarkup(buttons)
    await update.callback_query.edit_message_text(text="choose hero to sort", reply_markup=keyboard)

    return SORT_BY_HERO


async def next_hero_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data[SKIP_HEROES]:
        context.user_data[SKIP_HEROES] = False
    else:
        context.user_data[SKIP_HEROES] = True
    return await choose_hero_to_sort(update, context)


async def sort_by_hero(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()

    hero_id = update.callback_query.data
    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/matches",
                            params={"limit": 10, "hero_id": hero_id})
    res_json = response.json()
    if res_json:
        text = matches_to_str(res_json)
    else:
        text = "matches not found"
    button = InlineKeyboardButton(text="BACK", callback_data="BACK_TO_HERO_LIST")
    keyboard = InlineKeyboardMarkup.from_button(button)
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return SORT_BY_HERO


# MAIN MENU -> PLAYERS MENU -> HEROES -----------------------------------------------------------------------
async def player_heroes_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()

    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/heroes",
                            params={"sort": "games"})
    res_json = response.json()
    text = hero_stats(res_json)
    button = InlineKeyboardButton(text="BACK", callback_data=BACK_TO_PLAYERS_MENU)
    keyboard = InlineKeyboardMarkup.from_button(button)
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return PLAYER_HEROES


# MAIN MENU -> PLAYERS MENU -> PEERS -----------------------------------------------------------------------
async def peers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()

    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/peers",
                            params={"sort": "games"})
    res_json = response.json()
    text = peers_to_text(res_json)
    button = InlineKeyboardButton(text="BACK", callback_data=BACK_TO_PLAYERS_MENU)
    keyboard = InlineKeyboardMarkup.from_button(button)
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return PEERS


# MAIN MENU -> PLAYERS MENU -> TOTALS -----------------------------------------------------------------------
async def totals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()

    account_id = context.user_data.get(ACCOUNT_ID)
    response = requests.get(f"https://api.opendota.com/api/players/{account_id}/totals")
    res_json = response.json()
    text = totals_to_text(res_json)
    button = InlineKeyboardButton(text="BACK", callback_data=BACK_TO_PLAYERS_MENU)
    keyboard = InlineKeyboardMarkup.from_button(button)
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return TOTALS


def main() -> None:
    app = Application.builder().token("5581179119:AAFd8Da6TQdmTwtGqdn-3QQp2vcsSDnDEms").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(matches, pattern=f"^{MATCHES}$"),
                CallbackQueryHandler(check_account_id, pattern=f"^{PLAYERS}$")
            ],
            TYPING_MATCH_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_match_id)],
            MATCHES: [
                CallbackQueryHandler(matches, pattern=f"^{WRITE_ANOTHER_ID}$"),
                CallbackQueryHandler(start, pattern=f"^{MAIN_MENU}$")
            ],
            TYPE_ACCOUNT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_account_id)],
            WL: [CallbackQueryHandler(check_account_id, pattern=f"^{BACK_TO_PLAYERS_MENU}$")],
            RECENT_MATCHES: [CallbackQueryHandler(check_account_id, pattern=f"^{BACK_TO_PLAYERS_MENU}$")],
            SORT_BY_HERO: [
                CallbackQueryHandler(sort_by_hero, pattern="^[-+]?[0-9]+$"),
                CallbackQueryHandler(next_hero_list, pattern=f"^NEXT_HERO_LIST$"),
                CallbackQueryHandler(choose_hero_to_sort, pattern=f"^BACK_TO_HERO_LIST$"),
                CallbackQueryHandler(player_matches, pattern=f"^BACK_TO_PLAYERS_MATCHES$")
            ],
            PLAYER_MATCHES: [
                CallbackQueryHandler(sort_by_kda, pattern=f"^{SORT_BY_KILLS}$"),
                CallbackQueryHandler(sort_by_kda, pattern=f"^{SORT_BY_DEATHS}$"),
                CallbackQueryHandler(sort_by_kda, pattern=f"^{SORT_BY_ASSISTS}$"),
                CallbackQueryHandler(sort_by_wl, pattern=f"^{SORT_BY_WIN}$"),
                CallbackQueryHandler(sort_by_wl, pattern=f"^{SORT_BY_LOSE}$"),
                CallbackQueryHandler(choose_hero_to_sort, pattern=f"^{SORT_BY_HERO}$"),
                CallbackQueryHandler(player_matches, pattern=f"^{BACK_TO_PLAYERS_MATCHES}$"),
                CallbackQueryHandler(player_menu, pattern=f"^{BACK_TO_PLAYERS_MENU}$")
            ],
            PLAYER_HEROES: [
                CallbackQueryHandler(player_menu, pattern=f"^{BACK_TO_PLAYERS_MENU}$")
            ],
            PEERS: [
                CallbackQueryHandler(player_menu, pattern=f"^{BACK_TO_PLAYERS_MENU}$")
            ],
            TOTALS: [
                CallbackQueryHandler(player_menu, pattern=f"^{BACK_TO_PLAYERS_MENU}$")
            ],
            PLAYERS: [
                CallbackQueryHandler(type_account_id, pattern=f"^{WRITE_ANOTHER_ID}$"),
                CallbackQueryHandler(player_menu, pattern=f"^{BACK_TO_PLAYERS_MENU}$"),
                CallbackQueryHandler(start, pattern=f"^{MAIN_MENU}$"),
                CallbackQueryHandler(wl, pattern=f"^{WL}$"),
                CallbackQueryHandler(recent_matches, pattern=f"^{RECENT_MATCHES}$"),
                CallbackQueryHandler(player_matches, pattern=f"^{PLAYER_MATCHES}$"),
                CallbackQueryHandler(player_heroes_stats, pattern=f"^{PLAYER_HEROES}$"),
                CallbackQueryHandler(peers, pattern=f"^{PEERS}$"),
                CallbackQueryHandler(totals, pattern=f"^{TOTALS}$")
            ]
        },
        fallbacks=[]
    )
    app.add_handler(conv_handler)

    # mongodb_init()

    app.run_polling()


if __name__ == "__main__":
    main()
