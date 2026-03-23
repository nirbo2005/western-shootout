import random
from .game_override import GameStateOverride
from src.events.events import EventConstants
from .game_calculations import GameCalculations
from .game_events import WesternShootoutEvents as Events

class GameState(GameStateOverride):
    def __init__(self, config):
        super().__init__(config)
        self.current_timeline = None
        self.calc = GameCalculations(self)

    def get_state_dict(self):
        state = super().get_state_dict()
        state["total_multiplier"] = self.win_manager.total_multiplier
        state["round_data"] = self.current_timeline
        return state

    def run_spin(self, sim, simulation_seed=None):
        self.reset_seed(sim)
        self.reset_book()
        
        self.spin_payout = 0
        self.free_payout = 0

        bet_mode_obj = self.get_current_betmode()
        cost = getattr(bet_mode_obj, '_cost', getattr(bet_mode_obj, 'cost', 1.0))
        
        # KONDÍCIÓK KINYERÉSE (Ezt kell használni a harcban!)
        conditions = {}
        dist = self.get_current_betmode_distributions()
        if hasattr(dist, 'conditions'):
            conditions = dist.conditions
        elif hasattr(dist, '_conditions'):
            conditions = dist._conditions
        elif isinstance(dist, dict) and 'conditions' in dist:
            conditions = dist['conditions']
        
        force_group = conditions.get("force_group_shootout", False)
        force_angel = conditions.get("force_angel_revive", False)
        force_wincap = conditions.get("force_wincap", False)
        
        draw_chance = conditions.get("base_draw_chance", 0.150)
        win_chance = conditions.get("base_win_chance", 0.290)

        if force_group:
            event_type = Events.GROUP_SHOOTOUT
        elif force_angel:
            event_type = Events.ANGEL_REVIVE
        else:
            rand_type = random.random()
            if rand_type < draw_chance:
                event_type = Events.STANDARD_DRAW
            elif rand_type < (draw_chance + win_chance):
                event_type = Events.STANDARD_WIN
            else:
                event_type = Events.STANDARD_LOSE

        duel_steps = []
        p_hp, e_hp = 100.0, 100.0
        final_multiplier = 0.0
        winner = "NONE"

        if event_type in [Events.STANDARD_WIN, Events.STANDARD_LOSE]:
            turn = Events.SHOOTER_PLAYER if random.random() > 0.5 else Events.SHOOTER_ENEMY
            
            while p_hp > 0 and e_hp > 0 and len(duel_steps) < 12:
                attacker = turn
                is_p_atk = (attacker == Events.SHOOTER_PLAYER)
                
                if (event_type == Events.STANDARD_WIN and is_p_atk and len(duel_steps) >= 10) or \
                   (event_type == Events.STANDARD_LOSE and not is_p_atk and len(duel_steps) >= 10):
                    zone = Events.TARGET_HEAD
                    damage = e_hp if is_p_atk else p_hp
                else:
                    # JAVÍTVA: bet_mode_obj helyett conditions!
                    zone = self.calc.get_hit_target(is_p_atk, conditions)
                    damage = self.calc.calculate_damage(zone, not is_p_atk, conditions)
                    
                    if event_type == Events.STANDARD_WIN and not is_p_atk:
                        if p_hp - damage <= 0:
                            zone = Events.TARGET_FAIL
                            damage = 0.0
                    elif event_type == Events.STANDARD_LOSE and is_p_atk:
                        if e_hp - damage <= 0:
                            zone = Events.TARGET_FAIL
                            damage = 0.0
                
                if zone != Events.TARGET_FAIL:
                    if is_p_atk:
                        e_hp = max(0.0, round(e_hp - damage, 1))
                    else:
                        p_hp = max(0.0, round(p_hp - damage, 1))

                duel_steps.append({
                    "Shooter": attacker,
                    "Target": zone,
                    "PlayerHP": float(p_hp),
                    "EnemyHP": float(e_hp)
                })
                turn = Events.SHOOTER_ENEMY if turn == Events.SHOOTER_PLAYER else Events.SHOOTER_PLAYER

            winner = Events.SHOOTER_PLAYER if e_hp <= 0 else Events.SHOOTER_ENEMY
            final_multiplier = 2.0 if winner == Events.SHOOTER_PLAYER else 0.0

        elif event_type == Events.STANDARD_DRAW:
            turn = Events.SHOOTER_PLAYER if random.random() > 0.5 else Events.SHOOTER_ENEMY
            draw_length = 12 
            
            while len(duel_steps) < draw_length:
                attacker = turn
                is_p_atk = (attacker == Events.SHOOTER_PLAYER)
                # JAVÍTVA: bet_mode_obj helyett conditions!
                zone = self.calc.get_hit_target(is_p_atk, conditions)
                damage = self.calc.calculate_damage(zone, not is_p_atk, conditions)
                
                if is_p_atk and (e_hp - damage <= 0):
                    zone = Events.TARGET_FAIL
                    damage = 0.0
                elif not is_p_atk and (p_hp - damage <= 0):
                    zone = Events.TARGET_FAIL
                    damage = 0.0
                
                if zone != Events.TARGET_FAIL:
                    if is_p_atk: e_hp = max(0.0, round(e_hp - damage, 1))
                    else: p_hp = max(0.0, round(p_hp - damage, 1))

                duel_steps.append({
                    "Shooter": attacker, "Target": zone, "PlayerHP": float(p_hp), "EnemyHP": float(e_hp)
                })
                turn = Events.SHOOTER_ENEMY if turn == Events.SHOOTER_PLAYER else Events.SHOOTER_PLAYER

            winner, final_multiplier = "DRAW", 1.0 

        elif event_type == Events.ANGEL_REVIVE:
            duel_steps = [
                {"Shooter": Events.SHOOTER_ENEMY, "Target": Events.TARGET_BODY, "PlayerHP": 50.0, "EnemyHP": 100.0},
                {"Shooter": Events.SHOOTER_ENEMY, "Target": Events.TARGET_BODY, "PlayerHP": 0.0, "EnemyHP": 100.0},
                {"Shooter": Events.SHOOTER_ANGEL, "Target": Events.SHOOTER_PLAYER, "PlayerHP": 100.0, "EnemyHP": 100.0},
                {"Shooter": Events.SHOOTER_PLAYER, "Target": Events.TARGET_HEAD, "PlayerHP": 100.0, "EnemyHP": 0.0}
            ]
            winner, final_multiplier = Events.SHOOTER_PLAYER, 5.0

        elif event_type == Events.GROUP_SHOOTOUT:
            num_enemies = random.randint(conditions.get("min_enemies", 5), conditions.get("max_enemies", 8))
            enemies = self.calc.calculate_group_shootout_hp(num_enemies)
            killed, survived_rounds = 0, 0
            
            group_multipliers = {
                5: [0.0, 5.0, 10.0, 25.0, 60.0, 150.0, 300.0],
                6: [0.0, 6.0, 15.0, 35.0, 80.0, 200.0, 400.0],
                7: [0.0, 7.0, 20.0, 50.0, 120.0, 300.0, 500.0],
                8: [0.0, 8.0, 25.0, 60.0, 150.0, 400.0, 500.0]
            }
            
            while p_hp > 0 and survived_rounds < 6:
                alive_enemies = [e for e, hp in enemies.items() if hp > 0]
                if not alive_enemies: break
                    
                target_enemy = random.choice(alive_enemies)
                # JAVÍTVA: conditions használata
                zone = self.calc.get_hit_target(True, conditions)
                if force_wincap: zone = Events.TARGET_HEAD
                    
                damage = self.calc.calculate_damage(zone, False, conditions)
                if zone != Events.TARGET_FAIL:
                    enemies[target_enemy] = max(0.0, round(enemies[target_enemy] - damage, 1))
                    if enemies[target_enemy] == 0.0: killed += 1
                        
                duel_steps.append({
                    "Shooter": Events.SHOOTER_PLAYER, "Target": zone,
                    "PlayerHP": float(p_hp), "EnemyHP": float(enemies.get(target_enemy, 0.0)),
                    "enemiesHP": enemies.copy()
                })
                
                alive_enemies = [e for e, hp in enemies.items() if hp > 0]
                for shooting_enemy in alive_enemies:
                    if p_hp <= 0: break
                    # JAVÍTVA: conditions használata
                    e_zone = self.calc.get_hit_target(False, conditions)
                    if force_wincap: e_zone = Events.TARGET_FAIL
                        
                    e_damage = self.calc.calculate_damage(e_zone, True, conditions)
                    if e_zone != Events.TARGET_FAIL:
                        p_hp = max(0.0, round(p_hp - e_damage, 1))
                        
                    duel_steps.append({
                        "Shooter": Events.SHOOTER_ENEMY, "ShooterID": shooting_enemy,
                        "Target": e_zone, "PlayerHP": float(p_hp), "EnemyHP": float(enemies[shooting_enemy]),
                        "enemiesHP": enemies.copy()
                    })
                    
                if p_hp > 0: survived_rounds += 1

            mult_list = group_multipliers.get(num_enemies, group_multipliers[5])
            safe_idx = min(survived_rounds, len(mult_list) - 1)
            final_multiplier = mult_list[safe_idx] + (killed * 3.0)
            winner = Events.SHOOTER_PLAYER if killed == num_enemies else Events.SHOOTER_ENEMY

        if final_multiplier > self.config.wincap or force_wincap:
            final_multiplier = self.config.wincap
            
        final_multiplier = float(final_multiplier)
        total_win_amount = cost * final_multiplier

        self.current_timeline = {
            "eventType": event_type, 
            "steps": duel_steps, 
            "winner": winner,
            "multiplier": final_multiplier 
        }

        self.spin_payout = total_win_amount
        self.win_manager.update_spinwin(total_win_amount)
        self.win_manager.update_gametype_wins(self.win_manager.base_game_mode)
        
        self.book.add_event({
            "index": len(self.book.events),
            "type": EventConstants.WIN_DATA.value,
            "numberRolled": int(sim + 1),
            "round_data": self.current_timeline
        })

        self.update_final_win()
        self.imprint_wins()

    def run_freespin(self, sim, simulation_seed=None):
        self.reset_seed(sim)
        self.reset_book()
        self.update_final_win()
        self.imprint_wins()