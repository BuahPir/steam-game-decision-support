import requests
import time
import re
import datetime
from typing import Optional, Dict

# -------------------------------------------------------------------
# NEW Scraper Class (from your code)
# This class finds the JSON endpoint and downloads the entire database.
# -------------------------------------------------------------------
class Scraper:
    def __init__(self, domain="www.cpubenchmark.net"):
        #parse arguments and get a list of items
        if not domain in ["www.videocardbenchmark.net", "www.cpubenchmark.net", "www.harddrivebenchmark.net"]:
            raise ValueError("Invaid domain given.")
        self.domain = domain
        self.url = {
            "www.cpubenchmark.net": "https://www.cpubenchmark.net/CPU_mega_page.html",
            "www.videocardbenchmark.net": "https://www.videocardbenchmark.net/GPU_mega_page.html",
            "www.harddrivebenchmark.net": "https://www.harddrivebenchmark.net/hdd-mega-page.html"
        }[domain]
        self.scrape()
    
    #search through the gpu list
    def search(self, query, limit=None):
        query_words = query.lower().split(" ")

        results = []
        for item in self.items:
            item_name_lower = item["name"].lower()
            matches = 0
            
            # --- START OF NEW LOGIC ---
            # Check if each word from the query is *in* the full item name
            for word in query_words:
                if word in item_name_lower:
                    matches += 1
            # --- END OF NEW LOGIC ---
            
            if matches > 0:
                results.append((item, matches))

        #sort to get the most relavent results on top
        results = sorted(results, key=lambda x: x[1], reverse=True)

        if limit != None:
            results = results[:limit]
        return results

    #get a single item based on its id
    def get_item(self, item_id):
        for item in self.items:
            if int(item["id"]) == int(item_id):
                return item
        return None

    #download and cache the data
    def scrape(self):
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",#Header to mimic a browser request
            "Accept-Language": "en-US,en;q=0.9",
            "referrer": self.url,
            "x-requested-with": "XMLHttpRequest",
            "accept": "application/json, text/javascript, */*; q=0.01",
        }
        r1 = session.get(self.url, headers=headers)
        
        url2 = f"https://{self.domain}/data/?_={str(int(time.time()*1000))}"
        r2 = session.get(url2, headers=headers)

        self.items = r2.json()["data"] 
        
        return self.items

    #get every item in the database, sorted by a specific critiera
    def get_sorted_list(self, sort_by="rank", order="descending", limit=None, item_type=None):
        results = []

        #define types for the values so that we know how to sort them
        if self.domain == "www.cpubenchmark.net":
            item_types = {
                "cat": "string", "cores": "number", "cpuCount": "number",
                "cpumark": "number", "date": "date", "href": "string",
                "id": "number", "logicals": "number", "name": "string",
                "output": "bool", "powerPerf": "number", "price": "number",
                "rank": "number", "samples": "number", "socket": "string",
                "speed": "number", "tdp": "number", "thread": "number",
                "threadValue": "number", "turbo": "number", "value": "number"
            }
        elif self.domain == "www.videocardbenchmark.net":
            item_types = {
                "bus": "string", "cat": "string", "coreClk": "number",
                "date": "date", "g2d": "number", "g3d": "number",
                "href": "string", "id": "number", "memClk": "speed",
                "memSize": "size", "name": "string", "output": "bool",
                "powerPerf": "number", "price": "number", "rank": "number",
                "samples": "number", "tdp": "number", "value": "number"
            }
        else:
            item_types = {
                "date": "date", "diskmark": "number", "href": "string",
                "id": "number", "name": "string", "output": "bool",
                "price": "number", "rank": "number", "samples": "number",
                "size": "size", "type": "string", "value": "number"
            }

        if item_type == None:
            if sort_by in item_types:        
                item_type = item_types[sort_by]
            else:
                item_type = "string"

        #filter the items and assign a number to each one, unless it is a string
        for item in self.items:
            value = item[sort_by]
            if value == "NA":
                continue

            if item_type == "string":
                results.append([item, str(value)])
            elif item_type == "number":
                if type(value) is int or type(value) is float:
                    results.append([item, float(value)])
                else:
                    result = re.sub(r"[^0123456789\.]", "", value)
                    if len(result) > 0:
                        results.append([item, float(result)])
            elif item_type == "bool":
                results.append([item, int(value)])
            elif item_type == "size":
                number, unit = value.split(" ")[:2]
                number = re.sub(r"[^0123456789\.]", "", number)
                if len(number) > 0:
                    number = float(number)
                    units = ["kb", "mb", "gb", "tb", "pb"]
                    if unit.lower() in units:
                        number *= 1000**(units.index(unit.lower())+1)
                    results.append([item, int(number)])
            elif item_type == "speed":
                number, unit = value.split(" ")[:2]
                number = re.sub(r"[^0123456789\.]", "", number)
                if len(number) > 0:
                    number = float(number)
                    units = ["khz", "mhz", "ghz"]
                    if unit.lower() in units:
                        number *= 1000**(units.index(unit.lower())+1)
                    results.append([item, int(number)])
            elif item_type == "date":
                months = ["jan", "feb", "mar", "apr",
                            "may", "jun", "jul", "aug",
                            "sep", "oct", "nov", "dec"]
                month, year = value.split(" ")[:2]
                month_int = months.index(month.lower())+1
                year_int = int(year)
                d = datetime.date(year_int, month_int, 1)
                unix_time = time.mktime(d.timetuple())
                results.append([item, int(unix_time)])

        #sort items
        if order == "descending":
            reverse = True
        else:
            reverse = False
        results.sort(key=lambda x: x[1], reverse=reverse)

        if limit != None:
            results = results[:limit]
        return results

