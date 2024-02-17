from itertools import islice
import numpy as np
import requests

from constants import AB_CLASSIFIER, ET_CLASSIFIER, GB_CLASSIFIER, HGB_CLASSIFIER, RF_CLASSIFIER, heroes_col, mydb, logger, pro_players_col


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
        return "🟩WON"
    elif not radiant_win and player_slot > 127:
        return "🟩WON"
    else:
        return "🟥LOST"


def matches_to_str(res_json) -> str:
    text = ""
    for match in res_json:
        text += win_or_loose(match["player_slot"], match["radiant_win"]) + " with "
        text += get_hero_name(match["hero_id"]) + ", "
        text += "K/D/A - " + "/".join([str(match["kills"]), str(match["deaths"]), str(match["assists"])]) + "\n"
    return text


def count_winrate(games, wins) -> str:
    return str(int((wins * 100) / games)) + "%"


def hero_stats(res_json):
    heroes = []
    games = []
    won = []
    won_percent = []
    for i in range(10):
        hero = res_json[i]
        games.append(hero["games"])
        won.append(hero["win"])
        winrate = count_winrate(hero["games"], hero["win"])
        won_percent.append(winrate)
        heroes.append(get_hero_name(int(hero["hero_id"]))[:5])
    ans = {
        "heroes": heroes,
        "games": games,
        "won": won,
        "won_percent": won_percent
    }
    return ans


def peers_to_dict(res_json):
    counter = 0
    players = []
    games = []
    won = []
    won_percent = []
    for peer in res_json:
        counter += 1
        players.append(peer["personaname"][:5])
        games.append(peer["games"])
        won.append(peer["win"])
        winrate = count_winrate(peer["games"], peer["win"])
        won_percent.append(winrate)
        if counter == 10:
            break
    ans = {
        "players": players,
        "games": games,
        "won": won,
        "won_percent": won_percent
    }
    return ans


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


def get_wordcloud_list(res_json):
    words = res_json["my_word_counts"] | res_json["all_word_counts"]
    sorted_words = dict(sorted(words.items(), key=lambda item: item[1], reverse=True))

    return dict(islice(sorted_words.items(), 10))


def pro_players_to_text(players) -> str:
    text = ""
    for player in players:
        text += "\n\nname: " + player["name"].replace('<', '')
        if player["team_name"]:
            text += "\nteam: " + player["team_name"]
        if player["country_code"]:
            text += "\ncountry code: " + player["country_code"]
        if player["account_id"]:
            text += "\naccount id: <code>{}</code>".format(player["account_id"])
    return text


def get_pro_matches(res_json) -> str:
    text = ""
    for match in res_json:
        if match["league_id"] and not match["deactivate_time"]:
            text += match["team_name_radiant"] + " " + str(match["radiant_score"])
            text += " vs " + str(match["dire_score"]) + " " + match["team_name_dire"] + "\n"
    return text


def get_public_matches(res_json, favourite_players) -> str:
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
                        if favourite_players:
                            for fav_players in favourite_players["players"]:
                                if player["account_id"] in fav_players.values():
                                    text += "⭐"
                        text += "<code>{}</code> {} - {}\n".format(player["account_id"],
                                                                   player["name"].replace('<', ''),
                                                                   get_hero_name(player["hero_id"]))
            text += "\n"
    if is_pro_player:
        return text
    else:
        return ""


def get_league_match_button_text(match) -> str:
    if 'scoreboard' not in match or match['scoreboard']['duration'] == 0:
        return ''

    radiant = dire = "unknown"

    if "radiant_team" in match:
        radiant = match["radiant_team"]["team_name"]
    if "dire_team" in match:
        dire = match["dire_team"]["team_name"]

    h, m = divmod(match["scoreboard"]["duration"], 60)
    duration = "⌛️ {}:{:02}".format(int(h), int(m))

    text = "{} 🆚 {} {:>10}".format(
        radiant, dire, duration
    )
    return text


