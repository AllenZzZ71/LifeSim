import os
import json
import random
import string

CHARACTER_DIR = "./chars"
WORLD_DIR = "./world/events"
CITIES_DIR = "./world/worldmap/cities"
BODY_DIR = "./body"
TIME_DIR = "./world/time.json"

TRAITS = ["aa", "ab", "ac", "ad", "ae", "af", "ag", "ah", "ai", "aj"]
NAMES = [
    "Jordan", "Taylor", "Alex", "Riley", "Quinn", "Sky", "Avery", "Phoenix", "Reese", "River",
    "Kai", "Zane", "Leo", "Max", "Jasper", "Milo", "Ezra", "Orion", "Silas", "Luca",
    "Lena", "Nova", "Rhea", "Mira", "Aria", "Zara", "Ivy", "Nina", "Clio", "Talia",
    "Nyx", "Thorne", "Lyra", "Zephyr", "Onyx", "Dax", "Sol", "Ember", "Vera", "Ash",
    "Noah", "Sage", "Lior", "Indigo", "Isla", "Remy", "Bellamy", "Elio", "Wren", "Marlowe"
]

def load_json(path, fallback=None):
    if not os.path.exists(path):
        return fallback if fallback is not None else {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        print(f"Warning: Failed to load {path}, resetting to fallback.")
        return fallback if fallback is not None else {}

def generate_unique_id(length=6):
    existing = set(f[:-5] for f in os.listdir(CHARACTER_DIR) if f.endswith(".json"))
    while True:
        new_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
        if new_id not in existing:
            return new_id

def generate_stat_block():
    return ''.join([str(random.randint(0, 99)).zfill(2) for _ in range(10)])

def create_body_file(char_id):
    body_data = {
        "body": {
            "head": {"health": 100},
            "torso": {"health": 100},
            "left_arm": {"health": 100},
            "right_arm": {"health": 100},
            "left_leg": {"health": 100},
            "right_leg": {"health": 100}
        }
    }
    os.makedirs(BODY_DIR, exist_ok=True)
    with open(f"{BODY_DIR}/{char_id}.json", "w") as f:
        json.dump(body_data, f, indent=2)

def get_all_city_ids():
    ids = []
    for fname in os.listdir(CITIES_DIR):
        if fname.endswith(".json"):
            path = os.path.join(CITIES_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8-sig") as f:
                    content = f.read().strip()
                    if not content:
                        continue  # skip empty files
                    data = json.loads(content)
                    if isinstance(data, dict) and "id" in data:
                        ids.append(data["id"])
            except Exception as e:
                print(f"⚠️ Failed to load {path}: {e}")
                continue
    return ids

def generate_character(city_ids):
    char_id = generate_unique_id()
    name = random.choice(NAMES)
    age = random.randint(0, 100)
    gender = random.randint(0, 1)  # 0 = Male, 1 = Female
    birthtick = load_json(TIME_DIR)["tick"]
    traits = random.sample(TRAITS, 2)
    personality = generate_stat_block()
    stats = generate_stat_block()
    fightStats = generate_stat_block()
    relationships = {}
    current_location = random.choice(city_ids) if city_ids else None

    character_data = [
        char_id,
        name,
        age,
        gender,
         birthtick,
        traits,
        personality,
        stats,
        fightStats,
        relationships,
        current_location
    ]

    os.makedirs(CHARACTER_DIR, exist_ok=True)
    with open(f"{CHARACTER_DIR}/{char_id}.json", "w") as f:
        json.dump(character_data, f, indent=2)

    log_dir = os.path.join(WORLD_DIR, char_id)
    os.makedirs(log_dir, exist_ok=True)

    with open(f"{log_dir}/memory.json", "w") as f:
        json.dump({"facts": []}, f)
    open(f"{log_dir}/messages.jsonl", "w").close()
    with open(f"{log_dir}/summaries.json", "w") as f:
        json.dump({"events": []}, f)

    create_body_file(char_id)

def generate_n_characters(n=100):
    city_ids = get_all_city_ids()
    for _ in range(n):
        generate_character(city_ids)

if __name__ == "__main__":
    generate_n_characters(100)
    print("✅ 100 characters generated with city-based locations.")
