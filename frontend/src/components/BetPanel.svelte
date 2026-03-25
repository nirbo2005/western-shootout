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
        selectedCharacter,
        isAutoBetActive,
        autoSpinsLeft,
        errorMessage
    } from '../store/GameStore';
    import { stakeClient } from '../api/StakeClient';
    import { sequencePlayer } from '../game/SequencePlayer';
    import { gameEngine } from '../game/GameEngine';

    let activeTab: 'manual' | 'auto' = 'manual';
    let autoSpinInput: number | string = 10;
    let stopOnWin: boolean = false;

    $: backendMode = ($isMagnetActive && $isArmorActive) ? 'extreme' : 
                     $isMagnetActive ? 'magnet' : 
                     $isArmorActive ? 'armor' : 'base';

    // Reaktív költségszorzó a Smart Kalkulátorhoz
    $: costMultiplier = ($isMagnetActive && $isArmorActive) ? 2.3 :
                        $isMagnetActive ? 1.8 :
                        $isArmorActive ? 1.5 : 1.0;

    // Teljes költség kijelző változója
    let displayTotalBet = $totalBet.toFixed(2);

    $: {
        // Ha nem épp a Total Bet mezőbe gépel a user, frissítsük a megjelenített értéket
        if (document.activeElement?.id !== 'totalBetInput') {
            displayTotalBet = $totalBet.toFixed(2);
        }

        $isMagnetActive;
        $isArmorActive;
        $selectedCharacter;

        if (gameEngine && $gameState === 'IDLE') {
            try {
                gameEngine.updateVisualsFromStores();
            } catch (e) {}
        }
    }

    // Ha a user a Teljes Költség mezőt írja át
    function handleTotalInput(e: Event) {
        const target = e.target as HTMLInputElement;
        const val = parseFloat(target.value);
        if (!isNaN(val) && val >= 0) {
            baseBet.set(Number((val / costMultiplier).toFixed(2)));
        }
    }

    async function handleBet() {
        if ($gameState !== 'IDLE' || $currentBalance < $totalBet) {
            if ($isAutoBetActive) stopAutoBet();
            return;
        }

        const activeBaseBet = $baseBet;
        const activeTotalBet = $totalBet;
        const modeToSend = backendMode;
        const charToSend = $selectedCharacter;
        
        try {
            const response = await stakeClient.play(activeTotalBet, activeBaseBet, modeToSend, charToSend);
            await sequencePlayer.play(response);
        } catch (error) {
            console.error(error);
            stopAutoBet();
            gameState.set('IDLE');
        }
    }

    function startAutoBet() {
        const spins = parseInt(autoSpinInput.toString(), 10);
        if (isNaN(spins) || spins <= 0) return;

        isAutoBetActive.set(true);
        autoSpinsLeft.set(spins);
        
        // Elmentjük a leállási feltételeket a sessionStorage-be, hogy a SequencePlayer elérje
        if (typeof sessionStorage !== 'undefined') {
            sessionStorage.setItem('ws_stop_on_win', stopOnWin ? 'true' : 'false');
        }

        handleBet();
    }

    function stopAutoBet() {
        isAutoBetActive.set(false);
        autoSpinsLeft.set(0);
    }

    function quickBet(mult: number) {
        if ($gameState !== 'IDLE' || $isAutoBetActive) return;
        baseBet.update((v: number) => {
            const newVal = Number((v * mult).toFixed(2));
            return newVal < 0.1 ? 0.1 : newVal;
        });
    }

    function toggleMagnet() {
        if ($isAutoBetActive) return;
        isMagnetActive.update((v: boolean) => !v);
    }

    function toggleArmor() {
        if ($isAutoBetActive) return;
        isArmorActive.update((v: boolean) => !v);
    }
</script>

