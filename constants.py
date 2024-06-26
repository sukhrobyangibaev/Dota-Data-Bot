import logging
import pickle
import sys
import pymongo
from gensim.models import Word2Vec

logging.basicConfig(
    # filename='dota_data_bot.log',
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logging.getLogger("httpx").setLevel(logging.WARNING)
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
    TYPE_ADMIN_MESSAGE,
    FAVOURITE_PLAYERS,
    ADD_NEW_PLAYER,
    DELETE_PLAYER,
    CHOOSE_PLAYER,
    # to predict
    LIVE_LEAGUE,
    SELECTED_LEAGUE_MATCH
) = range(71)

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["opendotabot"]
heroes_col = mydb["heroes"]
pro_players_col = mydb["proplayers"]
users_col = mydb["users"]
chats_col = mydb["chats"]
fav_players_col = mydb["fav_players"]

with open('models/10min/et_classifier.pkl', 'rb') as f:
    M10_ET_CLASSIFIER = pickle.load(f)
with open('models/10min/rf_classifier.pkl', 'rb') as f:
    M10_RF_CLASSIFIER = pickle.load(f)
with open('models/10min/hgb_classifier.pkl', 'rb') as f:
    M10_HGB_CLASSIFIER = pickle.load(f)
with open('models/10min/gb_classifier.pkl', 'rb') as f:
    M10_GB_CLASSIFIER = pickle.load(f)
with open('models/10min/cart_classifier.pkl', 'rb') as f:
    M10_CART_CLASSIFIER = pickle.load(f)
with open('models/10min/cart_classifier.pkl', 'rb') as f:
    M10_C45_CLASSIFIER = pickle.load(f)
with open('models/10min/cart_classifier.pkl', 'rb') as f:
    M10_AB_CLASSIFIER = pickle.load(f)  

with open('models/20min/et_classifier.pkl', 'rb') as f:
    M20_ET_CLASSIFIER = pickle.load(f)
with open('models/20min/rf_classifier.pkl', 'rb') as f:
    M20_RF_CLASSIFIER = pickle.load(f)
with open('models/20min/hgb_classifier.pkl', 'rb') as f:
    M20_HGB_CLASSIFIER = pickle.load(f)
with open('models/20min/gb_classifier.pkl', 'rb') as f:
    M20_GB_CLASSIFIER = pickle.load(f)
with open('models/20min/cart_classifier.pkl', 'rb') as f:
    M20_CART_CLASSIFIER = pickle.load(f)
with open('models/20min/cart_classifier.pkl', 'rb') as f:
    M20_C45_CLASSIFIER = pickle.load(f)
with open('models/20min/cart_classifier.pkl', 'rb') as f:
    M20_AB_CLASSIFIER = pickle.load(f) 

with open('models/30min/et_classifier.pkl', 'rb') as f:
    M30_ET_CLASSIFIER = pickle.load(f)
with open('models/30min/rf_classifier.pkl', 'rb') as f:
    M30_RF_CLASSIFIER = pickle.load(f)
with open('models/30min/hgb_classifier.pkl', 'rb') as f:
    M30_HGB_CLASSIFIER = pickle.load(f)
with open('models/30min/gb_classifier.pkl', 'rb') as f:
    M30_GB_CLASSIFIER = pickle.load(f)
with open('models/30min/cart_classifier.pkl', 'rb') as f:
    M30_CART_CLASSIFIER = pickle.load(f)
with open('models/30min/cart_classifier.pkl', 'rb') as f:
    M30_C45_CLASSIFIER = pickle.load(f)
with open('models/30min/cart_classifier.pkl', 'rb') as f:
    M30_AB_CLASSIFIER = pickle.load(f) 

heroes_model = Word2Vec.load("models/winner_hero_embeddings.model")
items_model = Word2Vec.load("models/dota2_items_embeddings.model")

kda_obj = {
    "KILLS": "kills",
    "DEATHS": "deaths",
    "ASSISTS": "assists"
}

wl_obj = {
    "WIN": 1,
    "LOSE": 0
}

DEVELOPER_CHAT_ID = '1476403327'