import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from scipy import stats
from typing import Dict, List, Tuple

class FeatureEngineer:
    def __init__(self):
        self.scaler = StandardScaler()
        self.minmax_scaler = MinMaxScaler()
        self.feature_names = []
    
    def extract_basic_features(self, match_data: pd.DataFrame) -> pd.DataFrame:
        """Osnovni feature-i: forma, golovi, H2H"""
        features = pd.DataFrame()
        
        # 1. Forma tima (poslednjih 5/10/15 utakmica)
        for window in [5, 10, 15]:
            features[f'team1_form_{window}'] = self._rolling_form(match_data, 'team1', window)
            features[f'team2_form_{window}'] = self._rolling_form(match_data, 'team2', window)
        
        # 2. Golovi (prosek i standardna devijacija)
        features['team1_avg_goals'] = self._rolling_mean(match_data, 'team1', 'goals_for')
        features['team2_avg_goals'] = self._rolling_mean(match_data, 'team2', 'goals_for')
        features['team1_avg_conceded'] = self._rolling_mean(match_data, 'team1', 'goals_against')
        features['team2_avg_conceded'] = self._rolling_mean(match_data, 'team2', 'goals_against')
        
        # 3. Head-to-Head statistika
        h2h_stats = self._head_to_head_stats(match_data)
        features['h2h_wins_ratio'] = h2h_stats['wins_ratio']
        features['h2h_avg_goals'] = h2h_stats['avg_goals']
        
        return features
    
    def extract_advanced_features(self, match_data: pd.DataFrame, xg_data: pd.DataFrame) -> pd.DataFrame:
        """Napredni feature-i: xG, posed lopte, preciznost"""
        features = pd.DataFrame()
        
        # 1. xG (očekivani golovi) podaci
        if xg_data is not None:
            features['team1_xG_per_match'] = self._get_xg_rating(xg_data, 'team1')
            features['team2_xG_per_match'] = self._get_xg_rating(xg_data, 'team2')
            features['xG_difference'] = features['team1_xG_per_match'] - features['team2_xG_per_match']
        
        # 2. Posed lopte (ako imamo podatke)
        possession_data = match_data.get('possession', None)
        if possession_data is not None:
            features['team1_possession'] = possession_data['home']
            features['team2_possession'] = possession_data['away']
        
        # 3. Broj šuteva i preciznost
        features['team1_shots_on_target'] = self._rolling_mean(match_data, 'team1', 'shots_on_target')
        features['team2_shots_on_target'] = self._rolling_mean(match_data, 'team2', 'shots_on_target')
        
        # 4. Konverzija šuteva u golove
        features['team1_conversion_rate'] = features['team1_avg_goals'] / (features['team1_shots_on_target'] + 0.01)
        features['team2_conversion_rate'] = features['team2_avg_goals'] / (features['team2_shots_on_target'] + 0.01)
        
        return features
    
    def extract_external_features(self, fifa_rankings: pd.DataFrame, 
                                   elo_ratings: Dict, 
                                   injury_data: Dict) -> pd.DataFrame:
        """Eksterni feature-i: FIFA rang, ELO, povrede"""
        features = pd.DataFrame()
        
        # 1. FIFA rang lista
        features['team1_fifa_rank'] = self._get_fifa_rank(fifa_rankings, 'team1')
        features['team2_fifa_rank'] = self._get_fifa_rank(fifa_rankings, 'team2')
        features['fifa_rank_diff'] = features['team2_fifa_rank'] - features['team1_fifa_rank']
        
        # 2. ELO rejting
        features['team1_elo'] = elo_ratings.get('team1', 1500)
        features['team2_elo'] = elo_ratings.get('team2', 1500)
        features['elo_diff'] = features['team1_elo'] - features['team2_elo']
        
        # 3. Povrede igrača (procenat nedostupnih ključnih igrača)
        features['team1_injuries'] = self._injury_factor(injury_data, 'team1')
        features['team2_injuries'] = self._injury_factor(injury_data, 'team2')
        
        # 4. Vrednost tima (Transfermarkt)
        features['team1_market_value'] = self._get_market_value('team1')
        features['team2_market_value'] = self._get_market_value('team2')
        
        return features
    
    def extract_contextual_features(self, match_data: pd.DataFrame) -> pd.DataFrame:
        """Kontekstualni feature-i: domaći teren, vreme, odmor"""
        features = pd.DataFrame()
        
        # 1. Domaći teren faktor
        features['home_advantage'] = match_data['venue'].apply(lambda x: 1.2 if x == 'home' else (1.0 if x == 'neutral' else 0.8))
        
        # 2. Dani odmora između utakmica
        features['team1_days_rest'] = self._calculate_rest_days(match_data, 'team1')
        features['team2_days_rest'] = self._calculate_rest_days(match_data, 'team2')
        features['rest_difference'] = features['team1_days_rest'] - features['team2_days_rest']
        
        # 3. Vremenski uslovi (temperatura, kiša)
        if 'weather' in match_data.columns:
            features['temperature'] = match_data['weather'].apply(lambda x: x.get('temp', 20))
            features['rain_probability'] = match_data['weather'].apply(lambda x: x.get('rain', 0.2))
        
        return features
    
    def create_all_features(self, match_data: pd.DataFrame, 
                           xg_data: pd.DataFrame = None,
                           fifa_rankings: pd.DataFrame = None,
                           elo_ratings: Dict = None,
                           injury_data: Dict = None) -> Tuple[pd.DataFrame, np.ndarray]:
        """Kreira sve feature-ove i target varijablu"""
        
        # Ekstrahuj sve grupe feature-a
        basic_features = self.extract_basic_features(match_data)
        advanced_features = self.extract_advanced_features(match_data, xg_data) if xg_data is not None else pd.DataFrame()
        external_features = self.extract_external_features(fifa_rankings, elo_ratings, injury_data) if fifa_rankings is not None else pd.DataFrame()
        contextual_features = self.extract_contextual_features(match_data)
        
        # Kombinuj sve feature-ove
        all_features = pd.concat([basic_features, advanced_features, external_features, contextual_features], axis=1)
        
        # Popuni missing vrednosti
        all_features = all_features.fillna(all_features.mean())
        
        # Izbaci beskonačne vrednosti
        all_features = all_features.replace([np.inf, -np.inf], 0)
        
        # Normalizacija
        feature_matrix = self.scaler.fit_transform(all_features)
        
        self.feature_names = all_features.columns.tolist()
        
        # Target varijabla (1 - domaćin pobedio, 0.5 - nerešeno, 0 - gost pobedio)
        target = match_data['result'].map({'W': 1, 'D': 0.5, 'L': 0}).values
        
        return pd.DataFrame(feature_matrix, columns=self.feature_names), target
    
    def _rolling_form(self, data, team_col, window):
        """Izračunava formu (bodovi u zadnjih N utakmica)"""
        # Implementacija rolling forme
        return np.random.uniform(0, 3, len(data))  # Demo
    
    def _rolling_mean(self, data, team_col, value_col):
        """Rolling prosek za dati kolon"""
        return np.random.uniform(0.5, 2.5, len(data))  # Demo
    
    def _head_to_head_stats(self, data):
        """H2H statistika"""
        return {'wins_ratio': np.random.uniform(0, 1), 'avg_goals': np.random.uniform(1, 3)}
    
    def _get_xg_rating(self, xg_data, team):
        """Dohvata xG rating za tim"""
        return np.random.uniform(1.0, 2.5)
    
    def _get_fifa_rank(self, fifa_rankings, team):
        """Dohvata FIFA rang"""
        return np.random.randint(1, 200)
    
    def _injury_factor(self, injury_data, team):
        """Faktor povreda (0-1, gde je 1 najgore)"""
        return np.random.uniform(0, 0.3)
    
    def _get_market_value(self, team):
        """Vrednost tima u milionima €"""
        return np.random.uniform(100, 1000)
    
    def _calculate_rest_days(self, data, team):
        """Broj dana odmora od poslednje utakmice"""
        return np.random.randint(3, 10)