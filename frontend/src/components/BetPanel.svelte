<script lang="ts">
    import { 
        currentBalance, 
        baseBet, 
        totalBet, 
        gameState, 
        isMagnetActive, 
        isArmorActive,
        potentialMaxWin,
        duelCooldown,
        selectedCharacter
    } from '../store/GameStore';
    import { stakeClient } from '../api/StakeClient';
    import { sequencePlayer } from '../game/SequencePlayer';
    import { gameEngine } from '../game/GameEngine';

    $: backendMode = ($isMagnetActive && $isArmorActive) ? 'extreme' : 
                     $isMagnetActive ? 'magnet' : 
                     $isArmorActive ? 'armor' : 'base';

    $: {
        // Reaktív függőségek explicit megadása a real-time frissítéshez
        $isMagnetActive;
        $isArmorActive;
        $selectedCharacter;

        if (gameEngine && $gameState === 'IDLE') {
            try {
                gameEngine.updateVisualsFromStores();
            } catch (e) {
            }
        }
    }

    async function handleBet() {
        if ($gameState !== 'IDLE' || $currentBalance < $totalBet) return;

        const activeBaseBet = $baseBet;
        const activeTotalBet = $totalBet;
        const modeToSend = backendMode;
        const charToSend = $selectedCharacter;
        
        try {
            const response = await stakeClient.play(activeTotalBet, activeBaseBet, modeToSend, charToSend);
            await sequencePlayer.play(response);
        } catch (error) {
            console.error(error);
            gameState.set('IDLE');
        }
    }

    function quickBet(mult: number) {
        if ($gameState !== 'IDLE') return;
        baseBet.update((v: number) => {
            const newVal = Number((v * mult).toFixed(2));
            return newVal < 0.1 ? 0.1 : newVal;
        });
    }

    function toggleMagnet() {
        isMagnetActive.update((v: boolean) => !v);
    }

    function toggleArmor() {
        isArmorActive.update((v: boolean) => !v);
    }
</script>

<div class="bet-panel">
    <div class="balance-display">
        <span class="label">Egyenleg</span>
        <span class="value">${$currentBalance.toFixed(2)}</span>
    </div>

    <div class="input-group">
        <div class="label">Karakter Választás</div>
        <div class="char-selection">
            <button 
                class="char-btn" 
                class:active={$selectedCharacter === 'hero'}
                on:click={() => selectedCharacter.set('hero')}
                disabled={$gameState !== 'IDLE'}
            >
                Hős (Bal)
            </button>
            <button 
                class="char-btn" 
                class:active={$selectedCharacter === 'bandit'}
                on:click={() => selectedCharacter.set('bandit')}
                disabled={$gameState !== 'IDLE'}
            >
                Bandita (Jobb)
            </button>
        </div>
    </div>

    <div class="input-group">
        <label for="betAmount">Alaptét összege</label>
        <div class="input-wrapper">
            <input 
                id="betAmount"
                type="number" 
                bind:value={$baseBet} 
                min="0.1" 
                step="0.1"
                disabled={$gameState !== 'IDLE'}
            />
            <button disabled={$gameState !== 'IDLE'} on:click={() => quickBet(0.5)}>1/2</button>
            <button disabled={$gameState !== 'IDLE'} on:click={() => quickBet(2)}>2x</button>
        </div>
    </div>

    <div class="modifiers">
        <button 
            class="mod-btn" 
            class:active={$isMagnetActive}
            on:click={toggleMagnet}
            disabled={$gameState !== 'IDLE'}
        >
            Mágnes (+80%)
        </button>
        <button 
            class="mod-btn" 
            class:active={$isArmorActive}
            on:click={toggleArmor}
            disabled={$gameState !== 'IDLE'}
        >
            Páncél (+50%)
        </button>
    </div>

    <div class="total-info">
        <div class="info-row">
            <span>Összes levonás:</span>
            <span>${$totalBet.toFixed(2)}</span>
        </div>
        <div class="info-row highlight">
            <span>Alap nyeremény (2x):</span>
            <span>${($baseBet * 2).toFixed(2)}</span>
        </div>
        <div class="info-row extra">
            <span>Max Win (500x):</span>
            <span>${$potentialMaxWin.toFixed(2)}</span>
        </div>
    </div>

    <button 
        class="shoot-btn" 
        class:cooldown={$gameState === 'COOLDOWN'}
        disabled={$gameState !== 'IDLE' || $currentBalance < $totalBet}
        on:click={handleBet}
    >
        {#if $gameState === 'IDLE'}
            LÖVÉS
        {:else if $gameState === 'COOLDOWN'}
            {$duelCooldown}...
        {:else}
            PÁRBAJ...
        {/if}
    </button>
</div>

<style>
    .char-selection {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    .char-btn {
        flex: 1;
        padding: 0.5rem;
        background: #2a2a35;
        color: #fff;
        border: 2px solid transparent;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .char-btn.active {
        background: #4a4a5a;
        border-color: #fca311;
        font-weight: bold;
    }
    .char-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
</style>