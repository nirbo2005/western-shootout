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
        mode_name = getattr(bet_mode_obj, '_name', getattr(bet_mode_obj, 'name', "base"))
        
        # Kondíciók kinyerése
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
        
        # 1. BIZTOSÍTÉK: Ha nincs ott a predeterminált dictionary, fallback a régire (biztonság)
        standard_weights = conditions.get("standard_weights", {"win": 284287, "draw": 147885, "lose": 553728})

        # ---------------------------------------------------------------------
        # SORSOLÁSI LOGIKA (Előre Determinált)
        # ---------------------------------------------------------------------
        if force_group:
            event_type = Events.GROUP_SHOOTOUT
        elif force_angel:
            event_type = Events.ANGEL_REVIVE
        else:
            total_std_weight = standard_weights["win"] + standard_weights["draw"] + standard_weights["lose"]
            if total_std_weight > 0:
                # Precíz húzás a megadott Excel darabszámokból
                rand_val = random.randint(1, total_std_weight)
                if rand_val <= standard_weights["draw"]:
                    event_type = Events.STANDARD_DRAW
                elif rand_val <= (standard_weights["draw"] + standard_weights["win"]):
                    event_type = Events.STANDARD_WIN
                else:
                    event_type = Events.STANDARD_LOSE
            else:
                # Vészhelyzeti fallback (ha hibás a config)
                event_type = Events.STANDARD_LOSE

        duel_steps = []
        p_hp, e_hp = 100.0, 100.0
        final_multiplier = 0.0
        winner = "NONE"

        # Célzott Group kimenetel
        target_group_outcome = None

        if event_type in [Events.STANDARD_WIN, Events.STANDARD_LOSE]:
            turn = Events.SHOOTER_PLAYER if random.random() > 0.5 else Events.SHOOTER_ENEMY
            
            while p_hp > 0 and e_hp > 0 and len(duel_steps) < 12:
                attacker = turn
                is_p_atk = (attacker == Events.SHOOTER_PLAYER)
                
                # Biztosíték: Garantált fejlövés a 10. lépésnél, ha muszáj befejezni
                if (event_type == Events.STANDARD_WIN and is_p_atk and len(duel_steps) >= 10) or \
                   (event_type == Events.STANDARD_LOSE and not is_p_atk and len(duel_steps) >= 10):
                    zone = Events.TARGET_HEAD
                    damage = e_hp if is_p_atk else p_hp
                else:
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
                zone = self.calc.get_hit_target(is_p_atk, conditions)
                damage = self.calc.calculate_damage(zone, not is_p_atk, conditions)
                
                # Halál megakadályozása mindkét oldalon
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
            matrix = getattr(self.config, "group_shootout_matrix", {}).get(mode_name, [])
            
            if matrix:
                outcomes, weights = zip(*[( (o[0], o[1], o[2]), o[3] ) for o in matrix])
                target_outcome = random.choices(outcomes, weights=weights, k=1)[0]
                
                num_enemies = target_outcome[0]
                target_rounds = target_outcome[1]
                final_multiplier = target_outcome[2]
                
                # Cél elmentése
                target_group_outcome = target_outcome
            else:
                num_enemies = random.randint(5, 8)
                target_rounds = random.randint(1, 6)
                final_multiplier = 10.0
            
            duel_steps, p_hp, winner = self.calc.generate_predetermined_group_shootout(
                num_enemies, target_rounds, conditions
            )

        if final_multiplier > self.config.wincap or force_wincap:
            final_multiplier = self.config.wincap
            
        final_multiplier = float(final_multiplier)
        
        # ---------------------------------------------------------------------
        # KIFIZETÉS JAVÍTÁSA (V4 COST-AWARE MODELL)
        # A nyeremény mindig az 1.0x-es alaptétre vonatkozik, nem a mód árára (cost)!
        # ---------------------------------------------------------------------
        total_win_amount = 1.0 * final_multiplier

        self.current_timeline = {
            "eventType": event_type, 
            "steps": duel_steps, 
            "winner": winner,
            "multiplier": final_multiplier 
        }
        
        if event_type == Events.GROUP_SHOOTOUT and target_group_outcome:
            self.current_timeline["target_outcome"] = {
                "enemies": target_group_outcome[0],
                "rounds": target_group_outcome[1]
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