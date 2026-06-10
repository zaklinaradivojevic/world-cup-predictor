"""
Base Features - osnovni statistički feature-i za ML model
- Forma tima (rolling prosek)
- Golovi (postignuti/primljeni)
- Head-to-Head statistika
- Domaći teren faktor
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

class BaseFeatures:
    """
    Osnovni feature-i koji ne zahtevaju eksterne API-je
    """
    
    def __init__(self):
        self.feature_names = []
    
    def calculate_form(self, team_matches: pd.DataFrame, window: int = 5) -> float:
        """
        Izračunava formu tima na osnovu poslednjih N utakmica
        
        Formula: (W*3 + D*1 + L*0) / (window * 3)
        Rezultat je od 0 do 1 (1 = savršena forma)
        
        Args:
            team_matches: DataFrame sa istorijskim utakmicama
            window: Broj utakmica za analizu (5, 10, 15)
        
        Returns:
            float: Forma tima (0-1)
        """
        if len(team_matches) == 0:
            return 0.5  # Neutralna forma ako nema podataka
        
        # Uzmi poslednjih 'window' utakmica
        recent = team_matches.tail(window)
        
        # Mapiramo rezultate u bodove
        points_map = {'W': 3, 'D': 1, 'L': 0}
        points = recent['result'].map(points_map).sum()
        
        # Maksimalni mogući bodovi
        max_points = window * 3
        
        return points / max_points if max_points > 0 else 0.5
    
    def calculate_rolling_goals(self, team_matches: pd.DataFrame, 
                                  stat: str = 'goals_for', 
                                  window: int = 5) -> float:
        """
        Izračunava prosečne golove u poslednjih N utakmica
        
        Args:
            team_matches: DataFrame sa utakmicama
            stat: 'goals_for' ili 'goals_against'
            window: Broj utakmica
        
        Returns:
            float: Prosečan broj golova
        """
        if len(team_matches) == 0:
            return 1.0  # Default prosek
        
        recent = team_matches.tail(window)
        return recent[stat].mean()
    
    def calculate_goal_difference(self, team_matches: pd.DataFrame, window: int = 5) -> float:
        """
        Gol razlika u poslednjih N utakmica
        
        Returns:
            float: Prosečna gol razlika po utakmici
        """
        recent = team_matches.tail(window)
        diff = (recent['goals_for'] - recent['goals_against']).mean()
        return diff
    
    def calculate_h2h_stats(self, h2h_matches: pd.DataFrame) -> Dict:
        """
        Head-to-Head statistika između dva tima
        
        Args:
            h2h_matches: DataFrame sa svim međusobnim utakmicama
        
        Returns:
            Dict sa H2H statistikom
        """
        if len(h2h_matches) == 0:
            return {
                'wins_ratio': 0.5,
                'goals_avg': 1.5,
                'total_matches': 0,
                'home_advantage_h2h': 0.5
            }
        
        # Računamo pobede (gledamo sa strane tima1)
        wins = len(h2h_matches[h2h_matches['result'] == 'W'])
        draws = len(h2h_matches[h2h_matches['result'] == 'D'])
        losses = len(h2h_matches[h2h_matches['result'] == 'L'])
        
        total = len(h2h_matches)
        wins_ratio = wins / total if total > 0 else 0.5
        
        # Prosečni golovi u H2H
        goals_avg = (h2h_matches['goals_for'].mean() + h2h_matches['goals_against'].mean()) / 2
        
        # Domaći teren faktor u H2H (koliko puta je domaćin dobio)
        home_matches = h2h_matches[h2h_matches['venue'] == 'home']
        home_wins = len(home_matches[home_matches['result'] == 'W'])
        home_advantage_h2h = home_wins / len(home_matches) if len(home_matches) > 0 else 0.5
        
        return {
            'wins_ratio': wins_ratio,
            'goals_avg': goals_avg,
            'total_matches': total,
            'home_advantage_h2h': home_advantage_h2h
        }
    
    def home_advantage_factor(self, venue: str, team_strength: float = 0.5) -> float:
        """
        Faktor domaćeg terena
        
        Args:
            venue: 'home', 'away', 'neutral'
            team_strength: Jačina tima (0-1) - za bonus/penal
        
        Returns:
            float: Multiplikator za verovatnoću pobede (0.7 - 1.3)
        """
        base_factor = {
            'home': 1.20,      # Domaćin ima 20% prednosti
            'neutral': 1.00,   # Neutralan teren
            'away': 0.85       # Gost ima 15% hendikepa
        }.get(venue, 1.00)
        
        # Dodatni bonus za jake timove na domaćem terenu
        if venue == 'home' and team_strength > 0.6:
            base_factor += 0.05
        
        return base_factor
    
    def extract_all_base_features(self, 
                                   team1_matches: pd.DataFrame,
                                   team2_matches: pd.DataFrame,
                                   h2h_matches: pd.DataFrame,
                                   venue: str = 'neutral') -> np.ndarray:
        """
        Ekstrahuje sve osnovne feature-ove
        
        Returns:
            np.ndarray: Feature vektor
        """
        features = []
        
        # Forma (3 različita windows-a)
        for window in [5, 10, 15]:
            features.append(self.calculate_form(team1_matches, window))
            features.append(self.calculate_form(team2_matches, window))
        
        # Golovi
        features.append(self.calculate_rolling_goals(team1_matches, 'goals_for', 5))
        features.append(self.calculate_rolling_goals(team2_matches, 'goals_for', 5))
        features.append(self.calculate_rolling_goals(team1_matches, 'goals_against', 5))
        features.append(self.calculate_rolling_goals(team2_matches, 'goals_against', 5))
        
        # Gol razlika
        features.append(self.calculate_goal_difference(team1_matches, 5))
        features.append(self.calculate_goal_difference(team2_matches, 5))
        
        # H2H statistika
        h2h = self.calculate_h2h_stats(h2h_matches)
        features.append(h2h['wins_ratio'])
        features.append(h2h['goals_avg'] / 3.0)  # Normalizacija
        features.append(h2h['home_advantage_h2h'])
        
        # Domaći teren
        team1_strength = self.calculate_form(team1_matches, 15)
        features.append(self.home_advantage_factor(venue, team1_strength))
        
        # Razlike (feature engineering)
        features.append(features[1] - features[0])  # forma razlika
        features.append(features[4] - features[5])  # gol razlika
        
        self.feature_names = [
            'team1_form_5', 'team2_form_5',
            'team1_form_10', 'team2_form_10',
            'team1_form_15', 'team2_form_15',
            'team1_goals_for', 'team2_goals_for',
            'team1_goals_against', 'team2_goals_against',
            'team1_goal_diff', 'team2_goal_diff',
            'h2h_wins_ratio', 'h2h_goals_avg', 'h2h_home_advantage',
            'venue_factor', 'form_diff', 'goal_diff_diff'
        ]
        
        return np.array(features)
    
    def get_feature_names(self) -> List[str]:
        """Vraća imena feature-ova"""
        return self.feature_names


# Testiranje
if __name__ == "__main__":
    # Mock podaci za test
    mock_matches = pd.DataFrame({
        'result': ['W', 'W', 'D', 'L', 'W', 'W'],
        'goals_for': [2, 3, 1, 0, 2, 4],
        'goals_against': [1, 1, 1, 2, 0, 1],
        'venue': ['home', 'away', 'home', 'away', 'home', 'neutral']
    })
    
    bf = BaseFeatures()
    form = bf.calculate_form(mock_matches, window=5)
    print(f"Forma tima: {form:.2%}")
    
    goals = bf.calculate_rolling_goals(mock_matches, 'goals_for', 5)
    print(f"Prosek golova: {goals:.2f}")