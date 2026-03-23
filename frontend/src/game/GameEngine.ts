import { Application, Container, Graphics, Text, BlurFilter, AnimatedSprite, Ticker } from 'pixi.js';
import { isMagnetActive, isArmorActive, selectedCharacter } from '../store/GameStore';
import { get } from 'svelte/store';
import { assetLoader } from './AssetLoader';

class GameEngine {
    private app: Application | null = null;
    private mainContainer = new Container();
    private worldContainer = new Container();
    private uiContainer = new Container();
    private powerupContainer = new Container();
    
    // FIZIKAI ENTITÁSOK (Bal mindig Hős, Jobb mindig Bandita)
    private player!: AnimatedSprite; 
    private enemy!: AnimatedSprite;
    
    public extraCharacters: Map<string, AnimatedSprite> = new Map();
    
    // FIZIKAI UI ELEMEK (Bal oldali csík, Jobb oldali csík)
    private playerHPBar!: Graphics;
    private enemyHPBar!: Graphics;
    private playerHPText!: Text;
    private enemyHPText!: Text;
    private resultText: Text | null = null;
    
    private hasDrawnGun = false;
    private shakeIntensity = 0;

    public async initialize(canvas: HTMLCanvasElement) {
        if (this.app) {
            this.destroy();
        }

        this.app = new Application();
        await this.app.init({
            canvas,
            width: 1280,
            height: 720,
            backgroundColor: 0x0a0f14,
            antialias: true,
            resolution: window.devicePixelRatio || 1,
            autoDensity: true,
        });

        this.app.stage.addChild(this.mainContainer);
        this.mainContainer.addChild(this.worldContainer);
        this.mainContainer.addChild(this.powerupContainer);
        this.mainContainer.addChild(this.uiContainer);

        await assetLoader.initialize();
        this.setupScene();
        
        this.app.ticker.add(this.update, this);
    }

    private setupScene() {
        const skyGfx = new Graphics().rect(0, 0, 1280, 550).fill(0x0a0f14);
        this.worldContainer.addChild(skyGfx);

        const starsGfx = new Graphics();
        for (let i = 0; i < 80; i++) {
            const x = Math.random() * 1280;
            const y = Math.random() * 450;
            const size = Math.random() * 1.5 + 0.5;
            starsGfx.circle(x, y, size).fill({ color: 0xffffff, alpha: Math.random() * 0.6 + 0.2 });
        }
        this.worldContainer.addChild(starsGfx);

        const groundGfx = new Graphics()
            .rect(0, 550, 1280, 170).fill(0x231a12)
            .rect(0, 550, 1280, 4).fill({ color: 0x000000, alpha: 0.4 });
        this.worldContainer.addChild(groundGfx);

        this.createCharacters();
        this.createHPBars();
        
        // ALAPÁLLAPOT (IDLE) - 100 HP vizuális megjelenítése induláskor
        this.updateHPVisuals(100, 100);
    }

    private createCharacters() {
        // BAL OLDALI FIZIKAI SPRITE (Mindig a Hős kinézet)
        this.player = new AnimatedSprite(assetLoader.getHeroTextures('idle'));
        this.player.animationSpeed = 0.15;
        this.player.scale.set(4, 4);
        this.player.anchor.set(0.5, 1);
        this.player.x = 300;
        this.player.y = 560;
        this.player.tint = 0xffffff;
        this.player.play();
        this.worldContainer.addChild(this.player);

        // JOBB OLDALI FIZIKAI SPRITE (Mindig a Bandita kinézet)
        this.enemy = new AnimatedSprite(assetLoader.getHeroTextures('idle'));
        this.enemy.animationSpeed = 0.15;
        this.enemy.scale.set(-4, 4);
        this.enemy.anchor.set(0.5, 1);
        this.enemy.x = 980;
        this.enemy.y = 560;
        this.enemy.tint = 0xffcccc;
        this.enemy.play();
        this.worldContainer.addChild(this.enemy);

        this.updateVisualsFromStores();
    }

