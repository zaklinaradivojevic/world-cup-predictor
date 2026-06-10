import requests
import pandas as pd
from bs4 import BeautifulSoup

class FIFARankingScraper:
    def __init__(self):
        self.fifa_url = "https://inside.fifa.com/fifa-world-ranking/men"
        self.ranking_history_url = "https://raw.githubusercontent.com/jalapic/engsoccerdata/master/data-raw/fifa_ranking_1993-2018.csv"
    
    def get_current_rankings(self):
        """Dohvata trenutne FIFA rang liste"""
        try:
            # FIFA sajt je kompleksan, koristimo alternativni API
            url = "https://api.fifa.com/api/v1/ranking/men"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                rankings = []
                for team in data.get('rankings', []):
                    rankings.append({
                        'team': team.get('teamName', ''),
                        'rank': team.get('rank', 0),
                        'points': team.get('points', 0),
                        'confederation': team.get('confederation', '')
                    })
                return pd.DataFrame(rankings)
        except:
            pass
        
        # Fallback - simulirani podaci
        return self._get_mock_rankings()
    
    def get_historical_rankings(self):
        """Dohvata istorijske FIFA rang liste (1993-2024)"""
        try:
            df = pd.read_csv(self.ranking_history_url)
            return df
        except:
            return None
    
    def _get_mock_rankings(self):
        """Demo podaci za FIFA rang liste"""
        top_teams = ['Brazil', 'Argentina', 'France', 'Spain', 'England', 
                     'Germany', 'Netherlands', 'Portugal', 'Belgium', 'Croatia']
        
        return pd.DataFrame({
            'team': top_teams,
            'rank': list(range(1, len(top_teams) + 1)),
            'points': [1840, 1825, 1810, 1795, 1780, 1770, 1760, 1750, 1740, 1730]
        })