import sys
import os
import json
import io
import csv
import zstandard as zstd
from pathlib import Path

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Villámgyors JSON parser (ha telepítve van)
try:
    import orjson
    JSON_LOADS = orjson.loads
    HAS_ORJSON = True
except ImportError:
    import json
    JSON_LOADS = json.loads
    HAS_ORJSON = False

current_dir = Path(__file__).resolve().parent
math_sdk_root = current_dir.parent
if str(math_sdk_root) not in sys.path:
    sys.path.insert(0, str(math_sdk_root))

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class WesternExplorer(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Western Shootout - RGS Math Explorer v12.0 (Cost-Aware V4)")
        self.geometry("1400x900")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="MATH STATS", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.pack(pady=20)

        self.mode_var = ctk.StringVar(value="base")
        for mode in ["base", "armor", "magnet", "extreme"]:
            rb = ctk.CTkRadioButton(
                self.sidebar, 
                text=mode.capitalize(), 
                variable=self.mode_var, 
                value=mode, 
                command=self.load_and_analyze
            )
            rb.pack(pady=10, padx=20, anchor="w")

        # Dinamikus Költség Kijelző
        self.cost_lbl = ctk.CTkLabel(self.sidebar, text="Bet Cost: 1.0x", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f1c40f")
        self.cost_lbl.pack(pady=(10, 20))

        self.v_label = ctk.CTkLabel(self.sidebar, text="STEP VERIFIER (Last Win):", font=ctk.CTkFont(size=11, weight="bold"))
        self.v_label.pack(pady=(10, 0), padx=20, anchor="w")
        
        self.step_box = ctk.CTkTextbox(self.sidebar, width=200, height=300, font=ctk.CTkFont(size=10), fg_color="#1e1e1e")
        self.step_box.pack(pady=10, padx=10)

        engine_text = "Engine: Predetermined (V4)\nParser: ORJSON (Turbo)" if HAS_ORJSON else "Engine: Predetermined (V4)\nParser: Standard (Slow)\nTip: pip install orjson"
        self.info_lbl = ctk.CTkLabel(self.sidebar, text=engine_text, font=ctk.CTkFont(size=10), text_color="#2ecc71" if HAS_ORJSON else "gray")
        self.info_lbl.pack(side="bottom", pady=10)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        self.stats_labels = {}
        metrics = ["RTP", "Hit Rate", "Volatility", "Zero Rate", "Max Win", "Outcomes"]
        for i, metric in enumerate(metrics):
            frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
            frame.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            
            lbl_title = ctk.CTkLabel(frame, text=metric.upper(), font=ctk.CTkFont(size=11, weight="bold"), text_color="#3498db")
            lbl_title.pack(pady=(10, 0))
            
            lbl_val = ctk.CTkLabel(frame, text="-", font=ctk.CTkFont(size=22, weight="bold"))
            lbl_val.pack(pady=(0, 10))
            self.stats_labels[metric] = lbl_val

        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, columnspan=6, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        self.content_frame.grid_columnconfigure(0, weight=2)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        self.chart_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.chart_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.outcome_scroll = ctk.CTkScrollableFrame(self.content_frame, label_text="Események Eloszlása (Excel validáció)")
        self.outcome_scroll.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        self.load_and_analyze()

    def load_and_analyze(self):
        self.step_box.delete("1.0", "end")
        
        for widget in self.outcome_scroll.winfo_children():
            widget.destroy()

        mode = self.mode_var.get()
        mode_costs = {"base": 1.0, "armor": 1.5, "magnet": 1.8, "extreme": 2.3}
        cost = mode_costs.get(mode, 1.0)
        
        # Frissítjük a UI-t a helyes költséggel
        self.cost_lbl.configure(text=f"Bet Cost: {cost}x")
        
        book_path = math_sdk_root / "games" / "stake_western_95" / "library" / "books" / f"books_{mode}.jsonl.zst"
        if not book_path.exists():
            book_path = math_sdk_root / "games" / "stake_western_95" / "library" / "publish_files" / f"books_{mode}.jsonl.zst"
            if not book_path.exists():
                self.step_box.insert("1.0", f"Hiba: Fájl nem található\n{book_path}")
                return

        csv_path = math_sdk_root / "games" / "stake_western_95" / "library" / "lookup_tables" / f"lookUpTable_{mode}.csv"
        if not csv_path.exists():
            csv_path = math_sdk_root / "games" / "stake_western_95" / "library" / "publish_files" / f"lookUpTable_{mode}_0.csv"

        try:
            weights = {}
            if csv_path.exists():
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            try: weights[int(row[0])] = int(row[1])
                            except ValueError: continue
                                
            use_fallback_weights = len(weights) == 0

            parsed_rows = []
            last_win_data = None
            
            with open(book_path, 'rb') as f:
                dctx = zstd.ZstdDecompressor()
                with dctx.stream_reader(f) as reader:
                    text_stream = io.TextIOWrapper(reader, encoding='utf-8')
                    for line in text_stream:
                        if not line.strip(): continue
                        obj = JSON_LOADS(line)
                        sim_id = obj.get("id")
                        w = weights.get(sim_id, 1 if use_fallback_weights else 0)
                        
                        mult = 0.0
                        event_label = "Ismeretlen Esemény"
                        
                        for ev in obj.get("events", []):
                            if isinstance(ev, dict) and "round_data" in ev:
                                round_data = ev["round_data"]
                                if "multiplier" in round_data:
                                    mult = float(round_data["multiplier"])
                                
                                target = round_data.get("target_outcome")
                                if target:
                                    event_label = f"Group Shootout ({target['enemies']},{target['rounds']})"
                                else:
                                    if mult == 0.0: event_label = "Standard Vesztés"
                                    elif mult == 1.0: event_label = "Standard Döntetlen"
                                    elif mult == 2.0: event_label = "Standard Nyerés"
                                    elif mult == 5.0: event_label = "Angel Revive"
                                    elif mult >= 500.0: event_label = "Wincap"
                                    else: event_label = "Ismeretlen"
                                
                                if mult > 0 and w > 0:
                                    last_win_data = {
                                        "mult": mult,
                                        "label": event_label,
                                        "steps": round_data.get("steps", [])
                                    }
                                break
                                
                        parsed_rows.append({
                            "mult": mult,
                            "weight": w,
                            "label": event_label
                        })

            total_spins = sum(r["weight"] for r in parsed_rows)
            if total_spins == 0:
                self.step_box.insert("1.0", "Hiba: A súlyozott minta 0.")
                return
            
            total_win = sum(r["mult"] * r["weight"] for r in parsed_rows)
            
            # --- V4 COST-AWARE RTP SZÁMÍTÁS ---
            total_spent = total_spins * cost
            rtp = (total_win / total_spent) * 100
            
            hit_spins = sum(r["weight"] for r in parsed_rows if r["mult"] > 0)
            hit_rate = (hit_spins / total_spins) * 100
            zero_spins = sum(r["weight"] for r in parsed_rows if r["mult"] == 0)
            zero_rate = (zero_spins / total_spins) * 100
            max_win = max((r["mult"] for r in parsed_rows if r["weight"] > 0), default=0.0)

            mean_mult = total_win / total_spins
            variance = sum(r["weight"] * ((r["mult"] - mean_mult) ** 2) for r in parsed_rows) / total_spins
            volatility = np.sqrt(variance)

            self.stats_labels["RTP"].configure(text=f"{rtp:.4f}%", text_color="#2ecc71" if 95.0 <= rtp <= 97.0 else "#e74c3c")
            self.stats_labels["Hit Rate"].configure(text=f"{hit_rate:.2f}%")
            self.stats_labels["Volatility"].configure(text=f"{volatility:.2f}")
            self.stats_labels["Zero Rate"].configure(text=f"{zero_rate:.2f}%")
            self.stats_labels["Max Win"].configure(text=f"{max_win:.2f}x")
            self.stats_labels["Outcomes"].configure(text=f"{total_spins:,}")

            event_dict = {}
            for r in parsed_rows:
                if r["weight"] > 0:
                    key = (r["label"], r["mult"])
                    event_dict[key] = event_dict.get(key, 0) + r["weight"]
                
            sorted_events = sorted(event_dict.items(), key=lambda x: (-x[0][1], x[0][0]))
            
            for (label, mult), count in sorted_events:
                prob = (count / total_spins) * 100
                
                row_frame = ctk.CTkFrame(self.outcome_scroll, fg_color="#1e1e1e", corner_radius=5)
                row_frame.pack(fill="x", pady=2, padx=2)
                
                color = "#e74c3c" if mult == 0 else "#2ecc71" if mult <= 2 else "#f1c40f"
                if "Group" in label: color = "#9b59b6" 
                
                lbl_mult = ctk.CTkLabel(row_frame, text=f"{mult:.2f}x", font=ctk.CTkFont(weight="bold"), text_color=color, width=60, anchor="w")
                lbl_mult.pack(side="left", padx=5, pady=5)
                
                lbl_name = ctk.CTkLabel(row_frame, text=label, font=ctk.CTkFont(size=10), text_color="#ecf0f1", anchor="w")
                lbl_name.pack(side="left", fill="x", expand=True)

                lbl_count = ctk.CTkLabel(row_frame, text=f"{count:,} db ({prob:.3f}%)", font=ctk.CTkFont(size=10), text_color="#aaaaaa")
                lbl_count.pack(side="right", padx=5, pady=5)

            if last_win_data:
                steps = last_win_data["steps"]
                self.step_box.insert("1.0", f"MODE: {mode}\nLABEL: {last_win_data['label']}\nWIN: {last_win_data['mult']}x\n\nSTEPS:\n{json.dumps(steps, indent=2)}")
            else:
                self.step_box.insert("1.0", "Nincs nyertes kör a könyvben.")
            
            weights_arr = np.array([r["weight"] for r in parsed_rows], dtype=np.int64)
            mults_arr = np.array([r["mult"] for r in parsed_rows], dtype=np.float64)
            
            valid_mask = weights_arr > 0
            if np.any(valid_mask):
                unrolled_mults = np.repeat(mults_arr[valid_mask], weights_arr[valid_mask])
            else:
                unrolled_mults = np.array([])
                
            self.update_charts(unrolled_mults, cost)
            
        except Exception as e:
            self.step_box.insert("1.0", f"Analízis hiba: {str(e)}")

    def update_charts(self, multipliers, cost):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        plt.close('all')
        if len(multipliers) == 0: return

        plt.rcParams.update({'text.color': "white", 'axes.labelcolor': "white", 'xtick.color': "white", 'ytick.color': "white"})
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 8), facecolor='#2b2b2b')
        fig.subplots_adjust(hspace=0.4, bottom=0.1, top=0.95, left=0.15, right=0.95)

        wins_only = multipliers[multipliers > 0]
        if len(wins_only) > 0:
            ax1.hist(wins_only, bins=50, color='#3498db', alpha=0.8, log=True)
            ax1.set_title("Win Distribution", pad=10)
            ax1.set_xlabel("Multiplier (x)")
        ax1.set_facecolor('#1e1e1e')
        ax1.grid(True, alpha=0.1)

        # RTP konvergencia cost figyelembevételével
        cum_rtp = (np.cumsum(multipliers) / ((np.arange(len(multipliers)) + 1) * cost)) * 100
        
        if len(cum_rtp) > 10000:
            indices = np.linspace(0, len(cum_rtp)-1, 10000, dtype=int)
            cum_rtp_plot = cum_rtp[indices]
            x_axis = indices
        else:
            cum_rtp_plot = cum_rtp
            x_axis = np.arange(len(cum_rtp))
            
        ax2.plot(x_axis, cum_rtp_plot, color='#2ecc71', linewidth=1.5)
        ax2.axhline(y=96.0, color='#e67e22', linestyle='--', alpha=0.5, label="Target 96%")
        ax2.set_title("RTP Convergence (Cost Adjusted)", pad=10)
        ax2.set_xlabel("Iterations")
        ax2.set_ylabel("Cumulative RTP %")
        ax2.set_facecolor('#1e1e1e')
        ax2.grid(True, alpha=0.1)

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

if __name__ == "__main__":
    app = WesternExplorer()
    app.mainloop()