    private createHPBars() {
        const createBar = (x: number, y: number, isPlayer: boolean) => {
            const container = new Container();
            const bg = new Graphics().roundRect(0, 0, 240, 12, 6).fill({ color: 0x000000, alpha: 0.7 });
            const bar = new Graphics();
            const text = new Text({ 
                text: "100 HP", 
                style: { fill: 0xffffff, fontSize: 18, fontWeight: '900', stroke: { color: 0x000000, width: 4 } } 
            });
            text.y = -30;
            if (!isPlayer) text.x = 240 - text.width;
            container.addChild(bg, bar, text);
            container.x = x; container.y = y;
            this.uiContainer.addChild(container);
            return { bar, text };
        };

        const pUI = createBar(100, 450, true);
        this.playerHPBar = pUI.bar; 
        this.playerHPText = pUI.text;
        
        const eUI = createBar(940, 450, false);
        this.enemyHPBar = eUI.bar; 
        this.enemyHPText = eUI.text;
    }

    // LOGIKAI HP -> FIZIKAI ROUTER
    public updateHPVisuals(logicalPVal: number, logicalEVal: number) {
        const char = get(selectedCharacter);
        
        // Útválasztás: ha banditára fogadtunk, a logikai pVal a jobb oldali UI-ra megy
        const leftHP = char === 'hero' ? logicalPVal : logicalEVal;
        const rightHP = char === 'hero' ? logicalEVal : logicalPVal;

        const getHPColor = (val: number) => {
            if (val > 60) return 0x2ecc71;
            if (val > 30) return 0xf1c40f;
            return 0xe74c3c;
        };

        const drawBar = (g: Graphics, val: number) => {
            if (!g || g.destroyed) return;
            const color = getHPColor(val);
            g.clear().roundRect(0, 0, Math.max(0, (val / 100) * 240), 12, 6).fill(color);
        };

        drawBar(this.playerHPBar, leftHP);
        drawBar(this.enemyHPBar, rightHP);
        
        if (this.playerHPText && !this.playerHPText.destroyed) {
            this.playerHPText.text = `${Math.ceil(leftHP)} HP`;
        }
        if (this.enemyHPText && !this.enemyHPText.destroyed) {
            this.enemyHPText.text = `${Math.ceil(rightHP)} HP`;
            this.enemyHPText.x = 240 - this.enemyHPText.width;
        }
    }

    public setupGroupShootoutEnemies(count: number) {
        const char = get(selectedCharacter);
        
        // A logikai ENEMY eltüntetése
        const logicalEnemySprite = char === 'hero' ? this.enemy : this.player;
        logicalEnemySprite.visible = false;
        
        const logicalEnemyHPBarContainer = char === 'hero' ? this.enemyHPBar.parent : this.playerHPBar.parent;
        if (logicalEnemyHPBarContainer) {
            logicalEnemyHPBarContainer.visible = false;
        }
        
        // Az ellenség vizuális skintje: Ha hősre fogadtunk, akkor Banditák spawnolnak, ha Banditára, akkor Hősök.
        const enemyTint = char === 'hero' ? 0xdd9999 : 0xffffff;

        for (let i = 0; i < count; i++) {
            const id = `ENEMY_${i+1}`;
            const eSprite = new AnimatedSprite(assetLoader.getHeroTextures('idle'));
            eSprite.animationSpeed = Math.random() * 0.05 + 0.12;
            eSprite.scale.set(-2.5, 2.5); // Kis ellenségek méretezése
            eSprite.anchor.set(0.5, 1);
            
            const row = Math.floor(i / 3);
            const col = i % 3;
            // A pozíció mindig a jobb oldalra esik a Group Shootoutnál
            eSprite.x = 800 + (col * 140) + (row * 60);
            eSprite.y = 520 + (row * 80);
            eSprite.tint = enemyTint;
            
            eSprite.play();
            this.worldContainer.addChild(eSprite);
            this.extraCharacters.set(id, eSprite);
        }
    }

