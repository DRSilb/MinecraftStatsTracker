import json
import os
import re
import requests
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)
project_folder = '/home/DRSilb/MinecraftStatsTracker'
logging.info(f"Using project folder path: {project_folder}")
DATA_DIR = os.path.join(project_folder, 'data')
logging.info(f"Constructed DATA_DIR path is: {DATA_DIR}")
ALL_ADVANCEMENTS_FILE_PATH = os.path.join(DATA_DIR, 'all_advancements.json')

def is_uuid(id_string):
    if not isinstance(id_string, str):
        return False
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$', re.IGNORECASE)
    return bool(uuid_pattern.match(id_string))

def get_player_type(player_id):
    """Determines if a player ID is Java (UUID) or Bedrock (XUID-like)."""
    if is_uuid(player_id):
        return "java"
    if player_id.startswith("00000000-0000-0000-") and player_id.count('-') == 4:
        return "bedrock"
    if len(player_id) == 16 and all(c in '0123456789abcdefABCDEF' for c in player_id):
        return "bedrock"
    if len(player_id) >= 16 and player_id.isdigit():
        return "bedrock"
    return "unknown"

def fetch_java_username(uuid):
    """Fetches Java player username from Mojang API."""
    clean_uuid = uuid.strip().rstrip('_')
    if not is_uuid(clean_uuid):
        logging.warning(f"Invalid UUID format after cleaning: '{uuid}' became '{clean_uuid}'. Skipping Mojang API call.")
        return uuid
    formatted_uuid = clean_uuid.replace('-', '')
    try:
        response = requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{formatted_uuid}", timeout=5)
        if response.status_code == 200:
            return response.json().get('name', clean_uuid)
        elif response.status_code == 204:
             return clean_uuid
        else:
            logging.error(f"Mojang API error for {formatted_uuid} (from {uuid}): {response.status_code}")
    except requests.RequestException as e:
        logging.error(f"Request error fetching Java username for {formatted_uuid} (from {uuid}): {e}")
    return clean_uuid

