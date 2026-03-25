import sys
import os
from pathlib import Path
import functools

# Kényszerítjük a gyökérkönyvtárat a python path-ba, 
# hogy a 'src' és a 'games' mappák modulként látszódjanak.
math_sdk_root = Path(__file__).resolve().parent
if str(math_sdk_root) not in sys.path:
    sys.path.insert(0, str(math_sdk_root))

# Abszolút importok a math-sdk gyökerétől indítva
from games.western_shootout.gamestate import GameState
from games.western_shootout.game_config import GameConfig
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs

def apply_sdk_patches():
    """
    SDK Patch: Biztosítja, hogy a get_distribution_moments 
    ne dobjon TypeError-t hiányzó argumentumok miatt.
    """
    try:
        from src.write_data import write_configs as wc
        original_get_moments = wc.get_distribution_moments
        
        @functools.wraps(original_get_moments)
        def patched_get_moments(dist, *args, **kwargs):
            return original_get_moments(dist)
            
        wc.get_distribution_moments = patched_get_moments
    except (ImportError, AttributeError):
        pass

if __name__ == "__main__":
    apply_sdk_patches()

    # KONFIGURÁCIÓS VÁLTOZÓK DEFINIÁLÁSA
    num_threads = 8          # 8 magra állítva a gyorsabb futásért
    batching_size = 250000   # 4 batch-ben fog lefutni módonként
    compression = True
    profiling = False

    # Pontosan 1.000.000 mintaszám a PREDETERMINÁLT MÁTRIX (Excel) miatt!
    num_sim_args = {
        "base": 1000000,
        "armor": 1000000,
        "magnet": 1000000,
        "extreme": 1000000,
    }
    
    # A game_id megfelel a provider_gameName_rtp formátumnak
    game_id = "stake_western_95"
    config = GameConfig(game_id)
    gamestate = GameState(config)

    print(f"Starting simulation for {game_id} with 1 MILLION samples per mode...")
    
    # Könyvgenerálás a definiált változókkal
    create_books(
        gamestate,
        config,
        num_sim_args,
        batching_size,
        num_threads,
        compression,
        profiling,
    )

    # Konfigurációs fájlok generálása a frontend/backend számára
    print("Generating math and event configurations...")
    generate_configs(gamestate)
    print("Done.")