from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.metrics import make_scorer, accuracy_score
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
import joblib
import numpy as np
from ..config import Config

class HyperparameterTuner:
    def __init__(self):
        self.best_params = {}
    
    def tune_xgboost(self, X_train, y_train):
        """Grid search za XGBoost"""
        print("🔍 Tuning XGBoost hyperparametara...")
        print(f"   Testiram {len(Config.XGBOOST_GRID)} kombinacija...")
        
        xgb_model = xgb.XGBClassifier(
            random_state=Config.RANDOM_STATE,
            eval_metric='mlogloss',
            use_label_encoder=False
        )
        
        # Randomized search za efikasnost
        random_search = RandomizedSearchCV(
            xgb_model,
            Config.XGBOOST_GRID,
            n_iter=30,
            cv=Config.CV_FOLDS,
            scoring='accuracy',
            n_jobs=-1,
            random_state=Config.RANDOM_STATE,
            verbose=1
        )
        
        random_search.fit(X_train, y_train)
        
        print(f"✅ Najbolji parametri: {random_search.best_params_}")
        print(f"📊 Najbolja tačnost: {random_search.best_score_:.2%}")
        
        self.best_params['xgboost'] = random_search.best_params_
        self.save_best_params('xgboost', random_search.best_params_)
        
        return random_search.best_estimator_
    
    def tune_random_forest(self, X_train, y_train):
        """Grid search za Random Forest"""
        print("🔍 Tuning Random Forest hyperparametara...")
        
        rf_model = RandomForestClassifier(random_state=Config.RANDOM_STATE)
        
        random_search = RandomizedSearchCV(
            rf_model,
            Config.RF_GRID,
            n_iter=20,
            cv=Config.CV_FOLDS,
            scoring='accuracy',
            n_jobs=-1,
            random_state=Config.RANDOM_STATE,
            verbose=1
        )
        
        random_search.fit(X_train, y_train)
        
        print(f"✅ Najbolji parametri: {random_search.best_params_}")
        print(f"📊 Najbolja tačnost: {random_search.best_score_:.2%}")
        
        self.best_params['random_forest'] = random_search.best_params_
        self.save_best_params('random_forest', random_search.best_params_)
        
        return random_search.best_estimator_
    
    def save_best_params(self, model_name, params):
        """Čuva najbolje parametre za kasnije korišćenje"""
        import json
        import os
        
        os.makedirs('backend/data/models', exist_ok=True)
        
        with open(f'backend/data/models/{model_name}_best_params.json', 'w') as f:
            json.dump(params, f, indent=2)
    
    def load_best_params(self, model_name):
        """Učitava najbolje parametre"""
        import json
        import os
        
        path = f'backend/data/models/{model_name}_best_params.json'
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return None