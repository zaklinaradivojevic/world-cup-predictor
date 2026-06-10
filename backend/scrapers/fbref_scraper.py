import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from tqdm import tqdm
from fake_useragent import UserAgent
from ..config import Config

class FBrefScraper:
    def __init__(self):
        self.base_url = "https://fbref.com"
        self.ua = UserAgent()  # Dynamically generated User-Agent
        self.headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def _get_safe_response(self, url, retries=3, delay=3):
        """
        Bezbedno dohvatanje strane sa čekanjem i ponavljanjem
        Izbegava 403 Forbidden grešku
        """
        for attempt in range(retries):
            try:
                # Rotiraj User-Agent za svaki pokušaj
                self.headers['User-Agent'] = self.ua.random
                response = requests.get(url, headers=self.headers, timeout=15)
                
                if response.status_code == 200:
                    print(f"✅ Uspesno dohvaceno: {url}")
                    return response
                elif response.status_code == 403:
                    print(f"⚠️ Pokušaj {attempt+1}: 403 Forbidden za {url}")
                    print(f"   Čekam {delay * (attempt + 1)} sekundi...")
                else:
                    print(f"⚠️ Pokušaj {attempt+1}: Status {response.status_code} za {url}")
                    
            except Exception as e:
                print(f"⚠️ Pokušaj {attempt+1}: Greška - {e}")
            
            # Čekaj sve duže pri svakom pokušaju
            time.sleep(delay * (attempt + 1))
        
        print(f"❌ Neuspešno dohvatanje nakon {retries} pokušaja: {url}")
        return None
    
    def scrape_team_stats(self, competition, season):
        """Skida kompletne statistike timova za ligu/turnir"""
        competition_map = {
            'Premier League': '9',
            'La Liga': '12',
            'Serie A': '11',
            'Bundesliga': '20',
            'World Cup': '1'
        }
        
        comp_id = competition_map.get(competition, '9')
        url = f"{self.base_url}/en/comps/{comp_id}/{season}/stats/{season}-{competition.replace(' ', '-')}-Stats"
        
        print(f"   Dohvatam statistike: {url}")
        response = self._get_safe_response(url)
        
        if response is None:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'stats_standard'})
        
        if table:
            df = pd.read_html(str(table))[0]
            df['competition'] = competition
            df['season'] = season
            print(f"   Učitano {len(df)} timova")
            return df
        
        print(f"   Tabela nije pronađena za {competition} {season}")
        return None
    
    def scrape_match_results(self, competition, season):
        """Skida sve rezultate utakmica za sezonu"""
        comp_map = {'Premier League': '9', 'La Liga': '12', 'World Cup': '1'}
        comp_id = comp_map.get(competition, '9')
        
        url = f"{self.base_url}/en/comps/{comp_id}/{season}/schedule/{season}-{competition.replace(' ', '-')}-Schedule"
        
        print(f"   Dohvatam rezultate: {url}")
        response = self._get_safe_response(url)
        
        if response is None:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'sched_all'})
        
        if table:
            df = pd.read_html(str(table))[0]
            print(f"   Učitano {len(df)} utakmica")
            return df
        
        print(f"   Tabela sa rezultatima nije pronađena")
        return None
    
    def scrape_shot_data(self, competition, season):
        """Skida podatke o šutevima (xG) - napredno"""
        comp_map = {'Premier League': '9', 'La Liga': '12', 'World Cup': '1'}
        comp_id = comp_map.get(competition, '9')
        
        url = f"{self.base_url}/en/comps/{comp_id}/{season}/shooting/{season}-{competition.replace(' ', '-')}-Shooting"
        
        print(f"   Dohvatam xG podatke: {url}")
        response = self._get_safe_response(url)
        
        if response is None:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'stats_shooting'})
        
        if table:
            df = pd.read_html(str(table))[0]
            print(f"   Učitano {len(df)} redova xG podataka")
            return df
        
        print(f"   Tabela sa xG podacima nije pronađena")
        return None
    
    def save_to_csv(self, df: pd.DataFrame, filename: str):
        """Čuva podatke u data/raw folder"""
        # Kreiraj putanju ka data/raw folderu
        save_dir = os.path.join('backend', 'data', 'raw')
        os.makedirs(save_dir, exist_ok=True)
        
        save_path = os.path.join(save_dir, filename)
        df.to_csv(save_path, index=False)
        print(f"💾 Podaci sačuvani u {save_path}")
        return save_path
    
    def scrape_and_save_all(self, competition='World Cup', season='2026'):
        """
        Glavna funkcija - skida sve podatke i čuva ih u CSV fajlove
        """
        print("\n" + "="*60)
        print(f"🚀 FBref Scraper - {competition} {season}")
        print("="*60)
        
        results = {}
        
        # 1. Utakmice
        print("\n📊 1. Skidam rezultate utakmica...")
        matches_df = self.scrape_match_results(competition, season)
        if matches_df is not None:
            path = self.save_to_csv(matches_df, f'{competition}_{season}_matches.csv')
            results['matches'] = path
            time.sleep(2)  # Pauza između zahteva
        
        # 2. Statistike timova
        print("\n📈 2. Skidam statistike timova...")
        stats_df = self.scrape_team_stats(competition, season)
        if stats_df is not None:
            path = self.save_to_csv(stats_df, f'{competition}_{season}_team_stats.csv')
            results['team_stats'] = path
            time.sleep(2)
        
        # 3. xG podaci
        print("\n🎯 3. Skidam xG podatke...")
        xg_df = self.scrape_shot_data(competition, season)
        if xg_df is not None:
            path = self.save_to_csv(xg_df, f'{competition}_{season}_xg_data.csv')
            results['xg_data'] = path
        
        print("\n" + "="*60)
        print("✅ FBref prikupljanje završeno!")
        print(f"📁 Sačuvani fajlovi u: backend/data/raw/")
        for key, path in results.items():
            print(f"   - {key}: {os.path.basename(path)}")
        print("="*60)
        
        return results
    
    def load_local_csv(self, filename: str) -> pd.DataFrame:
        """
        Učitava lokalno sačuvan CSV fajl (ako već postoji)
        Umesto da ponovo skida sa interneta
        """
        file_path = os.path.join('backend', 'data', 'raw', filename)
        
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            print(f"📂 Učitani lokalni podaci: {filename} ({len(df)} redova)")
            return df
        else:
            print(f"⚠️ Fajl ne postoji: {file_path}")
            return None


# Testiranje skripta
if __name__ == "__main__":
    scraper = FBrefScraper()
    
    # Opcija 1: Skini sve podatke sa interneta
    # scraper.scrape_and_save_all('World Cup', '2026')
    
    # Opcija 2: Učitaj lokalno sačuvane podatke (ako već postoje)
    df = scraper.load_local_csv('World_Cup_2026_matches.csv')
    if df is not None:
        print("\n📋 Pregled podataka:")
        print(df.head())
    
    # Opcija 3: Samo testiraj jednu funkciju
    # matches = scraper.scrape_match_results('World Cup', '2026')
    # if matches is not None:
    #     print(matches.head())