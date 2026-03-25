import { currentBalance, serverSeedHash, currentNonce, clientSeed, previousServerSeed, errorMessage, isAutoBetActive } from '../store/GameStore';
import { get } from 'svelte/store';
import type { DuelResponse, GameStatus, RgsEvent } from '../types/rgs-schema';

export class StakeClient {
    private readonly BASE_URL = 'http://localhost:8000';

    private handleError(message: string) {
        console.error(`[StakeClient Hiba]: ${message}`);
        errorMessage.set(message);
        // Ha auto-bet ment éppen, állítsuk le hiba esetén!
        isAutoBetActive.set(false);
    }

    public async initialize(): Promise<{ status: string }> {
        try {
            const response = await fetch(`${this.BASE_URL}/status`);
            if (response.ok) {
                const data: GameStatus = await response.json();
                if (data.server_seed_hash) {
                    serverSeedHash.set(data.server_seed_hash);
                }
                if (data.nonce !== undefined) {
                    currentNonce.set(data.nonce);
                }
                if (data.client_seed) {
                    clientSeed.set(data.client_seed);
                }
            } else {
                this.handleError("Backend szerver elérhető, de hibás státuszt adott vissza.");
            }
        } catch (e) {
            console.warn("Backend nem elérhető inicializáláskor. (Hálózat vagy CORS hiba)");
            this.handleError("Nem sikerült csatlakozni a játékszerverhez. Kérlek, ellenőrizd a kapcsolatot!");
        }
        return { status: "ready" };
    }

    public async rotateSeed(): Promise<void> {
        try {
            const response = await fetch(`${this.BASE_URL}/rotate-seed`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail || `HTTP hiba: ${response.status}`);
            }
            
            const data = await response.json();
            serverSeedHash.set(data.new_server_seed_hash);
            previousServerSeed.set(data.old_server_seed);
            currentNonce.set(data.nonce);
        } catch (error: any) {
            console.error("Seed rotation error:", error);
            if (error instanceof TypeError && error.message.includes('fetch')) {
                this.handleError("Nem sikerült a seed csere. (Hálózat/CORS hiba)");
            } else {
                this.handleError(`Hiba a seed cseréjekor: ${error.message}`);
            }
            throw error;
        }
    }

    public async play(totalBet: number, baseBet: number, mode: string, selectedCharacter: string = 'hero'): Promise<DuelResponse> {
        
        // 1. Kliens oldali egyenleg ellenőrzés (hogy elkerüljük a felesleges API hívást)
        const balance = get(currentBalance);
        if (balance < totalBet) {
            const err = "Nincs elegendő egyenleged a pörgetéshez!";
            this.handleError(err);
            throw new Error(err);
        }

        try {
            const payload = {
                bet: totalBet,
                base_bet: baseBet,
                mode: mode,
                selected_character: selectedCharacter,
                client_seed: get(clientSeed)
            };

            const response = await fetch(`${this.BASE_URL}/play`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const detail = typeof errorData.detail === 'string' 
                    ? errorData.detail 
                    : JSON.stringify(errorData.detail);
                
                const errMsg = detail || `Szerver hiba történt (HTTP ${response.status})`;
                this.handleError(errMsg);
                throw new Error(errMsg);
            }

            const data: DuelResponse = await response.json();

            const winEvent = data.events.find((e: RgsEvent) => e.round_data !== undefined);
            const roundData = winEvent?.round_data;

            if (roundData) {
                const stepsFormatted = roundData.steps.map((step: any) => {
                    const shooter = step.Shooter || 'ismeretlen';
                    const target = step.Target || 'ismeretlen';
                    const enemyHp = step.EnemyHP !== undefined ? step.EnemyHP : '?';
                    const playerHp = step.PlayerHP !== undefined ? step.PlayerHP : '?';
                    return `{Shooter: ${shooter}, Target: ${target}, EnemyHP: ${enemyHp}, PlayerHP: ${playerHp}}`;
                }).join(', ');

                console.log(`[RGS PLAY VÁLASZ FELDOLGOZVA]
- Játékmód: ${mode}
- Szorzó: ${data.multiplier}x
- Győztes: ${roundData.winner}
- Lépések: [${stepsFormatted}]`);
            }

            if (data.server_seed_hash) {
                serverSeedHash.set(data.server_seed_hash);
            }
            if (data.nonce !== undefined) {
                currentNonce.set(data.nonce);
            }

            // Pénz azonnali levonása a sikeres válasz után
            currentBalance.update(b => b - totalBet);

            return data;
        } catch (error: any) {
            console.error("Stake API Play Error:", error);
            if (error instanceof TypeError && error.message.includes('fetch')) {
                const errMsg = "Nem sikerült csatlakozni a szerverhez. Ellenőrizd, hogy fut-e a backend.";
                this.handleError(errMsg);
                throw new Error(errMsg);
            }
            throw error;
        }
    }

    public async endRound(payout: number): Promise<void> {
        try {
            const response = await fetch(`${this.BASE_URL}/end-round`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail || `End-round hiba: ${response.status}`);
            }

            if (payout > 0) {
                currentBalance.update(b => b + payout);
                console.log(`[RGS END-ROUND] Sikeres körlezárás. Jóváírva: ${payout}`);
            }

        } catch (error: any) {
            console.error("Stake API End-Round Error:", error);
            this.handleError(`Hiba a kifizetés jóváírásakor: ${error.message}`);
            throw error;
        }
    }
}

export const stakeClient = new StakeClient();