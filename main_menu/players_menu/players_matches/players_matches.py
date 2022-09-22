# MAIN MENU -> PLAYERS MENU -> PLAYERS MATCHES -------------------------------------------------------------
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from constants import PLAYER_MATCHES, ACCOUNT_ID, kda_obj, wl_obj, SKIP_HEROES, heroes_col, SORT_BY_HERO
from helpers import helpers


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
