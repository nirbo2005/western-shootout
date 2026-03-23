import random
from .game_events import WesternShootoutEvents as Events

class GameCalculations:
    def __init__(self, gamestate):
        self.gamestate = gamestate

    def get_hit_target(self, is_player_attacker: bool, conditions: dict) -> str:
        """Meghatározza a találat helyét a módosítók (Magnet) alapján."""
        magnet_mult = conditions.get("magnet_multiplier", 1.0)
        
        # Alap találati esélyek
        base_hit_chance = 0.6 if is_player_attacker else 0.4
        
        # Mágnes csak a játékos esélyeit növeli
        actual_hit_chance = base_hit_chance * (magnet_mult if is_player_attacker else 1.0)
        
        if random.random() > actual_hit_chance:
            return Events.TARGET_FAIL
            
        rand = random.random()
        if rand < 0.2: return Events.TARGET_HEAD
        if rand < 0.7: return Events.TARGET_BODY
        return Events.TARGET_LEGS

    def calculate_damage(self, zone: str, is_player_receiving: bool, conditions: dict) -> float:
        """Kiszámolja a sebzést a módosítók (Armor) alapján."""
        armor_mult = conditions.get("armor_multiplier", 1.0)

        damage_map = {
            Events.TARGET_HEAD: 100.0,
            Events.TARGET_BODY: 40.0,
            Events.TARGET_LEGS: 20.0,
            Events.TARGET_FAIL: 0.0
        }
        
        base_damage = damage_map.get(zone, 0.0)
        
        # Páncél csak a játékos által bekapott sebzést csökkenti
        if is_player_receiving:
            return base_damage * armor_mult
        return base_damage

    def calculate_group_shootout_hp(self, count: int) -> dict:
        """Generál HP-t az ellenségeknek a csoportos harchoz."""
        enemies = {}
        for i in range(count):
            enemies[f"ENEMY_{i+1}"] = 100.0
        return enemies