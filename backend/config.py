import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API ključevi
    SPORTMONKS_TOKEN = os.getenv('SPORTMONKS_TOKEN', '')
    FOOTBALL_DATA_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY', '')
    
    # Putanje
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_RAW_DIR = os.path.join(BASE_DIR, 'data/raw')
    DATA_PROCESSED_DIR = os.path.join(BASE_DIR, 'data/processed')
    MODELS_DIR = os.path.join(BASE_DIR, 'data/models')
    
    # Parametri za trening
    TEST_SIZE = 0.2
    RANDOM_STATE = 42
    CV_FOLDS = 5
    
    # Feature grupe
    FEATURE_GROUPS = {
        'basic': ['form', 'goals_scored', 'goals_conceded', 'h2h'],
        'advanced': ['xG', 'xGA', 'possession', 'shots_on_target', 'pass_accuracy'],
        'external': ['fifa_ranking', 'elo_rating', 'players_injuries'],
        'contextual': ['home_advantage', 'weather', 'days_since_last_match']
    }
    
    # Turnir specifične postavke
    COMPETITIONS = {
        'World Cup': {'id': 1, 'teams': 48, 'years': [1930, 1934, 1938, 1950, 1954, 1958, 1962, 1966, 1970, 1974, 1978, 1982, 1986, 1990, 1994, 1998, 2002, 2006, 2010, 2014, 2018, 2022, 2026]},
        'UEFA Champions League': {'id': 2, 'teams': 32},
        'English Premier League': {'id': 3, 'teams': 20},
        'La Liga': {'id': 4, 'teams': 20},
        'Serie A': {'id': 5, 'teams': 20},
        'Bundesliga': {'id': 6, 'teams': 18},
    }
    
    # Hyperparameter grid za XGBoost
    XGBOOST_GRID = {
        'n_estimators': [100, 200, 300, 500],
        'max_depth': [4, 6, 8, 10],
        'learning_rate': [0.01, 0.05, 0.1, 0.2],
        'subsample': [0.6, 0.8, 1.0],
        'colsample_bytree': [0.6, 0.8, 1.0],
        'gamma': [0, 0.1, 0.2, 0.3],
        'reg_alpha': [0, 0.05, 0.1, 0.5],
        'reg_lambda': [0.5, 1.0, 1.5, 2.0]
    }
    
    # Hyperparameter grid za Random Forest
    RF_GRID = {
        'n_estimators': [100, 200, 300],
        'max_depth': [10, 20, 30, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'max_features': ['sqrt', 'log2']
    }
        # ============ DODATO: Mock data flag ============
    USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'true').lower() == 'true'
    
    # OpenWeatherMap API
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')
    
    @classmethod
    def is_api_available(cls, api_name: str) -> bool:
        """Proverava da li je API ključ dostupan"""
        keys = {
            'sportmonks': cls.SPORTMONKS_TOKEN,
            'football_data': cls.FOOTBALL_DATA_API_KEY,
            'openweather': cls.OPENWEATHER_API_KEY
        }
        return bool(keys.get(api_name, ''))
    
    @classmethod
    def get_api_status(cls) -> dict:
        """Vraća status svih API-jeva"""
        return {
            'sportmonks': bool(cls.SPORTMONKS_TOKEN),
            'football_data': bool(cls.FOOTBALL_DATA_API_KEY),
            'openweather': bool(cls.OPENWEATHER_API_KEY),
            'use_mock_data': cls.USE_MOCK_DATA
        }