    public spawnAngel() {
        const char = get(selectedCharacter);
        const logicalPlayerSprite = char === 'hero' ? this.player : this.enemy;

        const angel = new AnimatedSprite(assetLoader.getHeroTextures('idle'));
        angel.animationSpeed = 0.15;
        angel.scale.set(3, 3);
        angel.anchor.set(0.5, 1);
        
        // Az angyal pont a logikai játékos fölé spawnol
        angel.x = logicalPlayerSprite.x;
        angel.y = logicalPlayerSprite.y - 250;
        angel.tint = 0xffffaa;
        angel.alpha = 0.8;
        angel.play();
        
        this.worldContainer.addChild(angel);
        this.extraCharacters.set('ANGEL', angel);
    }

    // LOGIKAI KARAKTER -> FIZIKAI SPRITE ROUTER
    public getCharacter(logicalId: string): AnimatedSprite | null {
        const char = get(selectedCharacter);
        
        if (logicalId === 'PLAYER') {
            return char === 'hero' ? this.player : this.enemy;
        }
        if (logicalId === 'ENEMY') {
            return char === 'hero' ? this.enemy : this.player;
        }
        
        return this.extraCharacters.get(logicalId) || null;
    }

    public async playShootSequence(attackerId: string, targetId: string, hit: boolean, zone: string) {
        if (!this.app) return;
        
        // Lekérjük a fizikai sprite-okat
        const attacker = this.getCharacter(attackerId);
        const target = this.getCharacter(targetId);
        
        if (!attacker || !target) return;

        if (!attacker.destroyed) {
            attacker.textures = assetLoader.getHeroTextures('draw_and_shoot');
            attacker.loop = false;
            attacker.gotoAndPlay(0);

            await new Promise<void>(res => {
                const timeout = setTimeout(res, 450);
                attacker.onFrameChange = (frame: number) => {
                    if (frame >= 3) {
                        clearTimeout(timeout);
                        attacker.onFrameChange = undefined;
                        res();
                    }
                };
            });
        }

        // Fizikai X skálázás alapján tudjuk, hogy merre néz (4 = jobb, -4 = bal)
        const isAttackerFacingRight = attacker.scale.x > 0;
        const sX = attacker.x + (isAttackerFacingRight ? 60 : -60);
        const sY = attacker.y - (attacker.getBounds().height * 0.5);

        const eX = target.x;
        let eY = target.y - (target.getBounds().height * 0.5); 
        if (hit) {
            if (zone === 'HEAD') eY = target.y - target.getBounds().height + 20;
            if (zone === 'LEGS') eY = target.y - 20;
        } else {
            eY = target.y - target.getBounds().height - 100;
        }

        this.playMuzzleFlash(sX, sY);
        await this.fireTracer(sX, sY, eX, eY);

        if (hit && !target.destroyed) {
            const originalTint = target.tint; // Mentsük el a fizikai sprite eredeti színét
            target.tint = 0xff0000;
            setTimeout(() => { 
                if (!target.destroyed) {
                    target.tint = originalTint; // Villogás után állítsuk vissza
                } 
            }, 80);
            this.applyHitEffect(target, zone);
            // Ha a bal oldali sprite kapja a találatot, nagyobbat rázkódik a képernyő
            this.shakeIntensity = target === this.player ? 12 : 5;
        }

        if (!attacker.destroyed) {
            attacker.textures = assetLoader.getHeroTextures('idle');
            attacker.loop = true;
            attacker.play();
        }
    }

