export type AttackerType = 'PLAYER' | 'ENEMY' | 'ANGEL' | string;
export type HitZone = 'HEAD' | 'BODY' | 'LEGS' | 'FAIL' | string;
export type GameEventType = 'STANDARD_WIN' | 'STANDARD_LOSE' | 'STANDARD_DRAW' | 'GROUP_SHOOTOUT' | 'ANGEL_REVIVE';
export type DuelWinner = 'PLAYER' | 'ENEMY' | 'DRAW' | 'NONE';

export interface DuelStep {
    Shooter: AttackerType;
    ShooterID?: string; // Több ellenfél (Group Shootout) esetén azonosítja a lövőt
    Target: HitZone;
    PlayerHP: number;
    EnemyHP: number;
    enemiesHP?: Record<string, number>; // Group Shootout esetén az összes ellenfél HP-ja
    isRevive?: boolean;
}

export interface DuelTimeline {
    eventType: GameEventType;
    winner: DuelWinner;
    steps: DuelStep[];
}

export interface RgsEvent {
    index?: number;
    type?: string;
    numberRolled?: number;
    finalMultiplier?: number;
    round_data?: DuelTimeline; 
    [key: string]: any; 
}

export interface DuelResponse {
    bet: number;         // A teljes levont összeg (költség, total_bet)
    base_bet: number;    // Az alaptét, ami alapján a nyereményszorzó kalkulálódik
    multiplier: number;
    payout: number;
    events: RgsEvent[];
    server_seed_hash: string;
    nonce: number;
    result_float?: number;
    selected_character: string; // A kiválasztott karakter azonosítója
}

export interface GameStatus {
    status: string;
    server_seed_hash: string;
    nonce: number;
    client_seed: string;
}