def get_league_match_info(match) -> str:
    radiant = dire = "unknown"

    if "radiant_team" in match:
        radiant = match["radiant_team"]["team_name"]
    if "dire_team" in match:
        dire = match["dire_team"]["team_name"]

    h, m = divmod(match["scoreboard"]["duration"], 60)
    duration = "{}:{:02}".format(int(h), int(m))

    radiant_score = match["scoreboard"]["radiant"]["score"]
    dire_score = match["scoreboard"]["dire"]["score"]

    match_id = match["match_id"]
    league_id = match["league_id"]
    league_node_id = match["league_node_id"]
    spectators = match["spectators"]
    stream_delay_s = match["stream_delay_s"]
    radiant_series_wins = match["radiant_series_wins"]
    dire_series_wins = match["dire_series_wins"]
    series_type = match["series_type"]

    radiant_tower_state = match['scoreboard']['radiant']['tower_state']
    radiant_barracks_state = match['scoreboard']['radiant']['barracks_state']

    if 'picks' in match['scoreboard']['radiant']:
        radiant_picks = [pick['hero_id'] for pick in match['scoreboard']['radiant']['picks']]
    else:
        radiant_picks = []

    radiant_net_worth = sum(player['net_worth'] for player in match['scoreboard']['radiant']['players'])
    radiant_xp_per_min = sum(player['xp_per_min'] for player in match['scoreboard']['radiant']['players'])

    dire_tower_state = match['scoreboard']['dire']['tower_state']
    dire_barracks_state = match['scoreboard']['dire']['barracks_state']

    if 'picks' in match['scoreboard']['dire']:
        dire_picks = [pick['hero_id'] for pick in match['scoreboard']['dire']['picks']]
    else:
        dire_picks = []

    dire_net_worth = sum(player['net_worth'] for player in match['scoreboard']['dire']['players'])
    dire_xp_per_min = sum(player['xp_per_min'] for player in match['scoreboard']['dire']['players'])

    net_worth_lead = radiant_net_worth - dire_net_worth
    net_worth_lead_str = ''
    if net_worth_lead > 0:
        net_worth_lead_str = '🟢 {}'.format(net_worth_lead)
    elif net_worth_lead < 0:
        net_worth_lead_str = '🔴 {}'.format(-net_worth_lead)

    xp_per_min_lead = radiant_xp_per_min - dire_xp_per_min
    xp_per_min_lead_str = ''
    if xp_per_min_lead > 0:
        xp_per_min_lead_str = '🟢 {}'.format(xp_per_min_lead)
    elif xp_per_min_lead < 0:
        xp_per_min_lead_str = '🔴 {}'.format(-xp_per_min_lead)
    
    text = """🟢{} vs {}🔴
    duration: {}
    score: {} vs {}
    net_worth_lead: {}
    xp_per_min_lead: {}

    match_id: {}
    league_id: {}
    league_node_id: {}
    spectators: {}
    stream_delay_s: {}
    radiant_series_wins: {}
    dire_series_wins: {}
    series_type: {}

    radiant_tower_state: {}
    radiant_barracks_state: {}
    radiant_picks: {}
    radiant_net_worth: {}
    radiant_xp_per_min: {}

    dire_tower_state: {}
    dire_barracks_state: {}
    dire_picks: {}
    dire_net_worth: {}
    dire_xp_per_min: {}
    """.format(
            radiant, dire,
            duration,
            radiant_score, dire_score,
            net_worth_lead_str,
            xp_per_min_lead_str,
            match_id,
            league_id,
            league_node_id,
            spectators,
            stream_delay_s,
            radiant_series_wins,
            dire_series_wins,
            series_type,
            radiant_tower_state,
            radiant_barracks_state,
            ' '.join(str(pick) for pick in radiant_picks),
            radiant_net_worth,
            radiant_xp_per_min,
            dire_tower_state,
            dire_barracks_state,
            ' '.join(str(pick) for pick in dire_picks),
            dire_net_worth,
            dire_xp_per_min
        )
    
    return text

