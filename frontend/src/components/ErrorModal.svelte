<script lang="ts">
    import { errorMessage } from '../store/GameStore';
    import { fade, fly } from 'svelte/transition';

    function closeError() {
        errorMessage.set(null);
    }
</script>

{#if $errorMessage}
    <div class="error-overlay" transition:fade={{ duration: 200 }}>
        
        <div class="error-box" transition:fly={{ y: -50, duration: 300 }}>
            <div class="error-header">
                ⚠️ Hiba Történt
            </div>
            <div class="error-content">
                {$errorMessage}
            </div>
            <button class="error-btn" on:click={closeError}>
                Rendben
            </button>
        </div>

    </div>
{/if}

<style>
    .error-overlay {
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        z-index: 10000; /* Nagyon magas z-index, hogy minden felett legyen */
        display: flex;
        align-items: center;
        justify-content: center;
        backdrop-filter: blur(4px);
    }

    .error-box {
        background: #1e1e1e;
        border: 2px solid #e74c3c;
        border-radius: 12px;
        width: 400px;
        max-width: 90%;
        box-shadow: 0 15px 35px rgba(231, 76, 60, 0.2);
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }

    .error-header {
        background: #e74c3c;
        color: white;
        padding: 15px;
        font-weight: 800;
        font-size: 18px;
        text-transform: uppercase;
        text-align: center;
        letter-spacing: 1px;
    }

    .error-content {
        padding: 25px 20px;
        color: #ecf0f1;
        font-size: 15px;
        text-align: center;
        line-height: 1.5;
    }

    .error-btn {
        background: #2b2b2b;
        color: #fff;
        border: none;
        border-top: 1px solid #333;
        padding: 15px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        transition: background 0.2s;
    }

    .error-btn:hover {
        background: #333;
        color: #e74c3c;
    }
</style>