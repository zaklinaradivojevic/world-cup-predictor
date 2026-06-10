"""
Advanced Features - napredni statistički feature-i
- xG (Expected Goals) iz Understat-a
- FIFA rang lista
- ELO rejting
- Povrede igrača
- Vremenski uslovi
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional

class AdvancedFeatures:
    """
    Napredni feature-i koji zahtevaju eksterne API-je ili dodatne podatke
    """
    
    def __init__(self):
        self.feature_names = []
    
    def get_xg_factor(self, team_xg: float, league_avg_xg: float = 1.5) -> float:
        """
        xG (Expected Goals) faktor
        
        xG pokazuje koliko je tim trebao da postigne golova
        Razlika između stvarnih i očekivanih golova pokazuje "sreću"
        
        Args:
            team_xg: Prosečan xG tima po utakmici
            league_avg_xg: Prosečan xG u ligi
        
        Returns:
            float: Normalizovan xG faktor (0-1)
        """
        if team_xg <= 0:
            return 0.5
        
        # Normalizacija (tipično xG je između 0.5 i 2.5)
        normalized = min(1.0, max(0.0, (team_xg - 0.5) / 2.5))
        return normalized
    
    def get_xg_diff_factor(self, team1_xg: float, team2_xg: float) -> float:
        """
        Razlika u xG između timova
        
        Returns:
            float: Razlika normalizovana na [-1, 1]
        """
        diff = team1_xg - team2_xg
        # Normalizacija na [-1, 1] (tipična razlika je do 1.5)
        return max(-1.0, min(1.0, diff / 1.5))
    
    def get_fifa_rank_factor(self, rank: int, total_teams: int = 211) -> float:
        """
        FIFA rang lista faktor
        
        Args:
            rank: FIFA rang (1 = najbolji)
            total_teams: Ukupan broj timova u rangu
        
        Returns:
            float: Normalizovan rang (1 = najbolji, 0 = najlošiji)
        """
        if rank <= 0:
            return 0.5
        
        # Inverzna normalizacija (bolji rang = veći faktor)
        return 1.0 - ((rank - 1) / total_teams)
    
    def get_elo_factor(self, elo_rating: float, base_elo: float = 1500) -> float:
        """
        ELO rejting faktor
        
        Args:
            elo_rating: ELO rejting tima
            base_elo: Početni ELO
        
        Returns:
            float: Normalizovan ELO faktor (0-1)
        """
        # Tipičan ELO raspon je 1400-2200
        normalized = (elo_rating - 1400) / 800
        return max(0.0, min(1.0, normalized))
    
    def get_elo_win_probability(self, elo1: float, elo2: float) -> float:
        """
        Verovatnoća pobede na osnovu ELO razlike
        
        Formula: P = 1 / (1 + 10^((elo2 - elo1)/400))
        
        Returns:
            float: Verovatnoća pobede tima1 (0-1)
        """
        elo_diff = elo2 - elo1
        return 1.0 / (1.0 + 10 ** (elo_diff / 400))
    
    def get_injury_factor(self, 
                          injured_key_players: int, 
                          total_key_players: int = 11,
                          importance: str = 'high') -> float:
        """
        Faktor povreda ključnih igrača
        
        Args:
            injured_key_players: Broj povređenih ključnih igrača
            total_key_players: Ukupan broj ključnih igrača
            importance: 'low', 'medium', 'high'
        
        Returns:
            float: Faktor uticaja povreda (0 = nema uticaja, 1 = ogroman uticaj)
        """
        if total_key_players == 0:
            return 0
        
        # Procenat povređenih ključnih igrača
        injury_percentage = injured_key_players / total_key_players
        
        # Težina važnosti igrača
        importance_weight = {
            'low': 0.5,
            'medium': 1.0,
            'high': 1.5
        }.get(importance, 1.0)
        
        # Kombinovani faktor
        factor = min(1.0, injury_percentage * importance_weight)
        
        return factor
    
    def get_weather_factors(self, weather_data: Dict) -> Dict:
        """
        Konvertuje vremenske podatke u feature-e
        
        Args:
            weather_data: Dict iz weather_scraper-a
        
        Returns:
            Dict sa vremenskim faktorima
        """
        from backend.scrapers.weather_scraper import WeatherScraper
        
        scraper = WeatherScraper()
        return scraper.get_weather_factors(weather_data)
    
    def get_tournament_experience(self, 
                                   world_cup_appearances: int,
                                   knockout_rounds: int = 0) -> float:
        """
        Iskustvo tima na velikim takmičenjima
        
        Args:
            world_cup_appearances: Broj nastupa na SP
            knockout_rounds: Broj puta prošao grupnu fazu
        
        Returns:
            float: Faktor iskustva (0-1)
        """
        # Normalizacija (maks 20 nastupa)
        appearance_factor = min(1.0, world_cup_appearances / 20)
        
        # Bonus za iskustvo u nokaut fazi
        knockout_factor = min(0.3, knockout_rounds * 0.05)
        
        return min(1.0, appearance_factor + knockout_factor)
    
    def extract_all_advanced_features(self,
                                       team1_xg: Optional[float] = None,
                                       team2_xg: Optional[float] = None,
                                       team1_fifa_rank: Optional[int] = None,
                                       team2_fifa_rank: Optional[int] = None,
                                       team1_elo: Optional[float] = None,
                                       team2_elo: Optional[float] = None,
                                       team1_injuries: int = 0,
                                       team2_injuries: int = 0,
                                       weather_data: Optional[Dict] = None,
                                       team1_wc_appearances: int = 0,
                                       team2_wc_appearances: int = 0) -> np.ndarray:
        """
        Ekstrahuje sve napredne feature-ove
        
        Returns:
            np.ndarray: Feature vektor
        """
        features = []
        
        # xG faktori
        if team1_xg is not None:
            features.append(self.get_xg_factor(team1_xg))
            features.append(self.get_xg_factor(team2_xg))
            features.append(self.get_xg_diff_factor(team1_xg, team2_xg))
        else:
            features.extend([0.5, 0.5, 0.0])
        
        # FIFA rang
        if team1_fifa_rank is not None:
            features.append(self.get_fifa_rank_factor(team1_fifa_rank))
            features.append(self.get_fifa_rank_factor(team2_fifa_rank))
        else:
            features.extend([0.5, 0.5])
        
        # ELO rejting
        if team1_elo is not None:
            features.append(self.get_elo_factor(team1_elo))
            features.append(self.get_elo_factor(team2_elo))
            features.append(self.get_elo_win_probability(team1_elo, team2_elo))
        else:
            features.extend([0.5, 0.5, 0.5])
        
        # Povrede
        features.append(self.get_injury_factor(team1_injuries))
        features.append(self.get_injury_factor(team2_injuries))
        
        # Vremenski uslovi
        if weather_data:
            weather_factors = self.get_weather_factors(weather_data)
            features.append(weather_factors['fatigue_factor'])
            features.append(weather_factors['advantage_attacking'])
        else:
            features.extend([0.2, 0.5])  # Default vrednosti
        
        # Turnirsko iskustvo
        features.append(self.get_tournament_experience(team1_wc_appearances))
        features.append(self.get_tournament_experience(team2_wc_appearances))
        
        self.feature_names = [
            'xg_team1', 'xg_team2', 'xg_diff',
            'fifa_team1', 'fifa_team2',
            'elo_team1', 'elo_team2', 'elo_win_prob',
            'injuries_team1', 'injuries_team2',
            'weather_fatigue', 'weather_attack_advantage',
            'tournament_exp_team1', 'tournament_exp_team2'
        ]
        
        return np.array(features)


# Testiranje
if __name__ == "__main__":
    af = AdvancedFeatures()
    
    # Test xG
    xg_factor = af.get_xg_factor(2.1)
    print(f"xG faktor za tim sa 2.1 xG: {xg_factor:.2f}")
    
    # Test ELO verovatnoće
    prob = af.get_elo_win_probability(2100, 1900)
    print(f"ELO verovatnoća pobede (2100 vs 1900): {prob:.2%}")
    
    # Test povreda
    injury = af.get_injury_factor(3, 11, 'high')
    print(f"Faktor povreda (3/11 ključnih): {injury:.2f}")