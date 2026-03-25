import { 
    gameState, 
    playerHP, 
    enemyHP, 
    multiEnemiesHP, 
    currentRound, 
    spendBullet,
    resetDuelState,
    betHistory,
    currentBetMode,
    selectedCharacter,
    saveGameState,
    clearGameState,
    isAutoBetActive,
    autoSpinsLeft,
    totalBet,
    baseBet,
    isResuming // <-- ÚJ IMPORT
} from '../store/GameStore';
import { get } from 'svelte/store';
import { gameEngine } from './GameEngine';
import { stakeClient } from '../api/StakeClient';
import type { DuelResponse, RgsEvent, DuelTimeline, DuelStep } from '../types/rgs-schema';

class SequencePlayer {
    private isPlaying = false;

    private log(message: string, data?: any) {
        console.log(`%c[SequencePlayer]%c ${message}`, 'color: #f1c40f; font-weight: bold', 'color: #ccc');
        if (data) console.log(data);
    }

    private delay(ms: number) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    public async play(data: DuelResponse, skipToStep: number = 0) {
        if (this.isPlaying) return;
        
        // 1. Az események kinyerése az RGS 'events' tömbből
        const winEvent = data.events?.find((e: RgsEvent) => e.round_data !== undefined);
        const timeline = winEvent?.round_data;

        if (!timeline || !timeline.steps) {
            console.error("[SequencePlayer] Érvénytelen válasz struktúra (Nincs round_data):", data);
            gameState.set('IDLE');
            // Ha hiba van, leállítjuk az autobetet
            isAutoBetActive.set(false);
            if (get(isResuming)) isResuming.set(false);
            return;
        }
        
        this.isPlaying = true;

        try {
            const steps = timeline.steps;
            
            // 2. Előkészítés
            if (skipToStep === 0) {
                gameEngine.cleanup();
                gameEngine.updateVisualsFromStores();
                resetDuelState();
                
                // Mentsük le a friss játékot az első lépés előtt
                saveGameState(data, 0);
            }
            
            gameState.set('SHOOTING');

            // 3. Minigame specifikus setupok
            if (timeline.eventType === 'GROUP_SHOOTOUT') {
                const firstStepWithEnemies = steps.find(s => s.enemiesHP);
                const enemyCount = firstStepWithEnemies?.enemiesHP ? Object.keys(firstStepWithEnemies.enemiesHP).length : 5;
                gameEngine.setupGroupShootoutEnemies(enemyCount);
            } else if (timeline.eventType === 'ANGEL_REVIVE') {
                // Az angyal később spawnol a steps során
            }

            // 4. Lépések lejátszása (vagy átugrása)
            let playerShotCount = 0;
            
            for (let i = 0; i < steps.length; i++) {
                const step = steps[i];

                if (step.Shooter === 'PLAYER') {
                    playerShotCount++;
                    currentRound.set(playerShotCount);
                }

                // Ha Resume módban vagyunk, átugorjuk az animációt a célig
                if (i < skipToStep) {
                    this.fastForwardStep(step, timeline.eventType, playerShotCount);
                    continue;
                }

                // --- HIBAJAVÍTÁS: ELTÜNTETJÜK AZ OVERLAY-T ---
                // Amint elérünk az első "valós" animációhoz, levesszük a homályosítást!
                if (get(isResuming)) {
                    isResuming.set(false);
                }
                // ----------------------------------------------

                try {
                    await this.processStep(step, timeline.eventType);
                    // Állapotmentés minden sikeres animált lépés után
                    saveGameState(data, i + 1);
                } catch (stepError) {
                    console.warn("[SequencePlayer] Hiba egy lépésnél:", stepError);
                }

                await this.delay(350);
            }

            // Biztosíték: Ha véletlenül pont a játék legvégén frissített rá, akkor is eltüntetjük az overlay-t a Result előtt
            if (get(isResuming)) {
                isResuming.set(false);
            }

            // 5. Eredmény megjelenítése és takarítás
            await this.handleResult(data, timeline);
            clearGameState(); // Töröljük a localStorage-t, a játék sikeresen befejeződött!

        } catch (error) {
            console.error("[SequencePlayer] Kritikus hiba:", error);
            gameEngine.showResultText("Rendszerhiba", 0xffffff);
            await this.delay(2000);
            gameState.set('IDLE');
            isAutoBetActive.set(false);
            if (get(isResuming)) isResuming.set(false);
        } finally {
            this.isPlaying = false;
        }
    }

