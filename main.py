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

        # Healing over time
        healed = HealingSystem.natural_healing_tick("player_001")
        if healed:
            print(f"🩹 Natural healing occurred:")
            for zone, old_hp, new_hp in healed:
                print(f"  {zone.replace('_', ' ').title()}: {old_hp} → {new_hp}")

        # Check player near-death recovery
        player_data = load_json(Config.PLAYER_PATH)
        if player_data:
            recovery_result = RecoverySystem.check_natural_recovery("player_001")
            if recovery_result["status"] == "death_risk":
                # Handle death risk from deterioration
                pass

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

# === GYM & BODYBUILDING SYSTEM ===
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any

# === MUSCLE SYSTEM ===
class MuscleSystem:
    MUSCLE_GROUPS = {
        "chest": {"name": "Chest", "icon": "💪", "base_size": 10},
        "shoulders": {"name": "Shoulders", "icon": "🤲", "base_size": 8},
        "arms": {"name": "Arms", "icon": "💪", "base_size": 9},
        "back": {"name": "Back", "icon": "🗿", "base_size": 12},
        "core": {"name": "Core", "icon": "🔥", "base_size": 8},
        "legs": {"name": "Legs", "icon": "🦵", "base_size": 15},
        "glutes": {"name": "Glutes", "icon": "🍑", "base_size": 11}
    }
    
    SIZE_DESCRIPTIONS = {
        (0, 5): "Severely Atrophied",
        (5, 10): "Skinny",
        (10, 15): "Normal",
        (15, 25): "Toned",
        (25, 35): "Muscular",
        (35, 50): "Very Muscular", 
        (50, 70): "Bodybuilder",
        (70, 90): "Mass Monster",
        (90, 100): "Inhuman"
    }

    @staticmethod
    def initialize_physique(char_id: str) -> Dict[str, Any]:
        """Initialize character's muscle data."""
        physique = {
            "muscles": {},
            "body_fat": random.randint(8, 20),
            "total_mass": 0,
            "training_history": [],
            "supplements": {},
            "last_workout": None,
            "recovery_status": {},
            "strength_multiplier": 1.0
        }
        
        # Initialize muscle groups
        for muscle_id, muscle_info in MuscleSystem.MUSCLE_GROUPS.items():
            base_size = muscle_info["base_size"]
            physique["muscles"][muscle_id] = {
                "size": base_size + random.randint(-3, 3),
                "definition": random.randint(5, 15),
                "fatigue": 0,
                "last_trained": None,
                "training_volume": 0
            }
        
        physique["total_mass"] = sum(m["size"] for m in physique["muscles"].values())
        
        physique_path = os.path.join("./body/physique", f"{char_id}.json")
        save_json(physique_path, physique)
        return physique

    @staticmethod
    def load_physique(char_id: str) -> Dict[str, Any]:
        """Load character's physique data."""
        physique_path = os.path.join("./body/physique", f"{char_id}.json")
        physique = load_json(physique_path)
        if not physique or "muscles" not in physique:
            return MuscleSystem.initialize_physique(char_id)
        return physique

    @staticmethod
    def save_physique(char_id: str, physique: Dict[str, Any]) -> None:
        """Save character's physique data."""
        physique_path = os.path.join("./body/physique", f"{char_id}.json")
        save_json(physique_path, physique)

    @staticmethod
    def get_size_description(size: int) -> str:
        """Get description for muscle size."""
        for (min_size, max_size), desc in MuscleSystem.SIZE_DESCRIPTIONS.items():
            if min_size <= size < max_size:
                return desc
        return "Godlike"

    @staticmethod
    def display_physique(char_id: str, name: str) -> None:
        """Display character's physique stats."""
        physique = MuscleSystem.load_physique(char_id)
        
        print_header(f"{name}'s Physique", "💪")
        
        # Overall stats
        total_mass = physique["total_mass"]
        body_fat = physique["body_fat"]
        
        print(f"📊 Total Muscle Mass: {total_mass:.1f}kg")
        print(f"🥩 Body Fat: {body_fat}%")
        print(f"💪 Overall Build: {MuscleSystem.get_overall_build(total_mass, body_fat)}")
        
        print_section("Muscle Groups", "💪")
        for muscle_id, muscle_data in physique["muscles"].items():
            muscle_info = MuscleSystem.MUSCLE_GROUPS[muscle_id]
            size = muscle_data["size"]
            definition = muscle_data["definition"]
            fatigue = muscle_data["fatigue"]
            
            size_desc = MuscleSystem.get_size_description(size)
            fatigue_icon = "😴" if fatigue > 70 else "😓" if fatigue > 40 else "💪"
            
            bar = create_progress_bar(int(size), 100, 12)
            print(f"  {muscle_info['icon']} {muscle_info['name']:<10}: {bar} ({size_desc}) {fatigue_icon}")

    @staticmethod
    def get_overall_build(total_mass: float, body_fat: int) -> str:
        """Determine overall body build description."""
        if body_fat > 25:
            return "Bulky"
        elif body_fat < 8:
            return "Shredded"
        elif total_mass > 120:
            return "Mass Monster"
        elif total_mass > 90:
            return "Bodybuilder"
        elif total_mass > 70:
            return "Athletic"
        else:
            return "Lean"

# === SUPPLEMENT SYSTEM ===
class SupplementSystem:
    SUPPLEMENTS = {
        "protein_powder": {
            "name": "Protein Powder",
            "description": "Boosts muscle growth by 25%",
            "cost": 30,
            "duration": 7,  # days
            "effects": {"muscle_growth": 1.25, "recovery": 1.1},
            "icon": "🥤"
        },
        "creatine": {
            "name": "Creatine",
            "description": "Increases strength and power by 15%",
            "cost": 25,
            "duration": 30,
            "effects": {"strength": 1.15, "power": 1.15},
            "icon": "⚡"
        },
        "bcaa": {
            "name": "BCAA",
            "description": "Reduces fatigue and improves recovery",
            "cost": 35,
            "duration": 14,
            "effects": {"fatigue_reduction": 0.7, "recovery": 1.3},
            "icon": "🔋"
        },
        "pre_workout": {
            "name": "Pre-Workout",
            "description": "Intense energy boost for training",
            "cost": 40,
            "duration": 10,
            "effects": {"training_intensity": 1.4, "strength": 1.1},
            "icon": "🔥"
        },
        "testosterone": {
            "name": "Testosterone (TRT)",
            "description": "Medical testosterone therapy",
            "cost": 200,
            "duration": 30,
            "effects": {"muscle_growth": 1.8, "strength": 1.3, "recovery": 1.5},
            "side_effects": {"aggression": 1.2},
            "icon": "💉",
            "prescription": True
        },
        "anavar": {
            "name": "Anavar (Oxandrolone)",
            "description": "Mild anabolic steroid for cutting",
            "cost": 300,
            "duration": 21,
            "effects": {"muscle_growth": 1.6, "fat_loss": 1.4, "strength": 1.25},
            "side_effects": {"liver_stress": 1.3},
            "icon": "💊",
            "illegal": True
        },
        "trenbolone": {
            "name": "Trenbolone",
            "description": "Powerful anabolic steroid",
            "cost": 500,
            "duration": 28,
            "effects": {"muscle_growth": 2.5, "strength": 1.8, "aggression": 1.5},
            "side_effects": {"aggression": 2.0, "health_risk": 1.8},
            "icon": "☠️",
            "illegal": True
        },
        "hgh": {
            "name": "Human Growth Hormone",
            "description": "Premium muscle building hormone",
            "cost": 800,
            "duration": 60,
            "effects": {"muscle_growth": 2.0, "recovery": 2.0, "fat_loss": 1.6},
            "side_effects": {"health_risk": 1.4},
            "icon": "🧬",
            "illegal": True
        }
    }

    @staticmethod
    def display_supplement_shop() -> None:
        """Display supplement shop interface."""
        print_header("Supplement Shop", "🏪")
        
        legal_sups = []
        prescription_sups = []
        illegal_sups = []
        
        for sup_id, sup_data in SupplementSystem.SUPPLEMENTS.items():
            if sup_data.get("illegal"):
                illegal_sups.append((sup_id, sup_data))
            elif sup_data.get("prescription"):
                prescription_sups.append((sup_id, sup_data))
            else:
                legal_sups.append((sup_id, sup_data))
        
        print_section("Legal Supplements", "✅")
        for i, (sup_id, sup_data) in enumerate(legal_sups, 1):
            print(f"{i}. {sup_data['icon']} {sup_data['name']:<20} - ${sup_data['cost']}")
            print(f"   {sup_data['description']}")
        
        print_section("Prescription Only", "🩺")
        for i, (sup_id, sup_data) in enumerate(prescription_sups, len(legal_sups) + 1):
            print(f"{i}. {sup_data['icon']} {sup_data['name']:<20} - ${sup_data['cost']}")
            print(f"   {sup_data['description']} (Requires medical consultation)")
        
        print_section("Black Market", "🕶️")
        for i, (sup_id, sup_data) in enumerate(illegal_sups, len(legal_sups) + len(prescription_sups) + 1):
            print(f"{i}. {sup_data['icon']} {sup_data['name']:<20} - ${sup_data['cost']}")
            print(f"   {sup_data['description']} (ILLEGAL - Health risks!)")

    @staticmethod
    def apply_supplement(char_id: str, supplement_id: str) -> Dict[str, Any]:
        """Apply supplement effects to character."""
        physique = MuscleSystem.load_physique(char_id)
        supplement = SupplementSystem.SUPPLEMENTS.get(supplement_id)
        
        if not supplement:
            return {"success": False, "message": "Unknown supplement"}
        
        # Check if already taking this supplement
        active_sups = physique.get("supplements", {})
        if supplement_id in active_sups:
            return {"success": False, "message": f"Already taking {supplement['name']}"}
        
        # Add supplement to active list
        current_time = TimeManager.get_current_time()
        active_sups[supplement_id] = {
            "start_tick": current_time["tick"],
            "duration": supplement["duration"],
            "effects": supplement["effects"],
            "side_effects": supplement.get("side_effects", {})
        }
        
        physique["supplements"] = active_sups
        MuscleSystem.save_physique(char_id, physique)
        
        return {
            "success": True,
            "message": f"Started taking {supplement['name']}",
            "duration": supplement["duration"],
            "effects": supplement["effects"]
        }

