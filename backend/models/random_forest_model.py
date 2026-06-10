"""
Random Forest Model - Ensemble of decision trees za predikciju
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import accuracy_score
import joblib
import json
from typing import Dict, Optional

class RandomForestModel:
    """
    Random Forest klasifikator za predikciju ishoda utakmice
    """
    
    def __init__(self, random_state: int = 42):
        self.model = None
        self.best_params = None
        self.random_state = random_state
        self.is_trained = False
        self.feature_importance = None
    
    def get_default_params(self) -> Dict:
        """Default parametri za Random Forest"""
        return {
            'n_estimators': 200,
            'max_depth': 20,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'max_features': 'sqrt',
            'random_state': self.random_state,
            'n_jobs': -1
        }
    
    def get_hyperparameter_grid(self) -> Dict:
        """Grid za hyperparameter tuning"""
        return {
            'n_estimators': [100, 200, 300, 500],
            'max_depth': [10, 20, 30, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['sqrt', 'log2', None]
        }
    
    def tune_hyperparameters(self, X_train: np.ndarray, y_train: np.ndarray,
                            n_iter: int = 20) -> Dict:
        """
        Hyperparameter tuning koristeći RandomizedSearchCV
        """
        print("🔍 Tuning Random Forest hyperparametara...")
        
        rf_model = RandomForestClassifier(random_state=self.random_state)
        
        random_search = RandomizedSearchCV(
            rf_model,
            self.get_hyperparameter_grid(),
            n_iter=n_iter,
            cv=5,
            scoring='accuracy',
            n_jobs=-1,
            random_state=self.random_state,
            verbose=1
        )
        
        random_search.fit(X_train, y_train)
        
        self.best_params = random_search.best_params_
        print(f"✅ Najbolji parametri: {self.best_params}")
        print(f"📊 Najbolja tačnost: {random_search.best_score_:.2%}")
        
        return self.best_params
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: Optional[np.ndarray] = None,
              y_val: Optional[np.ndarray] = None,
              tune: bool = False) -> Dict:
        """
        Trenira Random Forest model
        """
        print("🌲 Treniram Random Forest model...")
        
        # Hyperparameter tuning ako je zatraženo
        if tune:
            self.tune_hyperparameters(X_train, y_train)
            params = self.best_params
        else:
            params = self.get_default_params()
        
        # Kreiraj i treniraj model
        self.model = RandomForestClassifier(**params)
        self.model.fit(X_train, y_train)
        
        self.is_trained = True
        
        # Feature importance
        self.feature_importance = self.model.feature_importances_
        
        # Evaluacija
        train_pred = self.model.predict(X_train)
        train_acc = accuracy_score(y_train, train_pred)
        
        result = {
            'train_accuracy': train_acc,
            'best_params': params,
            'feature_importance': self.feature_importance.tolist()
        }
        
        if X_val is not None and y_val is not None:
            val_pred = self.model.predict(X_val)
            val_acc = accuracy_score(y_val, val_pred)
            result['validation_accuracy'] = val_acc
            print(f"📊 Validaciona tačnost: {val_acc:.2%}")
        
        print(f"✅ Random Forest model istreniran (trening tačnost: {train_acc:.2%})")
        
        return result
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predviđa klase"""
        if not self.is_trained:
            raise ValueError("Model nije istreniran!")
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predviđa verovatnoće"""
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
        
        return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
    
    def save(self, path: str = 'backend/data/models/random_forest.pkl'):
        """Čuva model"""
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.model, path)
        print(f"💾 Random Forest model sačuvan na {path}")
    
    def load(self, path: str = 'backend/data/models/random_forest.pkl'):
        """Učitava model"""
        self.model = joblib.load(path)
        self.is_trained = True
        print(f"📂 Random Forest model učitan sa {path}")


# Testiranje
if __name__ == "__main__":
    X_train = np.random.rand(100, 10)
    y_train = np.random.randint(0, 3, 100)
    
    model = RandomForestModel()
    model.train(X_train, y_train, tune=False)
    print(f"Feature importance: {model.feature_importance[:5]}")