    // Animáció nélküli, gyors állapotbeállítás (Resume-hoz)
    private fastForwardStep(step: DuelStep, eventType: string, playerShotCount: number) {
        const shooterId = (step as any).ShooterID || step.Shooter;
        const targetZone = step.Target;
        const isHit = targetZone !== 'FAIL';

        // Angyal spawnolása csendben
        if (shooterId === 'ANGEL' && !gameEngine.extraCharacters.has('ANGEL')) {
            gameEngine.spawnAngel();
        }

        // Töltények elhasználása
        if (shooterId === 'PLAYER') {
            spendBullet((playerShotCount - 1) % 6);
        }

        // Halál animációk beállítása azonnal
        if (isHit) {
            let targetId = 'ENEMY';
            if (step.Shooter === 'PLAYER') {
                if (eventType === 'GROUP_SHOOTOUT' && step.enemiesHP) {
                    const aliveEnemies = Object.keys(step.enemiesHP).filter(id => step.enemiesHP![id] > 0);
                    targetId = aliveEnemies[0] || 'ENEMY_1';
                }
            } else if (step.Shooter === 'ANGEL') {
                targetId = 'PLAYER';
            } else {
                targetId = 'PLAYER';
            }

            if (targetId === 'PLAYER' && step.PlayerHP !== undefined && step.PlayerHP <= 0) {
                gameEngine.playDeathAnim('PLAYER');
            } else if (eventType === 'GROUP_SHOOTOUT' && step.enemiesHP) {
                Object.keys(step.enemiesHP).forEach(id => {
                    if (step.enemiesHP![id] <= 0) {
                        gameEngine.playDeathAnim(id);
                    }
                });
            } else if (targetId === 'ENEMY' && step.EnemyHP !== undefined && step.EnemyHP <= 0) {
                gameEngine.playDeathAnim('ENEMY');
            }
        }

        // Store-ok frissítése
        if (step.PlayerHP !== undefined) playerHP.set(step.PlayerHP);
        if (step.EnemyHP !== undefined) enemyHP.set(step.EnemyHP);
        if (step.enemiesHP) multiEnemiesHP.set(step.enemiesHP);
        
        gameEngine.jumpToHP(get(playerHP), get(enemyHP));
    }

    private async processStep(step: DuelStep, eventType: string) {
        const shooterId = (step as any).ShooterID || step.Shooter;
        const targetZone = step.Target;
        const isHit = targetZone !== 'FAIL';

        let targetId = 'ENEMY';
        if (step.Shooter === 'PLAYER') {
            if (eventType === 'GROUP_SHOOTOUT') {
                if (step.enemiesHP) {
                    const aliveEnemies = Object.keys(step.enemiesHP).filter(id => step.enemiesHP![id] > 0);
                    targetId = aliveEnemies[0] || 'ENEMY_1';
                } else {
                    targetId = 'ENEMY_1';
                }
            } else {
                targetId = 'ENEMY';
            }
        } else if (step.Shooter === 'ANGEL') {
            targetId = 'PLAYER';
        } else {
            targetId = 'PLAYER';
        }

        if (shooterId === 'ANGEL' && !gameEngine.extraCharacters.has('ANGEL')) {
            gameEngine.spawnAngel();
            await this.delay(800);
        }

        if (shooterId === 'PLAYER') {
            const currentR = get(currentRound);
            spendBullet((currentR - 1) % 6);
        }

        await gameEngine.playShootSequence(shooterId, targetId, isHit, targetZone);

        if (isHit) {
            if (targetId === 'PLAYER' && step.PlayerHP !== undefined && step.PlayerHP <= 0) {
                gameEngine.playDeathAnim('PLAYER');
            } else if (eventType === 'GROUP_SHOOTOUT' && step.enemiesHP) {
                Object.keys(step.enemiesHP).forEach(id => {
                    if (step.enemiesHP![id] <= 0) {
                        gameEngine.playDeathAnim(id);
                    }
                });
            } else if (targetId === 'ENEMY' && step.EnemyHP !== undefined && step.EnemyHP <= 0) {
                gameEngine.playDeathAnim('ENEMY');
            }
        }

        if (step.PlayerHP !== undefined) playerHP.set(step.PlayerHP);
        if (step.EnemyHP !== undefined) enemyHP.set(step.EnemyHP);
        if (step.enemiesHP) multiEnemiesHP.set(step.enemiesHP);
        
        gameEngine.updateHPVisuals(get(playerHP), get(enemyHP));
    }

