import requests
import json
import pandas as pd

class UnderstatScraper:
    """
    Understat pruža xG (očekivane golove) podatke
    Ovo je najvredniji izvor podataka za predikciju
    """
    def __init__(self):
        self.base_url = "https://understat.com"
        self.league_ids = {
            'EPL': 'EPL',
            'La Liga': 'La_liga',
            'Serie A': 'Serie_A',
            'Bundesliga': 'Bundesliga',
            'Ligue 1': 'Ligue_1'
        }
    
    def get_league_data(self, league_name, season):
        """Dohvata xG podatke za ligu"""
        league_id = self.league_ids.get(league_name, 'EPL')
        
        # Understat koristi JavaScript da učitava podatke
        # Ovo je pojednostavljen pristup
        url = f"{self.base_url}/league/{league_id}/{season}"
        
        # U stvarnosti bi trebalo koristiti Selenium ili Playwright
        # jer Understat dinamički učitava podatke
        
        return self._mock_xg_data()  # Za demo
    
    def _mock_xg_data(self):
        """Demo xG podaci (u produkciji bi bili stvarni)"""
        return pd.DataFrame({
            'team': ['Man City', 'Liverpool', 'Arsenal', 'Bayern', 'Real Madrid'],
            'xG_per_match': [2.1, 1.9, 1.8, 2.0, 1.9],
            'xGA_per_match': [0.8, 1.0, 0.9, 0.9, 1.1],
            'npxG': [1.8, 1.6, 1.5, 1.7, 1.6],
            'shots_per_match': [15.2, 14.8, 14.1, 15.5, 14.3]
        })
    
    def get_team_xg_trend(self, team_name, matches=10):
        """Dohvata trend xG za poslednjih N utakmica"""
        # Ključno za detekciju forme koja ne zavisi od sreće
        return {
            'xG_last_5': 1.9,
            'xG_trend': 'up',  # up/down/stable
            'performance_vs_xG': 0.2  # koliko golova više/ manje od očekivanog
        }