"""
XGBoost Model - Gradient boosting za predikciju fudbalskih utakmica
Sa hyperparameter tuning-om i cross-validation
"""

import xgboost as xgb
import numpy as np
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.metrics import accuracy_score, classification_report
import joblib
import json
import os
from typing import Dict, Optional, Tuple

class XGBoostModel:
    """
    XGBoost klasifikator za predikciju ishoda utakmice
    Klase: 0 = gost pobedio, 1 = nerešeno, 2 = domaćin pobedio
    """
    
    def __init__(self, random_state: int = 42):
        self.model = None
        self.best_params = None
        self.random_state = random_state
        self.is_trained = False
        self.feature_importance = None
        
    def get_default_params(self) -> Dict:
        """Default parametri za XGBoost"""
        return {
            'n_estimators': 200,
            'max_depth': 6,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'gamma': 0.1,
            'reg_alpha': 0.05,
            'reg_lambda': 1.0,
            'min_child_weight': 3,
            'random_state': self.random_state,
            'eval_metric': 'mlogloss',
            'use_label_encoder': False
        }
    
    def get_hyperparameter_grid(self) -> Dict:
        """Grid za hyperparameter tuning"""
        return {
            'n_estimators': [100, 200, 300, 500],
            'max_depth': [4, 6, 8, 10],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'subsample': [0.6, 0.8, 1.0],
            'colsample_bytree': [0.6, 0.8, 1.0],
            'gamma': [0, 0.1, 0.2, 0.3],
            'reg_alpha': [0, 0.05, 0.1, 0.5],
            'reg_lambda': [0.5, 1.0, 1.5, 2.0]
        }
    
    def tune_hyperparameters(self, X_train: np.ndarray, y_train: np.ndarray,
                            X_val: np.ndarray, y_val: np.ndarray,
                            n_iter: int = 30) -> Dict:
        """
        Hyperparameter tuning koristeći RandomizedSearchCV
        
        Args:
            X_train, y_train: Trening podaci
            X_val, y_val: Validacioni podaci
            n_iter: Broj kombinacija za testiranje
        
        Returns:
            Dict: Najbolji parametri
        """
        print("🔍 Tuning XGBoost hyperparametara...")
        
        xgb_model = xgb.XGBClassifier(
            random_state=self.random_state,
            eval_metric='mlogloss',
            use_label_encoder=False
        )
        
        random_search = RandomizedSearchCV(
            xgb_model,
            self.get_hyperparameter_grid(),
            n_iter=n_iter,
            cv=5,
            scoring='accuracy',
            n_jobs=-1,
            random_state=self.random_state,
            verbose=1
        )
        
        # Kombinuj trening i validaciju za tuning
        X_combined = np.vstack([X_train, X_val])
        y_combined = np.hstack([y_train, y_val])
        
        random_search.fit(X_combined, y_combined)
        
        self.best_params = random_search.best_params_
        print(f"✅ Najbolji parametri: {self.best_params}")
        print(f"📊 Najbolja tačnost: {random_search.best_score_:.2%}")
        
        return self.best_params
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: Optional[np.ndarray] = None,
              y_val: Optional[np.ndarray] = None,
              tune: bool = False) -> Dict:
        """
        Trenira XGBoost model
        
        Args:
            X_train, y_train: Trening podaci
            X_val, y_val: Validacioni podaci (opciono)
            tune: Da li izvršiti hyperparameter tuning
        
        Returns:
            Dict: Istorija treninga i metrike
        """
        print("🤖 Treniram XGBoost model...")
        
        # Hyperparameter tuning ako je zatraženo
        if tune and X_val is not None:
            self.tune_hyperparameters(X_train, y_train, X_val, y_val)
            params = self.best_params
        else:
            params = self.get_default_params()
        
        # Kreiraj i treniraj model
        self.model = xgb.XGBClassifier(**params)
        
        # Ako imamo validacioni skup, koristi ga za early stopping
        if X_val is not None and y_val is not None:
            eval_set = [(X_val, y_val)]
            self.model.fit(
                X_train, y_train,
                eval_set=eval_set,
                verbose=False
            )
        else:
            self.model.fit(X_train, y_train)
        
        self.is_trained = True
        
        # Izračunaj feature importance
        self.feature_importance = self.model.feature_importances_
        
        # Evaluacija na trening skupu
        train_pred = self.model.predict(X_train)
        train_acc = accuracy_score(y_train, train_pred)
        
        result = {
            'train_accuracy': train_acc,
            'best_params': params,
            'feature_importance': self.feature_importance.tolist()
        }
        
        # Evaluacija na validacionom skupu ako postoji
        if X_val is not None and y_val is not None:
            val_pred = self.model.predict(X_val)
            val_acc = accuracy_score(y_val, val_pred)
            result['validation_accuracy'] = val_acc
            print(f"📊 Validaciona tačnost: {val_acc:.2%}")
        
        print(f"✅ XGBoost model istreniran (trening tačnost: {train_acc:.2%})")
        
        return result
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predviđa klase"""
        if not self.is_trained:
            raise ValueError("Model nije istreniran!")
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predviđa verovatnoće za svaku klasu"""
        if not self.is_trained:
            raise ValueError("Model nije istreniran!")
        return self.model.predict_proba(X)
    
    def get_feature_importance(self, feature_names: list) -> Dict:
        """Vraća feature importance sa imenima"""
        if self.feature_importance is None:
            return {}
        
        importance_dict = {}
        for name, imp in zip(feature_names, self.feature_importance):
            importance_dict[name] = float(imp)
        
        # Sortiraj po važnosti
        return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
    
    def save(self, path: str = 'backend/data/models/xgboost_model.pkl'):
        """Čuva model"""
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.model, path)
        
        # Sačuvaj i parametre
        params_path = path.replace('.pkl', '_params.json')
        with open(params_path, 'w') as f:
            json.dump(self.best_params or self.get_default_params(), f, indent=2)
        
        print(f"💾 XGBoost model sačuvan na {path}")
    
    def load(self, path: str = 'backend/data/models/xgboost_model.pkl'):
        """Učitava model"""
        self.model = joblib.load(path)
        self.is_trained = True
        print(f"📂 XGBoost model učitan sa {path}")


# Testiranje
if __name__ == "__main__":
    # Mock podaci za test
    X_train = np.random.rand(100, 10)
    y_train = np.random.randint(0, 3, 100)
    X_val = np.random.rand(50, 10)
    y_val = np.random.randint(0, 3, 50)
    
    model = XGBoostModel()
    model.train(X_train, y_train, X_val, y_val, tune=False)
    
    # Test predikcije
    pred = model.predict(X_val[:5])
    proba = model.predict_proba(X_val[:5])
    print(f"Predikcije: {pred}")
    print(f"Verovatnoće: {proba}")