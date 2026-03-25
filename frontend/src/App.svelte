<script lang="ts">
    import { onMount } from 'svelte';
    import './app.css'; // Külső stíluslap importálása
    
    import GameCanvas from './components/GameCanvas.svelte';
    import BetPanel from './components/BetPanel.svelte';
    import ProvablyFair from './components/ProvablyFair.svelte';
    import BetHistory from './components/BetHistory.svelte';
    import RevolverUI from './components/RevolverUI.svelte';
    
    // --- ÚJ IMPORTOK: RESUME STATE ÉS HIBAKEZELÉS ---
    import ErrorModal from './components/ErrorModal.svelte';
    import { isResuming, storedActiveGame, currentStepIndex } from './store/GameStore';
    import { sequencePlayer } from './game/SequencePlayer';
    import { stakeClient } from './api/StakeClient';
  
    let isInitialized = false;
  
    onMount(async () => {
        try {
            await stakeClient.initialize();
            isInitialized = true;
            
            // Ha van félbemaradt játék, rövid késleltetéssel (hogy a Canvas betöltsön) elindítjuk
            if ($isResuming && $storedActiveGame) {
                setTimeout(() => {
                    sequencePlayer.play($storedActiveGame, $currentStepIndex);
                }, 800);
            }
        } catch (error) {
            console.error("Initialization failed:", error);
        }
    });
</script>
  
<main>
    {#if isInitialized}
        <div class="game-layout">
            
            <ErrorModal />
            
            {#if $isResuming}
                <div class="resume-overlay">
                    <div class="resume-box">
                        <h2>⚠️ Félbemaradt játék!</h2>
                        <p>Visszaállítás folyamatban...</p>
                        <div class="spinner"></div>
                    </div>
                </div>
            {/if}

            <aside class="sidebar">
                <div class="panel-section top-panel">
                    <BetPanel />
                </div>
                <div class="panel-section history-panel">
                    <BetHistory />
                </div>
            </aside>
            
            <section class="game-container">
                <div class="game-wrapper">
                    <GameCanvas />
                </div>
                
                <div class="revolver-wrapper">
                    <RevolverUI />
                </div>

                <div class="pf-wrapper">
                    <ProvablyFair />
                </div>
            </section>
        </div>
    {:else}
        <div class="loading-screen">
            <span>Hitelesítés folyamatban...</span>
        </div>
    {/if}
</main>

<style>
    /* CSS a Resume Overlay-hez */
    .resume-overlay {
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0, 0, 0, 0.85);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        backdrop-filter: blur(5px);
    }
    .resume-box {
        background: #1e1e1e;
        border: 2px solid #f1c40f;
        padding: 30px;
        border-radius: 12px;
        text-align: center;
        color: #fff;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .resume-box h2 {
        color: #f1c40f;
        margin-top: 0;
        margin-bottom: 10px;
    }
    .spinner {
        margin: 20px auto 0;
        width: 40px; height: 40px;
        border: 4px solid rgba(255,255,255,0.1);
        border-left-color: #f1c40f;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    @keyframes spin { 100% { transform: rotate(360deg); } }
</style>