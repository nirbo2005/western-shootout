import os
import io
import json
import csv
import zstandard as zstd
import bisect
from typing import Dict, Any, Optional

class RGSReader:
    def __init__(self):
        self.root_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "math-sdk", 
            "games", 
            "stake_western_95", 
            "library"
        ))
        
        # A cache már csak az ID-kat és a súlyokat tárolja, NEM a teljes JSON-t!
        self.cache: Dict[str, dict] = {}
        self.load_index_data()

    def load_index_data(self):
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
                        'book_path': valid_book, # Csak az útvonalat mentjük el!
                        'cum_weights': cum_weights,
                        'sim_ids': sim_ids,
                        'total_weight': current_cum
                    }
                    print(f"INFO: Indexed {mode} (total weight: {current_cum})")
                except Exception as e:
                    print(f"ERROR: Failed to load index data for {mode}: {e}")
            else:
                print(f"WARNING: Missing book or CSV for {mode}.")

    def _fetch_single_row_from_zst(self, book_path: str, target_id: int) -> Optional[Dict[str, Any]]:
        """Lassan, de memóriabiztosan kikeresi az egyetlen nyertes sort a tömörített fájlból."""
        try:
            with open(book_path, 'rb') as f:
                dctx = zstd.ZstdDecompressor()
                with dctx.stream_reader(f) as reader:
                    text_stream = io.TextIOWrapper(reader, encoding='utf-8')
                    for line in text_stream:
                        if not line.strip(): continue
                        # Csak egy gyors string keresés (gyorsabb, mint minden sort JSON parse-olni)
                        if f'"id": {target_id},' in line or f'"id":{target_id},' in line:
                            row = json.loads(line)
                            if row['id'] == target_id:
                                return row
            return None
        except Exception as e:
            print(f"ERROR reading zst: {e}")
            return None

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
        
        # 3. Lépés: Most, hogy megvan a nyertes ID, kiolvassuk a fájlból
        return self._fetch_single_row_from_zst(data['book_path'], selected_id)

    def reload_cache(self):
        self.cache.clear()
        self.load_index_data()

rgs_reader = RGSReader()