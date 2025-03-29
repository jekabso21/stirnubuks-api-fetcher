from .base import BaseAPIHandler
from typing import Dict, Any, List, Tuple
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import json

class StartListAPI(BaseAPIHandler):
    BASE_URL = "https://www.stirnubuks.lv/api/"
    
    def __init__(self, posms: str, distances: List[str], auth_token: str, test_mode: bool = False, group_configs: Dict[str, Dict[str, Any]] = None):
        super().__init__()
        self.posms = posms
        self.distances = distances  # Now accepts a list of distances
        self.AUTH_TOKEN = auth_token
        self.test_mode = test_mode
        self.group_configs = group_configs or {}  # Dictionary to store custom group names and image links
        
    def _translate_gender(self, dzimums: str) -> str:
        """Translate gender code to full Latvian words"""
        gender_map = {
            'S': 'Sievietes',
            'V': 'Vīrieši'
        }
        return gender_map.get(dzimums, dzimums)
    
    def _fetch_single_distance(self, distance: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Fetch data for a single distance"""
        params = {
            "module": "results_startlist",
            "auth_token": self.AUTH_TOKEN,
            "distance": distance,
            "posms": self.posms
        }
        
        if self.test_mode:
            params["gads"] = "2024"
            
        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return distance, response.json()
        except Exception as e:
            self.logger.error(f"Error fetching data for distance {distance}: {str(e)}")
            return distance, []

    def fetch_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch data for all distances concurrently"""
        all_data = {}
        
        # Use ThreadPoolExecutor for concurrent API calls
        with ThreadPoolExecutor(max_workers=min(len(self.distances), 10)) as executor:
            # Submit all fetch tasks
            future_to_distance = {
                executor.submit(self._fetch_single_distance, distance): distance 
                for distance in self.distances
            }
            
            # Process results as they complete
            for future in as_completed(future_to_distance):
                distance, data = future.result()
                if data:  # Only add if we got valid data
                    all_data[distance] = data
        
        return all_data

    def process_data(self, all_data: Dict[str, List[Dict[str, Any]]]) -> None:
        """Process all fetched data into the required format"""
        if not all_data:
            self.logger.warning("No data to process")
            return

        result = []
        
        # Process each distance's data
        for distance, participants in all_data.items():
            # First, group participants by gender
            gender_groups = {}
            for participant in participants:
                gender = self._translate_gender(participant.get('dzimums', ''))
                if gender not in gender_groups:
                    gender_groups[gender] = []
                gender_groups[gender].append(participant)

            # Create one entry for each distance+gender combination
            for gender, gender_participants in gender_groups.items():
                # Get custom group name and image link from config if available
                group_key = str(f"{distance}_{gender}")
                group_config = self.group_configs.get(group_key, {})
                custom_name = group_config.get('name', group_key)
                image_link = group_config.get('image_link', '')
                
                # Create a single object for all participants in this distance+gender
                group_data = {
                    'group': custom_name,
                    'gender': gender
                }
                
                # Add up to 30 participants
                for i in range(1, 31):
                    if i <= len(gender_participants):
                        participant = gender_participants[i-1]
                        group_data[f'name{i}'] = str(participant.get('full_name', ''))
                        group_data[f'image{i}'] = image_link
                        group_data[f'points{i}'] = str(participant.get('punkti', ''))
                    else:
                        # Fill empty slots if we don't have enough participants
                        group_data[f'name{i}'] = ''
                        group_data[f'image{i}'] = image_link
                        group_data[f'points{i}'] = ''
                
                result.append(group_data)

        try:
            os.makedirs(self.output_dir, exist_ok=True)
            filepath = os.path.join(self.output_dir, "all_participants.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({"teams": result}, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error in save/verify process: {str(e)}")