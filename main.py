import os
from dotenv import load_dotenv
import helpers

from telegram.ext import (
    PicklePersistence,
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from constants import *
from main_menu import start, main_menu, error_handler
from main_menu.admin import send_admin_message, admin
from main_menu.fav_players import get_new_player, get_players_order, add_new_player, type_delete_number, \
    favourite_players, type_choose_number, get_chosen_players_order
from main_menu.live import live
from main_menu.live_league import live_league
from main_menu.matches import matches, get_match_id
from main_menu.players_menu import check_account_id, save_account_id, player_menu, \
    type_account_id, wl, recent_matches, player_heroes_stats, peers, totals, \
    leaver_status, refresh, wordcloud
from main_menu.players_menu.players_matches import next_hero_list, choose_hero_to_sort, player_matches, sort_by_hero, \
    sort_by_kda, sort_by_wl
from main_menu.pro_player import type_pro_player, get_pro_player_name

load_dotenv()

def main() -> None:
    persistence = PicklePersistence(filepath='persistence.pkl')

    app = Application.builder().token(os.getenv('TOKEN')).persistence(persistence).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.Regex("^🔍 SEARCH MATCHES$"), matches),
                MessageHandler(filters.Regex("^📈 PLAYER'S STATS$"), check_account_id),
                MessageHandler(filters.Regex("^🔍 SEARCH PRO PLAYERS$"), type_pro_player),
                MessageHandler(filters.Regex("^⭐ FAVOURITE PLAYERS$"), favourite_players),
                MessageHandler(filters.Regex("^🔴 LIVE MATCHES$"), live),
                MessageHandler(filters.Regex("^🔵 LIVE LEAGUE MATCHES$"), live_league)
            ],
            LIVE: [
                MessageHandler(filters.Regex("^MAIN MENU$"), main_menu)
            ],
            TYPING_MATCH_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_match_id)],
            TYPE_PRO_PLAYER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pro_player_name)],
            ADD_NEW_PLAYER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_new_player)],
            DELETE_PLAYER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_players_order)],
            CHOOSE_PLAYER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_chosen_players_order)],
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
                MessageHandler(filters.Regex("^CHOOSE PLAYER$"), type_choose_number),
                MessageHandler(filters.Regex("^BACK$"), main_menu),
            ],
            PLAYERS: [
                MessageHandler(filters.Regex("^CHOOSE ANOTHER PLAYER$"), favourite_players),
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
            MessageHandler(filters.Regex("^🔵 LIVE LEAGUE MATCHES$"), live_league),
            MessageHandler(filters.Regex("^MAIN MENU$"), main_menu)
        ],
        persistent=True,
        name='main_conv'
    )
    app.add_handler(conv_handler)
    app.add_error_handler(error_handler)

    helpers.mongodb_heroes_init()
    helpers.mongodb_pro_players_init()

    app.run_polling()


if __name__ == "__main__":
    main()
