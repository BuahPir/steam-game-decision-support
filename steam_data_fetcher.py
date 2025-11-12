import re
import time
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone

APPDETAILS = "https://store.steampowered.com/api/appdetails"
APPREVIEWS = "https://store.steampowered.com/appreviews/"
STEAMCHARTS_JSON = "https://steamcharts.com/app/{appid}/chart-data.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
}

@dataclass
class SteamGame:
    appid: int
    name: str
    price_formatted: Optional[str]
    price_numeric: Optional[int]
    release_year: Optional[int]
    steam_rating_label: Optional[str]
    total_reviews: Optional[int]
    min_ram_gb: Optional[float]
    cpu_minimal: Optional[str]
    gpu_minimal: Optional[str]
    genres: Optional[str]
    steamcharts_avg_30d: Optional[float]
    steamcharts_current: Optional[int]
    
    # Converted values for DSS
    release_year_score: Optional[int] = None
    cpu_mark_score: Optional[int] = None
    gpu_g3d_score: Optional[int] = None
    rating_score: Optional[int] = None

class SteamDataFetcher:
    """Fetch and process Steam game data"""
    
    def __init__(self, cc="id", lang="english", delay=1.7):
        self.cc = cc
        self.lang = lang
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        if not text:
            return ""
        text = re.sub(r"(?i)<\s*br\s*/?>", "\n", text)
        text = re.sub(r"(?i)</\s*li\s*>", "\n", text)
        text = re.sub(r"(?i)</\s*p\s*>", "\n", text)
        text = re.sub(r"(?i)</\s*div\s*>", "\n", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{2,}", "\n", text)
        return re.sub(r"[ \t]+", " ", text).strip()
    
    def _parse_ram_gb(self, text: str) -> Optional[float]:
        """Extract RAM in GB from text"""
        if not text:
            return None
        m = re.search(r"(\d+(?:\.\d+)?)\s*GB(?:\s*(?:RAM|Memory))?", text, flags=re.I)
        return float(m.group(1)) if m else None
    
    def _parse_cpu_min(self, text: str) -> Optional[str]:
        """Extract minimum CPU requirement"""
        if not text:
            return None
        cpu_regex = r"((?:Intel|AMD|Ryzen|Core|i3|i5|i7|i9|Qualcomm|Snapdragon)\s[^\n,;]+)"
        m = re.search(cpu_regex, text, flags=re.I)
        if not m:
            return None
        txt = m.group(1).strip()

        if " or " in txt.lower() or " / " in txt:
            txt = re.split(r'\s+(?:or|/)\s+', txt, flags=re.I)[0]

        txt = re.sub(r"\s*\([^)]+\)", "", txt)
        return txt[:100] if txt else None
    
    def _parse_gpu_min(self, text: str) -> Optional[str]:
        """Extract minimum GPU requirement"""
        if not text:
            return None
        gpu_regex = r"((?:NVIDIA|GeForce|GTX|RTX|AMD\s+Radeon|Radeon|Intel\s+(?:Arc|HD\s+Graphics|Iris))\s[^\n,;]+)"

        m = re.search(gpu_regex, text, flags=re.I)

        if not m:
            return None
        txt = m.group(1).strip()

        if " or " in txt.lower() or " / " in txt:
            txt = re.split(r'\s+(?:or|/)\s+', txt, flags=re.I)[0]

        txt = re.sub(r"\s*\([^)]+\)", "", txt)
        return txt[:100] if txt else None
    
    def get_app_details(self, appid: int) -> Optional[Dict[str, Any]]:
        """Fetch app details from Steam API"""
        url = f"{APPDETAILS}?appids={appid}&cc={self.cc}&l={self.lang}"
        try:
            r = self.session.get(url, timeout=30)
            if r.status_code == 200:
                data = r.json()
                return data.get(str(appid))
            return None
        except Exception as e:
            print(f"Error fetching appid {appid}: {e}")
            return None
    
    def get_review_summary(self, appid: int) -> Dict[str, Any]:
        """Fetch review summary from Steam"""
        url = f"{APPREVIEWS}{appid}?json=1&language=all"
        try:
            r = self.session.get(url, timeout=10)
            r.raise_for_status()
            js = r.json()
            if js.get("success") == 1 and "query_summary" in js:
                return js["query_summary"]
        except Exception as e:
            print(f"Review error {appid}: {e}")
        return {}
    
    def get_steamcharts_30d(self, appid: int) -> Dict[str, Any]:
        """Fetch SteamCharts data (30-day average)"""
        url = STEAMCHARTS_JSON.format(appid=appid)
        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            data = r.json()
            if not isinstance(data, list):
                return {}
            
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(days=30)
            last_30 = [int(p[1]) for p in data if datetime.fromtimestamp(p[0]/1000, tz=timezone.utc) >= cutoff]
            current = int(data[-1][1]) if data else None
            
            if not last_30:
                return {"avg_30d": None, "current": current}
            
            return {
                "avg_30d": round(sum(last_30)/len(last_30), 2),
                "current": current
            }
        except Exception:
            return {}
    
    def convert_release_year(self, year: Optional[int]) -> Optional[int]:
        """Convert release year to score (1-5)"""
        if not year:
            return None
        if year >= 2020:
            return 4
        elif year >= 2015 and year < 2020:
            return 3
        elif year >= 2010 and year < 2015:
            return 2
        else:
            return 1
    
    def convert_rating_to_score(self, rating_label: Optional[str]) -> Optional[int]:
        """Convert Steam rating label to score (1-8)"""
        if not rating_label:
            return None
        
        rating_map = {
            "overwhelmingly positive": 8,
            "very positive": 7,
            "positive": 6,
            "mostly positive": 5,
            "mixed": 4,
            "mostly negative": 3,
            "negative": 2,
            "very negative": 1
        }
        
        return rating_map.get(rating_label.lower(), 4)
    
    def fetch_game_data(self, appid: int) -> Optional[SteamGame]:
        """Fetch complete game data"""
        details = self.get_app_details(appid)
        
        if not details or not details.get("success"):
            return None
        
        data = details["data"]
        
        # Extract basic info
        name = data.get("name")
        price_overview = data.get("price_overview") or {}
        price_formatted = price_overview.get("final_formatted")
        price_numeric = price_overview.get("final")

        # Extract release year
        release_str = (data.get("release_date") or {}).get("date") or ""
        m_year = re.search(r"(20\d{2}|19\d{2})", release_str)
        release_year = int(m_year.group(1)) if m_year else None
        
        # Extract PC requirements
        req = data.get("pc_requirements") or {}
        pc_min_raw = self._clean_html(req.get("minimum", ""))
        
        min_ram = self._parse_ram_gb(pc_min_raw)
        cpu_min = self._parse_cpu_min(pc_min_raw)
        gpu_min = self._parse_gpu_min(pc_min_raw)
        
        # Extract genres
        genres_list = data.get("genres", [])
        genres_str = ", ".join([g['description'] for g in genres_list]) if genres_list else None
        
        # Fetch reviews
        time.sleep(self.delay)
        rev = self.get_review_summary(appid)
        rating_label = rev.get("review_score_desc")
        tot_pos = rev.get("total_positive") or 0
        tot_neg = rev.get("total_negative") or 0
        total_reviews = (rev.get("total_reviews") or (tot_pos + tot_neg)) or None
        
        # Fetch SteamCharts
        time.sleep(self.delay)
        sc = self.get_steamcharts_30d(appid)
        
        # Create game object
        game = SteamGame(
            appid=appid,
            name=name,
            price_formatted=price_formatted,
            price_numeric=price_numeric,
            release_year=release_year,
            steam_rating_label=rating_label,
            total_reviews=total_reviews,
            min_ram_gb=min_ram,
            cpu_minimal=cpu_min,
            gpu_minimal=gpu_min,
            genres=genres_str,
            steamcharts_avg_30d=sc.get("avg_30d"),
            steamcharts_current=sc.get("current")
        )
        
        # Convert to scores
        game.release_year_score = self.convert_release_year(release_year)
        game.rating_score = self.convert_rating_to_score(rating_label)
        
        return game
    
    def fetch_multiple_games(self, appids: List[int]) -> List[Dict[str, Any]]:
        """Fetch multiple games"""
        games = []
        
        for i, appid in enumerate(appids):
            print(f"Fetching game {i+1}/{len(appids)}: AppID {appid}")
            game = self.fetch_game_data(appid)
            
            if game:
                games.append(asdict(game))
                print(f"  ✓ {game.name}")
            else:
                print(f"  ✗ Failed to fetch AppID {appid}")
            
            # Delay between requests
            if i < len(appids) - 1:
                time.sleep(self.delay)
        
        return games