# -------------------------------------------------------------------
# GLOBAL INSTANCES
# Create one scraper for CPU and one for GPU when the server starts.
# This downloads the data once and caches it.
# -------------------------------------------------------------------
print("Initializing PassMark CPU database (this may take a moment)...")
try:
    cpu_scraper = Scraper(domain="www.cpubenchmark.net")
    print("...CPU database loaded.")
except Exception as e:
    print(f"CRITICAL: Failed to load CPU database: {e}")
    cpu_scraper = None

print("Initializing PassMark GPU database (this may take a moment)...")
try:
    gpu_scraper = Scraper(domain="www.videocardbenchmark.net")
    print("...GPU database loaded.")
except Exception as e:
    print(f"CRITICAL: Failed to load GPU database: {e}")
    gpu_scraper = None


# -------------------------------------------------------------------
# BENCHMARK FETCHER CLASS (UPDATED)
# This class now uses the Scraper instances to find scores.
# -------------------------------------------------------------------
class BenchmarkFetcher:
    """
    Uses the global Scraper instances to find benchmark scores
    and convert them to a 1-5 scale for the DSS.
    """
    
    def __init__(self):
        # Caches to avoid re-searching for the same 1-5 score
        self.cpu_cache: Dict[str, Optional[int]] = {}
        self.gpu_cache: Dict[str, Optional[int]] = {}

    def get_cpu_mark(self, cpu_name: Optional[str]) -> Optional[int]:
        """Get CPU benchmark score (1-5)"""
        if not cpu_name or not cpu_scraper:
            return 2 # Default score if no name or scraper failed
        
        normalized = cpu_name.lower().strip()
        if normalized in self.cpu_cache:
            return self.cpu_cache[normalized]
        
        print(f"Searching for CPU: {cpu_name}...")
        results = cpu_scraper.search(cpu_name, limit=1)
        
        if not results:
            print(f"  ✗ CPU '{cpu_name}' not found. Using default score.")
            self.cpu_cache[normalized] = 2
            return 2
            
        item = results[0][0] # Get the item dict from the (item, match_count) tuple
        raw_score = item.get("cpumark")
        
        if not raw_score:
            print(f"  ✗ CPU '{item['name']}' found but has no score. Using default.")
            self.cpu_cache[normalized] = 2
            return 2
        
        if isinstance(raw_score, str):
            raw_score = raw_score.replace(",", "")
        try:
            score_1_5 = self.convert_cpu_score(float(raw_score))
            print(f"  ✓ Found '{item['name']}' with score {raw_score}. (Converted to {score_1_5})")
            self.cpu_cache[normalized] = score_1_5
            return score_1_5
        except Exception as e:
            print(f"  ✗ Error converting CPU score: {e}")
            self.cpu_cache[normalized] = 2
            return 2

    def get_gpu_g3d_mark(self, gpu_name: Optional[str]) -> Optional[int]:
        """Get GPU benchmark score (1-5)"""
        if not gpu_name or not gpu_scraper:
            return 2 # Default score if no name or scraper failed
        
        normalized = gpu_name.lower().strip()
        if normalized in self.gpu_cache:
            return self.gpu_cache[normalized]

        print(f"Searching for GPU: {gpu_name}...")
        results = gpu_scraper.search(gpu_name, limit=1)
        
        if not results:
            print(f"  ✗ GPU '{gpu_name}' not found. Using default score.")
            self.gpu_cache[normalized] = 2
            return 2
            
        item = results[0][0]
        raw_score = item.get("g3d") # For GPUs, the score is 'g3d'
        
        if not raw_score:
            print(f"  ✗ GPU '{item['name']}' found but has no score. Using default.")
            self.gpu_cache[normalized] = 2
            return 2
        
        if isinstance(raw_score, str):
            raw_score = raw_score.replace(",", "")
        
        try:
            score_1_5 = self.convert_gpu_score(float(raw_score))
            print(f"  ✓ Found '{item['name']}' with score {raw_score}. (Converted to {score_1_5})")
            self.gpu_cache[normalized] = score_1_5
            return score_1_5
        except Exception as e:
            print(f"  ✗ Error converting GPU score: {e}")
            self.gpu_cache[normalized] = 2
            return 2

    # --- SCORE CONVERSION (Unchanged) ---
    
    def convert_cpu_score(self, raw_score: int) -> int:
        """
        Convert raw CPU Mark to 1-5 scale based on criteria
        5: > 13000
        4: > 8500 and <= 13000
        3: > 5000 and <= 8500
        2: > 3500 and <= 5000
        1: <= 3500
        """
        if raw_score > 13000:
            return 5
        elif raw_score > 8500:
            return 4
        elif raw_score > 5000:
            return 3
        elif raw_score > 3500:
            return 2
        else:
            return 1
    
    def convert_gpu_score(self, raw_score: int) -> int:
        """
        Convert raw G3D Mark to 1-5 scale based on criteria
        5: > 13000
        4: > 8500 and <= 13000
        3: > 5000 and <= 8500
        2: > 2000 and <= 5000
        1: <= 2000
        """
        if raw_score > 13000:
            return 5
        elif raw_score > 8500:
            return 4
        elif raw_score > 5000:
            return 3
        elif raw_score > 2000:
            return 2
        else:
            return 1