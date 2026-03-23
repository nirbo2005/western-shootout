from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class PlayRequest(BaseModel):
    bet: float = Field(..., gt=0)
    base_bet: float = Field(..., gt=0)
    mode: str
    selected_character: str = Field(default="hero")
    client_seed: Optional[str] = None

class EndRoundRequest(BaseModel):
    pass

class StatusResponse(BaseModel):
    status: str
    server_seed_hash: str
    nonce: int
    client_seed: str

class RotateSeedResponse(BaseModel):
    old_server_seed: Optional[str]
    new_server_seed_hash: str
    nonce: int

class PlayResponse(BaseModel):
    bet: float
    base_bet: float
    multiplier: float
    payout: float
    events: List[Dict[str, Any]]
    server_seed_hash: str
    nonce: int
    result_float: float
    selected_character: str