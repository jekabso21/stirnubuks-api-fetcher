from .base import BaseAPIHandler
from typing import Dict, Any, List, Tuple
import requests
import logging
from datetime import datetime
import time
import threading
import os
import json

class SummaryAPI(BaseAPIHandler):  # Renamed from LiveResultsAPI to SummaryAPI
    BASE_URL = "https://www.stirnubuks.lv/api/"
    
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
            "limit": 100  # Increase the limit to get more participants
        }
        
        # Only add posms if it's not empty
        if self.posms:
            params["posms"] = self.posms
        
        if self.test_mode:
            params["gads"] = "2024"
            
        try:
            print(f"Fetching summary data for distance {distance}")  # Debug print
            print(f"URL params: {params}")  # Debug print
            response = requests.get(self.BASE_URL, params=params)
            print(f"Response status: {response.status_code}")  # Debug print
            print(f"Response content: {response.text[:200]}")  # Debug print first 200 chars
            response.raise_for_status()
            return distance, response.json()
        except Exception as e:
            self.logger.error(f"Error fetching summary for distance {distance}: {str(e)}")
            print(f"Error in _fetch_single_distance: {str(e)}")  # Debug print
            return distance, []

    def process_data(self, all_data: Dict[str, List[Dict[str, Any]]]) -> None:
        """Process all fetched data into the required format"""
        if not all_data:
            self.logger.warning("No data to process")
            return

        result = []
        
        # Sort distances to ensure consistent order
        sorted_distances = sorted(all_data.keys())
        
        # Process each distance's data
        for distance in sorted_distances:
            participants = all_data[distance]
            # First, group participants by gender
            gender_groups = {}
            for participant in participants:
                gender = self._translate_gender(participant.get('dzimums', ''))
                if gender not in gender_groups:
                    gender_groups[gender] = []
                gender_groups[gender].append(participant)

            # Process females first, then males
            gender_order = ['Sievietes', 'Vīrieši']
            for gender in gender_order:
                if gender in gender_groups:
                    gender_participants = gender_groups[gender]
                    group_key = str(f"{distance}_{gender}")
                    group_config = self.group_configs.get(group_key, {})
                    custom_name = group_config.get('name', group_key)
                    image_path = group_config.get('image', '')
                    
                    # Create a single object for all participants in this distance+gender
                    group_data = {
                        'group': custom_name,
                        'gender': gender
                    }
                    
                    # Add up to 60 participants per group
                    for i in range(1, 61):
                        if i <= len(gender_participants):
                            participant = gender_participants[i-1]
                            group_data[f'Name{i}'] = str(participant.get('Name', '')) if participant.get('Name') else ''
                            group_data[f'Image{i}'] = image_path
                            race_time = participant.get('RaceTime')
                            group_data[f'Time{i}'] = str(race_time) if race_time is not None else ''
                            group_data[f'StartaNr{i}'] = f"{i}"
                            # Add dal_id as number
                            group_data[f'Number{i}'] = str(participant.get('dal_id', ''))
                        else:
                            group_data[f'Name{i}'] = ''
                            group_data[f'Image{i}'] = ''
                            group_data[f'Time{i}'] = ''
                            group_data[f'StartaNr{i}'] = ''
                            group_data[f'Number{i}'] = ''
                    
                    result.append(group_data)

        try:
            os.makedirs(self.output_dir, exist_ok=True)
            filepath = os.path.join(self.output_dir, "summary_results.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({"teams": result}, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error in save/verify process: {str(e)}")

    def fetch_and_process(self):
        """Single fetch and process operation"""
        try:
            print("Fetching summary results...")  # Debug print
            all_data = self.fetch_data()
            
            if all_data:
                self.process_data(all_data)
                self.logger.info("Summary results updated successfully")
                print("Summary results updated successfully")
                return True
            else:
                print("No data received from API")
                return False
                
        except Exception as e:
            self.logger.error(f"Error fetching summary: {str(e)}")
            print(f"Error fetching summary: {str(e)}")
            return False 