import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from tqdm import tqdm
from ..config import Config

class FBrefScraper:
    def __init__(self):
        self.base_url = "https://fbref.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_team_stats(self, competition, season):
        """Skida kompletne statistike timova za ligu/turnir"""
        # Konstruiši URL za ligu
        competition_map = {
            'Premier League': '9',
            'La Liga': '12',
            'Serie A': '11',
            'Bundesliga': '20',
            'World Cup': '1'
        }
        
        comp_id = competition_map.get(competition, '9')
        url = f"{self.base_url}/en/comps/{comp_id}/{season}/stats/{season}-{competition.replace(' ', '-')}-Stats"
        
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Pronađi tabelu sa statistikama
        table = soup.find('table', {'id': 'stats_standard'})
        
        if table:
            df = pd.read_html(str(table))[0]
            df['competition'] = competition
            df['season'] = season
            return df
        
        return None
    
    def scrape_match_results(self, competition, season):
        """Skida sve rezultate utakmica za sezonu"""
        comp_map = {'Premier League': '9', 'La Liga': '12', 'World Cup': '1'}
        comp_id = comp_map.get(competition, '9')
        
        url = f"{self.base_url}/en/comps/{comp_id}/{season}/schedule/{season}-{competition.replace(' ', '-')}-Schedule"
        response = requests.get(url, headers=self.headers)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'sched_all'})
        
        if table:
            df = pd.read_html(str(table))[0]
            return df
        
        return None
    
    def scrape_shot_data(self, competition, season):
        """Skida podatke o šutevima (xG) - napredno"""
        comp_map = {'Premier League': '9', 'La Liga': '12', 'World Cup': '1'}
        comp_id = comp_map.get(competition, '9')
        
        url = f"{self.base_url}/en/comps/{comp_id}/{season}/shooting/{season}-{competition.replace(' ', '-')}-Shooting"
        response = requests.get(url, headers=self.headers)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'stats_shooting'})
        
        if table:
            df = pd.read_html(str(table))[0]
            return df
        
        return None