# === GYM SYSTEM ===
class GymSystem:
    GYM_EQUIPMENT = {
        "bench_press": {
            "name": "Bench Press",
            "targets": ["chest", "shoulders", "arms"],
            "primary": "chest",
            "intensity": "high",
            "strength_gain": 3,
            "fatigue": 25,
            "icon": "🏋️"
        },
        "squat_rack": {
            "name": "Squat Rack", 
            "targets": ["legs", "glutes", "core"],
            "primary": "legs",
            "intensity": "high",
            "strength_gain": 4,
            "fatigue": 30,
            "icon": "🦵"
        },
        "deadlift": {
            "name": "Deadlift",
            "targets": ["back", "legs", "glutes", "core"],
            "primary": "back",
            "intensity": "extreme",
            "strength_gain": 5,
            "fatigue": 35,
            "icon": "💀"
        },
        "pull_ups": {
            "name": "Pull-ups",
            "targets": ["back", "arms"],
            "primary": "back", 
            "intensity": "medium",
            "strength_gain": 2,
            "fatigue": 20,
            "icon": "🤸"
        },
        "dumbbell_rows": {
            "name": "Dumbbell Rows",
            "targets": ["back", "arms"],
            "primary": "back",
            "intensity": "medium",
            "strength_gain": 2,
            "fatigue": 15,
            "icon": "🏋️"
        },
        "shoulder_press": {
            "name": "Shoulder Press",
            "targets": ["shoulders", "arms"],
            "primary": "shoulders",
            "intensity": "medium",
            "strength_gain": 2,
            "fatigue": 18,
            "icon": "🤲"
        },
        "leg_press": {
            "name": "Leg Press",
            "targets": ["legs", "glutes"],
            "primary": "legs",
            "intensity": "high",
            "strength_gain": 3,
            "fatigue": 25,
            "icon": "🦵"
        },
        "cable_flyes": {
            "name": "Cable Flyes",
            "targets": ["chest"],
            "primary": "chest",
            "intensity": "medium",
            "strength_gain": 2,
            "fatigue": 15,
            "icon": "💪"
        },
        "bicep_curls": {
            "name": "Bicep Curls",
            "targets": ["arms"],
            "primary": "arms",
            "intensity": "low",
            "strength_gain": 1,
            "fatigue": 10,
            "icon": "💪"
        },
        "crunches": {
            "name": "Crunches",
            "targets": ["core"],
            "primary": "core",
            "intensity": "low",
            "strength_gain": 1,
            "fatigue": 12,
            "icon": "🔥"
        }
    }
    
    WORKOUT_ROUTINES = {
        "push_day": {
            "name": "Push Day (Chest, Shoulders, Triceps)",
            "exercises": ["bench_press", "shoulder_press", "cable_flyes", "bicep_curls"],
            "icon": "💪"
        },
        "pull_day": {
            "name": "Pull Day (Back, Biceps)",
            "exercises": ["deadlift", "pull_ups", "dumbbell_rows"],
            "icon": "🤸"
        },
        "leg_day": {
            "name": "Leg Day (Legs, Glutes)",
            "exercises": ["squat_rack", "leg_press", "crunches"],
            "icon": "🦵"
        },
        "full_body": {
            "name": "Full Body Workout",
            "exercises": ["bench_press", "squat_rack", "pull_ups", "crunches"],
            "icon": "🏋️"
        },
        "strength_focus": {
            "name": "Strength Training",
            "exercises": ["deadlift", "squat_rack", "bench_press"],
            "icon": "💀"
        }
    }

    @staticmethod
    def display_gym_menu() -> None:
        """Display gym training options."""
        print_header("Iron Temple Gym", "🏋️")
        
        print_section("Workout Routines", "💪")
        for i, (routine_id, routine) in enumerate(GymSystem.WORKOUT_ROUTINES.items(), 1):
            exercises = ", ".join([GymSystem.GYM_EQUIPMENT[ex]["name"] for ex in routine["exercises"]])
            print(f"{i}. {routine['icon']} {routine['name']}")
            print(f"   Exercises: {exercises}")
        
        print(f"\n{len(GymSystem.WORKOUT_ROUTINES) + 1}. 🎯 Custom Workout (Choose specific exercises)")
        print(f"{len(GymSystem.WORKOUT_ROUTINES) + 2}. 💊 Buy Supplements")
        print(f"{len(GymSystem.WORKOUT_ROUTINES) + 3}. 📊 Check Physique Stats")
        print(f"{len(GymSystem.WORKOUT_ROUTINES) + 4}. 🚪 Leave Gym")

    @staticmethod
    def execute_workout(player: Player, routine_id: str = None, custom_exercises: List[str] = None) -> None:
        """Execute a workout routine."""
        physique = MuscleSystem.load_physique(player.data[0])
        
        # Determine exercises
        if routine_id:
            routine = GymSystem.WORKOUT_ROUTINES[routine_id]
            exercises = routine["exercises"]
            workout_name = routine["name"]
        elif custom_exercises:
            exercises = custom_exercises
            workout_name = "Custom Workout"
        else:
            return
        
        print_header(f"Starting: {workout_name}", "🏋️")
        
        # Check recovery status
        current_time = TimeManager.get_current_time()
        if physique.get("last_workout"):
            days_since_last = (current_time["tick"] - physique["last_workout"]) // 1
            if days_since_last < 1:
                print(f"⚠️ Warning: You worked out recently! Overtraining risk increased.")
        
        total_fatigue = 0
        muscle_gains = {}
        strength_gain = 0
        
        # Execute each exercise
        for exercise_id in exercises:
            exercise = GymSystem.GYM_EQUIPMENT[exercise_id]
            print(f"\n{exercise['icon']} Performing {exercise['name']}...")
            
            # Calculate intensity based on stats and supplements
            player_stats = StatManager.get_stat_block(player.data[8])
            base_intensity = 1.0
            
            # Apply supplement effects
            for sup_id, sup_data in physique.get("supplements", {}).items():
                effects = sup_data.get("effects", {})
                if "training_intensity" in effects:
                    base_intensity *= effects["training_intensity"]
            
            # Calculate gains
            exercise_fatigue = exercise["fatigue"] * base_intensity
            exercise_strength = exercise["strength_gain"] * base_intensity
            
            # Apply to targeted muscles
            for target_muscle in exercise["targets"]:
                if target_muscle not in muscle_gains:
                    muscle_gains[target_muscle] = 0
                
                # Primary muscle gets more gains
                multiplier = 1.5 if target_muscle == exercise["primary"] else 1.0
                gain = (exercise_strength * multiplier * base_intensity) / len(exercise["targets"])
                muscle_gains[target_muscle] += gain
            
            total_fatigue += exercise_fatigue
            strength_gain += exercise_strength
            
            # Random workout event
            if random.randint(1, 100) <= 15:
                event = GymSystem.get_random_workout_event()
                print(f"   {event['icon']} {event['message']}")
                if event.get("bonus"):
                    strength_gain *= event["bonus"]
        
        # Apply gains to physique
        GymSystem.apply_workout_gains(physique, muscle_gains, total_fatigue, strength_gain)
        
        # Update workout history
        physique["last_workout"] = current_time["tick"]
        physique["training_history"].append({
            "tick": current_time["tick"],
            "workout": workout_name,
            "exercises": exercises,
            "fatigue": total_fatigue,
            "gains": muscle_gains
        })
        
        MuscleSystem.save_physique(player.data[0], physique)
        
        # Update player stats
        GymSystem.update_player_stats(player, strength_gain)
        
        print_header("Workout Complete!", "✅")
        print(f"💪 Strength gained: +{strength_gain:.1f}")
        print(f"😓 Total fatigue: {total_fatigue:.1f}")
        
        for muscle, gain in muscle_gains.items():
            muscle_name = MuscleSystem.MUSCLE_GROUPS[muscle]["name"]
            print(f"🎯 {muscle_name}: +{gain:.1f} size")
        
        # Advance time
        TimeManager.advance_time()

    @staticmethod
    def apply_workout_gains(physique: Dict[str, Any], muscle_gains: Dict[str, float], 
                          fatigue: float, strength_gain: float) -> None:
        """Apply workout gains to physique."""
        # Apply muscle gains with supplement modifiers
        for muscle_id, gain in muscle_gains.items():
            if muscle_id in physique["muscles"]:
                # Apply supplement effects
                modified_gain = gain
                for sup_id, sup_data in physique.get("supplements", {}).items():
                    effects = sup_data.get("effects", {})
                    if "muscle_growth" in effects:
                        modified_gain *= effects["muscle_growth"]
                
                # Apply gain
                physique["muscles"][muscle_id]["size"] += modified_gain
                physique["muscles"][muscle_id]["size"] = min(100, physique["muscles"][muscle_id]["size"])
                
                # Add training volume
                physique["muscles"][muscle_id]["training_volume"] += gain
        
        # Update total mass
        physique["total_mass"] = sum(m["size"] for m in physique["muscles"].values())

    @staticmethod
    def update_player_stats(player: Player, strength_gain: float) -> None:
        """Update player combat stats based on workout."""
        stats = StatManager.get_stat_block(player.data[8])
        
        # Increase strength and endurance
        strength_increase = max(1, int(strength_gain // 3))
        endurance_increase = max(1, int(strength_gain // 4))
        
        stats[0] = min(99, stats[0] + strength_increase)  # Strength
        stats[1] = min(99, stats[1] + endurance_increase)  # Endurance
        
        player.data[8] = ''.join(f"{x:02d}" for x in stats)
        player.save()
        
        print(f"📈 Combat Stats - Strength: +{strength_increase}, Endurance: +{endurance_increase}")

    @staticmethod
    def get_random_workout_event() -> Dict[str, Any]:
        """Get random workout events for flavor."""
        events = [
            {"message": "Perfect form! Extra gains!", "icon": "⭐", "bonus": 1.2},
            {"message": "You hit a new personal record!", "icon": "🏆", "bonus": 1.15},
            {"message": "Great mind-muscle connection!", "icon": "🧠", "bonus": 1.1},
            {"message": "You pushed through the burn!", "icon": "🔥", "bonus": 1.1},
            {"message": "Solid technique today!", "icon": "✅"},
            {"message": "You're feeling the pump!", "icon": "💪"},
            {"message": "That was a grind, but worth it!", "icon": "😤"}
        ]
        return random.choice(events)

    def gym_interface(player: Player) -> None:
        """Main gym interface."""
        while True:
            GymSystem.display_gym_menu()
            
            total_options = len(GymSystem.WORKOUT_ROUTINES) + 4
            
            try:
                choice = int(input(f"\n🏋️ Choose your action (1-{total_options}): "))
                
                if choice <= len(GymSystem.WORKOUT_ROUTINES):
                    # Execute workout routine
                    routine_id = list(GymSystem.WORKOUT_ROUTINES.keys())[choice - 1]
                    GymSystem.execute_workout(player, routine_id=routine_id)
                    break
                    
                elif choice == len(GymSystem.WORKOUT_ROUTINES) + 1:
                    # Custom workout
                    GymSystem.custom_workout_interface(player)
                    break
                    
                elif choice == len(GymSystem.WORKOUT_ROUTINES) + 2:
                    # Buy supplements
                    GymSystem.supplement_shop_interface(player)
                    
                elif choice == len(GymSystem.WORKOUT_ROUTINES) + 3:
                    # Check physique
                    MuscleSystem.display_physique(player.data[0], player.data[1])
                    input("\nPress Enter to continue...")
                    
                elif choice == len(GymSystem.WORKOUT_ROUTINES) + 4:
                    # Leave gym
                    break
                    
            except ValueError:
                print(f"{Icons.ERROR} Invalid input.")

    def custom_workout_interface(player: Player) -> None:
        """Interface for creating custom workouts."""
        print_section("Custom Workout Builder", "🎯")
        
        available_exercises = list(GymSystem.GYM_EQUIPMENT.keys())
        selected_exercises = []
        
        print("Available exercises:")
        for i, exercise_id in enumerate(available_exercises, 1):
            exercise = GymSystem.GYM_EQUIPMENT[exercise_id]
            targets = ", ".join(exercise["targets"])
            print(f"{i:2d}. {exercise['icon']} {exercise['name']:<20} (Targets: {targets})")
        
        print(f"\nSelect exercises for your workout (enter numbers separated by spaces):")
        print(f"Example: 1 3 5 (for multiple exercises)")
        
        try:
            selections = input("Your selection: ").strip().split()
            for selection in selections:
                idx = int(selection) - 1
                if 0 <= idx < len(available_exercises):
                    selected_exercises.append(available_exercises[idx])
            
            if selected_exercises:
                print(f"\nSelected exercises:")
                for exercise_id in selected_exercises:
                    exercise = GymSystem.GYM_EQUIPMENT[exercise_id]
                    print(f"  {exercise['icon']} {exercise['name']}")
                
                confirm = input("\nStart this workout? (y/n): ").lower().strip()
                if confirm in ['y', 'yes']:
                    GymSystem.execute_workout(player, custom_exercises=selected_exercises)
            else:
                print("No valid exercises selected.")
                
        except ValueError:
            print("Invalid input format.")

    def supplement_shop_interface(player: Player) -> None:
        """Interface for buying supplements."""
        SupplementSystem.display_supplement_shop()
        
        # TODO: Implement actual purchasing when currency system is added
        print(f"\n💰 Supplement purchasing will be available when currency system is implemented!")
        input("Press Enter to continue...")

    # === PHYSIQUE EFFECTS ON COMBAT ===
    def apply_physique_to_combat_stats(char_id: str, base_stats: List[int]) -> List[int]:
        """Modify combat stats based on physique."""
        physique = MuscleSystem.load_physique(char_id)
        modified_stats = base_stats.copy()
        
        # Calculate strength multiplier from muscle mass
        total_mass = physique.get("total_mass", 70)
        strength_multiplier = min(2.0, 1.0 + (total_mass - 70) / 100)
        
        # Calculate speed penalty from excessive mass
        if total_mass > 100:
            speed_penalty = (total_mass - 100) / 200
            modified_stats[3] = max(1, int(modified_stats[3] * (1 - speed_penalty)))
        
        # Apply strength boost
        modified_stats[0] = min(99, int(modified_stats[0] * strength_multiplier))
        
        # Endurance boost from leg muscles
        leg_mass = physique["muscles"].get("legs", {}).get("size", 15)
        endurance_multiplier = 1.0 + (leg_mass - 15) / 50
        modified_stats[1] = min(99, int(modified_stats[1] * endurance_multiplier))
        
        return modified_stats

# === DEATH SYSTEM CORE ===
class DeathSystem:
    DEATH_CAUSES = {
        "head_trauma": {
            "name": "Severe Head Trauma",
            "description": "Critical brain injury from combat",
            "chance_base": 85,  # % chance of death when triggered
            "medical_help_reduction": 40,
            "icon": "💀"
        },
        "blood_loss": {
            "name": "Massive Blood Loss",
            "description": "Hemorrhaging from multiple wounds",
            "chance_base": 70,
            "medical_help_reduction": 50,
            "icon": "🩸"
        },
        "organ_failure": {
            "name": "Organ Failure",
            "description": "Critical damage to vital organs",
            "chance_base": 75,
            "medical_help_reduction": 35,
            "icon": "💔"
        },
        "shock": {
            "name": "Traumatic Shock",
            "description": "Body shutting down from trauma",
            "chance_base": 60,
            "medical_help_reduction": 60,
            "icon": "⚡"
        },
        "suffocation": {
            "name": "Suffocation",
            "description": "Cannot breathe due to injuries",
            "chance_base": 80,
            "medical_help_reduction": 45,
            "icon": "🫁"
        }
    }
    
    NEAR_DEATH_STAGES = {
        0: {"name": "Critical", "description": "Unconscious, barely breathing", "icon": "💀"},
        1: {"name": "Grave", "description": "In and out of consciousness", "icon": "😵"},
        2: {"name": "Serious", "description": "Weak but conscious", "icon": "😰"},
        3: {"name": "Stable", "description": "Conscious but hurt", "icon": "😓"},
        4: {"name": "Recovering", "description": "Walking wounded", "icon": "🤕"}
    }

    @staticmethod
    def check_death_conditions(char_id: str) -> Dict[str, Any]:
        """Check if character should enter near-death or death state."""
        body = CombatSystem.load_body(char_id)
        
        # Calculate overall condition
        total_health = sum(zone["health"] for zone in body.values())
        max_health = len(body) * 100
        health_percentage = (total_health / max_health) * 100
        
        # Check specific death triggers
        head_health = body.get("head", {}).get("health", 100)
        torso_health = body.get("torso", {}).get("health", 100)
        
        death_risks = []
        
        # Head trauma check
        if head_health <= 5:
            death_risks.append("head_trauma")
        elif head_health <= 15:
            # Near-death from head trauma
            return {"status": "near_death", "cause": "head_trauma", "severity": 0}
        
        # Torso damage check (vital organs)
        if torso_health <= 3:
            death_risks.append("organ_failure")
        elif torso_health <= 12:
            return {"status": "near_death", "cause": "organ_failure", "severity": 1}
        
        # Overall blood loss
        if health_percentage <= 15:
            death_risks.append("blood_loss")
        elif health_percentage <= 25:
            return {"status": "near_death", "cause": "blood_loss", "severity": 1}
        
        # Multiple injuries causing shock
        injured_zones = sum(1 for zone in body.values() if zone["health"] < 50)
        if injured_zones >= 4 and health_percentage <= 40:
            death_risks.append("shock")
        elif injured_zones >= 3 and health_percentage <= 35:
            return {"status": "near_death", "cause": "shock", "severity": 2}
        
        # Breathing issues from torso/head damage
        if (head_health <= 20 and torso_health <= 30):
            death_risks.append("suffocation")
        
        if death_risks:
            return {"status": "death_risk", "causes": death_risks}
        elif health_percentage <= 30:
            return {"status": "near_death", "cause": "blood_loss", "severity": 3}
        
        return {"status": "stable"}

    @staticmethod
    def trigger_near_death(char_id: str, char_name: str, cause: str, severity: int) -> Dict[str, Any]:
        """Trigger near-death state."""
        print_header(f"💀 {char_name} is Near Death!", "💀")
        
        stage = DeathSystem.NEAR_DEATH_STAGES[severity]
        cause_info = DeathSystem.DEATH_CAUSES.get(cause, {"description": "Unknown cause"})
        
        print(f"{stage['icon']} Condition: {stage['name']} - {stage['description']}")
        print(f"🏥 Cause: {cause_info['description']}")
        
        # Save near-death state
        near_death_data = {
            "active": True,
            "cause": cause,
            "severity": severity,
            "start_tick": TimeManager.get_current_time()["tick"],
            "medical_attention": False,
            "deterioration_chance": 30 - (severity * 5),  # Worse condition = more likely to get worse
            "recovery_chance": 10 + (severity * 15)        # Better condition = more likely to recover
        }
        
        near_death_path = os.path.join("./body/near_death", f"{char_id}.json")
        save_json(near_death_path, near_death_data)
        
        return near_death_data

    @staticmethod
    def check_death_roll(char_id: str, cause: str, medical_help: bool = False) -> Dict[str, Any]:
        """Roll for actual death."""
        cause_data = DeathSystem.DEATH_CAUSES.get(cause, {"chance_base": 50, "medical_help_reduction": 0})
        
        base_chance = cause_data["chance_base"]
        if medical_help:
            base_chance -= cause_data["medical_help_reduction"]
        
        # Character stats affect survival
        if(char_id != "player_001"):
            char_data = CharacterManager.get_character_data(char_id)
        else:
            char_data = getPlayer()
        if char_data and len(char_data) > 8:
            stats = StatManager.get_stat_block(char_data[8])
            endurance = stats[1] if len(stats) > 1 else 20
            toughness = stats[6] if len(stats) > 6 else 20
            willpower = stats[9] if len(stats) > 9 else 20
            
            # Higher stats reduce death chance
            stat_bonus = (endurance + toughness + willpower) / 10
            base_chance -= stat_bonus
        
        # Clamp between 5% and 95%
        death_chance = max(5, min(95, base_chance))
        
        print(f"💀 Death chance: {death_chance}%")
        if medical_help:
            print("🏥 Medical assistance is helping!")
        
        roll = random.randint(1, 100)
        print(f"🎲 Fate roll: {roll}")
        
        if roll <= death_chance:
            return {"outcome": "death", "cause": cause, "roll": roll, "chance": death_chance}
        else:
            return {"outcome": "survival", "cause": cause, "roll": roll, "chance": death_chance}

# === MEDICAL SYSTEM ===
class MedicalSystem:
    MEDICAL_INTERVENTIONS = {
        "field_medicine": {
            "name": "Field Medicine",
            "description": "Basic first aid and emergency care",
            "effectiveness": 30,
            "cost": 0,
            "time": 1,
            "requirements": [],
            "icon": "🩹"
        },
        "paramedic": {
            "name": "Paramedic Response",
            "description": "Professional emergency medical technician",
            "effectiveness": 55,
            "cost": 200,
            "time": 2,
            "requirements": [],
            "icon": "🚑"
        },
        "emergency_room": {
            "name": "Emergency Room",
            "description": "Hospital emergency department",
            "effectiveness": 75,
            "cost": 1000,
            "time": 4,
            "requirements": [],
            "icon": "🏥"
        },
        "trauma_center": {
            "name": "Trauma Center",
            "description": "Specialized trauma surgery unit",
            "effectiveness": 90,
            "cost": 5000,
            "time": 8,
            "requirements": ["major_city"],
            "icon": "⚕️"
        },
        "experimental": {
            "name": "Experimental Treatment",
            "description": "Cutting-edge medical procedures",
            "effectiveness": 95,
            "cost": 25000,
            "time": 12,
            "requirements": ["major_city", "high_tech"],
            "icon": "🧬"
        }
    }

    @staticmethod
    def get_available_medical_care(location_id: str) -> List[str]:
        """Get available medical options based on location."""
        city_info = WorldManager.get_city_info(location_id)
        population = WorldManager.count_population_in_city(location_id)
        
        available = ["field_medicine"]  # Always available
        
        if population > 10:
            available.append("paramedic")
        
        if population > 50:
            available.append("emergency_room")
        
        if population > 200:  # Major city
            available.append("trauma_center")
        
        if population > 500:  # High-tech major city
            available.append("experimental")
        
        return available

    @staticmethod
    def medical_intervention_menu(char_id: str, char_name: str) -> Optional[str]:
        """Display medical intervention options."""
        # Get location
        if(char_id == "player_001"):
            char_data = getPlayer()
        else:    
            char_data = CharacterManager.get_character_data(char_id)
        location_id = char_data[10] if char_data and len(char_data) > 10 else "unknown"

        print(char_data)
        print(location_id)
        
        available_care = MedicalSystem.get_available_medical_care(location_id)
        
        print_header(f"Medical Care for {char_name}", "🏥")
        city_info = WorldManager.get_city_info(location_id)
        print(f"📍 Location: {city_info['name']}, {city_info['country']}")
        
        print_section("Available Medical Care", "⚕️")
        for i, care_id in enumerate(available_care, 1):
            care = MedicalSystem.MEDICAL_INTERVENTIONS[care_id]
            print(f"{i}. {care['icon']} {care['name']}")
            print(f"   {care['description']}")
            print(f"   Effectiveness: {care['effectiveness']}% | Cost: ${care['cost']} | Time: {care['time']} hours")
        
        print(f"\n{len(available_care) + 1}. ❌ No medical care (accept fate)")
        
        while True:
            try:
                choice = int(input(f"\n🏥 Choose medical response (1-{len(available_care) + 1}): "))
                if choice == len(available_care) + 1:
                    return None  # No medical care
                elif 1 <= choice <= len(available_care):
                    return available_care[choice - 1]
            except ValueError:
                pass
            print(f"{Icons.ERROR} Invalid choice.")

    @staticmethod
    def apply_medical_care(char_id: str, char_name: str, care_type: str, 
                          near_death_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply medical intervention."""
        care = MedicalSystem.MEDICAL_INTERVENTIONS[care_type]
        
        print(f"\n{care['icon']} Applying {care['name']}...")
        print(f"⏱️ Treatment time: {care['time']} hours")
        
        # Simulate treatment time
        for i in range(care['time']):
            print(f"   {'█' * (i + 1)}{'░' * (care['time'] - i - 1)} {i + 1}/{care['time']} hours")
            sleep(0.3)
        
        # Calculate success
        base_success = care['effectiveness']
        
        # Character stats help
        char_data = CharacterManager.get_character_data(char_id)
        if char_data and len(char_data) > 8:
            stats = StatManager.get_stat_block(char_data[8])
            endurance = stats[1] if len(stats) > 1 else 20
            toughness = stats[6] if len(stats) > 6 else 20
            
            stat_bonus = (endurance + toughness) / 10
            base_success += stat_bonus
        
        # Severity affects success
        severity = near_death_data.get('severity', 0)
        severity_penalty = severity * 5  # Worse condition = harder to treat
        base_success -= severity_penalty
        
        success_chance = max(10, min(95, base_success))
        
        roll = random.randint(1, 100)
        print(f"\n🎲 Treatment success chance: {success_chance}%")
        print(f"🎲 Medical roll: {roll}")
        
        if roll <= success_chance:
            return {"success": True, "care_type": care_type, "roll": roll, "chance": success_chance}
        else:
            return {"success": False, "care_type": care_type, "roll": roll, "chance": success_chance}

# === DEATH CONSEQUENCES ===
class DeathConsequences:
    @staticmethod
    def handle_character_death(char_id: str, char_name: str, cause: str) -> None:
        """Handle the death of a character."""
        print_header(f"💀 {char_name} has died", "💀")
        
        cause_info = DeathSystem.DEATH_CAUSES.get(cause, {"description": "Unknown cause"})
        print(f"☠️ Cause of death: {cause_info['description']}")
        
        current_time = TimeManager.get_current_time()
        
        # Create death record
        death_record = {
            "name": char_name,
            "id": char_id,
            "death_tick": current_time["tick"],
            "death_date": f"{current_time['year']}-{current_time['month']:02d}-{current_time['day']:02d}",
            "cause": cause,
            "cause_description": cause_info["description"],
            "location": "unknown",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Get location info
        if (char_id != "player_001"):
            char_data = CharacterManager.get_character_data(char_id)
        else:
            char_data = getPlayer()
        if char_data and len(char_data) > 10:
            city_info = WorldManager.get_city_info(char_data[10])
            death_record["location"] = f"{city_info['name']}, {city_info['country']}"
        
        # Save to death registry
        death_registry_path = "./world/death_registry.json"
        registry = load_json(death_registry_path, {"deaths": []})
        registry["deaths"].append(death_record)
        save_json(death_registry_path, registry)
        
        if char_id == "player_001":
            DeathConsequences.handle_player_death(death_record)
        else:
            DeathConsequences.handle_npc_death(char_id, death_record)

    @staticmethod
    def handle_player_death(death_record: Dict[str, Any]) -> None:
        """Handle player character death."""
        print_section("Game Over", "💀")
        print(f"Your journey has come to an end in {death_record['location']}.")
        print(f"You will be remembered for your time in this world.")
        
        # Display final stats
        player_data = load_json(Config.PLAYER_PATH, [])
        if player_data:
            current_time = TimeManager.get_current_time()
            age = CharacterManager.calculate_age(current_time["tick"], player_data[4])
            print(f"\n📊 Final Statistics:")
            print(f"   🎂 Age at death: {age} years")
            print(f"   ⏰ Days survived: {(current_time['tick'] - player_data[4])}")
            
            # Show combat record if available
            combat_stats_path = "./player/combat_stats.json"
            if os.path.exists(combat_stats_path):
                stats = load_json(combat_stats_path)
                print(f"   ⚔️ Total fights: {stats.get('total_fights', 0)}")
                print(f"   🏆 Victories: {stats.get('wins', 0)}")
        
        # Offer new game or quit
        print(f"\nOptions:")
        print(f"1. 🔄 Start a new life")
        print(f"2. 👻 View death registry")
        print(f"3. 🚪 Quit game")
        
        while True:
            try:
                choice = int(input("Choose (1-3): "))
                if choice == 1:
                    DeathConsequences.start_new_game()
                    break
                elif choice == 2:
                    DeathConsequences.display_death_registry()
                elif choice == 3:
                    print("Thanks for playing! Rest in peace.")
                    exit()
            except ValueError:
                pass
            print(f"{Icons.ERROR} Invalid choice.")

    @staticmethod
    def handle_npc_death(char_id: str, death_record: Dict[str, Any]) -> None:
        """Handle NPC death."""
        print(f"💀 {death_record['name']} has passed away in {death_record['location']}.")
        
        # Move character file to deceased folder
        deceased_dir = "./chars/deceased"
        os.makedirs(deceased_dir, exist_ok=True)
        
        char_file = os.path.join(Config.CHARACTER_PATH, f"{char_id}.json")
        deceased_file = os.path.join(deceased_dir, f"{char_id}.json")
        
        if os.path.exists(char_file):
            import shutil
            shutil.move(char_file, deceased_file)
        
        # Remove from world
        body_file = os.path.join(Config.BODY_PATH, f"{char_id}.json")
        if os.path.exists(body_file):
            os.remove(body_file)

    @staticmethod
    def start_new_game() -> None:
        """Start a new game after death."""
        # Archive old player
        if os.path.exists(Config.PLAYER_PATH):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_path = f"./player/deceased/player_{timestamp}.json"
            os.makedirs(os.path.dirname(archive_path), exist_ok=True)
            import shutil
            shutil.copy(Config.PLAYER_PATH, archive_path)
            os.remove(Config.PLAYER_PATH)
        
        print_header("Starting New Life", "🌟")
        # Player class will create new character automatically

    @staticmethod
    def display_death_registry() -> None:
        """Display the death registry."""
        registry = load_json("./world/death_registry.json", {"deaths": []})
        deaths = registry.get("deaths", [])
        
        print_header("Death Registry", "💀")
        
        if not deaths:
            print("No deaths recorded yet.")
            return
        
        print(f"Total deaths: {len(deaths)}")
        print()
        
        # Show recent deaths
        recent_deaths = deaths[-10:]  # Last 10 deaths
        for death in recent_deaths:
            print(f"💀 {death['name']}")
            print(f"   📅 Died: {death['death_date']}")
            print(f"   📍 Location: {death['location']}")
            print(f"   ☠️ Cause: {death['cause_description']}")
            print()
        
        input("Press Enter to continue...")

# === RECOVERY SYSTEM ===
class RecoverySystem:
    @staticmethod
    def check_natural_recovery(char_id: str) -> Dict[str, Any]:
        """Check for natural recovery from near-death."""
        near_death_path = os.path.join("./body/near_death", f"{char_id}.json")
        
        # Check if file exists and load data
        if not os.path.exists(near_death_path):
            return {"status": "not_near_death"}
            
        near_death_data = load_json(near_death_path)
        
        # Validate data structure
        if not near_death_data or not isinstance(near_death_data, dict):
            # Clean up corrupted file
            try:
                os.remove(near_death_path)
            except:
                pass
            return {"status": "not_near_death"}
        
        # Check if near-death state is active
        if not near_death_data.get("active", False):
            # Clean up inactive near-death file
            try:
                os.remove(near_death_path)
            except:
                pass
            return {"status": "not_near_death"}
        
        # Get recovery chances with fallbacks
        recovery_chance = near_death_data.get("recovery_chance", 10)
        deterioration_chance = near_death_data.get("deterioration_chance", 30)
        
        # Validate chances are reasonable numbers
        if not isinstance(recovery_chance, (int, float)) or recovery_chance < 0:
            recovery_chance = 10
        if not isinstance(deterioration_chance, (int, float)) or deterioration_chance < 0:
            deterioration_chance = 30
        
        roll = random.randint(1, 100)
        
        if roll <= recovery_chance:
            # Natural recovery!
            return RecoverySystem.recover_from_near_death(char_id, "natural")
        elif roll <= (recovery_chance + deterioration_chance):
            # Condition worsens
            return RecoverySystem.worsen_condition(char_id)
        else:
            # No change
            return {"status": "stable"}

    @staticmethod
    def recover_from_near_death(char_id: str, recovery_type: str) -> Dict[str, Any]:
        """Recover from near-death state."""
        near_death_path = os.path.join("./body/near_death", f"{char_id}.json")
        
        # Clear near-death status (with error handling)
        if os.path.exists(near_death_path):
            try:
                os.remove(near_death_path)
            except OSError as e:
                print(f"{Icons.WARNING} Could not remove near-death file: {e}")
        
        # Apply recovery healing
        body = CombatSystem.load_body(char_id)
        for zone in body:
            if body[zone]["health"] < 20:
                body[zone]["health"] = min(50, body[zone]["health"] + 15)
        
        CombatSystem.save_body(char_id, body)
        
        return {
            "status": "recovered",
            "type": recovery_type,
            "message": "You have stabilized and are no longer in critical condition!"
        }

    @staticmethod
    def worsen_condition(char_id: str) -> Dict[str, Any]:
        """Worsen near-death condition."""
        near_death_path = os.path.join("./body/near_death", f"{char_id}.json")
        
        # Load data with validation
        if not os.path.exists(near_death_path):
            # File doesn't exist, create critical condition
            return {"status": "death_risk", "cause": "shock"}
            
        near_death_data = load_json(near_death_path)
        
        # Validate data structure
        if not near_death_data or not isinstance(near_death_data, dict):
            # Corrupted data, assume critical condition
            return {"status": "death_risk", "cause": "shock"}
        
        # Get current values with fallbacks
        current_severity = near_death_data.get("severity", 2)
        recovery_chance = near_death_data.get("recovery_chance", 10)
        
        # Validate severity is a reasonable number
        if not isinstance(current_severity, int) or current_severity < 0 or current_severity > 4:
            current_severity = 2
        
        new_severity = max(0, current_severity - 1)  # Lower number = worse condition
        
        # Update data with validation
        near_death_data["severity"] = new_severity
        near_death_data["deterioration_chance"] = near_death_data.get("deterioration_chance", 30) + 10
        near_death_data["recovery_chance"] = max(5, recovery_chance - 5)
        
        # Ensure directory exists before saving
        os.makedirs(os.path.dirname(near_death_path), exist_ok=True)
        
        try:
            save_json(near_death_path, near_death_data)
        except Exception as e:
            print(f"{Icons.WARNING} Could not save near-death data: {e}")
        
        if new_severity <= 0:
            # Critical condition - roll for death
            cause = near_death_data.get("cause", "shock")
            return {"status": "death_risk", "cause": cause}
        
        # Get stage info safely
        stage_info = DeathSystem.NEAR_DEATH_STAGES.get(new_severity, {
            "name": "Unknown", 
            "description": "Condition unknown"
        })
        
        return {
            "status": "worsened",
            "new_severity": new_severity,
            "message": f"Your condition has worsened to {stage_info['name']}"
        }
    
# === HEALING SYSTEM ===
class HealingSystem:
    HEALING_METHODS = [
        ("Rest and Sleep", "Natural healing over time", 5, 0, "time"),
        ("First Aid Kit", "Basic medical supplies", 15, 1, "item"), 
        ("Herbal Medicine", "Traditional healing remedies", 12, 1, "item"),
        ("Medical Treatment", "Professional medical care", 25, 3, "professional"),
        ("Physical Therapy", "Rehabilitation for injuries", 20, 2, "professional"),
        ("Pain Medication", "Temporary relief and healing boost", 10, 1, "item"),
        ("Hot Bath", "Soothing warm water therapy", 8, 0, "time"),
        ("Meditation", "Mental healing and pain management", 6, 0, "time")
    ]
    
    HEALING_ITEMS = {
        "bandages": {"heal": 8, "cost": 1, "description": "Basic wound dressing"},
        "antiseptic": {"heal": 12, "cost": 2, "description": "Prevents infection"},
        "painkillers": {"heal": 15, "cost": 3, "description": "Reduces pain and inflammation"},
        "healing_potion": {"heal": 30, "cost": 5, "description": "Magical healing elixir"}
    }

    @staticmethod
    def natural_healing_tick(char_id: str) -> None:
        """Apply natural healing over time."""
        body = CombatSystem.load_body(char_id)
        healed_parts = []
        
        for zone in CombatSystem.BODY_ZONES:
            if body[zone]["health"] < 100:
                # Heal 1-3 points naturally per day
                heal_amount = random.randint(1, 3)
                old_health = body[zone]["health"]
                body[zone]["health"] = min(100, body[zone]["health"] + heal_amount)
                
                if body[zone]["health"] > old_health:
                    healed_parts.append((zone, old_health, body[zone]["health"]))
        
        if healed_parts:
            CombatSystem.save_body(char_id, body)
            return healed_parts
        return []

    @staticmethod
    def apply_healing(char_id: str, method_name: str, heal_amount: int, target_zone: str = None) -> Dict[str, Any]:
        """Apply healing to character."""
        body = CombatSystem.load_body(char_id)
        result = {
            "success": False,
            "healed_zones": [],
            "message": ""
        }
        
        if target_zone and target_zone in body:
            # Heal specific zone
            old_health = body[target_zone]["health"]
            body[target_zone]["health"] = min(100, body[target_zone]["health"] + heal_amount)
            
            if body[target_zone]["health"] > old_health:
                result["healed_zones"].append({
                    "zone": target_zone,
                    "old_health": old_health,
                    "new_health": body[target_zone]["health"],
                    "healed": body[target_zone]["health"] - old_health
                })
                result["success"] = True
                result["message"] = f"{method_name} healed {target_zone} for {body[target_zone]['health'] - old_health} points"
        else:
            # Heal all injured zones
            for zone in CombatSystem.BODY_ZONES:
                if body[zone]["health"] < 100:
                    old_health = body[zone]["health"]
                    # Distribute healing across injured parts
                    zone_heal = min(heal_amount // 2, 100 - body[zone]["health"])
                    body[zone]["health"] = min(100, body[zone]["health"] + zone_heal)
                    
                    if body[zone]["health"] > old_health:
                        result["healed_zones"].append({
                            "zone": zone,
                            "old_health": old_health,
                            "new_health": body[zone]["health"],
                            "healed": body[zone]["health"] - old_health
                        })
            
            if result["healed_zones"]:
                result["success"] = True
                result["message"] = f"{method_name} provided general healing"
        
        if result["success"]:
            CombatSystem.save_body(char_id, body)
        
        return result

    @staticmethod
    def healing_menu(player: Player) -> None:
        """Display healing options menu."""
        print_header("Healing Center", "🏥")
        
        # Check current injuries
        body = CombatSystem.load_body(player.data[0])
        injured_zones = [(zone, health["health"]) for zone, health in body.items() if health["health"] < 100]
        
        if not injured_zones:
            print(f"{Icons.SUCCESS} You are in perfect health! No healing needed.")
            return
        
        print_section("Current Injuries", "🩹")
        total_injury = 0
        for zone, health in injured_zones:
            damage = 100 - health
            total_injury += damage
            status = "🔴" if health < 20 else "🟡" if health < 50 else "🟠"
            bar = create_progress_bar(health, 100, 12)
            print(f"  {status} {zone.replace('_', ' ').title():<12}: {bar} ({damage} damage)")
        
        print(f"\n📊 Total Injury Level: {total_injury} points")
        
        print_section("Healing Options", "💊")
        for i, (name, desc, heal_power, cost, method_type) in enumerate(HealingSystem.HEALING_METHODS, 1):
            cost_str = f"${cost}" if cost > 0 else "Free"
            print(f"{i:2d}. {name:<20} - {desc} ({heal_power} HP, {cost_str})")
        
        print(f"\n{len(HealingSystem.HEALING_METHODS) + 1}. Back to main menu")
        
        while True:
            try:
                choice = int(input(f"\n🏥 Choose healing method (1-{len(HealingSystem.HEALING_METHODS) + 1}): "))
                if choice == len(HealingSystem.HEALING_METHODS) + 1:
                    return
                elif 1 <= choice <= len(HealingSystem.HEALING_METHODS):
                    method = HealingSystem.HEALING_METHODS[choice - 1]
                    HealingSystem.execute_healing(player, method, injured_zones)
                    break
            except ValueError:
                pass
            print(f"{Icons.ERROR} Invalid choice.")

    @staticmethod
    def execute_healing(player: Player, method: Tuple, injured_zones: List) -> None:
        """Execute the chosen healing method."""
        name, description, heal_power, cost, method_type = method
        
        # TODO: Implement cost system when you add currency
        # For now, we'll just apply the healing
        
        if method_type == "time":
            print(f"\n⏰ You spend time on {name.lower()}...")
            TimeManager.advance_time()  # Time-based healing advances time
        
        # Choose target zone for focused healing
        if len(injured_zones) > 1 and method_type in ["item", "professional"]:
            print(f"\n🎯 Choose which injury to focus on:")
            for i, (zone, health) in enumerate(injured_zones, 1):
                damage = 100 - health
                print(f"{i}. {zone.replace('_', ' ').title()} ({damage} damage)")
            print(f"{len(injured_zones) + 1}. Treat all injuries equally")
            
            while True:
                try:
                    target_choice = int(input("Target: "))
                    if target_choice == len(injured_zones) + 1:
                        target_zone = None
                        break
                    elif 1 <= target_choice <= len(injured_zones):
                        target_zone = injured_zones[target_choice - 1][0]
                        break
                except ValueError:
                    pass
                print(f"{Icons.ERROR} Invalid choice.")
        else:
            target_zone = None
        
        # Apply healing
        result = HealingSystem.apply_healing(player.data[0], name, heal_power, target_zone)
        
        if result["success"]:
            print(f"\n{Icons.SUCCESS} {result['message']}")
            
            for healed in result["healed_zones"]:
                zone_name = healed["zone"].replace('_', ' ').title()
                print(f"  🩹 {zone_name}: {healed['old_health']} → {healed['new_health']} (+{healed['healed']})")
                
            player.log_action("healing", f"Used {name}")
            
            # Update stats based on healing type
            if method_type == "time":
                # Resting improves willpower and focus
                stats = StatManager.get_stat_block(player.data[8])
                stats[9] = min(99, stats[9] + 1)  # Willpower
                stats[7] = min(99, stats[7] + 1)  # Focus
                player.data[8] = ''.join(f"{x:02d}" for x in stats)
                player.save()
                print(f"  {Icons.STATS} Rest also improved your mental state!")
                
        else:
            print(f"\n{Icons.WARNING} {name} had no effect. You may already be too healthy!")

# === INJURY REPORTING SYSTEM ===
class InjuryReporter:
    @staticmethod
    def get_injury_status(body: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get detailed injury status for reporting."""
        injuries = []
        
        for zone, data in body.items():
            health = data["health"]
            if health < 100:
                severity = InjuryReporter.get_injury_severity(health)
                injuries.append({
                    "zone": zone,
                    "health": health,
                    "damage": 100 - health,
                    "severity": severity["level"],
                    "description": severity["description"],
                    "icon": severity["icon"]
                })
        
        return injuries

    @staticmethod
    def get_injury_severity(health: int) -> Dict[str, str]:
        """Determine injury severity based on health."""
        if health >= 80:
            return {"level": "Minor", "description": "Light bruising", "icon": "🟢"}
        elif health >= 60:
            return {"level": "Moderate", "description": "Noticeable injury", "icon": "🟡"}
        elif health >= 40:
            return {"level": "Serious", "description": "Significant damage", "icon": "🟠"}
        elif health >= 20:
            return {"level": "Severe", "description": "Major injury", "icon": "🔴"}
        else:
            return {"level": "Critical", "description": "Life-threatening", "icon": "💀"}

    @staticmethod
    def display_injury_report(name: str, body: Dict[str, Any]) -> None:
        """Display comprehensive injury report."""
        injuries = InjuryReporter.get_injury_status(body)
        
        if not injuries:
            print(f"  💚 {name} is in perfect health!")
            return
        
        print(f"  🩹 {name}'s Injuries:")
        for injury in injuries:
            zone_name = injury["zone"].replace('_', ' ').title()
            print(f"    {injury['icon']} {zone_name:<12}: {injury['description']} ({injury['health']}/100 HP)")

# === ESCAPE AND SURRENDER SYSTEM ===
class EscapeSystem:
    ESCAPE_OUTCOMES = [
        "You slip away into the crowd!",
        "You duck around a corner and disappear!",
        "You sprint away through narrow alleys!",
        "You vault over a fence and escape!",
        "You blend into the shadows and vanish!",
        "You dash through a building and out the back!"
    ]
    
    FAILED_ESCAPE_OUTCOMES = [
        "You stumble while trying to run!",
        "Your opponent blocks your escape route!",
        "You trip over debris in your path!",
        "They grab you before you can get away!",
        "You run into a dead end!",
        "Your injuries slow you down too much!"
    ]

    @staticmethod
    def calculate_escape_chance(player_stats: List[int], player_body: Dict[str, Any], 
                               player_dynamic: Dict[str, Any], npc_stats: List[int]) -> int:
        """Calculate the chance of successful escape."""
        # Base escape chance from speed stat
        player_speed = player_stats[3]  # Speed stat
        npc_speed = npc_stats[3]
        
        # Base chance based on speed difference
        base_chance = 30 + (player_speed - npc_speed) * 2
        
        # Injury penalties
        injury_penalty = 0
        for zone, data in player_body.items():
            if data["health"] < 50:
                if zone in ["left_leg", "right_leg"]:
                    injury_penalty += 15  # Leg injuries hurt escape a lot
                elif zone == "torso":
                    injury_penalty += 10  # Torso injuries affect stamina
                else:
                    injury_penalty += 5   # Other injuries have minor impact
        
        # Confidence affects escape courage
        confidence_modifier = (player_dynamic["confidence"] - 50) // 10
        
        # Player experience helps with escape tactics
        experience_bonus = player_stats[4] // 10  # Experience stat
        
        final_chance = base_chance + confidence_modifier + experience_bonus - injury_penalty
        
        # Clamp between 5% and 85%
        return max(5, min(85, final_chance))

    @staticmethod
    def attempt_escape(combat_engine) -> bool:
        """Attempt to escape from combat."""
        print(f"\n{Icons.MOVE} {combat_engine.player[1]} attempts to flee!")
        
        # Calculate escape chance
        escape_chance = EscapeSystem.calculate_escape_chance(
            combat_engine.p_stats, combat_engine.player_body, 
            combat_engine.player_dynamic, combat_engine.n_stats
        )
        
        print(f"🎲 Escape chance: {escape_chance}%")
        
        # Roll for escape
        roll = random.randint(1, 100)
        print(f"🎲 Roll: {roll}")
        
        if roll <= escape_chance:
            # Successful escape!
            outcome = random.choice(EscapeSystem.ESCAPE_OUTCOMES)
            print(f"\n{Icons.SUCCESS} Success! {outcome}")
            
            # Boost confidence for successful escape
            combat_engine.update_confidence(
                combat_engine.player_dynamic, +15, "Successful escape", combat_engine.player[1]
            )
            
            # Log the escape
            if hasattr(combat_engine, 'player_obj'):
                combat_engine.player_obj.log_action("escape_combat", f"Escaped from {combat_engine.npc[1]}")
            
            return True
        else:
            # Failed escape!
            outcome = random.choice(EscapeSystem.FAILED_ESCAPE_OUTCOMES)
            print(f"\n{Icons.ERROR} Failed! {outcome}")
            
            # Confidence penalty for failed escape
            combat_engine.update_confidence(
                combat_engine.player_dynamic, -20, "Failed escape attempt", combat_engine.player[1]
            )
            
            # NPC gets confidence boost
            combat_engine.update_confidence(
                combat_engine.npc_dynamic, +10, "Prevented enemy escape", combat_engine.npc[1]
            )
            
            # Failed escape costs stamina and gives opponent free attack
            combat_engine.curr_stamina_p = max(0, combat_engine.curr_stamina_p - 15)
            print(f"💨 The escape attempt drained your stamina!")
            
            # Opponent gets a free counter-attack
            print(f"⚡ {combat_engine.npc[1]} takes advantage of your failed escape!")
            EscapeSystem.execute_punishment_attack(combat_engine)
            
            return False

    @staticmethod
    def execute_punishment_attack(combat_engine) -> None:
        """Execute a punishment attack when escape fails."""
        # Simple but brutal counter-attack
        damage = combat_engine.calc_random_damage(15, combat_engine.n_stats[0], 1.2, combat_engine.n_stats[4])
        target_zone = random.choice(["torso", "head", "left_arm", "right_arm"])
        
        combat_engine.player_body[target_zone]["health"] -= damage
        combat_engine.player_body[target_zone]["health"] = max(0, combat_engine.player_body[target_zone]["health"])
        
        print(f"{Icons.DAMAGE} {combat_engine.npc[1]} strikes your {target_zone} while you're vulnerable!")
        print(f"{Icons.CRITICAL} Damage dealt: {damage}")

# === SURRENDER SYSTEM ===
class SurrenderSystem:
    MERCY_FACTORS = {
        "empathy": 2.0,      # Empathetic NPCs more likely to show mercy
        "assertiveness": -1.0, # Assertive NPCs less likely to show mercy
        "intelligence": 1.0,   # Smart NPCs might see value in mercy
        "social": 1.5,        # Social NPCs understand mercy
        "wisdom": 1.2,        # Wise NPCs know when to stop
        "patience": 1.3       # Patient NPCs more forgiving
    }
    
    MERCY_RESPONSES = [
        "Fine, you're not worth my time anyway.",
        "Smart choice. Get out of here before I change my mind.",
        "I respect someone who knows when they're beaten.",
        "You show wisdom in surrender. Go, and remember this lesson.",
        "I'm not a monster. Just... stay down.",
        "Consider this a warning. Next time won't be so easy."
    ]
    
    BRUTAL_RESPONSES = [
        "Surrender won't save you now!",
        "Too late for mercy!",
        "You should have thought of that earlier!",
        "Begging won't help you now!",
        "I finish what I start!",
        "Weakness disgusts me!"
    ]

    @staticmethod
    def calculate_mercy_chance(npc_data: List[Any], combat_context: Dict[str, Any]) -> int:
        """Calculate chance that NPC will show mercy."""
        if len(npc_data) < 7:
            return 30  # Default mercy chance if no personality data
        
        # Get NPC personality stats
        personality_stats = StatManager.get_stat_block(npc_data[6])  # Personality string
        
        base_mercy = 25  # Base 25% chance
        
        # Personality modifiers
        if len(personality_stats) >= 6:
            empathy = personality_stats[0]
            assertiveness = personality_stats[1] 
            intelligence = personality_stats[3]
            social = personality_stats[6] if len(personality_stats) > 6 else 50
            wisdom = personality_stats[8] if len(personality_stats) > 8 else 50
            patience = personality_stats[9] if len(personality_stats) > 9 else 50
            
            mercy_score = (
                empathy * SurrenderSystem.MERCY_FACTORS["empathy"] +
                assertiveness * SurrenderSystem.MERCY_FACTORS["assertiveness"] +
                intelligence * SurrenderSystem.MERCY_FACTORS["intelligence"] +
                social * SurrenderSystem.MERCY_FACTORS["social"] +
                wisdom * SurrenderSystem.MERCY_FACTORS["wisdom"] +
                patience * SurrenderSystem.MERCY_FACTORS["patience"]
            ) / 100
            
            base_mercy += int(mercy_score)
        
        # Context modifiers
        if combat_context.get("player_health_percentage", 100) < 30:
            base_mercy += 15  # More mercy if player is badly hurt
        
        if combat_context.get("npc_confidence", 50) > 70:
            base_mercy += 10  # Confident NPCs can afford mercy
        
        if combat_context.get("fight_duration", 0) > 5:
            base_mercy -= 10  # Long fights make NPCs less merciful
        
        # Clamp between 5% and 80%
        return max(5, min(80, base_mercy))

    @staticmethod
    def handle_surrender(combat_engine) -> str:
        """Handle player surrender and determine NPC response."""
        print(f"\n🏳️ {combat_engine.player[1]} surrenders!")
        print(f"💬 \"I give up! Please, no more!\"")
        
        # Calculate combat context
        player_total_health = sum(data["health"] for data in combat_engine.player_body.values())
        player_health_percentage = (player_total_health / 600) * 100  # 6 zones * 100 HP each
        
        context = {
            "player_health_percentage": player_health_percentage,
            "npc_confidence": combat_engine.npc_dynamic["confidence"],
            "fight_duration": combat_engine.turn
        }
        
        # Calculate mercy chance
        mercy_chance = SurrenderSystem.calculate_mercy_chance(combat_engine.npc, context)
        
        print(f"\n🎲 {combat_engine.npc[1]} considers your surrender...")
        print(f"🤔 Mercy chance: {mercy_chance}%")
        
        # Roll for mercy
        roll = random.randint(1, 100)
        print(f"🎲 Roll: {roll}")
        
        if roll <= mercy_chance:
            # NPC shows mercy
            response = random.choice(SurrenderSystem.MERCY_RESPONSES)
            print(f"\n😌 {combat_engine.npc[1]}: \"{response}\"")
            print(f"{Icons.SUCCESS} You have been spared!")
            
            # Update confidence - mixed feelings about surrender
            combat_engine.update_confidence(
                combat_engine.player_dynamic, -10, "Surrendered but survived", combat_engine.player[1]
            )
            
            # Log the surrender
            if hasattr(combat_engine, 'player_obj'):
                combat_engine.player_obj.log_action("surrender_combat", f"Surrendered to {combat_engine.npc[1]} and was spared")
            
            return "mercy"
        else:
            # NPC continues the beating
            response = random.choice(SurrenderSystem.BRUTAL_RESPONSES)
            print(f"\n😠 {combat_engine.npc[1]}: \"{response}\"")
            print(f"{Icons.WARNING} Your surrender is ignored!")
            
            # Execute beating
            SurrenderSystem.execute_beating(combat_engine)
            
            # Log the brutal surrender
            if hasattr(combat_engine, 'player_obj'):
                combat_engine.player_obj.log_action("surrender_combat", f"Surrendered to {combat_engine.npc[1]} but was beaten anyway")
            
            return "brutal"

    @staticmethod
    def execute_beating(combat_engine) -> None:
        """Execute a beating when surrender is ignored."""
        print(f"\n💀 {combat_engine.npc[1]} continues the assault!")
        
        # Multiple attacks while player is helpless
        attacks = random.randint(2, 4)
        total_damage = 0
        
        for i in range(attacks):
            damage = combat_engine.calc_random_damage(12, combat_engine.n_stats[0], 1.0, combat_engine.n_stats[4])
            target_zone = random.choice(CombatSystem.BODY_ZONES)
            
            combat_engine.player_body[target_zone]["health"] -= damage
            combat_engine.player_body[target_zone]["health"] = max(0, combat_engine.player_body[target_zone]["health"])
            
            total_damage += damage
            
            zone_name = target_zone.replace('_', ' ')
            print(f"  💥 Strike {i+1}: {damage} damage to {zone_name}")
            
            sleep(0.5)  # Dramatic pause between strikes
        
        print(f"\n{Icons.CRITICAL} Total damage from beating: {total_damage}")
        
        # Massive confidence loss
        combat_engine.update_confidence(
            combat_engine.player_dynamic, -30, "Beaten while helpless", combat_engine.player[1]
        )
        
        # NPC gains confidence from dominance
        combat_engine.update_confidence(
            combat_engine.npc_dynamic, +20, "Dominated surrendered opponent", combat_engine.npc[1]
        )


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
    
    # Player Emergency when defeated
    def handle_player_medical_emergency(self, condition: Dict[str, Any]) -> None:
        """Handle player medical emergency during/after combat."""
        char_id = self.player[0]
        char_name = self.player[1]

        # Also get player data properly
        char_data = load_json(Config.PLAYER_PATH, [])
        if not char_data:
            print(f"{Icons.ERROR} Player data not found!")
            return
        
        if condition["status"] == "near_death":
            near_death_data = DeathSystem.trigger_near_death(
                char_id, char_name, condition["cause"], condition["severity"]
            )
            
            # Single medical intervention for near-death
            medical_choice = MedicalSystem.medical_intervention_menu(char_id, char_name)
            
            if medical_choice:
                result = MedicalSystem.apply_medical_care(char_id, char_name, medical_choice, near_death_data)
                if result["success"]:
                    print(f"\n{Icons.SUCCESS} Medical treatment successful! You have been stabilized.")
                    RecoverySystem.recover_from_near_death(char_id, medical_choice)
                else:
                    print(f"\n{Icons.ERROR} Medical treatment failed...")
                    death_result = DeathSystem.check_death_roll(char_id, condition["cause"], True)
                    if death_result["outcome"] == "death":
                        DeathConsequences.handle_character_death(char_id, char_name, condition["cause"])
            else:
                print(f"\n💀 No medical care chosen. Rolling for survival...")
                death_result = DeathSystem.check_death_roll(char_id, condition["cause"], False)
                if death_result["outcome"] == "death":
                    DeathConsequences.handle_player_death(death_result)
                else:
                    print(f"\n{Icons.SUCCESS} Against all odds, you survived!")
                    RecoverySystem.recover_from_near_death(char_id, "miracle")
        
        elif condition["status"] == "death_risk":
            # Handle ALL death risks in one medical intervention
            print(f"\n💀 Multiple critical conditions detected!")
            
            # List all the conditions
            for cause in condition["causes"]:
                print(f"   💀 {DeathSystem.DEATH_CAUSES[cause]['description']}")
            
            print(f"\n🏥 Emergency medical intervention required for multiple trauma!")
            medical_choice = MedicalSystem.medical_intervention_menu(char_id, char_name)
            medical_help = medical_choice is not None
            
            # Roll for survival against ALL conditions at once
            survived_all = True
            for cause in condition["causes"]:
                death_result = DeathSystem.check_death_roll(char_id, cause, medical_help)
                if death_result["outcome"] == "death":
                    print(f"\n💀 Fatal: {DeathSystem.DEATH_CAUSES[cause]['name']}")
                    DeathConsequences.handle_player_death(death_result)
                    return  # Player is dead, end here
                else:
                    print(f"\n{Icons.SUCCESS} Survived: {DeathSystem.DEATH_CAUSES[cause]['name']}")
            
            if survived_all:
                print(f"\n{Icons.SUCCESS} You survived all critical conditions!")

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
                # Check for near-death/death after combat
                player_condition = DeathSystem.check_death_conditions(self.player[0])
                if player_condition["status"] in ["death_risk", "near_death"]:
                    self.handle_player_medical_emergency(player_condition)
                break
            elif self.check_defeat(self.npc_body):
                print(f"\n{Icons.SUCCESS} {self.npc[1]} has been defeated!")
                                # Check for near-death/death after combat
                npc_condition = DeathSystem.check_death_conditions(self.npc[0])
                if npc_condition["status"] in ["death_risk", "near_death"]:
                    self.handle_npc_medical_emergency(npc_condition)
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
        """Display comprehensive combat status with injury reporting."""
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
        
        # Display body status with injury reporting
        CombatSystem.display_body_status(self.player[1], self.player_body)
        InjuryReporter.display_injury_report(self.player[1], self.player_body)
        
        CombatSystem.display_body_status(self.npc[1], self.npc_body)
        InjuryReporter.display_injury_report(self.npc[1], self.npc_body)

    def player_turn(self) -> None:
        """Handle player combat turn with full mechanics."""
        print(f"\n{Icons.PLAYER} {self.player[1]}'s turn!")
        
        # Check for panic/skip turn
        if random.randint(1, 100) <= self.player_dynamic["skip_turn_chance"]:
            print(f"😱 {self.player[1]} is too panicked to act!")
            self.cooldown_p += 200
            return True
        
        # Action choice menu
        print("\n⚔️ Choose your action:")
        print("1. 👊 Punch (Accurate, Moderate Damage)")
        print("2. 🦵 Kick (Harder, Less Accurate)")
        print("3. 🏃 Attempt to Escape")
        print("4. 🏳️ Surrender")
        
        while True:
            try:
                action = int(input("Action (1-4): "))
                if action in [1, 2, 3, 4]:
                    break
            except ValueError:
                pass
            print(f"{Icons.ERROR} Invalid input.")
        
        if action == 3:  # Escape attempt
            if EscapeSystem.attempt_escape(self):
                return False  # Combat ends if escape successful
            else:
                # Failed escape, turn continues with penalty already applied
                return True
        
        elif action == 4:  # Surrender
            result = SurrenderSystem.handle_surrender(self)
            return False  # Combat ends regardless of mercy/brutal outcome
        
        else:  # Normal attack (punch or kick)
            # Existing attack code with zone selection and prediction
            atk_type = action  # 1 for punch, 2 for kick
            
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
            return True


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
        
        # Update confidence (need fixing) Note: Weird logic when parried
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
        print("10. 🏥 Visit healing center")
        print("11. 🏋️ Go to the Gym")
        print("0. 🚪 Quit game")

    def handle_daily_choice(self) -> bool:
        """Handle player's daily choice. Returns False if player wants to quit."""
        self.display_daily_menu()
        
        while True:
            try:
                choice = int(input(f"\n{Icons.PLAYER} Choose your action (0-11): "))
                
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
                    
                elif choice == 10:  # Healing
                    HealingSystem.healing_menu(self.player)

                elif choice == 11:  # Gym
                    GymSystem.gym_interface(self.player)

                else:
                    print(f"{Icons.ERROR} Invalid choice. Please choose 0-9.")
                    continue
                
                # Advance time and simulate world (except for stats check)
                if choice not in [9, 10, 11]:
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