<div class="bet-panel">
    <div class="balance-display">
        <span class="label">Egyenleg</span>
        <span class="value">${$currentBalance.toFixed(2)}</span>
    </div>

    <div class="tabs">
        <button 
            class="tab-btn" 
            class:active={activeTab === 'manual'} 
            on:click={() => activeTab = 'manual'}
            disabled={$isAutoBetActive || $gameState !== 'IDLE'}
        >
            Manuális
        </button>
        <button 
            class="tab-btn" 
            class:active={activeTab === 'auto'} 
            on:click={() => activeTab = 'auto'}
            disabled={$isAutoBetActive || $gameState !== 'IDLE'}
        >
            Auto
        </button>
    </div>

    <div class="input-group">
        <div class="label">Karakter Választás</div>
        <div class="char-selection">
            <button 
                class="char-btn" 
                class:active={$selectedCharacter === 'hero'}
                on:click={() => selectedCharacter.set('hero')}
                disabled={$gameState !== 'IDLE' || $isAutoBetActive}
            >
                Hős (Bal)
            </button>
            <button 
                class="char-btn" 
                class:active={$selectedCharacter === 'bandit'}
                on:click={() => selectedCharacter.set('bandit')}
                disabled={$gameState !== 'IDLE' || $isAutoBetActive}
            >
                Bandita (Jobb)
            </button>
        </div>
    </div>

    <div class="input-group split-inputs">
        <div class="input-half">
            <label for="baseBet">Alaptét</label>
            <input 
                id="baseBet"
                type="number" 
                bind:value={$baseBet} 
                min="0.1" 
                step="0.1"
                disabled={$gameState !== 'IDLE' || $isAutoBetActive}
            />
        </div>
        <div class="input-half highlight-input">
            <label for="totalBetInput">Teljes Költség</label>
            <input 
                id="totalBetInput"
                type="number" 
                value={displayTotalBet} 
                on:input={handleTotalInput}
                min="0.1" 
                step="0.1"
                disabled={$gameState !== 'IDLE' || $isAutoBetActive}
            />
        </div>
    </div>

    <div class="quick-btns">
        <button disabled={$gameState !== 'IDLE' || $isAutoBetActive} on:click={() => quickBet(0.5)}>1/2</button>
        <button disabled={$gameState !== 'IDLE' || $isAutoBetActive} on:click={() => quickBet(2)}>2x</button>
    </div>

    <div class="modifiers">
        <button 
            class="mod-btn" 
            class:active={$isMagnetActive}
            on:click={toggleMagnet}
            disabled={$gameState !== 'IDLE' || $isAutoBetActive}
        >
            Mágnes (+80%)
        </button>
        <button 
            class="mod-btn" 
            class:active={$isArmorActive}
            on:click={toggleArmor}
            disabled={$gameState !== 'IDLE' || $isAutoBetActive}
        >
            Páncél (+50%)
        </button>
    </div>

    <div class="total-info">
        <div class="info-row highlight">
            <span>Alap nyeremény (2x):</span>
            <span>${($baseBet * 2).toFixed(2)}</span>
        </div>
        <div class="info-row extra">
            <span>Max Win (500x):</span>
            <span>${$potentialMaxWin.toFixed(2)}</span>
        </div>
    </div>

    {#if activeTab === 'auto' && !$isAutoBetActive}
        <div class="auto-settings">
            <div class="setting-row">
                <label>Pörgetések száma:</label>
                <input type="number" bind:value={autoSpinInput} min="1" disabled={$gameState !== 'IDLE'} />
            </div>
            <div class="setting-row checkbox-row">
                <label>
                    <input type="checkbox" bind:checked={stopOnWin} disabled={$gameState !== 'IDLE'} />
                    Állj meg, ha nyerek
                </label>
            </div>
        </div>
    {/if}

    {#if $isAutoBetActive}
        <button class="shoot-btn stop-auto" on:click={stopAutoBet}>
            STOP AUTO ({$autoSpinsLeft})
        </button>
    {:else}
        <button 
            class="shoot-btn" 
            class:cooldown={$gameState === 'COOLDOWN'}
            disabled={$gameState !== 'IDLE' || $currentBalance < $totalBet || !!$errorMessage}
            on:click={activeTab === 'auto' ? startAutoBet : handleBet}
        >
            {#if $errorMessage}
                HIBA
            {:else if $gameState === 'IDLE'}
                {activeTab === 'auto' ? 'START AUTO' : 'LÖVÉS'}
            {:else if $gameState === 'COOLDOWN'}
                {$duelCooldown}...
            {:else}
                PÁRBAJ...
            {/if}
        </button>
    {/if}
</div>

<style>
    .tabs {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    .tab-btn {
        flex: 1;
        padding: 0.6rem;
        background: #1e1e28;
        color: #888;
        border: 2px solid transparent;
        border-bottom: 2px solid #333;
        border-radius: 4px 4px 0 0;
        cursor: pointer;
        font-weight: bold;
        transition: all 0.2s;
    }
    .tab-btn.active {
        background: #2a2a35;
        color: #fff;
        border-bottom-color: #fca311;
    }
    .tab-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

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

    .split-inputs {
        display: flex;
        gap: 1rem;
        margin-bottom: 0.5rem;
    }
    .input-half {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 0.3rem;
    }
    .input-half label {
        font-size: 0.8rem;
        color: #aaa;
    }
    .input-half input {
        width: 100%;
        padding: 0.5rem;
        background: #1e1e28;
        border: 1px solid #333;
        border-radius: 4px;
        color: white;
        font-weight: bold;
    }
    .highlight-input input {
        border-color: #fca311;
        background: #2a2215;
    }

    .quick-btns {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    .quick-btns button {
        flex: 1;
        background: #333;
        color: #fff;
        border: none;
        padding: 0.4rem;
        border-radius: 4px;
        cursor: pointer;
    }
    .quick-btns button:hover:not(:disabled) {
        background: #444;
    }

    .auto-settings {
        background: #1a1a24;
        padding: 10px;
        border-radius: 6px;
        margin-bottom: 15px;
        border: 1px solid #333;
    }
    .setting-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .setting-row:last-child {
        margin-bottom: 0;
    }
    .setting-row input[type="number"] {
        width: 60px;
        background: #2a2a35;
        border: 1px solid #444;
        color: white;
        padding: 4px;
        border-radius: 4px;
        text-align: center;
    }
    .checkbox-row label {
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        font-size: 0.9rem;
    }

    .shoot-btn.stop-auto {
        background: #e74c3c;
        border-bottom-color: #c0392b;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(0.98); }
        100% { transform: scale(1); }
    }
</style>