    private async fireTracer(sx: number, sy: number, ex: number, ey: number) {
        if (!this.app) return;
        
        const bullet = new Graphics().circle(0, 0, 4).fill(0xffd700);
        bullet.x = sx; bullet.y = sy;
        
        const trail = new Graphics()
            .setStrokeStyle({ width: 3, color: 0xfff0ad, alpha: 0.6 })
            .moveTo(sx, sy)
            .lineTo(ex, ey);
        trail.filters = [new BlurFilter({ strength: 2 })];
        
        this.worldContainer.addChild(trail);
        this.worldContainer.addChild(bullet);

        return new Promise<void>(res => {
            let progress = 0;
            const ticker = this.app?.ticker;
            const speed = 0.25;
            
            const animate = (t: Ticker) => {
                if (bullet.destroyed || trail.destroyed) {
                    ticker?.remove(animate);
                    res();
                    return;
                }
                
                progress += speed * t.deltaTime;
                if (progress >= 1) {
                    ticker?.remove(animate);
                    bullet.destroy();
                    
                    let alpha = 0.6;
                    const fade = (ft: Ticker) => {
                        alpha -= 0.1 * ft.deltaTime;
                        trail.alpha = alpha;
                        if (alpha <= 0) {
                            ticker?.remove(fade);
                            trail.destroy();
                        }
                    };
                    ticker?.add(fade);
                    res();
                } else {
                    bullet.x = sx + (ex - sx) * progress;
                    bullet.y = sy + (ey - sy) * progress;
                }
            };
            ticker?.add(animate);
        });
    }

    private applyHitEffect(target: AnimatedSprite, zone: string) {
        if (!this.app || !target || target.destroyed) return;

        const label = new Text({ 
            text: zone === 'HEAD' ? 'CRITICAL!' : zone, 
            style: { fill: zone === 'HEAD' ? 0xffcc00 : 0xffffff, fontSize: 32, fontWeight: '900', stroke: {color: 0x000000, width: 4} } 
        });
        label.anchor.set(0.5);
        label.x = target.x;
        label.y = target.y - target.getBounds().height - 20;
        this.uiContainer.addChild(label);

        const ticker = this.app.ticker;
        const anim = (t: Ticker) => {
            if (label.destroyed) {
                ticker.remove(anim);
                return;
            }
            label.y -= 1.8 * t.deltaTime;
            label.alpha -= 0.04 * t.deltaTime;
            if (label.alpha <= 0) {
                ticker.remove(anim);
                label.destroy();
            }
        };
        ticker.add(anim);
    }

    private playMuzzleFlash(x: number, y: number) {
        if (!this.app) return;
        const flash = new Graphics().circle(0, 0, 30).fill({ color: 0xffd700, alpha: 0.9 });
        flash.x = x; flash.y = y;
        flash.filters = [new BlurFilter({ strength: 8 })];
        this.worldContainer.addChild(flash);
        setTimeout(() => { if (!flash.destroyed) flash.destroy(); }, 50);
    }

    private update(ticker: Ticker) {
        if (!this.app) return;

        if (this.shakeIntensity > 0) {
            this.mainContainer.x = (Math.random() - 0.5) * this.shakeIntensity;
            this.mainContainer.y = (Math.random() - 0.5) * this.shakeIntensity;
            this.shakeIntensity *= 0.88;
            if (this.shakeIntensity < 0.1) {
                this.shakeIntensity = 0;
                this.mainContainer.x = 0; this.mainContainer.y = 0;
            }
        }
    }

    public showResultText(msg: string, color: number) {
        this.cleanupResultText();
        this.resultText = new Text({ 
            text: msg, 
            style: { 
                fill: color, 
                fontSize: 84, 
                fontWeight: '900', 
                align: 'center', 
                stroke: { color: 0x000000, width: 10 },
                dropShadow: { color: 0x000000, blur: 4, distance: 4, alpha: 0.5 }
            } 
        });
        this.resultText.anchor.set(0.5); 
        this.resultText.x = 640; 
        this.resultText.y = 280;
        this.uiContainer.addChild(this.resultText);
    }

