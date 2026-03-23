from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from rgs_reader import rgs_reader
from provably_fair import ProvablyFair
from schemas import PlayRequest, EndRoundRequest, PlayResponse, StatusResponse, RotateSeedResponse

app = FastAPI(title="Western Shootout RGS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PFState:
    def __init__(self):
        self.engine = ProvablyFair()
        self.client_seed = "default_client_seed"
        self.nonce = 0

pf = PFState()

@app.get("/status", response_model=StatusResponse)
async def get_status():
    return {
        "status": "ready",
        "server_seed_hash": pf.engine.get_current_server_seed_hash(),
        "nonce": pf.nonce,
        "client_seed": pf.client_seed
    }

@app.post("/rotate-seed", response_model=RotateSeedResponse)
async def rotate_seed():
    old_seed = getattr(pf.engine, 'server_seed', getattr(pf.engine, 'current_server_seed', None))
    new_hash = pf.engine.rotate_server_seed()
    pf.nonce = 0
    
    return {
        "old_server_seed": old_seed,
        "new_server_seed_hash": new_hash,
        "nonce": pf.nonce
    }

@app.post("/play", response_model=PlayResponse)
async def play(req: PlayRequest):
    pf.nonce += 1
    if req.client_seed:
        pf.client_seed = req.client_seed

    current_server_seed = getattr(pf.engine, 'server_seed', getattr(pf.engine, 'current_server_seed', None))

    result_float = pf.engine.generate_result(
        current_server_seed,
        pf.client_seed,
        pf.nonce
    )
    
    outcome = rgs_reader.get_row_by_float(req.mode, result_float)
    
    if not outcome:
        raise HTTPException(status_code=500, detail=f"Mode '{req.mode}' simulation failed or not found.")

    events = outcome.get("events", [])
    multiplier_float = 0.0
    
    # 1. BIZTOSÍTÉK: Kiolvasás a round_data-ból
    for ev in events:
        if isinstance(ev, dict) and "round_data" in ev:
            rd = ev["round_data"]
            if "multiplier" in rd:
                try:
                    multiplier_float = float(rd["multiplier"])
                except:
                    pass
                break
                
    # 2. VÉSZTARTALÉK
    if multiplier_float == 0.0:
        mode_costs = {"base": 1.0, "armor": 1.5, "magnet": 1.8, "extreme": 2.3}
        cost = mode_costs.get(req.mode, 1.0)
        bgw = outcome.get("baseGameWins", 0.0)
        try:
            multiplier_float = float(bgw) / cost if bgw != "" else 0.0
        except:
            multiplier_float = 0.0

    return {
        "bet": req.bet,
        "base_bet": req.base_bet,
        "multiplier": round(multiplier_float, 2),
        "payout": round(req.base_bet * multiplier_float, 2),
        "events": events,
        "server_seed_hash": pf.engine.get_current_server_seed_hash(),
        "nonce": pf.nonce,
        "result_float": result_float,
        "selected_character": req.selected_character
    }

@app.post("/end-round")
async def end_round(req: EndRoundRequest):
    return {"status": "success", "message": "Round closed successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)