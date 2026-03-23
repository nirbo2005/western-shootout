import random
from typing import Dict, Optional

ZONE_MULTIPLIERS = {
    "HEAD": 1.5,
    "BODY": 1.0,
    "LEGS": 0.8,
    "FAIL": 0.0
}

# Group Shootout kifizetési tábla 5-8 játékosra (96% RTP kalibráció)
# A maximális túlélési bónuszok (a kill bónuszok nélkül, amik +3x per kill)
MAX_PAYOUTS = {
    5: 300.0,
    6: 400.0,
    7: 500.0,
    8: 500.0
}

def get_hit_chance(is_magnet: bool, is_player: bool) -> float:
    """Mágnes esetén +50% találati esély a játékosnak a base 60%-ra."""
    base_chance = 0.60 if is_player else 0.40
    magnet_mult = 1.5 if is_magnet else 1.0
    
    if is_player:
        return min(1.0, base_chance * magnet_mult)
    return base_chance

def get_target_zone(is_magnet: bool, is_player: bool) -> str:
    """Találati zóna kiválasztása."""
    if is_player and is_magnet:
        return random.choices(["HEAD", "BODY", "LEGS"], weights=[0.40, 0.50, 0.10])[0]
    return random.choices(["HEAD", "BODY", "LEGS"], weights=[0.20, 0.60, 0.20])[0]

def calculate_base_damage(zone: str) -> float:
    """Alapsebzés a zónák alapján."""
    if zone == "HEAD": return 100.0
    if zone == "BODY": return 40.0
    if zone == "LEGS": return 20.0
    return 0.0

def apply_armor(damage: float, is_armor: bool, is_player_taking_damage: bool) -> float:
    """Páncél módosító: 50%-kal csökkenti a bekapott sebzést."""
    if is_player_taking_damage and is_armor:
        return round(damage * 0.5, 1)
    return damage

def select_dead_eye_target(enemies: Dict[str, float]) -> Optional[str]:
    """Élő ellenség kiválasztása."""
    alive = [k for k, v in enemies.items() if v > 0]
    return random.choice(alive) if alive else None

def calculate_group_shootout_multiplier(total_enemies: int, survived_rounds: int, enemies_defeated: int) -> float:
    """Progresszív szorzó a Group Shootout minigame-hez."""
    group_multipliers = {
        5: [0.0, 5.0, 10.0, 25.0, 60.0, 150.0, 300.0],
        6: [0.0, 6.0, 15.0, 35.0, 80.0, 200.0, 400.0],
        7: [0.0, 7.0, 20.0, 50.0, 120.0, 300.0, 500.0],
        8: [0.0, 8.0, 25.0, 60.0, 150.0, 400.0, 500.0]
    }
    
    mult_list = group_multipliers.get(total_enemies, group_multipliers[5])
    safe_idx = min(survived_rounds, len(mult_list) - 1)
    
    survival_bonus = mult_list[safe_idx]
    kill_bonus = enemies_defeated * 3.0
    
    return min(500.0, survival_bonus + kill_bonus)

def calculate_draw_payout(cost: float) -> float:
    """Döntetlen esetén 1x szorzó (tét visszajár)."""
    return round(cost * 1.0, 2)