def load_json_file(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from {file_path}: {e}")
        except Exception as e:
            logging.error(f"Error loading file {file_path}: {e}")
    else:
        logging.warning(f"File not found: {file_path}")
    return None

PLAYER_FILES_DATA = {}
ALL_ADVANCEMENTS_DATA = []

def load_all_data():
    global PLAYER_FILES_DATA, ALL_ADVANCEMENTS_DATA
    raw_player_files = {}
    logging.info("--- Starting Data Loading ---")

    stats_dir = os.path.join(DATA_DIR, 'stats')
    advancements_dir = os.path.join(DATA_DIR, 'advancements')

    logging.info(f"Attempting to load data from stats_dir: {stats_dir}")
    logging.info(f"Attempting to load data from advancements_dir: {advancements_dir}")

    # Load the list of all possible advancements
    adv_list_path = ALL_ADVANCEMENTS_FILE_PATH
    logging.info(f"Advancements master list path: {adv_list_path}")
    ALL_ADVANCEMENTS_DATA = load_json_file(adv_list_path) or []
    if not ALL_ADVANCEMENTS_DATA:
        logging.warning(f"Advancement master list from {adv_list_path} is empty or failed to load.")
    else:
        logging.info(f"Successfully loaded {len(ALL_ADVANCEMENTS_DATA)} advancement definitions.")


    # 1. Process stats files
    if os.path.exists(stats_dir):
        logging.info(f"Stats directory found. Files within: {os.listdir(stats_dir)}")
        for filename in os.listdir(stats_dir):
            if filename.endswith('.json'):
                player_id = filename[:-5]
                file_path = os.path.join(stats_dir, filename)
                stats_data = load_json_file(file_path)
                if stats_data:
                    if player_id not in raw_player_files:
                        raw_player_files[player_id] = {"stats_data": None, "advancements_data": None}
                    raw_player_files[player_id]['stats_data'] = stats_data
    else:
        logging.error(f"STATS DIRECTORY NOT FOUND AT: {stats_dir}")

    # 2. Process advancements files
    if os.path.exists(advancements_dir):
        logging.info(f"Advancements directory found. Files within: {os.listdir(advancements_dir)}")
        for filename in os.listdir(advancements_dir):
            if filename.endswith('.json'):
                player_id = filename[:-5]
                file_path = os.path.join(advancements_dir, filename)
                advancements_data = load_json_file(file_path)
                if advancements_data:
                    if player_id not in raw_player_files:
                        raw_player_files[player_id] = {"stats_data": None, "advancements_data": None}
                    raw_player_files[player_id]['advancements_data'] = advancements_data
    else:
        logging.error(f"ADVANCEMENTS DIRECTORY NOT FOUND AT: {advancements_dir}")

    temp_player_files_data = {}
    for p_id_from_file, data_dict in raw_player_files.items():
        player_type = get_player_type(p_id_from_file)
        username_to_display = p_id_from_file

        if player_type == "java":
            username_to_display = fetch_java_username(p_id_from_file)

        display_name_str = username_to_display
        if username_to_display == p_id_from_file and len(p_id_from_file) > 8 and not is_uuid(p_id_from_file) and player_type != "java":
            display_name_str = f"{username_to_display} ({p_id_from_file[:8]}...)"

        temp_player_files_data[p_id_from_file] = {
            "id_from_file": p_id_from_file,
            "username": username_to_display,
            "type": player_type,
            "stats_data": data_dict["stats_data"],
            "advancements_data": data_dict["advancements_data"],
            "display_name": display_name_str,
            "has_stats": data_dict["stats_data"] is not None,
            "has_advancements": data_dict["advancements_data"] is not None
        }

    merged_by_fetched_username = {}
    for file_id_key, player_data_entry in temp_player_files_data.items():
        fetched_username = player_data_entry["username"]
        if fetched_username not in merged_by_fetched_username:
            player_data_entry["id"] = file_id_key
            merged_by_fetched_username[fetched_username] = player_data_entry
        else:
            existing_entry = merged_by_fetched_username[fetched_username]
            if player_data_entry["stats_data"] and not existing_entry["stats_data"]:
                existing_entry["stats_data"] = player_data_entry["stats_data"]
            if player_data_entry["advancements_data"] and not existing_entry["advancements_data"]:
                existing_entry["advancements_data"] = player_data_entry["advancements_data"]
            existing_entry["has_stats"] = existing_entry["stats_data"] is not None
            existing_entry["has_advancements"] = existing_entry["advancements_data"] is not None
            if is_uuid(file_id_key) and not is_uuid(existing_entry["id"]):
                existing_entry["id"] = file_id_key

    PLAYER_FILES_DATA = {}
    for username_key, data_obj in merged_by_fetched_username.items():
        canonical_id_for_player = data_obj["id"]
        PLAYER_FILES_DATA[canonical_id_for_player] = data_obj

    logging.info(f"--- Data Loading Complete. {len(PLAYER_FILES_DATA)} unique players processed. ---")

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/players')
def get_players():
    player_list = []
    for player_data_obj in PLAYER_FILES_DATA.values():
        if player_data_obj["stats_data"] or player_data_obj["advancements_data"]:
            player_list.append({
                "id": player_data_obj["id"],
                "username": player_data_obj["username"],
                "display_name": player_data_obj["display_name"],
                "type": player_data_obj["type"],
                "has_stats": player_data_obj["stats_data"] is not None,
                "has_advancements": player_data_obj["advancements_data"] is not None
            })
    player_list.sort(key=lambda p: p["display_name"].lower())
    return jsonify(player_list)

@app.route('/api/player_data/<player_id>')
def get_player_data(player_id):
    if player_id in PLAYER_FILES_DATA:
        return jsonify(PLAYER_FILES_DATA[player_id])
    for p_data in PLAYER_FILES_DATA.values():
        if p_data["username"] == player_id or p_data.get("id_from_file") == player_id :
            return jsonify(p_data)
    return jsonify({"error": "Player not found by ID or username"}), 404

@app.route('/api/stats_categories')
def get_stats_categories():
    categories = {
        "minecraft:custom": set(), "minecraft:killed": set(), "minecraft:killed_by": set(),
        "minecraft:used": set(), "minecraft:mined": set(), "minecraft:broken": set(),
        "minecraft:picked_up": set(), "minecraft:dropped": set(),
        "minecraft:crafted": set()
    }
    for player_data_value in PLAYER_FILES_DATA.values():
        if player_data_value.get("stats_data") and player_data_value["stats_data"].get("stats"):
            player_stats = player_data_value["stats_data"]["stats"]
            for category_key, stats_dict in player_stats.items():
                if category_key in categories and isinstance(stats_dict, dict):
                    categories[category_key].update(stats_dict.keys())
    for cat in categories: categories[cat] = sorted(list(categories[cat]))
    return jsonify(categories)

@app.route('/api/advancements_list')
def get_advancements_list():
    adv_list = []
    if ALL_ADVANCEMENTS_DATA:
        for adv_obj in ALL_ADVANCEMENTS_DATA:
            if not isinstance(adv_obj, dict) or 'orig' not in adv_obj or 'name' not in adv_obj:
                continue
            full_adv_id = f"minecraft:{adv_obj['orig']}"
            adv_list.append({
                "id": full_adv_id,
                "name": adv_obj.get('name', 'Unknown Advancement'),
                "desc": adv_obj.get('desc', 'No description available.'),
                "cat": adv_obj.get('cat', 'misc')
            })
    adv_list.sort(key=lambda x: x['name'])
    return jsonify(adv_list)

load_all_data()

if __name__ == '__main__':
    app.run(debug=False)
