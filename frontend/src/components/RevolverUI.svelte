<script lang="ts">
    import { chambers, currentRound } from '../store/GameStore';
    import { fade, scale } from 'svelte/transition';

    const positions = [
        { x: 50, y: 15 },  // 12 óra (1. töltény)
        { x: 80, y: 32 },  // 2 óra
        { x: 80, y: 68 },  // 4 óra
        { x: 50, y: 85 },  // 6 óra
        { x: 20, y: 68 },  // 8 óra
        { x: 20, y: 32 }   // 10 óra
    ];

    // Folyamatos forgás minden lépésnél, támogatva a végtelen hosszúságú (6+ körös) minigame-eket
    $: rotation = ($currentRound - 1) * 60;

    // Modulo 6 logika: az aktív kamra mindig 0 és 5 között marad
    $: activeIndex = ($currentRound - 1) % 6;

    // A vizuális töltények állapota
    $: displayChambers = positions.map((_, i) => {
        // Group shootoutnál és hosszú döntetlennél, ha az engine vizuálisan nem tölt újra
        // (nem reseteli a chambers store-t), kikényszerítjük, hogy az aktív index utáni kamrák 
        // egy új ciklusban teleinek látszódjanak, a kilőttek pedig üresnek.
        if (i < activeIndex) {
            return false; // Ebben a % 6 -os "henger ciklusban" már elsütöttük
        }
        // Az aktuális és a hátralévő kamrákhoz lekérjük a valós store állapotot
        // Ha az aktuális épp elsül (store szerint false), az is látszani fog (empty).
        return $chambers[i];
    });
</script>

<div class="revolver-container" in:fade>
    <div class="cylinder" style="transform: rotate({rotation}deg)">
        <div class="axis"></div>

        {#each positions as pos, i}
            <div 
                class="chamber" 
                class:empty={!displayChambers[i]}
                class:active={activeIndex === i}
                style="left: {pos.x}%; top: {pos.y}%; transform: translate(-50%, -50%);"
            >
                {#if displayChambers[i]}
                    <div class="bullet" in:scale={{duration: 200, start: 0.5}}>
                        <div class="primer"></div>
                    </div>
                {/if}
            </div>
        {/each}
    </div>
    
    <div class="round-indicator">
        KÖR: <span class="count">{$currentRound}</span>
    </div>
</div>