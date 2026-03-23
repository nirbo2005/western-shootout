import { writable, derived } from 'svelte/store';

const savedBalance = typeof sessionStorage !== 'undefined' ? sessionStorage.getItem('mock_stake_balance') : null;
const initialBalance = savedBalance ? parseFloat(savedBalance) : 1000;

export const currentBalance = writable<number>(initialBalance);
export const gameState = writable<'IDLE' | 'SHOOTING' | 'RESULT' | 'COOLDOWN'>('IDLE');
export const duelCooldown = writable<number>(0);

export const baseBet = writable<number>(1.0);
export const selectedCharacter = writable<string>('hero'); 

export const isMagnetActive = writable<boolean>(false);
export const isArmorActive = writable<boolean>(false);

export const chambers = writable<boolean[]>([true, true, true, true, true, true]);
export const currentRound = writable<number>(1);
export const showRevolver = writable<boolean>(true);

export const playerHP = writable<number>(100);
export const enemyHP = writable<number>(100);
export const multiEnemiesHP = writable<Record<string, number>>({});

export const serverSeedHash = writable<string>("Ismeretlen");
export const previousServerSeed = writable<string | null>(null);
export const clientSeed = writable<string>("lucky-seed");
export const currentNonce = writable<number>(0);

export const betHistory = writable<Array<{
    id: string;
    time: string;
    mode: string;
    bet: number;
    multiplier: number;
    payout: number;
}>>([]);

currentBalance.subscribe((value: number) => {
    if (typeof sessionStorage !== 'undefined') {
        sessionStorage.setItem('mock_stake_balance', value.toString());
    }
});

export const totalBet = derived(
    [baseBet, isMagnetActive, isArmorActive],
    ([$base, $magnet, $armor]: [number, boolean, boolean]) => {
        let costMultiplier = 1.0;
        if ($magnet && $armor) costMultiplier = 2.3;
        else if ($magnet) costMultiplier = 1.8;
        else if ($armor) costMultiplier = 1.5;
        
        return Number(($base * costMultiplier).toFixed(2));
    }
);

export const potentialMaxWin = derived(
    [baseBet],
    ([$base]: [number]) => Number(($base * 500).toFixed(2))
);

export const currentBetMode = derived(
    [isMagnetActive, isArmorActive],
    ([$magnet, $armor]: [boolean, boolean]) => {
        if ($magnet && $armor) return 'extreme';
        if ($magnet) return 'magnet';
        if ($armor) return 'armor';
        return 'base';
    }
);

export function resetDuelState() {
    playerHP.set(100);
    enemyHP.set(100);
    multiEnemiesHP.set({});
    chambers.set([true, true, true, true, true, true]);
    currentRound.set(1);
    showRevolver.set(true);
}

export function spendBullet(index: number) {
    chambers.update((c: boolean[]) => {
        const newChambers = [...c];
        if (index >= 0 && index < 6) newChambers[index] = false;
        return newChambers;
    });
}

export function setTotalBetManually(newTotal: number) {
    let costMultiplier = 1.0;
    
    isMagnetActive.subscribe((m: boolean) => {
        isArmorActive.subscribe((a: boolean) => {
            if (m && a) costMultiplier = 2.3;
            else if (m) costMultiplier = 1.8;
            else if (a) costMultiplier = 1.5;
        })();
    })();

    const calculatedBase = newTotal / costMultiplier;
    baseBet.set(Number(calculatedBase.toFixed(2)));
}