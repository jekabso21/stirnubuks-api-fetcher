from .base import BaseAPIHandler
from typing import Dict, Any, List, Tuple
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import json

class StartListAPI(BaseAPIHandler):
    BASE_URL = "https://www.stirnubuks.lv/api/"
    
    def __init__(self, posms: str, distances: List[str], auth_token: str, test_mode: bool = False):
        super().__init__()
        self.posms = posms
        self.distances = distances  # Now accepts a list of distances
        self.AUTH_TOKEN = auth_token
        self.test_mode = test_mode
        
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

        processed_data = {}
        
        # Process each distance's data
        for distance, participants in all_data.items():
            processed_data[distance] = []
            
            # Process each participant
            for participant in participants:
                # Get punkti value directly without any conversion
                punkti = participant.get('punkti', '')
                
                # Create participant data structure
                processed_participant = {
                    'image': "",  # Empty for now as specified
                    'gender': self._translate_gender(participant.get('dzimums', '')),
                    'number1': str(participant.get('dal_id', '')),
                    'Name1': participant.get('full_name', ''),
                    'subgroup': participant.get('grupa', ''),
                    'Number2': punkti  # Use punkti value directly without any modification
                }
                
                # Debug print before adding to list
                print(f"Final participant structure: {processed_participant}")
                
                processed_data[distance].append(processed_participant)

        # Debug print final structure before saving
        print(f"\nFinal data structure sample:")
        for distance in processed_data:
            print(f"{distance}: {processed_data[distance][:1]}")
        
        # Save all data to a single JSON file
        try:
            self.save_json(processed_data, "all_participants.json")
            
            # Verify saved data
            filepath = os.path.join(self.output_dir, "all_participants.json")
            with open(filepath, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                print("\nVerification of saved data:")
                for distance in saved_data:
                    if saved_data[distance]:
                        print(f"{distance} first entry Number2: {saved_data[distance][0]['Number2']}")
        except Exception as e:
            self.logger.error(f"Error in save/verify process: {str(e)}")