def get_league_match_features(match):
    features = []

    features.append(match["scoreboard"]["duration"])
    features.append(match["radiant_series_wins"])
    features.append(match["dire_series_wins"])

    features.append(
        match["scoreboard"]["radiant"]["score"]
        - match["scoreboard"]["dire"]["score"]
    )
    features.append(
        match["scoreboard"]["radiant"]["tower_state"]
        - match["scoreboard"]["dire"]["tower_state"]
    )
    features.append(
        match["scoreboard"]["radiant"]["barracks_state"]
        - match["scoreboard"]["dire"]["barracks_state"]
    )

    radiant_net_worth = 0
    dire_net_worth = 0

    for player in match["scoreboard"]["radiant"]["players"]:
        features.append(player["kills"])
        features.append(player["death"])
        features.append(player["assists"])
        features.append(player["last_hits"])
        features.append(player["gold"])
        features.append(player["level"])
        features.append(player["gold_per_min"])
        features.append(player["xp_per_min"])
        features.append(player["item0"])
        features.append(player["item1"])
        features.append(player["item2"])
        features.append(player["item3"])
        features.append(player["item4"])
        features.append(player["item5"])
        features.append(player["net_worth"])

        radiant_net_worth += player["net_worth"]

    for player in match["scoreboard"]["dire"]["players"]:
        features.append(player["kills"])
        features.append(player["death"])
        features.append(player["assists"])
        features.append(player["last_hits"])
        features.append(player["gold"])
        features.append(player["level"])
        features.append(player["gold_per_min"])
        features.append(player["xp_per_min"])
        features.append(player["item0"])
        features.append(player["item1"])
        features.append(player["item2"])
        features.append(player["item3"])
        features.append(player["item4"])
        features.append(player["item5"])
        features.append(player["net_worth"])

        dire_net_worth += player["net_worth"]

    features.append(radiant_net_worth - dire_net_worth)

    return np.array([features])


def predict_league_match_result(match):
    X = get_league_match_features(match)

    prediction = 'predictions: '

    et_pred = ET_CLASSIFIER.predict_proba(X)[0]
    et_pred_str = ''
    if et_pred[0] > et_pred[1]:
        et_pred_str = f"🔴 {round(et_pred[0] * 100)}%"
    else:
        et_pred_str = f"🟢 {round(et_pred[1] * 100)}%"

    rf_pred = RF_CLASSIFIER.predict_proba(X)[0]
    rf_pred_str = ''
    if rf_pred[0] > rf_pred[1]:
        rf_pred_str = f"🔴 {round(rf_pred[0] * 100)}%"
    else:
        rf_pred_str = f"🟢 {round(rf_pred[1] * 100)}%"

    hgb_pred = HGB_CLASSIFIER.predict_proba(X)[0]
    hgb_pred_str = ''
    if hgb_pred[0] > hgb_pred[1]:
        hgb_pred_str = f"🔴 {round(hgb_pred[0] * 100)}%"
    else:
        hgb_pred_str = f"🟢 {round(hgb_pred[1] * 100)}%"

    gb_pred = GB_CLASSIFIER.predict_proba(X)[0]
    gb_pred_str = ''
    if gb_pred[0] > gb_pred[1]:
        gb_pred_str = f"🔴 {round(gb_pred[0] * 100)}%"
    else:
        gb_pred_str = f"🟢 {round(gb_pred[1] * 100)}%"

    ab_pred = AB_CLASSIFIER.predict_proba(X)[0]
    ab_pred_str = ''
    if ab_pred[0] > ab_pred[1]:
        ab_pred_str = f"🔴 {round(ab_pred[0] * 100)}%"
    else:
        ab_pred_str = f"🟢 {round(ab_pred[1] * 100)}%"

    avg_pred = [
        (et_pred[0] + rf_pred[0] + hgb_pred[0] + gb_pred[0] + ab_pred[0]) / 5,
        (et_pred[1] + rf_pred[1] + hgb_pred[1] + gb_pred[1] + ab_pred[1]) / 5
    ]
    avg_pred_str = ''
    if avg_pred[0] > avg_pred[1]:
        avg_pred_str = f"🔴 {round(avg_pred[0] * 100)}%"
    else:
        avg_pred_str = f"🟢 {round(avg_pred[1] * 100)}%"

    prediction = """predictions:
        Extra Tree Classifier: {}
        Random Forest: {}
        Hist Gradient Boosting: {}
        Gradient Boosting: {}
        Adaboost: {}

        average: {}""".format(
        et_pred_str, 
        rf_pred_str, 
        hgb_pred_str, 
        gb_pred_str, 
        ab_pred_str, 
        avg_pred_str
    )

    return prediction
