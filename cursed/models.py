import random

def generate_rarity() -> str:
    """Assigns a rarity tier using weighted random selection."""
    tiers = ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Forbidden"]
    weights = [45, 27, 16, 8, 3, 1]
    return random.choices(tiers, weights=weights, k=1)[0]

def generate_stats() -> dict:
    """Generates the specific stats required for the redesign."""
    return {
        "Chaotic-ness": random.randint(0, 100),
        "Grass Meter": random.randint(0, 100)
    }
