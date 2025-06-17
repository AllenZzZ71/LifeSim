import os
import json
import random
from datetime import datetime

CHARACTER_PATH = "./chars"
TIME_PATH = "./world/time.json"
WORLD_DIR = "./world/events"
PLAYER_PATH = "./player/player.json"

# Tick rate: 1 = 1 day per tick
TICK_RATE = 30

# Utility: Load JSON
def load_json(path, fallback=None):
    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        return fallback if fallback is not None else {}

    try:
        with open(path, 'r', encoding='utf-8-sig') as f:  # <- key change
            content = f.read().strip()
            if not content:
                print(f"⚠️ Empty JSON file: {path}")
                return fallback if fallback is not None else {}
            return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON decode error in {path}: {e}")
        return fallback if fallback is not None else {}
    except IOError as e:
        print(f"⚠️ IO error reading {path}: {e}")
        return fallback if fallback is not None else {}


# Utility: Save JSON

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

# Initialize world time

def initialize_time():
    now = datetime.now()
    time_data = {
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "tick": 0
    }
    save_json(TIME_PATH, time_data)
    return time_data

# Advance time by 1 tick

def advance_time():
    if not os.path.exists(TIME_PATH):
        time_data = initialize_time()
    else:
        time_data = load_json(TIME_PATH)
    time_data["tick"] += TICK_RATE
    time_data["day"] += TICK_RATE

    if time_data["day"] > 30:
        time_data["day"] = 1
        time_data["month"] += 1
    if time_data["month"] > 12:
        time_data["month"] = 1
        time_data["year"] += 1

    save_json(TIME_PATH, time_data)
    print(f"[World Tick {time_data['tick']}] Date: {time_data['year']}-{time_data['month']:02d}-{time_data['day']:02d}")


# Modify Stats

def modify_stat(stat_string, index, amount):
    current = int(stat_string[index:index+2])
    updated = max(0, min(99, current + amount))
    return stat_string[:index] + str(updated).zfill(2) + stat_string[index+2:]



# Load all character IDs

def get_all_characters():
    files = os.listdir(CHARACTER_PATH)
    return [f[:-5] for f in files if f.endswith(".json")]

# --- Action Generator ---
def generate_action(actor, target):
    actor_name = actor[1]
    target_name = target[1]
    empathy = int(actor[6][0:2])
    assertiveness = int(actor[6][2:4])
    actions = []

    if empathy > 50:
        actions.append(f"{actor_name} comforted {target_name} during a tough moment.")
        actions.append(f"{actor_name} gave advice to {target_name} after a breakup.")
    if assertiveness > 50:
        actions.append(f"{actor_name} stood up for {target_name} in an argument.")
        actions.append(f"{actor_name} challenged {target_name} to improve themselves.")

    actions.append(f"{actor_name} chatted with {target_name} about the weather.")
    actions.append(f"{actor_name} ignored {target_name} completely.")

    return random.choice(actions)


def display_player_location(player):
    location_id = player[10] if len(player) > 10 else "unknown"
    city_path = f"./world/worldmap/cities/{location_id}.json"
    #print(city_path)

    if os.path.exists(city_path):
        city_data = load_json(city_path)
        #print(city_data)
        city_name = city_data.get("name", "Unknown City")
        country = city_data.get("country", "Unknown Country")
    else:
        city_name = "Unknown City"
        country = "Unknown Country"

    # Count NPCs in this location
    count = 0
    for cid in get_all_characters():
        char_data = load_json(os.path.join(CHARACTER_PATH, f"{cid}.json"))
        if len(char_data) > 6 and char_data[-1] == location_id:
            count += 1

    print(f"\n📍 Location: {city_name}, {country}")
    print(f"👥 Population in this city: {count}")


