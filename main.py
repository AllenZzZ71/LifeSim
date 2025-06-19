#!/usr/bin/env python3
"""
🌟 Life Simulation Game - Enhanced Edition
A text-based life simulation with NPCs, combat, and world progression.
"""

import os
import json
import random
from datetime import datetime
from time import sleep
from typing import Dict, List, Tuple, Optional, Any

# === CONFIGURATION ===
class Config:
    CHARACTER_PATH = "./chars"
    TIME_PATH = "./world/time.json"
    WORLD_DIR = "./world/events"
    PLAYER_PATH = "./player/player.json"
    BODY_PATH = "./body"
    CITY_PATH = "./world/worldmap/cities"
    
    TICK_RATE = 30  # Days per tick
    BASE_DAMAGE = 10
    BASE_COOLDOWN = 20

# === AESTHETIC CONSTANTS ===
class Icons:
    PLAYER = "👤"
    LOCATION = "📍"
    POPULATION = "👥"
    TIME = "🕐"
    FIGHT = "⚔️"
    TRAIN = "🏋️"
    MOVE = "🚶"
    INTERACT = "💬"
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    STATS = "📊"
    CONFIDENCE = "🧠"
    DAMAGE = "💢"
    CRITICAL = "🔥"
    MISS = "❌"
    BLOCK = "🛡️"
    STAMINA = "🔋"
    COOLDOWN = "⏱️"
    BIRTHDAY = "🎂"
    WORLD_TICK = "🌍"

# === UTILITY FUNCTIONS ===
def print_header(text: str, icon: str = "🌟") -> None:
    """Print a formatted header with decorative borders."""
    border = "═" * (len(text) + 4)
    print(f"\n╔{border}╗")
    print(f"║ {icon} {text} {icon} ║")
    print(f"╚{border}╝")

def print_section(title: str, icon: str = "📋") -> None:
    """Print a section divider."""
    print(f"\n{icon} {title}")
    print("─" * (len(title) + 3))

def load_json(path: str, fallback: Any = None) -> Dict[str, Any]:
    """Load JSON with comprehensive error handling."""
    if not os.path.exists(path):
        print(f"{Icons.ERROR} File not found: {path}")
        return fallback or {}

    try:
        with open(path, 'r', encoding='utf-8-sig') as f:
            content = f.read().strip()
            if not content:
                print(f"{Icons.WARNING} Empty JSON file: {path}")
                return fallback or {}
            return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"{Icons.WARNING} JSON decode error in {path}: {e}")
        return fallback or {}
    except IOError as e:
        print(f"{Icons.WARNING} IO error reading {path}: {e}")
        return fallback or {}

