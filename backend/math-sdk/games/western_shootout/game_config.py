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
        self.target_rtp = 0.9600
        self.rtp = self.target_rtp
        
        self.construct_paths(self.game_id)

        self.num_reels = 0
        self.num_rows = []

        # ---------------------------------------------------------------------
        # PREDETERMINÁLT MÁTRIX: Group Shootout pontos darabszámok 1 Millióból
        # V4: Cost-Aware eloszlás. (Hitrate drasztikusan módosítva a költségekhez)
        # Formátum: (Ellenfelek száma, Túlélés köre, Fix Szorzó, Darabszám)
        # ---------------------------------------------------------------------
        self.group_shootout_matrix = {
            "base": [
                (5, 1, 8.0, 499), (5, 2, 16.0, 250), (5, 3, 29.0, 120), (5, 4, 62.0, 80), (5, 5, 112.0, 40), (5, 6, 265.0, 10),
                (6, 1, 9.0, 501), (6, 2, 21.0, 250), (6, 3, 39.0, 120), (6, 4, 82.0, 80), (6, 5, 165.0, 40), (6, 6, 338.0, 10),
                (7, 1, 10.0, 500), (7, 2, 26.0, 250), (7, 3, 54.0, 120), (7, 4, 112.0, 80), (7, 5, 215.0, 40), (7, 6, 421.0, 10),
                (8, 1, 11.0, 500), (8, 2, 31.0, 250), (8, 3, 69.0, 120), (8, 4, 145.0, 80), (8, 5, 278.0, 40), (8, 6, 500.0, 10),
            ],
            "armor": [
                (5, 1, 8.0, 200), (5, 2, 16.0, 200), (5, 3, 29.0, 200), (5, 4, 62.0, 150), (5, 5, 112.0, 100), (5, 6, 265.0, 50),
                (6, 1, 9.0, 200), (6, 2, 21.0, 200), (6, 3, 39.0, 200), (6, 4, 82.0, 150), (6, 5, 165.0, 100), (6, 6, 338.0, 50),
                (7, 1, 10.0, 200), (7, 2, 26.0, 200), (7, 3, 54.0, 200), (7, 4, 112.0, 150), (7, 5, 215.0, 100), (7, 6, 421.0, 50),
                (8, 1, 11.0, 200), (8, 2, 31.0, 200), (8, 3, 69.0, 200), (8, 4, 145.0, 150), (8, 5, 278.0, 100), (8, 6, 500.0, 50),
            ],
            "magnet": [
                (5, 1, 8.0, 300), (5, 2, 16.0, 250), (5, 3, 29.0, 200), (5, 4, 62.0, 150), (5, 5, 112.0, 80), (5, 6, 265.0, 20),
                (6, 1, 9.0, 300), (6, 2, 21.0, 250), (6, 3, 39.0, 200), (6, 4, 82.0, 150), (6, 5, 165.0, 80), (6, 6, 338.0, 20),
                (7, 1, 10.0, 300), (7, 2, 26.0, 250), (7, 3, 54.0, 200), (7, 4, 112.0, 150), (7, 5, 215.0, 80), (7, 6, 421.0, 20),
                (8, 1, 11.0, 300), (8, 2, 31.0, 250), (8, 3, 69.0, 200), (8, 4, 145.0, 150), (8, 5, 278.0, 80), (8, 6, 500.0, 20),
            ],
            "extreme": [
                (5, 1, 8.0, 150), (5, 2, 16.0, 200), (5, 3, 29.0, 300), (5, 4, 62.0, 400), (5, 5, 112.0, 250), (5, 6, 265.0, 100),
                (6, 1, 9.0, 150), (6, 2, 21.0, 200), (6, 3, 39.0, 300), (6, 4, 82.0, 400), (6, 5, 165.0, 250), (6, 6, 338.0, 100),
                (7, 1, 10.0, 150), (7, 2, 26.0, 200), (7, 3, 54.0, 300), (7, 4, 112.0, 400), (7, 5, 215.0, 250), (7, 6, 421.0, 100),
                (8, 1, 11.0, 150), (8, 2, 31.0, 200), (8, 3, 69.0, 300), (8, 4, 145.0, 400), (8, 5, 278.0, 250), (8, 6, 500.0, 100),
            ]
        }

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
                        quota=0.9859, # 985,900 db
                        conditions={
                            "reel_weights": {}, "rtp_step": 0, "magnet_multiplier": 1.0, "armor_multiplier": 1.0,
                            "force_group_shootout": False, "force_angel_revive": False, "force_wincap": False,
                            "standard_weights": {"win": 284287, "draw": 147885, "lose": 553728}
                        },
                    ),
                    Distribution(
                        criteria="angel_revive", quota=0.0100, # 10,000 db
                        conditions={"reel_weights": {}, "rtp_step": 0, "magnet_multiplier": 1.0, "armor_multiplier": 1.0, "force_group_shootout": False, "force_angel_revive": True, "force_wincap": False},
                    ),
                    Distribution(
                        criteria="group_shootout", quota=0.0040, # 4,000 db
                        conditions={"reel_weights": {}, "rtp_step": 0, "magnet_multiplier": 1.0, "armor_multiplier": 1.0, "force_group_shootout": True, "force_wincap": False},
                    ),
                    Distribution(
                        criteria="wincap", quota=0.0001, win_criteria=self.wincap, # 100 db
                        conditions={"reel_weights": {}, "rtp_step": 0, "magnet_multiplier": 1.0, "armor_multiplier": 1.0, "force_group_shootout": False, "force_wincap": True},
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
                        quota=0.98125, # 981,250 db
                        conditions={
                            "reel_weights": {}, "rtp_step": 0, "magnet_multiplier": 1.0, "armor_multiplier": 0.5,
                            "force_group_shootout": False, "force_angel_revive": False, "force_wincap": False,
                            "standard_weights": {"win": 436025, "draw": 140000, "lose": 405225}
                        },
                    ),
                    Distribution(
                        criteria="angel_revive", quota=0.0150, # 15,000 db
                        conditions={"reel_weights": {}, "rtp_step": 0, "magnet_multiplier": 1.0, "armor_multiplier": 0.5, "force_group_shootout": False, "force_angel_revive": True, "force_wincap": False},
                    ),
                    Distribution(
                        criteria="group_shootout", quota=0.0036, # 3,600 db
                        conditions={"reel_weights": {}, "rtp_step": 0, "magnet_multiplier": 1.0, "armor_multiplier": 0.5, "force_group_shootout": True, "force_wincap": False},
                    ),
                    Distribution(
                        criteria="wincap", quota=0.00015, win_criteria=self.wincap, # 150 db
                        conditions={"reel_weights": {}, "rtp_step": 0, "magnet_multiplier": 1.0, "armor_multiplier": 0.5, "force_group_shootout": False, "force_wincap": True},
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
                        quota=0.9758, # 975,800 db
                        conditions={
                            "reel_weights": {}, "rtp_step": 0, "magnet_multiplier": 1.5, "armor_multiplier": 1.0,
                            "force_group_shootout": False, "force_angel_revive": False, "force_wincap": False,
                            "standard_weights": {"win": 586335, "draw": 130000, "lose": 259465}
                        },
                    ),
                    Distribution(
                        criteria="angel_revive", quota=0.0200, # 20,000 db
                        conditions={"reel_weights": {}, "rtp_step": 0, "magnet_multiplier": 1.5, "armor_multiplier": 1.0, "force_group_shootout": False, "force_angel_revive": True, "force_wincap": False},
                    ),
                    Distribution(
                        criteria="group_shootout", quota=0.0040, # 4,000 db
                        conditions={"reel_weights": {}, "rtp_step": 0, "magnet_multiplier": 1.5, "armor_multiplier": 1.0, "force_group_shootout": True, "force_wincap": False},
                    ),
                    Distribution(
                        criteria="wincap", quota=0.0002, win_criteria=self.wincap, # 200 db
                        conditions={"reel_weights": {}, "rtp_step": 0, "magnet_multiplier": 1.5, "armor_multiplier": 1.0, "force_group_shootout": False, "force_wincap": True},
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
                        quota=0.9641, # 964,100 db
                        conditions={
                            "reel_weights": {}, "rtp_step": 0, "magnet_multiplier": 1.5, "armor_multiplier": 0.5,
                            "force_group_shootout": False, "force_wincap": False,
                            "standard_weights": {"win": 600450, "draw": 120000, "lose": 243650}
                        },
                    ),
                    Distribution(
                        criteria="group_shootout", quota=0.0056, # 5,600 db
                        conditions={"reel_weights": {}, "rtp_step": 0, "magnet_multiplier": 1.5, "armor_multiplier": 0.5, "force_group_shootout": True, "force_wincap": False},
                    ),
                    Distribution(
                        criteria="angel_revive", quota=0.0300, # 30,000 db
                        conditions={"reel_weights": {}, "rtp_step": 0, "magnet_multiplier": 1.5, "armor_multiplier": 0.5, "force_group_shootout": False, "force_angel_revive": True, "force_wincap": False},
                    ),
                    Distribution(
                        criteria="wincap", quota=0.0003, win_criteria=self.wincap, # 300 db
                        conditions={"reel_weights": {}, "rtp_step": 0, "magnet_multiplier": 1.5, "armor_multiplier": 0.5, "force_group_shootout": False, "force_wincap": True},
                    ),
                ],
            ),
        ]

        self.normalize_quotas()

    def normalize_quotas(self):
        """Biztosítja, hogy a kvóták pontosan 1.0-át (100%) adjanak ki."""
        for mode in self.bet_modes:
            dists = getattr(mode, "distributions", getattr(mode, "_distributions", []))
            total_quota = sum(getattr(dist, "quota", getattr(dist, "_quota", 0.0)) for dist in dists)
            
            if total_quota > 0:
                for dist in dists:
                    current_quota = getattr(dist, "quota", getattr(dist, "_quota", 0.0))
                    new_quota = current_quota / total_quota
                    
                    if hasattr(dist, "quota"):
                        dist.quota = new_quota
                    elif hasattr(dist, "_quota"):
                        dist._quota = new_quota