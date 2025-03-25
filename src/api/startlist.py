from .base import BaseAPIHandler
from typing import Dict, Any, List
import requests
import logging

class StartListAPI(BaseAPIHandler):
    BASE_URL = "https://www.stirnubuks.lv/api/"
    AUTH_TOKEN = ""
    
    def __init__(self, posms: str, distance: str, test_mode: bool = False):
        super().__init__()
        self.posms = posms
        self.distance = distance
        self.test_mode = test_mode
        
    def fetch_data(self) -> List[Dict[str, Any]]:
        params = {
            "module": "results_startlist",
            "auth_token": self.AUTH_TOKEN,
            "distance": self.distance,
            "posms": self.posms
        }
        
        if self.test_mode:
            params["gads"] = "2024"
            
        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching data: {str(e)}")
            return []
            
    def process_data(self, data: List[Dict[str, Any]]) -> None:
        if not data:
            self.logger.warning("No data to process")
            return

        # Process and save teams data
        teams_data = self._group_by_team(data)
        self.save_json(teams_data, "teams_startlist.json")

        # Process and save subteams data
        subteams_data = self._group_by_subteam(data)
        self.save_json(subteams_data, "subteams_startlist.json")
        
    def _translate_gender(self, dzimums: str) -> str:
        """
        Translate gender code to full Latvian words
        S -> Sievietes (Women)
        V -> Vīrieši (Men)
        """
        gender_map = {
            'S': 'Sievietes',
            'V': 'Vīrieši'
        }
        return gender_map.get(dzimums, dzimums)
        
    def _group_by_team(self, participants: List[Dict[str, Any]]) -> Dict[str, Any]:
        teams = {}
        
        for participant in participants:
            team_name = participant.get('komanda', 'Unknown Team')
            
            if team_name not in teams:
                teams[team_name] = []
                
            participant_data = {
                'image_path': participant.get('image_path', ''),
                'gender': self._translate_gender(participant.get('dzimums', '')),
                'dal_id': participant.get('dal_id', ''),
                'full_name': participant.get('full_name', ''),
                'grupa': participant.get('grupa', ''),
                'punkti': participant.get('punkti', 0)
            }
            
            teams[team_name].append(participant_data)
            
        return teams
        
    def _group_by_subteam(self, participants: List[Dict[str, Any]]) -> Dict[str, Any]:
        subteams = {}
        
        for participant in participants:
            subteam_name = participant.get('grupa', 'Unknown Subteam')
            
            if subteam_name not in subteams:
                subteams[subteam_name] = []
                
            participant_data = {
                'group': participant.get('komanda', ''),
                'image_path': participant.get('image_path', ''),
                'gender': self._translate_gender(participant.get('dzimums', '')),
                'dal_id': participant.get('dal_id', ''),
                'full_name': participant.get('full_name', ''),
                'komanda': participant.get('komanda', ''),
                'punkti': participant.get('punkti', 0)
            }
            
            subteams[subteam_name].append(participant_data)
            
        return subteams