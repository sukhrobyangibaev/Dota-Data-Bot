import requests

from constants import heroes_col, mydb, logger, pro_players_col


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
    if hero_id:
        return heroes_col.find_one({"id": hero_id}).get("localized_name")
    else:
        return "picking hero"


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


def get_public_matches(res_json) -> str:
    text = ""
    is_pro_player = False
    for match in res_json:
        if not match["deactivate_time"]:
            text += "<code>{}</code> Radiant {} : {} Dire\n".format(match["match_id"], match["radiant_score"],
                                                                    match["dire_score"])
            if match["players"]:
                for player in match["players"]:
                    if "is_pro" in player:
                        is_pro_player = True
                        text += "<code>{}</code> {} - {}\n".format(player["account_id"], player["name"],
                                                                   get_hero_name(player["hero_id"]))
            text += "\n"
    if is_pro_player:
        return text
    else:
        return ""