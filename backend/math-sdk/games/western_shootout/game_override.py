from src.state.state import GeneralGameState as StakeEngineState
from .game_executables import GameExecutables
from src.calculations.statistics import get_random_outcome

class GameStateOverride(StakeEngineState):
    """
    This class is used to override or extend universal state.py functions.
    e.g: A specific game may have custom book properties to reset
    """

    def __init__(self, config):
        super().__init__(config)
        self.executables = GameExecutables(self)

    def reset_book(self):
        """Reset game specific properties"""
        super().reset_book()

    def assign_special_sym_function(self):
        pass

    def check_game_repeat(self):
        if not self.repeat:
            bet_mode = self.get_current_betmode()
            if hasattr(bet_mode, 'distributions') and len(bet_mode.distributions) > 0:
                win_criteria = bet_mode.distributions[0].win_criteria
                if win_criteria is not None and self.final_win != win_criteria:
                    self.repeat = True

    def get_current_bet_cost(self):
        """Returns the actual cost based on bet mode multipliers"""
        bet_mode = self.get_current_betmode()
        # Biztonságos elérés: az SDK belsőleg _cost-ra nevezi át, de a fallback a cost
        return getattr(bet_mode, '_cost', getattr(bet_mode, 'cost', 1.0))

    def update_final_win(self):
        """Ensure final win is calculated in currency units, not just multipliers"""
        # Kényszerített szinkronizáció az Assertion hiba elkerülésére az SDK alaposztályában
        if not hasattr(self, 'free_payout'):
            self.free_payout = 0
            
        # Alapértelmezett kifizetés számítás a win_manager alapján
        self.final_win = round(self.win_manager.spin_win + self.free_payout, 2)
        
        # Wincap validáció
        if self.final_win > self.config.wincap:
            self.final_win = self.config.wincap
            
        # A szorzó (multiplier) frissítése a kifizetés alapján
        cost = self.get_current_bet_cost()
        self.final_multiplier = round(self.final_win / cost, 4) if cost > 0 else 0