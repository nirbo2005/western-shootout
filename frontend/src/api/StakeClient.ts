import { currentBalance, serverSeedHash, currentNonce, clientSeed, previousServerSeed } from '../store/GameStore';
import { get } from 'svelte/store';
import type { DuelResponse, GameStatus, RgsEvent } from '../types/rgs-schema';

export class StakeClient {
    private readonly BASE_URL = 'http://localhost:8000';

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
            }
        } catch (e) {
            console.warn("Backend nem elérhető inicializáláskor. (Hálózat vagy CORS hiba)");
        }
        return { status: "ready" };
    }

    public async rotateSeed(): Promise<void> {
        try {
            const response = await fetch(`${this.BASE_URL}/rotate-seed`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP hiba: ${response.status}`);
            }
            
            const data = await response.json();
            serverSeedHash.set(data.new_server_seed_hash);
            previousServerSeed.set(data.old_server_seed);
            currentNonce.set(data.nonce);
        } catch (error: any) {
            console.error("Seed rotation error:", error);
            if (error instanceof TypeError && error.message.includes('fetch')) {
                throw new Error("Nem sikerült csatlakozni a szerverhez (Network/CORS hiba).");
            }
            throw error;
        }
    }

    public async play(totalBet: number, baseBet: number, mode: string, selectedCharacter: string = 'hero'): Promise<DuelResponse> {
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
                throw new Error(detail || `Szerver hiba történt (HTTP ${response.status})`);
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

            currentBalance.update(b => b - totalBet);

            return data;
        } catch (error: any) {
            console.error("Stake API Play Error:", error);
            if (error instanceof TypeError && error.message.includes('fetch')) {
                throw new Error("Nem sikerült csatlakozni a szerverhez. Ellenőrizd, hogy fut-e a backend.");
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
                throw new Error(`End-round hiba: ${response.status}`);
            }

            if (payout > 0) {
                currentBalance.update(b => b + payout);
                console.log(`[RGS END-ROUND] Sikeres körlezárás. Jóváírva: ${payout}`);
            }

        } catch (error) {
            console.error("Stake API End-Round Error:", error);
            throw error;
        }
    }
}

export const stakeClient = new StakeClient();