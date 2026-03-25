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

    def generate_predetermined_group_shootout(self, num_enemies: int, target_rounds: int, conditions: dict):
        """
        Előre determinált szimuláció. A golyók úgy vannak manipulálva, 
        hogy a játékos pontosan 'target_rounds' kört éljen túl, 
        és pontosan annyi ellenfelet öljön meg, amit az elvárt szorzó megkíván.
        """
        duel_steps = []
        p_hp = 100.0
        enemies = self.calculate_group_shootout_hp(num_enemies)
        
        # Matematikai Cél: Mennyi embert kell megölnie? (0.8 / kör arány, maximum num_enemies)
        target_kills = min(int(target_rounds * 0.8), num_enemies)
        kills_achieved = 0

        # Lejátszuk a köröket a halálos körig bezárólag (target_rounds + 1)
        for round_idx in range(1, target_rounds + 2):
            if round_idx > 6:
                break # Maximum 6 körös a játék
                
            alive_enemies = [e for e, hp in enemies.items() if hp > 0]
            if not alive_enemies:
                break # Nincs több ellenfél
                
            # --------------------------
            # 1. JÁTÉKOS LŐ (Player Turn)
            # --------------------------
            target_enemy = random.choice(alive_enemies)
            zone = self.get_hit_target(True, conditions)
            
            # Célzott Gyilkosság Manipuláció
            # Ha el vagyunk maradva a kill rátával, kényszerítünk egy garantált gyilkosságot
            rounds_left = target_rounds - round_idx + 1
            kills_needed = target_kills - kills_achieved
            
            if kills_needed > 0 and (random.random() < (kills_needed / max(1, rounds_left)) or round_idx == target_rounds):
                zone = Events.TARGET_HEAD
                damage = enemies[target_enemy] # Instant kill sebzés
            else:
                damage = self.calculate_damage(zone, False, conditions)
            
            # Sebzés kiosztása
            if zone != Events.TARGET_FAIL:
                enemies[target_enemy] = max(0.0, round(enemies[target_enemy] - damage, 1))
                if enemies[target_enemy] == 0.0:
                    kills_achieved += 1
                    
            duel_steps.append({
                "Shooter": Events.SHOOTER_PLAYER,
                "Target": zone,
                "PlayerHP": float(p_hp),
                "EnemyHP": float(enemies[target_enemy]),
                "enemiesHP": enemies.copy()
            })
            
            # Frissítjük az élő ellenfeleket a visszalövéshez
            alive_enemies = [e for e, hp in enemies.items() if hp > 0]
            if not alive_enemies:
                break
                
            # --------------------------
            # 2. ELLENFELEK LŐNEK (Enemy Turn)
            # --------------------------
            must_die = (round_idx == target_rounds + 1)
            
            for i, shooting_enemy in enumerate(alive_enemies):
                e_zone = self.get_hit_target(False, conditions)
                e_damage = self.calculate_damage(e_zone, True, conditions)
                
                if must_die:
                    # KIVÉGZÉSI FÁZIS: A játékosnak meg kell halnia ebben a körben
                    if i == len(alive_enemies) - 1 and p_hp - e_damage > 0:
                        e_zone = Events.TARGET_HEAD
                        e_damage = self.calculate_damage(e_zone, True, conditions)
                        # Biztosíték az Armor mód ellen (ahol a fejlövés is csak 50 HP)
                        if p_hp - e_damage > 0: 
                            e_damage = p_hp 
                else:
                    # TÚLÉLÉSI FÁZIS: A játékosnak túl kell élnie ezt a kört
                    if p_hp - e_damage <= 0:
                        e_zone = Events.TARGET_FAIL # A halálos találatot "Mellé"-re írjuk
                        e_damage = 0.0
                        
                if e_zone != Events.TARGET_FAIL:
                    p_hp = max(0.0, round(p_hp - e_damage, 1))
                    
                duel_steps.append({
                    "Shooter": Events.SHOOTER_ENEMY,
                    "ShooterID": shooting_enemy,
                    "Target": e_zone,
                    "PlayerHP": float(p_hp),
                    "EnemyHP": float(enemies[shooting_enemy]),
                    "enemiesHP": enemies.copy()
                })
                
                if p_hp <= 0:
                    break # A játékos meghalt, vége az ellenséges körnek

            if p_hp <= 0:
                break # Vége az egész minigame-nek

        winner = Events.SHOOTER_PLAYER if p_hp > 0 else Events.SHOOTER_ENEMY
        return duel_steps, p_hp, winner