def list_nearby_npcs(player):
    player_location = player[10]
    nearby_npcs = []

    for cid in get_all_characters():
        char_data = load_json(os.path.join(CHARACTER_PATH, f"{cid}.json"))
        if char_data and len(char_data) > 10 and char_data[10] == player_location:
            nearby_npcs.append((cid, char_data))

    if not nearby_npcs:
        print("\n🕵️ No one is around to interact with today.")
        return

    print("\n👥 People nearby:")
    for i, (cid, npc) in enumerate(nearby_npcs, 1):
        name = npc[1]
        stats = npc[8]
        speed = int(stats[6:8])
        strength = int(stats[0:2])
        print(f"{i}. {name} (Speed: {speed}, Strength: {strength}) ({npc[0]})")

    while True:
        try:
            choice = int(input("\nWho do you want to approach? (number): "))
            if 1 <= choice <= len(nearby_npcs):
                chosen_id, chosen_data = nearby_npcs[choice - 1]
                name = chosen_data[1]
                print(f"\n👋 You approach {name}. What do you want to do?\n")
                print("1. Chat")
                print("2. Pick a Fight")

                sub_choice = int(input("Choose (1 or 2): "))
                if sub_choice == 1:
                    print(f"\n💬 You greeted {name}. They smiled back.")
                    log_player_action(player, "interact_npc", f"Interacted with {name}")
                elif sub_choice == 2:
                    print(f"\n⚔️ You chose to fight {name}!")
                    initiate_fight(player, chosen_data)
                else:
                    print("❌ Invalid sub-choice.")
                break
        except ValueError:
            pass
        print("❌ Invalid input. Try again.")



# --- Log to Summary ---
def log_to_summary(npc_id, text):
    summary_path = os.path.join(WORLD_DIR, npc_id, "summaries.json")
    summaries = load_json(summary_path, {"events": []})

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    summaries["events"].append({
        "time": timestamp,
        "summary": text
    })

    save_json(summary_path, summaries)