    private async handleResult(data: DuelResponse, timeline: DuelTimeline) {
        const { payout, bet, multiplier } = data;
        
        betHistory.update((history: any[]) => [
            {
                id: Math.random().toString(36).substring(2, 9),
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
                mode: get(currentBetMode),
                bet: bet,
                multiplier: multiplier,
                payout: payout
            },
            ...history
        ].slice(0, 50));

        if (timeline.winner === 'PLAYER') {
            gameEngine.showResultText(`GYŐZELEM!\n$${payout.toFixed(2)}`, 0x2ecc71);
        } else if (timeline.winner === 'DRAW') {
            gameEngine.showResultText(`DÖNTETLEN\n$${payout.toFixed(2)}`, 0xf1c40f);
        } else {
            gameEngine.showResultText("VESZTETTÉL!", 0xe74c3c);
        }

        gameState.set('RESULT');

        if (payout > 0) {
            try {
                await stakeClient.endRound(payout);
            } catch (e) {
                console.error("[SequencePlayer] Hiba a kör lezárásakor", e);
            }
        }
        
        await this.delay(3000); // UI Várakozás
        
        gameState.set('IDLE');
        gameEngine.cleanupResultText();
        gameEngine.cleanup();

        // ---------------------------------------------------------
        // AUTOBET CIKLUS VIZSGÁLATA
        // ---------------------------------------------------------
        if (get(isAutoBetActive)) {
            let spinsLeft = get(autoSpinsLeft);
            const stopOnWinStr = typeof sessionStorage !== 'undefined' ? sessionStorage.getItem('ws_stop_on_win') : 'false';
            const stopOnWin = stopOnWinStr === 'true';

            // 1. Álljunk le, ha be van kapcsolva a Stop on Win és nyertünk
            if (stopOnWin && payout > 0) {
                this.log("Autobet leállítva (Stop on win).");
                isAutoBetActive.set(false);
                return;
            }

            // 2. Csökkentjük a pörgetések számát
            spinsLeft--;
            autoSpinsLeft.set(spinsLeft);

            // 3. Ha maradt még pörgetés, indítsuk újra!
            if (spinsLeft > 0) {
                this.log(`Autobet folytatódik. Hátralévő: ${spinsLeft}`);
                
                // Kis szünet, mielőtt újra meghívja az API-t
                await this.delay(100);
                
                try {
                    const activeTotalBet = get(totalBet);
                    const activeBaseBet = get(baseBet);
                    const modeToSend = get(currentBetMode);
                    const charToSend = get(selectedCharacter);
                    
                    const response = await stakeClient.play(activeTotalBet, activeBaseBet, modeToSend, charToSend);
                    this.play(response); // Rekurzív hívás
                } catch (error) {
                    console.error("Autobet megszakadt egy hiba miatt.");
                    isAutoBetActive.set(false);
                }
            } else {
                this.log("Autobet befejeződött (0 pörgetés maradt).");
                isAutoBetActive.set(false);
            }
        }
    }
}

export const sequencePlayer = new SequencePlayer();