    public cleanupResultText() {
        if (this.resultText) {
            if (!this.resultText.destroyed) this.resultText.destroy();
            this.resultText = null;
        }
    }

    public playDeathAnim(logicalId: string) {
        const char = this.getCharacter(logicalId);
        if (char && !char.destroyed) {
            char.textures = assetLoader.getHeroTextures('death');
            char.loop = false;
            char.gotoAndPlay(0);
        }
    }

    public cleanup() {
        this.cleanupResultText();
        this.uiContainer.children
            .filter((c: any) => c instanceof Text && c !== this.playerHPText && c !== this.enemyHPText)
            .forEach((c: any) => { if (!c.destroyed) c.destroy(); });
        
        this.powerupContainer.removeChildren();
        
        this.extraCharacters.forEach(char => {
            if (!char.destroyed) char.destroy();
        });
        this.extraCharacters.clear();

        // Fizikai entitások újra-engedélyezése
        this.player.visible = true;
        this.enemy.visible = true;
        if (this.playerHPBar.parent) this.playerHPBar.parent.visible = true;
        if (this.enemyHPBar.parent) this.enemyHPBar.parent.visible = true;

        if (this.player && !this.player.destroyed) {
            this.player.textures = assetLoader.getHeroTextures('idle');
            this.player.loop = true;
            this.player.tint = 0xffffff;
            this.player.play();
        }
        if (this.enemy && !this.enemy.destroyed) {
            this.enemy.textures = assetLoader.getHeroTextures('idle');
            this.enemy.loop = true;
            this.enemy.tint = 0xffcccc;
            this.enemy.play();
        }
        
        this.updateHPVisuals(100, 100);
        this.updateVisualsFromStores();
    }

    public updateVisualsFromStores() {
        if (!this.app) return;
        this.powerupContainer.removeChildren();
        
        const isArmor = get(isArmorActive);
        const isMagnet = get(isMagnetActive);
        const char = get(selectedCharacter);

        if (this.player && !this.player.destroyed && this.enemy && !this.enemy.destroyed) {
            // A Bal sprite (player) mindig fehér, a Jobb (enemy) mindig pirosas
            this.player.tint = 0xffffff;
            this.enemy.tint = 0xffcccc;

            // Logikai router a módosítókhoz
            const logicalPlayerSprite = char === 'hero' ? this.player : this.enemy;
            const logicalEnemySprite = char === 'hero' ? this.enemy : this.player;

            if (isArmor) {
                // A Páncél mindig a fogadott karaktert (logicalPlayer) védi
                const armorGfx = new Graphics()
                    .roundRect(-45, -140, 90, 150, 10)
                    .fill({ color: 0x3498db, alpha: 0.3 })
                    .stroke({ width: 4, color: 0xffffff, alpha: 0.6 });
                armorGfx.x = logicalPlayerSprite.x;
                armorGfx.y = logicalPlayerSprite.y;
                armorGfx.filters = [new BlurFilter({ strength: 2 })];
                this.powerupContainer.addChild(armorGfx);
            }

            if (isMagnet) {
                // A Mágnes mindig a célpontra (logicalEnemy) kerül
                const magnetGfx = new Graphics()
                    .circle(0, -70, 60)
                    .stroke({ width: 4, color: 0xe74c3c, alpha: 0.8 });
                
                magnetGfx.moveTo(-80, -70).lineTo(80, -70);
                magnetGfx.moveTo(0, -150).lineTo(0, 10);
                
                magnetGfx.x = logicalEnemySprite.x;
                magnetGfx.y = logicalEnemySprite.y;
                this.powerupContainer.addChild(magnetGfx);
            }
        }
    }

    public destroy() {
        if (this.app) {
            this.app.ticker.remove(this.update, this);
            this.app.destroy(true, { children: true, texture: true });
            this.app = null;
        }
    }
}

export const gameEngine = new GameEngine();