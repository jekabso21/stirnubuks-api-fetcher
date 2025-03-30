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
    
    def __init__(self, posms: str, distances: List[str], auth_token: str, update_interval: int = 30, test_mode: bool = False, group_configs: Dict[str, Dict[str, Any]] = None):
        super().__init__()
        self.posms = posms
        self.distances = distances
        self.AUTH_TOKEN = auth_token
        self.update_interval = update_interval
        self.test_mode = test_mode
        self.is_running = False
        self.thread = None
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
                group_key = str(f"{distance}_{gender}")
                group_config = self.group_configs.get(group_key, {})
                custom_name = group_config.get('name', group_key)
                image_path = group_config.get('image', '')
                
                # Create a single object for all participants in this distance+gender
                group_data = {
                    'group': custom_name,
                    'gender': gender
                }
                
                # Add up to 30 participants
                for i in range(1, 31):
                    if i <= len(gender_participants):
                        print(image_path)
                        participant = gender_participants[i-1]
                        group_data[f'name{i}'] = str(participant.get('Name', '')) if participant.get('Name') else ''
                        group_data[f'image{i}'] = image_path
                        race_time = participant.get('RaceTime')
                        group_data[f'points{i}'] = str(race_time) if race_time is not None else ''
                    else:
                        group_data[f'name{i}'] = ''
                        group_data[f'image{i}'] = ''  # Empty string for participant images
                        group_data[f'points{i}'] = ''
                
                result.append(group_data)

        try:
            os.makedirs(self.output_dir, exist_ok=True)
            filepath = os.path.join(self.output_dir, "summary_results.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({"teams": result}, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error in save/verify process: {str(e)}")

    def start_updates(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._update_loop)
            self.thread.daemon = True
            self.thread.start()

    def stop_updates(self):
        self.is_running = False
        if self.thread:
            self.thread.join()

    def _update_loop(self):
        while self.is_running:
            try:
                print("Updating summary results...")  # Debug print
                all_data = self.fetch_data()
                
                if all_data:
                    self.process_data(all_data)
                    self.logger.info("Summary results updated successfully")
                    print(f"Summary results updated in {self.SUMMARY_FILE}")  # Debug print
                else:
                    print("No data received from API")
                
                time.sleep(self.update_interval)
            except Exception as e:
                self.logger.error(f"Error in update loop: {str(e)}")
                print(f"Error in update loop: {str(e)}")
                time.sleep(5) 