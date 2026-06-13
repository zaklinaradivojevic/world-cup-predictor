"""
Data package - upravljanje podacima
- raw: sirovi podaci sa scraper-a
- processed: očišćeni podaci za ML
- models: sačuvani modeli
"""

from .data_loader import (
    load_raw_matches,
    load_fifa_rankings,
    load_elo_ratings,
    load_training_data,
    save_processed_data,
    save_model,
    load_model,
    list_available_data,
    create_sample_team_stats
)

__all__ = [
    'load_raw_matches',
    'load_fifa_rankings', 
    'load_elo_ratings',
    'load_training_data',
    'save_processed_data',
    'save_model',
    'load_model',
    'list_available_data',
    'create_sample_team_stats'
]