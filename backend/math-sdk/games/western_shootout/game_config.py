from pathlib import Path
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.config import BetMode

class GameConfig(Config):
    def __init__(self, game_id: str = "stake_western_95"):
        super().__init__()
        self.game_id = game_id
        
        current_dir = Path(__file__).resolve().parent
        lib_dir = current_dir / "library"
        
        self.library_path = str(lib_dir)
        self.config_path = str(lib_dir / "configs")
        self.book_path = str(lib_dir / "books")
        self.force_path = str(lib_dir / "forces")
        self.lut_path = str(lib_dir / "lookup_tables")
        
        for p in [self.config_path, self.book_path, self.force_path, self.lut_path]:
            Path(p).mkdir(parents=True, exist_ok=True)

        self.provider_number = 0
        self.working_name = "Western Shootout"
        self.wincap = 500.0
        self.win_type = "other"
        self.rtp = 0.9600
        
        self.construct_paths(self.game_id)

        self.num_reels = 0
        self.num_rows = []

        self.bet_modes = [
            BetMode(
                name="base",
                cost=1.0,
                rtp=0.9600,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="standard_duel",
                        quota=0.9859,
                        conditions={
                            "reel_weights": {},
                            "rtp_step": 0,
                            "magnet_multiplier": 1.0,
                            "armor_multiplier": 1.0,
                            "force_group_shootout": False,
                            "force_angel_revive": False,
                            "force_wincap": False,
                            "base_draw_chance": 0.150,
                            "base_win_chance": 0.345
                        },
                    ),
                    Distribution(
                        criteria="angel_revive",
                        quota=0.0100, 
                        conditions={
                            "reel_weights": {},
                            "rtp_step": 0,
                            "magnet_multiplier": 1.0,
                            "armor_multiplier": 1.0,
                            "force_group_shootout": False,
                            "force_angel_revive": True,
                            "force_wincap": False
                        },
                    ),
                    Distribution(
                        criteria="group_shootout",
                        quota=0.0040, 
                        conditions={
                            "reel_weights": {},
                            "rtp_step": 0,
                            "magnet_multiplier": 1.0,
                            "armor_multiplier": 1.0,
                            "force_group_shootout": True,
                            "min_enemies": 5,
                            "max_enemies": 8,
                            "force_wincap": False
                        },
                    ),
                    Distribution(
                        criteria="wincap",
                        quota=0.0001,
                        win_criteria=self.wincap,
                        conditions={
                            "reel_weights": {},
                            "rtp_step": 0,
                            "magnet_multiplier": 1.0,
                            "armor_multiplier": 1.0,
                            "force_group_shootout": False,
                            "force_wincap": True
                        },
                    ),
                ],
            ),
            BetMode(
                name="armor",
                cost=1.5,
                rtp=0.9600,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="standard_duel",
                        quota=0.9879,
                        conditions={
                            "reel_weights": {},
                            "rtp_step": 0,
                            "magnet_multiplier": 1.0,
                            "armor_multiplier": 0.5,
                            "force_group_shootout": False,
                            "force_angel_revive": False,
                            "force_wincap": False,
                            "base_draw_chance": 0.150,
                            "base_win_chance": 0.384
                        },
                    ),
                    Distribution(
                        criteria="angel_revive",
                        quota=0.0100,
                        conditions={
                            "reel_weights": {},
                            "rtp_step": 0,
                            "magnet_multiplier": 1.0,
                            "armor_multiplier": 0.5,
                            "force_group_shootout": False,
                            "force_angel_revive": True,
                            "force_wincap": False
                        },
                    ),
                    Distribution(
                        criteria="group_shootout",
                        quota=0.0020,
                        conditions={
                            "reel_weights": {},
                            "rtp_step": 0,
                            "magnet_multiplier": 1.0,
                            "armor_multiplier": 0.5,
                            "force_group_shootout": True,
                            "min_enemies": 5,
                            "max_enemies": 8,
                            "force_wincap": False
                        },
                    ),
                    Distribution(
                        criteria="wincap",
                        quota=0.0001,
                        win_criteria=self.wincap,
                        conditions={
                            "reel_weights": {},
                            "rtp_step": 0,
                            "magnet_multiplier": 1.0,
                            "armor_multiplier": 0.5,
                            "force_group_shootout": False,
                            "force_wincap": True
                        },
                    ),
                ],
            ),
            BetMode(
                name="magnet",
                cost=1.8,
                rtp=0.9600,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="standard_duel",
                        quota=0.9874,
                        conditions={
                            "reel_weights": {},
                            "rtp_step": 0,
                            "magnet_multiplier": 1.5,
                            "armor_multiplier": 1.0,
                            "force_group_shootout": False,
                            "force_angel_revive": False,
                            "force_wincap": False,
                            "base_draw_chance": 0.150,
                            "base_win_chance": 0.408
                        },
                    ),
                    Distribution(
                        criteria="angel_revive",
                        quota=0.0100,
                        conditions={
                            "reel_weights": {},
                            "rtp_step": 0,
                            "magnet_multiplier": 1.5,
                            "armor_multiplier": 1.0,
                            "force_group_shootout": False,
                            "force_angel_revive": True,
                            "force_wincap": False
                        },
                    ),
                    Distribution(
                        criteria="group_shootout",
                        quota=0.0025,
                        conditions={
                            "reel_weights": {},
                            "rtp_step": 0,
                            "magnet_multiplier": 1.5,
                            "armor_multiplier": 1.0,
                            "force_group_shootout": True,
                            "min_enemies": 5,
                            "max_enemies": 8,
                            "force_wincap": False
                        },
                    ),
                    Distribution(
                        criteria="wincap",
                        quota=0.0001,
                        win_criteria=self.wincap,
                        conditions={
                            "reel_weights": {},
                            "rtp_step": 0,
                            "magnet_multiplier": 1.5,
                            "armor_multiplier": 1.0,
                            "force_group_shootout": False,
                            "force_wincap": True
                        },
                    ),
                ],
            ),
            BetMode(
                name="extreme",
                cost=2.3,
                rtp=0.9600,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="standard_duel",
                        quota=0.9888,
                        conditions={
                            "reel_weights": {},
                            "rtp_step": 0,
                            "magnet_multiplier": 1.5,
                            "armor_multiplier": 0.5,
                            "force_group_shootout": False,
                            "force_wincap": False,
                            "base_draw_chance": 0.150,
                            "base_win_chance": 0.413
                        },
                    ),
                    Distribution(
                        criteria="group_shootout",
                        quota=0.0010,
                        conditions={
                            "reel_weights": {},
                            "rtp_step": 0,
                            "magnet_multiplier": 1.5,
                            "armor_multiplier": 0.5,
                            "force_group_shootout": True,
                            "min_enemies": 5,
                            "max_enemies": 8,
                            "force_wincap": False
                        },
                    ),
                    Distribution(
                        criteria="angel_revive",
                        quota=0.0100,
                        conditions={
                            "reel_weights": {},
                            "rtp_step": 0,
                            "magnet_multiplier": 1.5,
                            "armor_multiplier": 0.5,
                            "force_group_shootout": False,
                            "force_angel_revive": True,
                            "force_wincap": False
                        },
                    ),
                    Distribution(
                        criteria="wincap",
                        quota=0.0002,
                        win_criteria=self.wincap,
                        conditions={
                            "reel_weights": {},
                            "rtp_step": 0,
                            "magnet_multiplier": 1.5,
                            "armor_multiplier": 0.5,
                            "force_group_shootout": False,
                            "force_wincap": True
                        },
                    ),
                ],
            ),
        ]

    def normalize_quotas(self):
        for mode in self.bet_modes:
            total_quota = sum(dist.quota for dist in mode.distributions)
            if total_quota > 0:
                for dist in mode.distributions:
                    dist.quota /= total_quota

    def calibrate_all_modes_binary_search(self, get_rtp_callback, target_rtp: float = 0.9600, tolerance: float = 0.0001, max_iter: int = 50):
        self.normalize_quotas()
        
        for mode in self.bet_modes:
            low = 0.00001
            high = 0.99999
            
            target_dist = next((d for d in mode.distributions if d.criteria == "standard_duel"), None)
            if not target_dist:
                continue

            for _ in range(max_iter):
                mid = (low + high) / 2.0
                target_dist.conditions["base_win_chance"] = round(mid, 5)
                
                current_rtp = get_rtp_callback(mode.name)
                
                if abs(current_rtp - target_rtp) <= tolerance:
                    break
                    
                if current_rtp < target_rtp:
                    low = mid
                else:
                    high = mid