from .base import BaseAPIHandler
from typing import Dict, Any, List, Tuple
import requests
import logging
import os
import json

class AwardingAPI(BaseAPIHandler):
    BASE_URL = "https://www.stirnubuks.lv/api/"
    AWARDING_FILE = "awarding_results.json"  # Single file for all awarding results
    
    def __init__(self, posms: str, distances: List[str], auth_token: str, test_mode: bool = False, group_configs: Dict[str, Dict[str, Any]] = None):
        super().__init__()
        self.posms = posms
        self.distances = distances
        self.AUTH_TOKEN = auth_token
        self.test_mode = test_mode
        self.group_configs = group_configs or {}

    def fetch_data(self) -> Dict[str, Any]:
        """Implementation of abstract method from BaseAPIHandler"""
        all_data = {}
        for distance in self.distances:
            distance_name, data = self._fetch_single_distance(distance)
            if data:
                all_data[distance_name] = data
        return all_data

    def _translate_gender(self, dzimums: str) -> str:
        gender_map = {
            'S': 'Sievietes',
            'V': 'Vīrieši'
        }
        return gender_map.get(dzimums, dzimums)

    def _fetch_single_distance(self, distance: str) -> Tuple[str, List[Dict[str, Any]]]:
        params = {
            "module": "results_posms",
            "auth_token": self.AUTH_TOKEN,
            "distance": distance,
            "posms": self.posms
        }
        
        if self.test_mode:
            params["gads"] = "2024"
            
        try:
            print(f"Fetching awarding data for distance {distance}")  # Debug print
            print(f"URL params: {params}")  # Debug print
            response = requests.get(self.BASE_URL, params=params)
            print(f"Response status: {response.status_code}")  # Debug print
            print(f"Response content: {response.text[:200]}")  # Debug print first 200 chars
            response.raise_for_status()
            return distance, response.json()
        except Exception as e:
            self.logger.error(f"Error fetching awarding data for distance {distance}: {str(e)}")
            print(f"Error in _fetch_single_distance: {str(e)}")  # Debug print
            return distance, []

    def process_data(self, all_data: Dict[str, List[Dict[str, Any]]]) -> None:
        """Process all fetched data into the required format"""
        if not all_data:
            self.logger.warning("No data to process")
            return

        result = {"teams": []}  # Initialize with teams array
        
        # Process each distance's data
        for distance, participants in all_data.items():
            # First group participants by distance and grupa
            group_categories = {}
            for participant in participants:
                gender = self._translate_gender(participant.get('dzimums', ''))
                grupa = participant.get('grupa', 'Kopvērtējums')
                
                category_key = f"{distance}_{grupa}"
                if category_key not in group_categories:
                    group_categories[category_key] = {
                        'Sievietes': [],
                        'Vīrieši': []
                    }
                group_categories[category_key][gender].append(participant)

            # Process each category
            for category_key, gender_groups in group_categories.items():
                distance_name, grupa = category_key.split('_', 1)
                
                # Process each gender within the category
                for gender, participants_list in gender_groups.items():
                    if not participants_list:  # Skip if no participants
                        continue
                    
                    # Sort participants by race time
                    sorted_participants = sorted(
                        participants_list,
                        key=lambda x: float(x.get('RaceTime', '999999')) if x.get('RaceTime') and x.get('RaceTime').replace('.','',1).isdigit() else float('inf')
                    )

                    group_config = self.group_configs.get(category_key, {})
                    base_name = group_config.get('name', distance)
                    
                    # Create category entry
                    category_data = {
                        'grupa': grupa,  # Use grupa directly as specified in your JSON
                        'gender': gender
                    }

                    # Add top 3 participants
                    for i in range(1, 4):
                        if i <= len(sorted_participants):
                            participant = sorted_participants[i-1]
                            category_data[f'name{i}'] = str(participant.get('Name', ''))
                            category_data[f'image{i}'] = ''  # Empty string for image as shown in your JSON
                            category_data[f'time{i}'] = str(participant.get('RaceTime', ''))
                            category_data[f'number{i}'] = str(participant.get('dal_id', ''))
                        else:
                            category_data[f'name{i}'] = ''
                            category_data[f'image{i}'] = ''
                            category_data[f'time{i}'] = ''
                            category_data[f'number{i}'] = ''

                    # Append to teams array
                    result['teams'].append(category_data)

        try:
            os.makedirs(self.output_dir, exist_ok=True)
            filepath = os.path.join(self.output_dir, self.AWARDING_FILE)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error in save/verify process: {str(e)}") 