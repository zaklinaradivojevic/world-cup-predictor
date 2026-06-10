import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

class TournamentManager:
    """
    Upravlja BILO KOJIM fudbalskim prvenstvom
    - Svetsko prvenstvo
    - Evropsko prvenstvo
    - Liga šampiona
    - Nacionalne lige
    """
    
    def __init__(self):
        self.active_tournament = None
        self.tournaments_db = {}
    
    def register_tournament(self, name: str, config: Dict):
        """Registruje novo prvenstvo"""
        self.tournaments_db[name] = {
            'name': name,
            'config': config,
            'teams': [],
            'matches': [],
            'standings': {}
        }
        print(f"✅ Turnir '{name}' registrovan")
    
    def load_tournament_from_csv(self, csv_path: str, tournament_name: str):
        """Učitava timove i utakmice iz CSV fajla"""
        df = pd.read_csv(csv_path)
        
        config = {
            'type': df.attrs.get('tournament_type', 'league'),
            'teams': df['team'].unique().tolist(),
            'season': df.attrs.get('season', '2024'),
            'format': df.attrs.get('format', 'round_robin')
        }
        
        self.register_tournament(tournament_name, config)
        self.tournaments_db[tournament_name]['matches'] = df.to_dict('records')
        
        return True
    
    def create_custom_tournament(self, name: str, teams: List[str], 
                                  format: str = 'knockout', 
                                  groups: Optional[Dict] = None):
        """Kreira prilagođeno prvenstvo sa proizvoljnim timovima"""
        
        config = {
            'type': 'custom',
            'teams': teams,
            'format': format,  # 'knockout', 'group+knockout', 'league'
            'groups': groups
        }
        
        self.register_tournament(name, config)
        
        # Kreiraj raspored utakmica
        if format == 'knockout':
            self._create_knockout_bracket(name, teams)
        elif format == 'group+knockout' and groups:
            self._create_group_stage(name, groups)
        
        return True
    
    def _create_knockout_bracket(self, tournament_name: str, teams: List[str]):
        """Kreira knockout bracket"""
        import random
        
        # Random žreb
        shuffled_teams = random.sample(teams, len(teams))
        
        matches = []
        for i in range(0, len(shuffled_teams), 2):
            if i+1 < len(shuffled_teams):
                matches.append({
                    'round': 'Round of ' + str(len(shuffled_teams)),
                    'team1': shuffled_teams[i],
                    'team2': shuffled_teams[i+1],
                    'date': None,
                    'venue': 'neutral'
                })
        
        self.tournaments_db[tournament_name]['matches'] = matches
    
    def _create_group_stage(self, tournament_name: str, groups: Dict):
        """Kreira grupnu fazu"""
        matches = []
        
        for group_name, teams in groups.items():
            from itertools import combinations
            for team1, team2 in combinations(teams, 2):
                matches.append({
                    'round': 'Group Stage',
                    'group': group_name,
                    'team1': team1,
                    'team2': team2,
                    'date': None,
                    'venue': 'neutral'
                })
        
        self.tournaments_db[tournament_name]['matches'] = matches
    
    def update_match_result(self, tournament_name: str, 
                            team1: str, team2: str, 
                            goals1: int, goals2: int):
        """Ažurira rezultat utakmice"""
        for match in self.tournaments_db[tournament_name]['matches']:
            if match['team1'] == team1 and match['team2'] == team2:
                match['goals1'] = goals1
                match['goals2'] = goals2
                match['completed'] = True
                
                # Ažuriraj tabelu ako je grupna faza
                if 'group' in match:
                    self._update_group_standings(tournament_name, match)
                
                return True
        return False
    
    def _update_group_standings(self, tournament_name: str, match: Dict):
        """Ažurira tabelu u grupi"""
        group = match['group']
        team1 = match['team1']
        team2 = match['team2']
        g1, g2 = match['goals1'], match['goals2']
        
        if tournament_name not in self.tournaments_db:
            return
        
        if group not in self.tournaments_db[tournament_name]['standings']:
            self.tournaments_db[tournament_name]['standings'][group] = {}
        
        for team in [team1, team2]:
            if team not in self.tournaments_db[tournament_name]['standings'][group]:
                self.tournaments_db[tournament_name]['standings'][group][team] = {
                    'played': 0, 'won': 0, 'drawn': 0, 'lost': 0,
                    'goals_for': 0, 'goals_against': 0, 'points': 0
                }
        
        # Ažuriraj statistiku za tim1
        stats1 = self.tournaments_db[tournament_name]['standings'][group][team1]
        stats1['played'] += 1
        stats1['goals_for'] += g1
        stats1['goals_against'] += g2
        
        # Ažuriraj statistiku za tim2
        stats2 = self.tournaments_db[tournament_name]['standings'][group][team2]
        stats2['played'] += 1
        stats2['goals_for'] += g2
        stats2['goals_against'] += g1
        
        if g1 > g2:
            stats1['won'] += 1
            stats1['points'] += 3
            stats2['lost'] += 1
        elif g2 > g1:
            stats2['won'] += 1
            stats2['points'] += 3
            stats1['lost'] += 1
        else:
            stats1['drawn'] += 1
            stats1['points'] += 1
            stats2['drawn'] += 1
            stats2['points'] += 1
    
    def get_standings(self, tournament_name: str) -> Dict:
        """Vraća trenutnu tabelu"""
        return self.tournaments_db.get(tournament_name, {}).get('standings', {})
    
    def get_next_matches(self, tournament_name: str, limit: int = 10) -> List:
        """Vraća naredne utakmice"""
        matches = self.tournaments_db.get(tournament_name, {}).get('matches', [])
        return [m for m in matches if not m.get('completed', False)][:limit]