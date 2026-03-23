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
    selectedCharacter
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

    public async play(data: DuelResponse) {
        if (this.isPlaying) return;
        
        // 1. Az események kinyerése az RGS 'events' tömbből
        const winEvent = data.events?.find((e: RgsEvent) => e.round_data !== undefined);
        const timeline = winEvent?.round_data;

        if (!timeline || !timeline.steps) {
            console.error("[SequencePlayer] Érvénytelen válasz struktúra (Nincs round_data):", data);
            gameState.set('IDLE');
            return;
        }

        // KONZOL LOG: A nyers round_data kiírása a debugoláshoz
        console.group("%c🎯 RGS ROUND DATA LEJÁTSZÁSA", "color: #00ff00; font-weight: bold; font-size: 12px;");
        console.log("Esemény típusa:", timeline.eventType);
        console.log("Győztes:", timeline.winner);
        console.table(timeline.steps);
        console.groupEnd();
        
        this.isPlaying = true;

        try {
            const steps = timeline.steps;
            
            // 2. Előkészítés (reseteljük a vizualitást és alkalmazzuk a friss store állapotokat)
            gameEngine.cleanup();
            gameEngine.updateVisualsFromStores();
            resetDuelState();
            gameState.set('SHOOTING');

            // 3. Minigame specifikus setupok
            if (timeline.eventType === 'GROUP_SHOOTOUT') {
                const firstStepWithEnemies = steps.find(s => s.enemiesHP);
                const enemyCount = firstStepWithEnemies?.enemiesHP ? Object.keys(firstStepWithEnemies.enemiesHP).length : 5;
                gameEngine.setupGroupShootoutEnemies(enemyCount);
            } else if (timeline.eventType === 'ANGEL_REVIVE') {
                // Az angyal később spawnol a steps során
            }

            // 4. Lépések lejátszása
            let playerShotCount = 0;
            for (let i = 0; i < steps.length; i++) {
                const step = steps[i];

                // Körök kezelése (Modulo 6 forgatás a RevolverUI-ban)
                if (step.Shooter === 'PLAYER') {
                    playerShotCount++;
                    currentRound.set(playerShotCount);
                }

                try {
                    await this.processStep(step, timeline.eventType);
                } catch (stepError) {
                    console.warn("[SequencePlayer] Hiba egy lépésnél:", stepError);
                }

                await this.delay(350);
            }

            // 5. Eredmény megjelenítése
            await this.handleResult(data, timeline);

        } catch (error) {
            console.error("[SequencePlayer] Kritikus hiba:", error);
            gameEngine.showResultText("Rendszerhiba", 0xffffff);
            await this.delay(2000);
            gameState.set('IDLE');
        } finally {
            this.isPlaying = false;
        }
    }

    private async processStep(step: DuelStep, eventType: string) {
        // GROUP_SHOOTOUT esetén a backend a specifikus ellenség ID-ját a ShooterID-ben küldi
        const shooterId = (step as any).ShooterID || step.Shooter;
        const targetZone = step.Target;
        const isHit = targetZone !== 'FAIL';

        // 1. Célpont meghatározása
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

        // 2. Angyal spawnolása ha ő a lövő
        if (shooterId === 'ANGEL' && !gameEngine.extraCharacters.has('ANGEL')) {
            gameEngine.spawnAngel();
            await this.delay(800);
        }

        // 3. Töltény elhasználása (RevolverUI szinkron)
        if (shooterId === 'PLAYER') {
            const currentR = get(currentRound);
            spendBullet((currentR - 1) % 6);
        }

        // 4. Animáció lejátszása a GameEngine-nel (A GameEngine lefordítja a logikai ID-kat vizuális pozícióra)
        await gameEngine.playShootSequence(shooterId, targetId, isHit, targetZone);

        // 5. Halál animáció triggerelése
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

        // 6. Store-ok frissítése az animáció után
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
        
        await this.delay(3000);
        gameState.set('IDLE');
        gameEngine.cleanupResultText();
        gameEngine.cleanup();
    }
}

export const sequencePlayer = new SequencePlayer();