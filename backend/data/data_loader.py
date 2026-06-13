"""
Data Loader - učitavanje podataka iz raw/ i processed/ foldera
"""

import pandas as pd
import os
import joblib
from typing import Optional, Tuple, Dict

# Putanje
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, 'raw')
PROCESSED_DIR = os.path.join(BASE_DIR, 'processed')
MODELS_DIR = os.path.join(BASE_DIR, 'models')


def load_raw_matches(filename: str = 'sample_matches.csv') -> pd.DataFrame:
    """Učitava sirove podatke o utakmicama"""
    path = os.path.join(RAW_DIR, filename)
    if os.path.exists(path):
        df = pd.read_csv(path)
        print(f"✅ Učitano {len(df)} utakmica iz {filename}")
        return df
    else:
        print(f"⚠️ Fajl ne postoji: {path}")
        return pd.DataFrame()


def load_fifa_rankings() -> pd.DataFrame:
    """Učitava FIFA rang liste"""
    path = os.path.join(RAW_DIR, 'fifa_rankings.csv')
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


def load_elo_ratings() -> pd.DataFrame:
    """Učitava ELO rejtinge"""
    path = os.path.join(RAW_DIR, 'elo_ratings.csv')
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


def load_training_data(filename: str = 'training_data.csv') -> pd.DataFrame:
    """Učitava procesirane podatke spremne za ML"""
    path = os.path.join(PROCESSED_DIR, filename)
    if os.path.exists(path):
        df = pd.read_csv(path)
        print(f"✅ Učitano {len(df)} redova za trening")
        return df
    print(f"⚠️ Fajl ne postoji: {path}")
    return pd.DataFrame()


def save_processed_data(df: pd.DataFrame, filename: str):
    """Čuva procesirane podatke"""
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    path = os.path.join(PROCESSED_DIR, filename)
    df.to_csv(path, index=False)
    print(f"💾 Podaci sačuvani u {path}")


def save_model(model, name: str):
    """Čuva ML model"""
    os.makedirs(MODELS_DIR, exist_ok=True)
    path = os.path.join(MODELS_DIR, name)
    joblib.dump(model, path)
    print(f"💾 Model sačuvan u {path}")


def load_model(name: str):
    """Učitava ML model"""
    path = os.path.join(MODELS_DIR, name)
    if os.path.exists(path):
        return joblib.load(path)
    print(f"⚠️ Model ne postoji: {path}")
    return None


def list_available_data() -> Dict:
    """Lista svih dostupnih fajlova"""
    available = {'raw': [], 'processed': [], 'models': []}
    
    for folder in ['raw', 'processed', 'models']:
        folder_path = os.path.join(BASE_DIR, folder)
        if os.path.exists(folder_path):
            available[folder] = [f for f in os.listdir(folder_path) if not f.startswith('.')]
    
    return available


def create_sample_team_stats(team_name: str) -> Dict:
    """Kreira sample statistiku za tim (za demo)"""
    import random
    
    return {
        'team': team_name,
        'form_5': round(random.uniform(0.4, 1.0), 2),
        'form_10': round(random.uniform(0.4, 0.9), 2),
        'avg_goals_for': round(random.uniform(1.0, 2.5), 1),
        'avg_goals_against': round(random.uniform(0.5, 1.8), 1),
        'fifa_rank': random.randint(1, 50),
        'elo_rating': random.randint(1700, 2200)
    }


if __name__ == "__main__":
    print("="*50)
    print("📁 DATA FOLDER - Status")
    print("="*50)
    
    available = list_available_data()
    
    print("\n📂 Raw fajlovi:")
    for f in available['raw']:
        print(f"   - {f}")
    
    print("\n📂 Processed fajlovi:")
    for f in available['processed']:
        print(f"   - {f}")
    
    print("\n📂 Modeli:")
    for f in available['models']:
        print(f"   - {f}")
    
    print("\n" + "="*50)
    
    # Test učitavanja
    df = load_raw_matches()
    if not df.empty:
        print(f"\n📊 Primer podataka:\n{df.head()}")