def log_player_action(player, action_id, action_label):
    log_path = "./player/event/log.json"
    logs = load_json(log_path, [])
    
    logs.append({
        "tick": load_json(TIME_PATH)["tick"],
        "name": player[1],
        "action_id": action_id,
        "action": action_label,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    save_json(log_path, logs)


def simulate_day():
    characters = get_all_characters()
    for cid in characters:
        path = f"{CHARACTER_PATH}/{cid}.json"
        data = load_json(path)

        empathy_score = int(data[6][:2])
        assertiveness_score = int(data[6][2:4])
        discipline_score = int(data[6][4:6])

        possible_actions = []

        if empathy_score > 60:
            possible_actions.append("volunteered at the shelter")
        if assertiveness_score > 60:
            possible_actions.append("stood up for a friend in an argument")
        if discipline_score > 60:
            possible_actions.append("woke up early and exercised")
        if empathy_score < 30:
            possible_actions.append("ignored someone in need")
        if discipline_score < 30:
            possible_actions.append("slept through most of the day")

        if not possible_actions:
            possible_actions = ["went about their day quietly"]

        action = random.choice(possible_actions)

        log_path = f"./world/events/{cid}/summaries.json"
        summaries = load_json(log_path, {"events": []})
        summaries["events"].append({
            "tick": load_json(TIME_PATH)["tick"],
            "action": action
        })
        save_json(log_path, summaries)

        # == Uncomment to see log print(f"{data[1]} ({cid}) {action}.")


def char_to_char():
    character_ids = get_all_characters()
    characters = {}

    # Preload all character data
    for cid in character_ids:
        path = f"{CHARACTER_PATH}/{cid}.json"
        characters[cid] = load_json(path)

    for _ in range(10):  # simulate 10 pair interactions
        actor_id, target_id = random.sample(character_ids, 2)
        actor = characters[actor_id]
        target = characters[target_id]
        summary = generate_action(actor, target)
        print(summary)
        log_to_summary(actor_id, summary)
        log_to_summary(target_id, summary)

# Player Creation

def create_player():
    os.makedirs("./player", exist_ok=True)
    name = input("What is your character’s name? ")
    gender = input("Gender (male/female/other): ").lower()

    if(gender == "male"):
        gender = 0
    elif(gender == "female"):
        gender = 1
    else:
        gender = 2

    player = ["0", name, 0 , gender, load_json(TIME_PATH)["tick"] + 1, 0, random.sample(["aa", "ab", "ac", "ad", "ae", "af", "ag", "ah", "ai", "aj"], 2), "00000000000000000000", "00000000000000000000", {}]

    with open(PLAYER_PATH, "w") as f:
        json.dump(player, f, indent=2)

    print(f"\n🎉 Welcome to the world, {name}!\n")
    return player

def calculate_age(current_tick, birth_tick):
    return (current_tick - birth_tick) // 365

def getPlayer():
    if not os.path.exists(PLAYER_PATH):
        return None
    with open(PLAYER_PATH, "r") as f:
        return json.load(f)
    
def move_to_new_city(player):
    cities = []
    city_folder = "./world/worldmap/cities"
    
    for fname in os.listdir(city_folder):
        if fname.endswith(".json"):
            fpath = os.path.join(city_folder, fname)
            city_data = load_json(fpath)
            if not city_data or "id" not in city_data or "name" not in city_data:
                continue

            city_id = city_data["id"]
            city_name = city_data["name"]
            country = city_data.get("country", "Unknown")

            # Count population
            pop = 0
            for cid in get_all_characters():
                char = load_json(os.path.join(CHARACTER_PATH, f"{cid}.json"))
                if len(char) > 10 and char[10] == city_id:
                    pop += 1

            cities.append({
                "id": city_id,
                "name": city_name,
                "country": country,
                "population": pop
            })

    print("\n🗺️ Available Cities to Move To:")
    for i, city in enumerate(cities, 1):
        print(f"{i}. {city['name']} ({city['country']}) - Population: {city['population']}")

    while True:
        try:
            selection = int(input("\nWhere would you like to move? (number): "))
            if 1 <= selection <= len(cities):
                selected = cities[selection - 1]
                player[10] = selected["id"]  # update location
                print(f"\n🚶 You moved to {selected['name']}, {selected['country']}!")
                save_json(PLAYER_PATH, player)
                break
        except ValueError:
            pass
        print("❌ Invalid choice. Try again.")


# Fight FIGHT FIGHT!
def fight_loop(player, npc):
    from time import sleep

    BASE_DAMAGE = 10
    BASE_CD = 20

    def calc_damage(base, strength, multiplier=1.0):
        return int((base + strength * 0.5) * multiplier)

    def calc_cooldown(base, speed):
        return max(10, int(base + speed * 0.5))  # prevent cooldown < 0
    
    def calc_random_damage(base_dmg, strength, multiplier, exp):
        raw = calc_damage(base_dmg, strength, multiplier)
        consistency = 0.5 + (exp / 200)  # Between 0.5 and 1.0
        low = int(raw * consistency)
        return random.randint(low, raw)

    player_stats = player[8]
    npc_stats = npc[8]

    player_speed = int(player_stats[6:8])
    player_strength = int(player_stats[0:2])
    player_exp = int(player_stats[8:10])

    npc_speed = int(npc_stats[6:8])
    npc_strength = int(npc_stats[0:2])
    npc_exp = int(npc_stats[8:10])

    player_body = load_json(f"./body/{player[0]}.json")["body"]
    npc_body = load_json(f"./body/{npc[0]}.json")["body"]

    cooldown_cost_p = calc_cooldown(BASE_CD, player_speed)
    cooldown_cost_n = calc_cooldown(BASE_CD, npc_speed)
    cooldown_p = 0
    cooldown_n = 0
    turn = 0

    ZONES = ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"]
    print(f"\n⚔️ Fight starts between {player[1]} and {npc[1]}!\n")

    while True:
        print(f"\n🔁 Round {turn + 1}")

        cooldown_p = max(0, cooldown_p - cooldown_cost_p)
        cooldown_n = max(0, cooldown_n - cooldown_cost_n)

        print(f"\n⏱️ Cooldowns:")
        print(f"  {player[1]}'s Cooldown: {cooldown_p}")
        print(f"  {npc[1]}'s Cooldown   : {cooldown_n}")
        sleep(0.5)

        print(f"\n📊 {player[1]}'s Body Status:")
        for zone in ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"]:
            hp = player_body[zone]["health"]
            print(f"  {zone.replace('_', ' ').title():<12}: {hp} HP")

        print(f"\n📊 {npc[1]}'s Body Status:")
        for zone in ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"]:
            hp = npc_body[zone]["health"]
            print(f"  {zone.replace('_', ' ').title():<12}: {hp} HP")

        if cooldown_p <= cooldown_n:
            if cooldown_p > 0:
                    print(f"⏳ {player[1]}'s turn skipped — recovering...")
                    cooldown_p = max(0, cooldown_p - cooldown_cost_p)
                    cooldown_n = max(0, cooldown_n - cooldown_cost_n)
                    turn += 1
                    continue

            attacker, defender = player, npc
            atk_strength = player_strength
            def_body = npc_body
            def_name = npc[1]
            exp = player_exp

            # Attack type choice
            print("\n👊 Choose attack type:")
            print("1. Punch (Accurate, Moderate Damage)")
            print("2. Kick (Harder, Less Accurate)")

            while True:
                try:
                    atk_type = int(input("Attack type (1 or 2): "))
                    if atk_type in [1, 2]:
                        break
                except ValueError:
                    pass
                print("❌ Invalid input.")

            acc_bonus = 20 if atk_type == 1 else 5
            dmg_multiplier = 1.0 if atk_type == 1 else 1.5

            # Attack zone
            print("\n🎯 Choose body part to target:")
            for i, z in enumerate(ZONES, 1):
                print(f"{i}. {z.replace('_', ' ').title()}")

            while True:
                try:
                    atk_choice = int(input("Attack zone (1–6): "))
                    if 1 <= atk_choice <= 6:
                        target_zone = ZONES[atk_choice - 1]
                        break
                except ValueError:
                    pass
                print("❌ Invalid input.")

            # Show likely enemy attack (prediction)
            likely_zone = random.choices(
                ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"],
                weights=[25, 30, 10, 10, 12.5, 12.5],
                k=1
            )[0]
            est_chance = random.randint(30, 60)
            print(f"\n🧠 Prediction: Enemy likely to strike your **{likely_zone}** ({est_chance}% chance)")

            predicted_zone = input("🛡️ Choose zone to block: ").lower()
            predicted_zone = predicted_zone if predicted_zone in ZONES else random.choice(ZONES)

        else:
            if cooldown_n > 0:
                print(f"⏳ {npc[1]}'s turn skipped — recovering...")
                cooldown_p = max(0, cooldown_p - cooldown_cost_p)
                cooldown_n = max(0, cooldown_n - cooldown_cost_n)
                turn += 1
                continue
            attacker, defender = npc, player
            atk_strength = npc_strength
            def_body = player_body
            def_name = player[1]
            exp = npc_exp

            atk_type = random.choice([1, 2])
            acc_bonus = 20 if atk_type == 1 else 5
            dmg_multiplier = 1.0 if atk_type == 1 else 1.5
            target_zone = random.choices(ZONES, weights=[15, 30, 10, 10, 17.5, 17.5])[0]
            predicted_zone = random.choice(ZONES)

        # Accuracy check
        success_chance = min(95, acc_bonus + exp)
        is_predicted = (predicted_zone == target_zone and random.randint(0, 100) < success_chance)

        if is_predicted:
            print(f"🛡️ {def_name} predicted the strike to the {target_zone} and **PARRIED**!")
            dmg = calc_random_damage(BASE_DAMAGE, atk_strength, dmg_multiplier / 2, exp)
        else:
            print(f"💥 {attacker[1]} lands a {'Punch' if atk_type == 1 else 'Kick'} to {def_name}'s {target_zone}!")
            dmg = calc_random_damage(BASE_DAMAGE, atk_strength, dmg_multiplier, exp)

        def_body[target_zone]["health"] -= dmg
        def_body[target_zone]["health"] = max(0, def_body[target_zone]["health"])
        print(f"💢 Damage dealt: {dmg}")
        print(f"🧠 Accuracy factor (based on EXP {exp}): {int(50 + exp / 2)}–100% range")


        if any(def_body[part]["health"] <= 0 for part in ["head", "torso"]):
            print(f"\n☠️ {def_name} has been defeated!")
            break

        if attacker == player:
            cooldown_p += 200
        else:
            cooldown_n += 200
        turn += 1

    # Save body states
    save_json(f"./body/{player[0]}.json", {"body": player_body})
    save_json(f"./body/{npc[0]}.json", {"body": npc_body})




def initiate_fight(player, opponent):
    print(f"\n🥊 You have engaged in a fight with {opponent[1]}!")

    player_stats = player[8]  # fightStats
    npc_stats = opponent[8]

    def get_stat_block(stats_str):
        return [int(stats_str[i:i+2]) for i in range(0, 20, 2)]

    player_f = get_stat_block(player_stats)
    npc_f = get_stat_block(npc_stats)

    player_speed = player_f[6]
    npc_speed = npc_f[6]
    player_strength = player_f[0]
    npc_strength = npc_f[0]
    player_exp = player_f[8]
    npc_exp = npc_f[8]

    print(f"Your Speed: {player_speed}, Strength: {player_strength}, Experience: {player_exp}")
    print(f"{opponent[1]}'s Speed: {npc_speed}, Strength: {npc_strength}, Experience: {npc_exp}")

    # ✅ Now launch the fight loop
    fight_loop(player, opponent)


def player_daily_choice(player):
    DAILY_CHOICES = [
        {"id": "socialize", "label": "Socialize with someone"},
        {"id": "study", "label": "Study something new"},
        {"id": "exercise", "label": "Exercise your body"},
        {"id": "relax", "label": "Relax and do nothing"},
        {"id": "explore", "label": "Go explore a new place"},
        {"id": "interact", "label": "Interact with someone nearby"},
        {"id": "move_city", "label": "Move to a different city"}
    ]

    ACTION_STAT_EFFECTS = {
        "socialize": [(4, 1), (14, 1)],      # Empathy +1, Social +1
        "study": [(2, 2)],                   # Intelligence +2
        "exercise": [(0, 1), (16, 1)],       # Strength +1, Endurance +1
        "relax": [(18, 1)],                  # Luck +1 (arbitrary)
        "explore": [(12, 1), (10, 1)],       # Creativity +1, Assertiveness +1
        "interact": [(14, 1)]                # Social +1
    }

    STAT_NAMES = {
        0: "Strength",
        2: "Intelligence",
        4: "Empathy",
        6: "Discipline",
        8: "Charisma",
        10: "Assertiveness",
        12: "Creativity",
        14: "Social",
        16: "Endurance",
        18: "Luck"
    }


    print("\n🧭 What would you like to do today?\n")
    for idx, choice in enumerate(DAILY_CHOICES, 1):
        print(f"{idx}. {choice['label']}")

    while True:
        try:
            selection = int(input("\nChoose (1–7): "))
            if 1 <= selection <= len(DAILY_CHOICES):
                selected = DAILY_CHOICES[selection - 1]
                print(f"\n✅ You chose to: {selected['label']}")
                if selected["id"] == "interact":
                    list_nearby_npcs(player)
                elif selected["id"] == "move_city":
                    move_to_new_city(player)
                else:
                    log_player_action(player, selected["id"], selected["label"])

                # Apply stat boosts
                for idx, amt in ACTION_STAT_EFFECTS.get(selected["id"], []):
                        old_val = int(player[7][idx:idx+2])
                        player[7] = modify_stat(player[7], idx, amt)
                        new_val = int(player[7][idx:idx+2])
                        stat_name = STAT_NAMES.get(idx, f"Stat@{idx}")
                        print(f"📈 {stat_name} increased from {old_val} to {new_val}.")

                save_json(PLAYER_PATH, player)
                break
        except ValueError:
            pass
        print("❌ Invalid choice. Try again.")


def main():
    if not os.path.exists(PLAYER_PATH):
        player = create_player()
    else:
        player = getPlayer()
        current_tick = load_json(TIME_PATH)["tick"] + 1
        if (current_tick - player[4]) % 365 == 0:
            print("🎂 It's your birthday!")
            player[2] += 1
            save_json(PLAYER_PATH, player)

    advance_time()
    display_player_location(player)
    player_daily_choice(player)
    char_to_char()
    simulate_day()



if __name__ == "__main__":
    while(True):
        main()
