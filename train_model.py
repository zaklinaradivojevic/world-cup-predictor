"""
Trening XGBoost modela za predikciju fudbalskih utakmica
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import xgboost as xgb
import joblib
import os

# Kreiraj folder za modele ako ne postoji
os.makedirs('backend/data/models', exist_ok=True)

print("="*50)
print("🏆 TRENIRANJE XGBOOST MODELA")
print("="*50)

# ============================================
# 1. KREIRANJE SAMPLE PODATAKA ZA TRENING
# ============================================
print("\n📊 1. Kreiranje trening podataka...")

np.random.seed(42)
n_matches = 3000  # Povećano na 3000

teams = [
    "Brazil", "Argentina", "France", "Germany", "Spain", "England",
    "Netherlands", "Portugal", "Belgium", "Croatia", "Italy", "Uruguay",
    "Mexico", "USA", "Japan", "Morocco", "Senegal", "Australia"
]

team_strength = {
    'Brazil': 0.95, 'Argentina': 0.93, 'France': 0.92, 'Germany': 0.90,
    'Spain': 0.89, 'England': 0.88, 'Netherlands': 0.85, 'Portugal': 0.84,
    'Belgium': 0.83, 'Croatia': 0.80, 'Italy': 0.82, 'Uruguay': 0.78,
    'Mexico': 0.75, 'USA': 0.74, 'Japan': 0.72, 'Morocco': 0.70,
    'Senegal': 0.68, 'Australia': 0.65
}

data = []
for _ in range(n_matches):
    team1 = np.random.choice(teams)
    team2 = np.random.choice([t for t in teams if t != team1])
    venue = np.random.choice(['home', 'neutral', 'away'])
    
    strength1 = team_strength.get(team1, 0.70)
    strength2 = team_strength.get(team2, 0.70)
    
    home_factor = 1.20 if venue == 'home' else (0.85 if venue == 'away' else 1.00)
    
    # Izračunaj verovatnoće
    total_strength = strength1 * home_factor + strength2
    prob_home = (strength1 * home_factor) / total_strength
    prob_away = strength2 / total_strength
    prob_draw = 0.25 + (1 - abs(prob_home - prob_away)) * 0.1  # Osiguraj dovoljno nerešenih
    
    # Normalizacija
    total = prob_home + prob_draw + prob_away
    prob_home /= total
    prob_draw /= total
    prob_away /= total
    
    # Osiguraj da sve tri klase imaju šansu
    prob_home = max(0.2, min(0.6, prob_home))
    prob_draw = max(0.15, min(0.4, prob_draw))
    prob_away = max(0.2, min(0.6, prob_away))
    
    # Normalizacija ponovo
    total = prob_home + prob_draw + prob_away
    prob_home /= total
    prob_draw /= total
    prob_away /= total
    
    r = np.random.random()
    if r < prob_home:
        result = 0  # Domaćin pobedio
    elif r < prob_home + prob_draw:
        result = 1  # Nerešeno
    else:
        result = 2  # Gost pobedio
    
    data.append({
        'team1_strength': strength1,
        'team2_strength': strength2,
        'home_factor': home_factor,
        'venue_home': 1 if venue == 'home' else 0,
        'venue_neutral': 1 if venue == 'neutral' else 0,
        'venue_away': 1 if venue == 'away' else 0,
        'strength_diff': strength1 - strength2,
        'result': result
    })

df = pd.DataFrame(data)
print(f"   Kreirano {len(df)} utakmica za trening")

# Provera da li imamo sve klase
print(f"   Klase u y: {sorted(df['result'].unique())}")
print(f"   Distribucija:\n{df['result'].value_counts()}")

# ============================================
# 2. FEATURE-OVI I TARGET
# ============================================
print("\n🔧 2. Priprema feature-ova...")

feature_cols = ['team1_strength', 'team2_strength', 'home_factor', 
                'venue_home', 'venue_neutral', 'venue_away', 'strength_diff']

X = df[feature_cols].values
y = df['result'].values

print(f"   Feature-ovi: {feature_cols}")
print(f"   X shape: {X.shape}")
print(f"   y shape: {y.shape}")

# ============================================
# 3. TRENING/TEST PODELA
# ============================================
print("\n✂️ 3. Podela podataka...")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

print(f"   Trening: {len(X_train)} utakmica")
print(f"   Test: {len(X_test)} utakmica")

# ============================================
# 4. TRENIRANJE XGBOOST MODELA
# ============================================
print("\n🤖 4. Treniranje XGBoost modela...")

model = xgb.XGBClassifier(
    n_estimators=150,
    max_depth=6,
    learning_rate=0.1,
    random_state=42,
    eval_metric='mlogloss',
    use_label_encoder=False
)

model.fit(X_train, y_train)

# ============================================
# 5. EVALUACIJA
# ============================================
print("\n📊 5. Evaluacija modela...")

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"   Tačnost na test skupu: {accuracy:.2%}")

# ============================================
# 6. ČUVANJE MODELA
# ============================================
print("\n💾 6. Čuvanje modela...")

model_path = 'backend/data/models/xgboost_model.pkl'
joblib.dump(model, model_path)
print(f"   Model sačuvan u: {model_path}")

features_path = 'backend/data/models/features.txt'
with open(features_path, 'w') as f:
    for feat in feature_cols:
        f.write(feat + '\n')

print(f"   Feature-i sačuvani u: {features_path}")

# ============================================
# 7. TEST PREDIKCIJE
# ============================================
print("\n🔮 7. Test predikcije...")

test_features = np.array([[0.95, 0.93, 1.20, 1, 0, 0, 0.02]])
pred = model.predict(test_features)[0]
proba = model.predict_proba(test_features)[0]

results_map = {0: "Domaćin pobedio", 1: "Nerešeno", 2: "Gost pobedio"}
print(f"\n   Brazil (domaćin) vs Argentina:")
print(f"   Predikcija: {results_map[pred]}")
print(f"   Verovatnoće:")
print(f"      Brazil pobeda: {proba[0]:.1%}")
print(f"      Nerešeno: {proba[1]:.1%}")
print(f"      Argentina pobeda: {proba[2]:.1%}")

print("\n" + "="*50)
print("✅ TRENIRANJE ZAVRŠENO!")
print("="*50)
print(f"\n📈 Rezime:")
print(f"   Model: XGBoost Classifier")
print(f"   Tačnost: {accuracy:.2%}")
print(f"   Trening utakmica: {len(X_train)}")
print(f"   Test utakmica: {len(X_test)}")
print(f"   Feature-ova: {len(feature_cols)}")
print("="*50)   