def save_json(path: str, data: Any) -> None:
    """Save JSON with directory creation."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def create_progress_bar(value: int, max_value: int, width: int = 20) -> str:
    """Create a visual progress bar."""
    filled = int(width * value / max_value) if max_value > 0 else 0
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {value}/{max_value}"

# === TIME MANAGEMENT ===
class TimeManager:
    @staticmethod
    def initialize_time() -> Dict[str, int]:
        """Initialize world time with current date."""
        now = datetime.now()
        time_data = {
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "tick": 0
        }
        save_json(Config.TIME_PATH, time_data)
        return time_data

    @staticmethod
    def advance_time() -> None:
        """Advance world time by one tick."""
        time_data = load_json(Config.TIME_PATH) or TimeManager.initialize_time()
        time_data["tick"] += Config.TICK_RATE
        time_data["day"] += Config.TICK_RATE

        # Handle month/year rollover
        if time_data["day"] > 30:
            time_data["day"] = 1
            time_data["month"] += 1
        if time_data["month"] > 12:
            time_data["month"] = 1
            time_data["year"] += 1

        save_json(Config.TIME_PATH, time_data)
        print(f"{Icons.WORLD_TICK} [World Tick {time_data['tick']}] "
              f"Date: {time_data['year']}-{time_data['month']:02d}-{time_data['day']:02d}")

    @staticmethod
    def get_current_time() -> Dict[str, int]:
        """Get current world time."""
        return load_json(Config.TIME_PATH) or TimeManager.initialize_time()

# === STAT MANAGEMENT ===
class StatManager:
    STAT_NAMES = {
        0: "Strength", 2: "Endurance", 4: "Accuracy", 6: "Speed", 8: "Experience",
        10: "Reflex", 12: "Toughness", 14: "Focus", 16: "Stamina", 18: "Willpower"
    }
    
    PERSONALITY_NAMES = {
        0: "Empathy", 2: "Assertiveness", 4: "Discipline", 6: "Intelligence",
        8: "Charisma", 10: "Creativity", 12: "Social", 14: "Luck", 16: "Wisdom", 18: "Patience"
    }

    @staticmethod
    def modify_stat(stat_string: str, index: int, amount: int) -> str:
        """Modify a stat value within bounds (0-99)."""
        current = int(stat_string[index:index+2])
        updated = max(0, min(99, current + amount))
        return stat_string[:index] + f"{updated:02d}" + stat_string[index+2:]

    @staticmethod
    def get_stat_block(stats_str: str) -> List[int]:
        """Convert stat string to list of integers."""
        return [int(stats_str[i:i+2]) for i in range(0, len(stats_str), 2)]

    @staticmethod
    def display_stats(stats_str: str, stat_type: str = "Combat") -> None:
        """Display stats in a formatted table."""
        stats = StatManager.get_stat_block(stats_str)
        names = StatManager.STAT_NAMES if stat_type == "Combat" else StatManager.PERSONALITY_NAMES
        
        print_section(f"{stat_type} Stats", Icons.STATS)
        for i, (index, name) in enumerate(names.items()):
            if i < len(stats):
                bar = create_progress_bar(stats[i], 99, 15)
                print(f"  {name:<12}: {bar}")

# === CHARACTER MANAGEMENT ===
class CharacterManager:
    @staticmethod
    def get_all_characters() -> List[str]:
        """Get all character IDs from the character directory."""
        if not os.path.exists(Config.CHARACTER_PATH):
            return []
        files = os.listdir(Config.CHARACTER_PATH)
        return [f[:-5] for f in files if f.endswith(".json")]

    @staticmethod
    def get_character_data(char_id: str) -> Optional[List[Any]]:
        """Load character data by ID."""
        path = os.path.join(Config.CHARACTER_PATH, f"{char_id}.json")
        return load_json(path)

    @staticmethod
    def calculate_age(current_tick: int, birth_tick: int) -> int:
        """Calculate character age based on ticks."""
        return max(0, (current_tick - birth_tick) // 365)

# === WORLD MANAGEMENT ===
class WorldManager:
    @staticmethod
    def get_city_info(city_id: str) -> Dict[str, Any]:
        """Get city information by ID."""
        city_path = os.path.join(Config.CITY_PATH, f"{city_id}.json")
        city_data = load_json(city_path)
        return {
            "name": city_data.get("name", "Unknown City"),
            "country": city_data.get("country", "Unknown Country"),
            "id": city_id
        }

    @staticmethod
    def count_population_in_city(city_id: str) -> int:
        """Count NPCs in a specific city."""
        count = 0
        for char_id in CharacterManager.get_all_characters():
            char_data = CharacterManager.get_character_data(char_id)
            if char_data and len(char_data) > 10 and char_data[10] == city_id:
                count += 1
        return count

    @staticmethod
    def get_all_cities() -> List[Dict[str, Any]]:
        """Get all available cities with population data."""
        cities = []
        if not os.path.exists(Config.CITY_PATH):
            return cities
            
        for fname in os.listdir(Config.CITY_PATH):
            if fname.endswith(".json"):
                city_data = load_json(os.path.join(Config.CITY_PATH, fname))
                if city_data and "id" in city_data and "name" in city_data:
                    city_info = {
                        "id": city_data["id"],
                        "name": city_data["name"],
                        "country": city_data.get("country", "Unknown"),
                        "population": WorldManager.count_population_in_city(city_data["id"])
                    }
                    cities.append(city_info)
        return cities

# === COMBAT SYSTEM ===
class CombatSystem:
    BODY_ZONES = ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"]
    ZONE_MULTIPLIERS = {
        "head": 1.5, "torso": 1.0, "left_arm": 0.8,
        "right_arm": 0.8, "left_leg": 0.9, "right_leg": 0.9
    }

    @staticmethod
    def initialize_body(char_id: str) -> Dict[str, Any]:
        """Initialize body status for a character."""
        body_data = {
            "body": {zone: {"health": 100} for zone in CombatSystem.BODY_ZONES}
        }
        body_path = os.path.join(Config.BODY_PATH, f"{char_id}.json")
        save_json(body_path, body_data)
        return body_data["body"]

    @staticmethod
    def load_body(char_id: str) -> Dict[str, Any]:
        """Load character body status."""
        body_path = os.path.join(Config.BODY_PATH, f"{char_id}.json")
        body_data = load_json(body_path)
        if not body_data or "body" not in body_data:
            return CombatSystem.initialize_body(char_id)
        return body_data["body"]

    @staticmethod
    def save_body(char_id: str, body: Dict[str, Any]) -> None:
        """Save character body status."""
        body_path = os.path.join(Config.BODY_PATH, f"{char_id}.json")
        save_json(body_path, {"body": body})

    @staticmethod
    def display_body_status(name: str, body: Dict[str, Any]) -> None:
        """Display formatted body status."""
        print_section(f"{name}'s Body Status", Icons.STATS)
        for zone in CombatSystem.BODY_ZONES:
            hp = body[zone]["health"]
            bar = create_progress_bar(hp, 100, 12)
            status = "🔴" if hp < 20 else "🟡" if hp < 50 else "🟢"
            print(f"  {status} {zone.replace('_', ' ').title():<12}: {bar}")

# === PLAYER MANAGEMENT ===
class Player:
    def __init__(self):
        self.data = self.load_or_create()

    def load_or_create(self) -> List[Any]:
        """Load existing player or create new one."""
        if os.path.exists(Config.PLAYER_PATH):
            return load_json(Config.PLAYER_PATH, [])
        return self.create_new_player()

    def create_new_player(self) -> List[Any]:
        """Create a new player character."""
        print_header("Character Creation", Icons.PLAYER)
        
        name = input(f"{Icons.PLAYER} Enter your character's name: ").strip()
        while not name:
            name = input(f"{Icons.ERROR} Name cannot be empty. Try again: ").strip()

        print(f"\n{Icons.PLAYER} Choose your gender:")
        print("1. Male")
        print("2. Female") 
        print("3. Other")
        
        while True:
            try:
                gender_choice = int(input("Choice (1-3): "))
                if 1 <= gender_choice <= 3:
                    gender = gender_choice - 1
                    break
            except ValueError:
                pass
            print(f"{Icons.ERROR} Invalid choice. Please enter 1, 2, or 3.")

        current_time = TimeManager.get_current_time()
        
        # Generate random starting location
        cities = WorldManager.get_all_cities()
        starting_city = random.choice(cities)["id"] if cities else "city_001"
        
        player_data = [
            "player_001",  # ID
            name,          # Name
            18,            # Age
            gender,        # Gender
            current_time["tick"],  # Birth tick
            0,             # Experience
            ["beginner", "curious"],  # Traits
            "50505050505050505050",   # Personality stats
            "20202020202020202020",   # Combat stats  
            {},            # Inventory
            starting_city  # Location
        ]

        os.makedirs(os.path.dirname(Config.PLAYER_PATH), exist_ok=True)
        save_json(Config.PLAYER_PATH, player_data)
        
        # Initialize body
        CombatSystem.initialize_body("player_001")
        
        print_header(f"Welcome to the world, {name}!", Icons.SUCCESS)
        return player_data

    def save(self) -> None:
        """Save player data."""
        save_json(Config.PLAYER_PATH, self.data)

    def display_location(self) -> None:
        """Display player's current location with population."""
        location_id = self.data[10] if len(self.data) > 10 else "unknown"
        city_info = WorldManager.get_city_info(location_id)
        population = WorldManager.count_population_in_city(location_id)
        
        print_section("Current Location", Icons.LOCATION)
        print(f"  {Icons.LOCATION} City: {city_info['name']}, {city_info['country']}")
        print(f"  {Icons.POPULATION} Population: {population}")

    def get_nearby_npcs(self) -> List[Tuple[str, List[Any]]]:
        """Get list of NPCs in the same location."""
        player_location = self.data[10]
        nearby_npcs = []

        for char_id in CharacterManager.get_all_characters():
            char_data = CharacterManager.get_character_data(char_id)
            if char_data and len(char_data) > 10 and char_data[10] == player_location:
                nearby_npcs.append((char_id, char_data))

        return nearby_npcs

    def interact_with_npcs(self) -> None:
        """Handle NPC interaction interface."""
        nearby_npcs = self.get_nearby_npcs()
        
        if not nearby_npcs:
            print(f"\n{Icons.WARNING} No one is around to interact with today.")
            return

        print_section("People Nearby", Icons.POPULATION)
        for i, (char_id, npc) in enumerate(nearby_npcs, 1):
            name = npc[1]
            stats = StatManager.get_stat_block(npc[8])
            print(f"  {i}. {name} (Speed: {stats[3]}, Strength: {stats[0]}) [{npc[0]}]")

        while True:
            try:
                choice = int(input(f"\n{Icons.INTERACT} Who do you want to approach? (1-{len(nearby_npcs)}): "))
                if 1 <= choice <= len(nearby_npcs):
                    chosen_id, chosen_data = nearby_npcs[choice - 1]
                    self.handle_npc_interaction(chosen_data)
                    break
            except ValueError:
                pass
            print(f"{Icons.ERROR} Invalid input. Try again.")

    def handle_npc_interaction(self, npc_data: List[Any]) -> None:
        """Handle specific NPC interaction."""
        name = npc_data[1]
        print(f"\n{Icons.INTERACT} You approach {name}. What do you want to do?")
        print("1. Chat")
        print("2. Pick a Fight")

        while True:
            try:
                choice = int(input("Choose (1 or 2): "))
                if choice == 1:
                    print(f"\n{Icons.SUCCESS} You greeted {name}. They smiled back.")
                    self.log_action("interact_npc", f"Chatted with {name}")
                    break
                elif choice == 2:
                    print(f"\n{Icons.FIGHT} You challenged {name} to a fight!")
                    combat = CombatEngine(self.data, npc_data)
                    combat.start_fight()
                    break
            except ValueError:
                pass
            print(f"{Icons.ERROR} Invalid choice.")

    def log_action(self, action_id: str, action_label: str) -> None:
        """Log player action."""
        log_path = "./player/event/log.json"
        logs = load_json(log_path, [])
        
        current_time = TimeManager.get_current_time()
        logs.append({
            "tick": current_time["tick"],
            "name": self.data[1],
            "action_id": action_id,
            "action": action_label,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        save_json(log_path, logs)

# === ADVANCED COMBAT ENGINE ===
class CombatEngine:
    def __init__(self, player_data: List[Any], npc_data: List[Any]):
        self.player = player_data
        self.npc = npc_data
        self.player_body = CombatSystem.load_body(player_data[0])
        self.npc_body = CombatSystem.load_body(npc_data[0])
        
        # Combat stats
        self.p_stats = StatManager.get_stat_block(player_data[8])
        self.n_stats = StatManager.get_stat_block(npc_data[8])
        
        # Initialize combat state
        self.turn = 0
        self.cooldown_p = 0
        self.cooldown_n = 0
        
        # Calculate max stamina
        self.max_stamina_p = 10 + self.p_stats[8] * 5  # Based on stamina stat
        self.max_stamina_n = 10 + self.n_stats[8] * 5
        self.curr_stamina_p = self.max_stamina_p
        self.curr_stamina_n = self.max_stamina_n
        
        # Calculate cooldown costs
        self.cooldown_cost_p = self.calc_cooldown(Config.BASE_COOLDOWN, self.p_stats[3])
        self.cooldown_cost_n = self.calc_cooldown(Config.BASE_COOLDOWN, self.n_stats[3])
        
        # Initialize confidence system
        self.player_conf, self.npc_conf = self.calculate_starting_confidence()
        self.player_dynamic = self.init_dynamic_state(self.player_conf)
        self.npc_dynamic = self.init_dynamic_state(self.npc_conf)

    def calc_cooldown(self, base: int, speed: int) -> int:
        """Calculate cooldown based on speed stat."""
        return max(10, int(base - speed * 0.5))

    def calc_damage(self, base: int, strength: int, multiplier: float = 1.0) -> int:
        """Calculate base damage."""
        return int((base + strength * 0.5) * multiplier)

    def calc_random_damage(self, base_dmg: int, strength: int, multiplier: float, exp: int) -> int:
        """Calculate damage with experience-based consistency."""
        raw = self.calc_damage(base_dmg, strength, multiplier)
        consistency = 0.5 + (exp / 200)  # Between 0.5 and 1.0
        low = int(raw * consistency)
        return random.randint(low, raw)

    def calculate_starting_confidence(self) -> Tuple[int, int]:
        """Calculate starting confidence based on stats comparison."""
        player_power = sum(self.p_stats[:8])  # First 8 combat stats
        npc_power = sum(self.n_stats[:8])
        
        advantage = player_power - npc_power
        player_will = self.p_stats[9]  # Willpower
        npc_will = self.n_stats[9]
        
        player_conf = max(0, min(100, 50 + (advantage // 5) + player_will))
        npc_conf = max(0, min(100, 50 - (advantage // 5) + npc_will))
        
        return player_conf, npc_conf

    def init_dynamic_state(self, confidence: int) -> Dict[str, Any]:
        """Initialize dynamic combat state."""
        state = {
            "confidence": confidence,
            "slip_chance": 0,
            "crit_bonus": 0,
            "acc_bonus": 0,
            "dmg_multiplier": 1.0,
            "skip_turn_chance": 0,
            "stamina_penalty": False,
        }
        self.apply_confidence_penalties(state)
        return state

    def apply_confidence_penalties(self, dynamic: Dict[str, Any]) -> None:
        """Apply confidence-based modifiers."""
        conf = dynamic["confidence"]
        
        if conf >= 80:
            # Adrenaline Rush
            dynamic["crit_bonus"] = 5
            dynamic["acc_bonus"] = 5
            dynamic["dmg_multiplier"] = 1.1
            dynamic["slip_chance"] = 0
            dynamic["skip_turn_chance"] = 0
            dynamic["stamina_penalty"] = False
        elif 50 <= conf < 80:
            # Normal
            dynamic["crit_bonus"] = 0
            dynamic["acc_bonus"] = 0
            dynamic["dmg_multiplier"] = 1.0
            dynamic["slip_chance"] = 0
            dynamic["skip_turn_chance"] = 0
            dynamic["stamina_penalty"] = False
        elif 20 <= conf < 50:
            # Shaky
            dynamic["crit_bonus"] = 0
            dynamic["acc_bonus"] = -10
            dynamic["dmg_multiplier"] = 1.0
            dynamic["slip_chance"] = 0
            dynamic["skip_turn_chance"] = 0
            dynamic["stamina_penalty"] = False
        else:
            # Panicked
            dynamic["crit_bonus"] = 0
            dynamic["acc_bonus"] = -15
            dynamic["dmg_multiplier"] = 0.75
            dynamic["slip_chance"] = 10
            dynamic["skip_turn_chance"] = 10
            dynamic["stamina_penalty"] = True

    def update_confidence(self, dynamic: Dict[str, Any], amount: int, reason: str, name: str) -> None:
        """Update confidence and apply new penalties."""
        before = dynamic["confidence"]
        dynamic["confidence"] = max(0, min(100, before + amount))
        after = dynamic["confidence"]
        
        icon = "📈" if amount > 0 else "📉"
        print(f"{icon} {name}'s confidence: {before} → {after} — {reason}")
        self.apply_confidence_penalties(dynamic)

    def print_confidence_bar(self, dynamic: Dict[str, Any], name: str) -> None:
        """Display confidence as a visual bar."""
        val = dynamic["confidence"]
        bar = create_progress_bar(val, 100, 15)
        status = "💪" if val >= 80 else "😐" if val >= 50 else "😰" if val >= 20 else "😱"
        print(f"{Icons.CONFIDENCE} {name}'s Confidence: {status} {bar}")

    def apply_body_penalties(self, base_stats: List[int], body: Dict[str, Any], name: str) -> List[int]:
        """Apply injury penalties to stats."""
        stats = base_stats.copy()
        
        if body["head"]["health"] < 20:
            stats[2] = int(stats[2] * (body["head"]["health"] / 100))  # Accuracy
            print(f"{name} {Icons.WARNING} Head trauma: Coordination impaired")
        if body["torso"]["health"] < 20:
            stats[1] = int(stats[1] * (body["torso"]["health"] / 100))  # Endurance
            print(f"{name} {Icons.WARNING} Torso injury: Breathing impaired")
        if body["left_leg"]["health"] < 20 or body["right_leg"]["health"] < 20:
            stats[3] = int(stats[3] * 0.7)  # Speed
            print(f"{name} {Icons.WARNING} Leg injury: Movement slowed")
        if body["left_arm"]["health"] < 20 or body["right_arm"]["health"] < 20:
            stats[0] = int(stats[0] * 0.8)  # Strength
            print(f"{name} {Icons.WARNING} Arm injury: Attack weakened")
        
        # Enforce minimum values
        return [max(1, stat) for stat in stats]

    def start_fight(self) -> None:
        """Initialize and start the combat sequence."""
        print_header(f"Combat: {self.player[1]} vs {self.npc[1]}", Icons.FIGHT)
        
        # Display initial stats
        self.display_fighter_stats(self.player[1], self.p_stats)
        self.display_fighter_stats(self.npc[1], self.n_stats)
        
        input(f"\n{Icons.FIGHT} Press Enter to begin combat...")
        self.combat_loop()

    def display_fighter_stats(self, name: str, stats: List[int]) -> None:
        """Display fighter statistics."""
        print_section(f"{name}'s Combat Stats", Icons.STATS)
        stat_names = ["Strength", "Endurance", "Accuracy", "Speed", "Experience", 
                     "Reflex", "Toughness", "Focus", "Stamina", "Willpower"]
        
        for i, (stat_name, value) in enumerate(zip(stat_names, stats)):
            bar = create_progress_bar(value, 99, 10)
            print(f"  {stat_name:<12}: {bar}")

    def combat_loop(self) -> None:
        """Advanced combat loop with all original mechanics."""
        while True:
            self.turn += 1
            print_header(f"Round {self.turn}", Icons.FIGHT)
            
            # Recover stamina based on endurance
            recovery_p = 1 + (self.p_stats[1] * 0.5)
            recovery_n = 1 + (self.n_stats[1] * 0.5)
            self.curr_stamina_p = min(self.max_stamina_p, self.curr_stamina_p + recovery_p)
            self.curr_stamina_n = min(self.max_stamina_n, self.curr_stamina_n + recovery_n)
            
            # Update cooldowns
            self.cooldown_p = max(0, self.cooldown_p - self.cooldown_cost_p)
            self.cooldown_n = max(0, self.cooldown_n - self.cooldown_cost_n)
            
            # Display status
            self.display_combat_status()
            
            # Check defeat conditions
            if self.check_defeat(self.player_body):
                print(f"\n{Icons.ERROR} {self.player[1]} has been defeated!")
                break
            elif self.check_defeat(self.npc_body):
                print(f"\n{Icons.SUCCESS} {self.npc[1]} has been defeated!")
                break
            
            # Determine turn order based on cooldowns
            if self.cooldown_p <= self.cooldown_n:
                if self.cooldown_p > 0:
                    print(f"⏳ {self.player[1]}'s turn skipped — recovering...")
                    continue
                self.player_turn()
            else:
                if self.cooldown_n > 0:
                    print(f"⏳ {self.npc[1]}'s turn skipped — recovering...")
                    continue
                self.npc_turn()
            
            sleep(1)

        # Save body states
        CombatSystem.save_body(self.player[0], self.player_body)
        CombatSystem.save_body(self.npc[0], self.npc_body)

    def display_combat_status(self) -> None:
        """Display comprehensive combat status."""
        print(f"\n{Icons.COOLDOWN} Cooldowns:")
        print(f"  {self.player[1]}: {self.cooldown_p}")
        print(f"  {self.npc[1]}: {self.cooldown_n}")
        
        print(f"\n{Icons.STAMINA} Stamina:")
        p_stamina_bar = create_progress_bar(int(self.curr_stamina_p), self.max_stamina_p, 12)
        n_stamina_bar = create_progress_bar(int(self.curr_stamina_n), self.max_stamina_n, 12)
        print(f"  {self.player[1]}: {p_stamina_bar}")
        print(f"  {self.npc[1]}: {n_stamina_bar}")
        
        # Display confidence
        self.print_confidence_bar(self.player_dynamic, self.player[1])
        self.print_confidence_bar(self.npc_dynamic, self.npc[1])
        
        # Display body status
        CombatSystem.display_body_status(self.player[1], self.player_body)
        CombatSystem.display_body_status(self.npc[1], self.npc_body)

    def player_turn(self) -> None:
        """Handle player combat turn with full mechanics."""
        print(f"\n{Icons.PLAYER} {self.player[1]}'s turn!")
        
        # Check for panic/skip turn
        if random.randint(1, 100) <= self.player_dynamic["skip_turn_chance"]:
            print(f"😱 {self.player[1]} is too panicked to act!")
            self.cooldown_p += 200
            return
        
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
            print(f"{Icons.ERROR} Invalid input.")
        
        # Attack zone choice
        print("\n🎯 Choose body part to target:")
        for i, zone in enumerate(CombatSystem.BODY_ZONES, 1):
            print(f"{i}. {zone.replace('_', ' ').title()}")
        
        while True:
            try:
                zone_choice = int(input("Attack zone (1–6): "))
                if 1 <= zone_choice <= 6:
                    target_zone = CombatSystem.BODY_ZONES[zone_choice - 1]
                    break
            except ValueError:
                pass
            print(f"{Icons.ERROR} Invalid input.")
        
        # Prediction system
        likely_zone = random.choices(
            CombatSystem.BODY_ZONES,
            weights=[25, 30, 10, 10, 12.5, 12.5]
        )[0]
        est_chance = random.randint(30, 60)
        print(f"\n🧠 Prediction: Enemy likely to strike your **{likely_zone}** ({est_chance}% chance)")
        
        predicted_zone = input("🛡️ Choose zone to block: ").lower().strip()
        if predicted_zone not in CombatSystem.BODY_ZONES:
            predicted_zone = random.choice(CombatSystem.BODY_ZONES)
        
        # Execute attack
        self.execute_advanced_attack(atk_type, target_zone, predicted_zone, True)

    def npc_turn(self) -> None:
        """Handle NPC combat turn with AI."""
        print(f"\n{Icons.FIGHT} {self.npc[1]}'s turn!")
        
        # Check for panic/skip turn
        if random.randint(1, 100) <= self.npc_dynamic["skip_turn_chance"]:
            print(f"😱 {self.npc[1]} is too panicked to act!")
            self.cooldown_n += 200
            return
        
        # Simple AI decision making
        atk_type = random.choice([1, 2])
        target_zone = random.choices(
            CombatSystem.BODY_ZONES,
            weights=[15, 30, 10, 10, 17.5, 17.5]
        )[0]
        predicted_zone = random.choice(CombatSystem.BODY_ZONES)
        
        # Execute attack
        self.execute_advanced_attack(atk_type, target_zone, predicted_zone, False)

    def execute_advanced_attack(self, atk_type: int, target_zone: str, predicted_zone: str, is_player: bool) -> None:
        """Execute attack with full original mechanics."""
        if is_player:
            attacker, defender = self.player, self.npc
            attacker_stats = self.apply_body_penalties(self.p_stats, self.player_body, self.player[1])
            attacker_dynamic = self.player_dynamic
            defender_dynamic = self.npc_dynamic
            defender_body = self.npc_body
            attacker_name, defender_name = self.player[1], self.npc[1]
        else:
            attacker, defender = self.npc, self.player
            attacker_stats = self.apply_body_penalties(self.n_stats, self.npc_body, self.npc[1])
            attacker_dynamic = self.npc_dynamic
            defender_dynamic = self.player_dynamic
            defender_body = self.player_body
            attacker_name, defender_name = self.npc[1], self.player[1]
        
        # Attack parameters
        acc_bonus = 20 if atk_type == 1 else 5
        dmg_multiplier = 1.0 if atk_type == 1 else 1.5
        stamina_cost = 10 if atk_type == 1 else 15
        
        # Apply stamina cost
        if is_player:
            self.curr_stamina_p -= stamina_cost
            if self.curr_stamina_p <= 0:
                self.update_confidence(self.player_dynamic, -3, "Exhausted", attacker_name)
                dmg_multiplier *= 0.5
        else:
            self.curr_stamina_n -= stamina_cost
            if self.curr_stamina_n <= 0:
                self.update_confidence(self.npc_dynamic, -3, "Exhausted", attacker_name)
                dmg_multiplier *= 0.5
        
        # Accuracy calculation
        base_accuracy = acc_bonus + attacker_stats[4] + attacker_stats[2]  # Experience + Accuracy
        base_accuracy += attacker_dynamic["acc_bonus"]
        base_accuracy = max(5, min(95, base_accuracy))
        
        # Prediction check
        is_predicted = (predicted_zone == target_zone and random.randint(0, 100) < 70)
        
        # Hit roll
        hit_roll = random.randint(1, 100)
        
        if hit_roll > base_accuracy:
            print(f"{Icons.MISS} {attacker_name} missed the attack! ({hit_roll} > {base_accuracy})")
            self.update_confidence(attacker_dynamic, -10, "Attack missed", attacker_name)
            if is_player:
                self.cooldown_p += 200
            else:
                self.cooldown_n += 200
            return
        
        # Calculate damage
        base_damage = Config.BASE_DAMAGE
        strength = attacker_stats[0]
        experience = attacker_stats[4]
        
        # Apply dynamic modifiers
        dmg_multiplier *= attacker_dynamic["dmg_multiplier"]
        
        # Critical hit check
        crit_chance = min(30, 5 + (attacker_stats[2] // 4) + (experience // 10))
        crit_chance += attacker_dynamic["crit_bonus"]
        is_crit = random.randint(1, 100) <= crit_chance
        
        if is_crit:
            print(f"{Icons.CRITICAL} CRITICAL HIT! {attacker_name}'s attack strikes hard!")
            dmg_multiplier *= 1.75
        
        damage = self.calc_random_damage(base_damage, strength, dmg_multiplier, experience)
        
        # Apply zone multiplier
        final_damage = int(damage * CombatSystem.ZONE_MULTIPLIERS[target_zone])
        
        # Handle parry
        if is_predicted:
            print(f"{Icons.BLOCK} {defender_name} predicted the strike and **PARRIED**!")
            final_damage = int(final_damage * 0.5)
            self.update_confidence(defender_dynamic, +5, "Successful parry", defender_name)
        
        # Apply damage
        defender_body[target_zone]["health"] -= final_damage
        defender_body[target_zone]["health"] = max(0, defender_body[target_zone]["health"])
        
        attack_name = "Punch" if atk_type == 1 else "Kick"
        print(f"{Icons.DAMAGE} {attacker_name} lands a {attack_name} on {defender_name}'s {target_zone}!")
        print(f"{Icons.CRITICAL} Damage dealt: {final_damage}")
        
        # Update confidence
        self.update_confidence(attacker_dynamic, +7, "Landed a solid hit", attacker_name)
        self.update_confidence(defender_dynamic, -10, "Took damage", defender_name)
        
        # Set cooldown
        if is_player:
            self.cooldown_p += 200
        else:
            self.cooldown_n += 200

    def check_defeat(self, body: Dict[str, Any]) -> bool:
        """Check if character is defeated."""
        return body["head"]["health"] <= 0 or body["torso"]["health"] <= 0

# === TRAINING SYSTEM ===
class TrainingSystem:
    TRAINING_OPTIONS = [
        ("Shadowboxing", "Reflex", 5, 1),
        ("Heavy Bag", "Strength", 0, 2),
        ("Sprint Drills", "Speed", 3, 1),
        ("Focus Training", "Accuracy", 2, 1),
        ("Sparring", "Experience", 4, 2),
        ("Pain Tolerance", "Toughness", 6, 1),
        ("Zen Breathing", "Focus", 7, 1),
        ("Marathon Runs", "Stamina", 8, 2),
        ("Circuit Training", "Endurance", 1, 2),
        ("Mental Conditioning", "Willpower", 9, 1)
    ]

    @staticmethod
    def train_player(player: Player) -> None:
        """Handle player training interface."""
        print_header("Training Center", Icons.TRAIN)
        print("Choose your training type:")
        
        for i, (name, stat_name, _, _) in enumerate(TrainingSystem.TRAINING_OPTIONS, 1):
            print(f"{i:2d}. {name:<20} — Improves {stat_name}")

        while True:
            try:
                choice = int(input(f"\nSelect training (1-{len(TrainingSystem.TRAINING_OPTIONS)}): "))
                if 1 <= choice <= len(TrainingSystem.TRAINING_OPTIONS):
                    training_name, stat_label, stat_index, max_gain = TrainingSystem.TRAINING_OPTIONS[choice - 1]
                    TrainingSystem.execute_training(player, training_name, stat_label, stat_index, max_gain)
                    break
            except ValueError:
                pass
            print(f"{Icons.ERROR} Invalid choice.")

    @staticmethod
    def execute_training(player: Player, training_name: str, stat_label: str, 
                        stat_index: int, max_gain: int) -> None:
        """Execute the training and update stats."""
        stats = StatManager.get_stat_block(player.data[8])
        
        gain = random.randint(1, max_gain)
        old_val = stats[stat_index]
        stats[stat_index] = min(99, stats[stat_index] + gain)
        
        # Update player data
        player.data[8] = ''.join(f"{x:02d}" for x in stats)
        player.save()
        
        print(f"\n{Icons.SUCCESS} Training Complete!")
        print(f"{Icons.TRAIN} You trained **{training_name}** and gained **+{gain} {stat_label}**!")
        print(f"{Icons.STATS} {stat_label}: {old_val} → {stats[stat_index]}")
        
        # Advance time
        TimeManager.advance_time()

# === SIMULATION SYSTEM ===
class SimulationSystem:
    @staticmethod
    def simulate_world() -> None:
        """Simulate world events and NPC activities."""
        print_section("World Simulation", Icons.WORLD_TICK)
        
        characters = CharacterManager.get_all_characters()
        events_generated = 0
        
        for char_id in characters:
            char_data = CharacterManager.get_character_data(char_id)
            if not char_data:
                continue
                
            # Generate personality-based actions
            personality = StatManager.get_stat_block(char_data[6])
            empathy = personality[0] if len(personality) > 0 else 50
            assertiveness = personality[1] if len(personality) > 1 else 50
            
            actions = []
            if empathy > 60:
                actions.extend(["volunteered at local shelter", "helped an elderly neighbor"])
            if assertiveness > 60:
                actions.extend(["stood up for someone", "organized a community event"])
            if empathy < 30:
                actions.append("ignored someone in need")
            
            if not actions:
                actions = ["went about their day quietly", "spent time at home"]
            
            action = random.choice(actions)
            SimulationSystem.log_npc_event(char_id, char_data[1], action)
            events_generated += 1
        
        print(f"{Icons.SUCCESS} Generated {events_generated} world events")

    @staticmethod
    def log_npc_event(char_id: str, char_name: str, action: str) -> None:
        """Log an NPC event to their summary file."""
        summary_path = os.path.join(Config.WORLD_DIR, char_id, "summaries.json")
        summaries = load_json(summary_path, {"events": []})
        
        current_time = TimeManager.get_current_time()
        summaries["events"].append({
            "tick": current_time["tick"],
            "action": action,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        save_json(summary_path, summaries)

# === MAIN GAME LOOP ===
class GameEngine:
    def __init__(self):
        self.player = Player()
        self.running = True

    def display_daily_menu(self) -> None:
        """Display the daily action menu."""
        print_header("Daily Activities", Icons.TIME)
        print("What would you like to do today?")
        print()
        print("1. 💬 Socialize with someone nearby")
        print("2. 📚 Study and learn something new") 
        print("3. 🏃 Exercise and stay fit")
        print("4. 😴 Relax and recharge")
        print("5. 🗺️  Explore your surroundings")
        print("6. 👋 Interact with locals")
        print("7. 🚶 Move to a different city")
        print("8. 🏋️  Physical training")
        print("9. 📊 Check your stats")
        print("0. 🚪 Quit game")

    def handle_daily_choice(self) -> bool:
        """Handle player's daily choice. Returns False if player wants to quit."""
        self.display_daily_menu()
        
        while True:
            try:
                choice = int(input(f"\n{Icons.PLAYER} Choose your action (0-9): "))
                
                if choice == 0:
                    print(f"\n{Icons.SUCCESS} Thanks for playing! Goodbye!")
                    return False
                    
                elif choice == 1:  # Socialize
                    self.socialize_action()
                    
                elif choice == 2:  # Study
                    self.study_action()
                    
                elif choice == 3:  # Exercise
                    self.exercise_action()
                    
                elif choice == 4:  # Relax
                    self.relax_action()
                    
                elif choice == 5:  # Explore
                    self.explore_action()
                    
                elif choice == 6:  # Interact
                    self.player.interact_with_npcs()
                    
                elif choice == 7:  # Move city
                    self.move_city_action()
                    
                elif choice == 8:  # Training
                    TrainingSystem.train_player(self.player)
                    
                elif choice == 9:  # Check stats
                    self.display_player_stats()
                    continue  # Don't advance time for checking stats
                    
                else:
                    print(f"{Icons.ERROR} Invalid choice. Please choose 0-9.")
                    continue
                
                # Advance time and simulate world (except for stats check)
                if choice != 9:
                    TimeManager.advance_time()
                    SimulationSystem.simulate_world()
                    
                return True
                
            except ValueError:
                print(f"{Icons.ERROR} Please enter a number between 0-9.")

    def socialize_action(self) -> None:
        """Handle socializing action."""
        print(f"\n{Icons.INTERACT} You spent the day socializing with people in your area.")
        self.improve_stat(6, 1, "Social skills")  # Improve social stat
        self.player.log_action("socialize", "Socialized with locals")

    def study_action(self) -> None:
        """Handle studying action."""
        subjects = ["history", "science", "literature", "mathematics", "philosophy"]
        subject = random.choice(subjects)
        print(f"\n📚 You spent the day studying {subject}.")
        self.improve_stat(3, 2, "Intelligence")  # Improve intelligence
        self.player.log_action("study", f"Studied {subject}")

    def exercise_action(self) -> None:
        """Handle exercise action."""
        exercises = ["jogging", "swimming", "cycling", "hiking", "yoga"]
        exercise = random.choice(exercises)
        print(f"\n🏃 You went {exercise} and feel energized!")
        self.improve_stat(0, 1, "Strength")  # Improve strength
        self.improve_stat(1, 1, "Endurance")  # Improve endurance
        self.player.log_action("exercise", f"Did {exercise}")

    def relax_action(self) -> None:
        """Handle relaxation action."""
        activities = ["reading a book", "listening to music", "meditation", "watching clouds"]
        activity = random.choice(activities)
        print(f"\n😴 You relaxed by {activity}. You feel refreshed!")
        self.improve_stat(7, 1, "Focus")  # Improve focus
        self.player.log_action("relax", f"Relaxed by {activity}")

    def explore_action(self) -> None:
        """Handle exploration action."""
        locations = ["the old part of town", "a nearby park", "local markets", "cultural sites"]
        location = random.choice(locations)
        print(f"\n🗺️ You explored {location} and discovered something interesting!")
        self.improve_stat(5, 1, "Creativity")  # Improve creativity
        self.player.log_action("explore", f"Explored {location}")

    def move_city_action(self) -> None:
        """Handle moving to a new city."""
        cities = WorldManager.get_all_cities()
        
        if not cities:
            print(f"{Icons.ERROR} No cities available to move to.")
            return
            
        print_section("Available Cities", Icons.LOCATION)
        for i, city in enumerate(cities, 1):
            print(f"{i:2d}. {city['name']:<20} ({city['country']}) - Population: {city['population']}")

        while True:
            try:
                choice = int(input(f"\n{Icons.MOVE} Where would you like to move? (1-{len(cities)}): "))
                if 1 <= choice <= len(cities):
                    selected_city = cities[choice - 1]
                    self.player.data[10] = selected_city["id"]
                    self.player.save()
                    print(f"\n{Icons.SUCCESS} You moved to {selected_city['name']}, {selected_city['country']}!")
                    self.player.log_action("move_city", f"Moved to {selected_city['name']}")
                    break
            except ValueError:
                pass
            print(f"{Icons.ERROR} Invalid choice.")

    def improve_stat(self, stat_index: int, amount: int, stat_name: str) -> None:
        """Improve a player stat and display the change."""
        stats = StatManager.get_stat_block(self.player.data[8])
        old_val = stats[stat_index] if stat_index < len(stats) else 0
        
        if stat_index < len(stats):
            stats[stat_index] = min(99, stats[stat_index] + amount)
            self.player.data[8] = ''.join(f"{x:02d}" for x in stats)
            self.player.save()
            
            print(f"{Icons.STATS} {stat_name} improved: {old_val} → {stats[stat_index]} (+{amount})")

    def display_player_stats(self) -> None:
        """Display comprehensive player statistics."""
        print_header(f"{self.player.data[1]}'s Profile", Icons.PLAYER)
        
        # Basic info
        current_time = TimeManager.get_current_time()
        age = CharacterManager.calculate_age(current_time["tick"], self.player.data[4])
        gender_names = ["Male", "Female", "Other"]
        gender = gender_names[self.player.data[3]] if self.player.data[3] < 3 else "Unknown"
        
        print(f"📝 Name: {self.player.data[1]}")
        print(f"🎂 Age: {age} years old")
        print(f"⚧ Gender: {gender}")
        print(f"📅 Born: Tick {self.player.data[4]}")
        
        # Location info
        city_info = WorldManager.get_city_info(self.player.data[10])
        print(f"🏠 Location: {city_info['name']}, {city_info['country']}")
        
        # Stats
        StatManager.display_stats(self.player.data[7], "Personality")
        StatManager.display_stats(self.player.data[8], "Combat")
        
        # Body condition
        body = CombatSystem.load_body(self.player.data[0])
        CombatSystem.display_body_status(self.player.data[1], body)

    def check_birthday(self) -> None:
        """Check if it's the player's birthday."""
        current_time = TimeManager.get_current_time()
        if (current_time["tick"] - self.player.data[4]) % 365 == 0:
            print(f"\n{Icons.BIRTHDAY} Happy Birthday! You are now {self.player.data[2] + 1} years old!")
            self.player.data[2] += 1
            self.player.save()

    def run(self) -> None:
        """Main game loop."""
        print_header("Welcome to Life Simulation Game!", "🌟")
        print("A text-based life simulation with NPCs, combat, and world progression.")
        
        while self.running:
            try:
                # Display current status
                self.player.display_location()
                self.check_birthday()
                
                # Handle daily choice
                if not self.handle_daily_choice():
                    break
                    
                # Small delay for better UX
                sleep(0.5)
                
            except KeyboardInterrupt:
                print(f"\n\n{Icons.WARNING} Game interrupted by user.")
                confirm = input("Do you want to quit? (y/n): ").lower().strip()
                if confirm in ['y', 'yes']:
                    break
            except Exception as e:
                print(f"\n{Icons.ERROR} An error occurred: {e}")
                print("The game will continue...")

# === UTILITY FUNCTIONS FOR BACKWARDS COMPATIBILITY ===
def main():
    """Main function for backwards compatibility."""
    try:
        game = GameEngine()
        game.run()
    except Exception as e:
        print(f"{Icons.ERROR} Fatal error: {e}")
        print("Please check your game files and try again.")

def create_player():
    """Legacy function for creating a player."""
    player = Player()
    return player.data

def getPlayer():
    """Legacy function for getting player data."""
    if os.path.exists(Config.PLAYER_PATH):
        return load_json(Config.PLAYER_PATH)
    return None

def advance_time():
    """Legacy function for advancing time."""
    TimeManager.advance_time()

def get_all_characters():
    """Legacy function for getting all characters."""
    return CharacterManager.get_all_characters()

def simulate_day():
    """Legacy function for simulating a day."""
    SimulationSystem.simulate_world()

# === ENTRY POINT ===
if __name__ == "__main__":
    try:
        # Ensure required directories exist
        for directory in [Config.CHARACTER_PATH, Config.BODY_PATH, Config.CITY_PATH, 
                         os.path.dirname(Config.PLAYER_PATH), os.path.dirname(Config.TIME_PATH)]:
            os.makedirs(directory, exist_ok=True)
        
        # Start the game
        main()
        
    except KeyboardInterrupt:
        print(f"\n\n{Icons.SUCCESS} Thanks for playing! Goodbye!")
    except Exception as e:
        print(f"\n{Icons.ERROR} Critical error: {e}")
        print("Please check your installation and try again.")