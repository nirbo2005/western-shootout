import os
import io
import json
import csv
import zstandard as zstd
import bisect
from typing import Dict, Any, Optional

class RGSReader:
    def __init__(self):
        # A root_path most már a hivatalos game_id mappára (stake_western_95) mutat
        self.root_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "math-sdk", 
            "games", 
            "stake_western_95", 
            "library"
        ))
        self.cache: Dict[str, dict] = {}
        self.load_all_data()

    def load_all_data(self):
        modes = ["base", "armor", "magnet", "extreme"]
        
        for mode in modes:
            book_file = f"books_{mode}.jsonl.zst"
            csv_file = f"lookUpTable_{mode}.csv"
            csv_file_opt = f"lookUpTable_{mode}_0.csv"
            
            book_paths = [
                os.path.join(self.root_path, "publish_files", book_file),
                os.path.join(self.root_path, "books", book_file)
            ]
            csv_paths = [
                os.path.join(self.root_path, "publish_files", csv_file),
                os.path.join(self.root_path, "publish_files", csv_file_opt),
                os.path.join(self.root_path, "lookup_tables", csv_file),
                os.path.join(self.root_path, "lookup_tables", csv_file_opt)
            ]
            
            valid_book = next((p for p in book_paths if os.path.exists(p)), None)
            valid_csv = next((p for p in csv_paths if os.path.exists(p)), None)

            if valid_book and valid_csv:
                try:
                    books_dict = {}
                    with open(valid_book, 'rb') as f:
                        dctx = zstd.ZstdDecompressor()
                        with dctx.stream_reader(f) as reader:
                            text_stream = io.TextIOWrapper(reader, encoding='utf-8')
                            for line in text_stream:
                                row = json.loads(line)
                                books_dict[row['id']] = row
                    
                    cum_weights = []
                    sim_ids = []
                    current_cum = 0
                    
                    with open(valid_csv, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        for row in reader:
                            if not row or len(row) < 3: 
                                continue
                            try:
                                sim_id = int(row[0])
                                weight = int(row[1])
                                current_cum += weight
                                cum_weights.append(current_cum)
                                sim_ids.append(sim_id)
                            except ValueError:
                                continue 

                    self.cache[mode] = {
                        'books': books_dict,
                        'cum_weights': cum_weights,
                        'sim_ids': sim_ids,
                        'total_weight': current_cum
                    }
                    print(f"INFO: Loaded {mode} ({len(books_dict)} rows, total weight: {current_cum})")
                except Exception as e:
                    print(f"ERROR: Failed to load data for {mode}: {e}")
            else:
                print(f"WARNING: Missing book or CSV for {mode}.")

    def get_row_by_float(self, mode: str, result_float: float) -> Optional[Dict[str, Any]]:
        current_mode = mode if mode in self.cache and self.cache[mode] else "base"
        
        if current_mode not in self.cache or not self.cache[current_mode]:
            return None

        data = self.cache[current_mode]
        total_weight = data['total_weight']
        
        if total_weight == 0:
            return None
            
        target_weight = result_float * total_weight
        
        idx = bisect.bisect_right(data['cum_weights'], target_weight)
        idx = min(idx, len(data['sim_ids']) - 1)
        
        selected_id = data['sim_ids'][idx]
        return data['books'].get(selected_id)

    def reload_cache(self):
        self.cache.clear()
        self.load_all_data()

rgs_reader = RGSReader()