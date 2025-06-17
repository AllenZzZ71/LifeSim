import os
import json

# Corrected paths based on your structure
npcs_folder = "./chars"
world_state_file = "./world/world_state.json"

# Initialize centralized world map
world_map = {}

# Loop through each NPC file
for npc_file in os.listdir(npcs_folder):
    if npc_file.endswith(".json"):
        npc_path = os.path.join(npcs_folder, npc_file)
        with open(npc_path, 'r') as f:
            data = json.load(f)

        # Assume structure: [id, name, ..., current_location at index 5 or 6]
        current_location = data[5] if len(data) > 5 else "Unknown"

        # Add to world map
        if current_location not in world_map:
            world_map[current_location] = []
        world_map[current_location].append(data[0])  # NPC ID

# Save centralized world map
os.makedirs(os.path.dirname(world_state_file), exist_ok=True)
with open(world_state_file, 'w') as f:
    json.dump(world_map, f, indent=2)

print(f"✅ Saved centralized world map with {len(world_map)} locations to: {world_state_file}")
