"""
Evaluation Module - evaluacija performansi ML modela
Metrike: accuracy, precision, recall, f1-score, confusion matrix, ROC-AUC
"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    roc_auc_score,
    roc_curve,
    mean_absolute_error,
    mean_squared_error
)
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os

class ModelEvaluator:
    """
    Evaluacija performansi ML modela za predikciju fudbalskih utakmica
    """
    
    def __init__(self):
        self.results = {}
    
    def calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray, 
                          y_proba: Optional[np.ndarray] = None) -> Dict:
        """
        Izračunava sve metrike za klasifikaciju
        
        Args:
            y_true: Stvarne vrednosti
            y_pred: Predviđene vrednosti
            y_proba: Verovatnoće (opciono, za ROC-AUC)
        
        Returns:
            Dict: Sve metrike
        """
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision_macro': precision_score(y_true, y_pred, average='macro', zero_division=0),
            'recall_macro': recall_score(y_true, y_pred, average='macro', zero_division=0),
            'f1_macro': f1_score(y_true, y_pred, average='macro', zero_division=0),
            'precision_weighted': precision_score(y_true, y_pred, average='weighted', zero_division=0),
            'recall_weighted': recall_score(y_true, y_pred, average='weighted', zero_division=0),
            'f1_weighted': f1_score(y_true, y_pred, average='weighted', zero_division=0),
        }
        
        # Dodaj ROC-AUC ako imamo verovatnoće (za multi-class)
        if y_proba is not None and y_proba.shape[1] == 3:
            try:
                metrics['roc_auc_ovr'] = roc_auc_score(y_true, y_proba, multi_class='ovr', average='macro')
                metrics['roc_auc_ovo'] = roc_auc_score(y_true, y_proba, multi_class='ovo', average='macro')
            except:
                metrics['roc_auc_ovr'] = 0.0
                metrics['roc_auc_ovo'] = 0.0
        
        return metrics
    
    def confusion_matrix_analysis(self, y_true: np.ndarray, y_pred: np.ndarray, 
                                   class_names: List[str] = ['Away_Win', 'Draw', 'Home_Win']) -> Dict:
        """
        Analiza matrice konfuzije
        
        Returns:
            Dict: Matrica konfuzije i pojedinačne metrike po klasama
        """
        cm = confusion_matrix(y_true, y_pred)
        
        # Izračunaj metrike po klasama
        class_metrics = {}
        for i, class_name in enumerate(class_names):
            tp = cm[i, i]
            fp = cm[:, i].sum() - tp
            fn = cm[i, :].sum() - tp
            tn = cm.sum() - (tp + fp + fn)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            class_metrics[class_name] = {
                'true_positives': int(tp),
                'false_positives': int(fp),
                'false_negatives': int(fn),
                'true_negatives': int(tn),
                'precision': round(precision, 4),
                'recall': round(recall, 4),
                'f1_score': round(f1, 4)
            }
        
        return {
            'confusion_matrix': cm.tolist(),
            'class_metrics': class_metrics
        }
    
    def regression_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
        """
        Metrike za regresiju (npr. za predikciju golova)
        
        Args:
            y_true: Stvarni golovi
            y_pred: Predviđeni golovi
        """
        return {
            'mae': mean_absolute_error(y_true, y_pred),
            'mse': mean_squared_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mape': np.mean(np.abs((y_true - y_pred) / (y_true + 1))) * 100
        }
    
    def compare_models(self, model_predictions: Dict[str, Tuple[np.ndarray, np.ndarray]], 
                       y_true: np.ndarray) -> pd.DataFrame:
        """
        Upoređuje više modela
        
        Args:
            model_predictions: Dict {model_name: (y_pred, y_proba)}
            y_true: Stvarne vrednosti
        
        Returns:
            DataFrame sa poređenjem metrika
        """
        comparison = []
        
        for model_name, (y_pred, y_proba) in model_predictions.items():
            metrics = self.calculate_metrics(y_true, y_pred, y_proba)
            metrics['model'] = model_name
            comparison.append(metrics)
        
        df = pd.DataFrame(comparison)
        df = df.set_index('model')
        
        return df
    
    def plot_confusion_matrix(self, y_true: np.ndarray, y_pred: np.ndarray,
                              class_names: List[str] = ['Away Win', 'Draw', 'Home Win'],
                              save_path: Optional[str] = None):
        """
        Prikazuje i čuva matricu konfuzije
        """
        cm = confusion_matrix(y_true, y_pred)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=class_names, yticklabels=class_names)
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"📊 Matrica konfuzije sačuvana na {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_roc_curves(self, y_true: np.ndarray, y_proba: np.ndarray,
                        class_names: List[str] = ['Away Win', 'Draw', 'Home Win'],
                        save_path: Optional[str] = None):
        """
        Prikazuje ROC krive za multi-class klasifikaciju (One-vs-Rest)
        """
        from sklearn.preprocessing import label_binarize
        
        # Binarizuj true labels
        y_bin = label_binarize(y_true, classes=[0, 1, 2])
        
        plt.figure(figsize=(8, 6))
        
        for i, class_name in enumerate(class_names):
            fpr, tpr, _ = roc_curve(y_bin[:, i], y_proba[:, i])
            auc = roc_auc_score(y_bin[:, i], y_proba[:, i])
            plt.plot(fpr, tpr, label=f'{class_name} (AUC = {auc:.3f})')
        
        plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curves (One-vs-Rest)')
        plt.legend(loc="lower right")
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"📈 ROC krive sačuvane na {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_feature_importance(self, feature_importance: Dict[str, float],
                                top_n: int = 20,
                                save_path: Optional[str] = None):
        """
        Prikazuje najvažnije feature-e
        """
        # Sortiraj po važnosti
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        features, scores = zip(*sorted_features)
        
        plt.figure(figsize=(10, 8))
        plt.barh(range(len(features)), scores, color='steelblue')
        plt.yticks(range(len(features)), features)
        plt.xlabel('Importance')
        plt.title(f'Top {top_n} Feature Importance')
        plt.gca().invert_yaxis()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"📊 Feature importance sačuvan na {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def betting_simulation(self, y_true: np.ndarray, y_proba: np.ndarray,
                           odds: np.ndarray = None,
                           bet_amount: float = 10.0) -> Dict:
        """
        Simulacija klađenja na osnovu predikcija modela
        
        Args:
            y_true: Stvarni ishodi
            y_proba: Verovatnoće modela
            odds: Kvote (ako nema, koristi 1/proba)
            bet_amount: Iznos opklade po utakmici
        
        Returns:
            Dict: Profit, ROI, tačnost opklada
        """
        n_matches = len(y_true)
        predicted_classes = np.argmax(y_proba, axis=1)
        max_proba = np.max(y_proba, axis=1)
        
        # Ako nema kvota, koristi inverzne verovatnoće
        if odds is None:
            odds = 1.0 / (max_proba + 0.01)  # Dodaj mali epsilon
            odds = np.clip(odds, 1.5, 10.0)  # Ograniči kvote
        
        # Samo se kladimo kada je verovatnoća iznad praga
        threshold = 0.55
        valid_bets = max_proba > threshold
        
        total_bets = valid_bets.sum()
        correct_bets = ((predicted_classes == y_true) & valid_bets).sum()
        
        if total_bets > 0:
            # Izračunaj profit
            profits = []
            for i in range(n_matches):
                if valid_bets[i]:
                    if predicted_classes[i] == y_true[i]:
                        profit = bet_amount * (odds[i] - 1)
                    else:
                        profit = -bet_amount
                    profits.append(profit)
            
            total_profit = sum(profits)
            roi = (total_profit / (total_bets * bet_amount)) * 100
            accuracy = correct_bets / total_bets
        else:
            total_profit = 0
            roi = 0
            accuracy = 0
        
        return {
            'total_bets': int(total_bets),
            'correct_bets': int(correct_bets),
            'accuracy': round(accuracy * 100, 2),
            'total_profit': round(total_profit, 2),
            'roi': round(roi, 2),
            'avg_odds': round(odds[valid_bets].mean(), 2) if total_bets > 0 else 0
        }
    
    def save_evaluation_report(self, metrics: Dict, save_path: str = 'backend/data/models/evaluation_report.json'):
        """Čuva evaluacioni izveštaj kao JSON"""
        import os
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print(f"📄 Evaluacioni izveštaj sačuvan na {save_path}")
    
    def print_summary(self, metrics: Dict):
        """Štampa sažetak metrika"""
        print("\n" + "="*50)
        print("📊 EVALUACIJA MODELA")
        print("="*50)
        
        print(f"\n🎯 Osnovne metrike:")
        print(f"   Accuracy:  {metrics.get('accuracy', 0):.2%}")
        print(f"   Precision: {metrics.get('precision_macro', 0):.2%}")
        print(f"   Recall:    {metrics.get('recall_macro', 0):.2%}")
        print(f"   F1-Score:  {metrics.get('f1_macro', 0):.2%}")
        
        if 'roc_auc_ovr' in metrics:
            print(f"\n📈 ROC-AUC:")
            print(f"   One-vs-Rest:  {metrics.get('roc_auc_ovr', 0):.3f}")
            print(f"   One-vs-One:   {metrics.get('roc_auc_ovo', 0):.3f}")
        
        if 'total_bets' in metrics:
            print(f"\n💰 Simulacija klađenja:")
            print(f"   Opklade:      {metrics.get('total_bets', 0)}")
            print(f"   Pogađanja:    {metrics.get('correct_bets', 0)}")
            print(f"   Tačnost:      {metrics.get('accuracy', 0)}%")
            print(f"   Profit:       {metrics.get('total_profit', 0):.2f}€")
            print(f"   ROI:          {metrics.get('roi', 0):.2f}%")
        
        print("\n" + "="*50)


# Testiranje
if __name__ == "__main__":
    # Mock podaci
    y_true = np.random.randint(0, 3, 100)
    y_pred = np.random.randint(0, 3, 100)
    y_proba = np.random.rand(100, 3)
    y_proba = y_proba / y_proba.sum(axis=1, keepdims=True)
    
    evaluator = ModelEvaluator()
    
    # Izračunaj metrike
    metrics = evaluator.calculate_metrics(y_true, y_pred, y_proba)
    evaluator.print_summary(metrics)
    
    # Matrica konfuzije
    cm_analysis = evaluator.confusion_matrix_analysis(y_true, y_pred)
    print(f"\nMatrica konfuzije:\n{np.array(cm_analysis['confusion_matrix'])}")