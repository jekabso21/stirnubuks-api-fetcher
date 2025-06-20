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
            "limit": 100  # Increase the limit to get more participants
        }
        
        # Only add posms if it's not empty
        if self.posms:
            params["posms"] = self.posms
        
        if self.test_mode:
            params["gads"] = "2024"
            
        # Print API request details
        print(f"\nAPI Request for distance {distance}:")
        print(f"URL: {self.BASE_URL}")
        print(f"Parameters: {params}")
            
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
        total_participants = 0
        
        # Sort distances to ensure consistent order
        sorted_distances = sorted(all_data.keys())
        
        # Process each distance's data
        for distance in sorted_distances:
            participants = all_data[distance]
            print(f"\nProcessing distance {distance}:")
            print(f"Total participants recovered: {len(participants)}")
            
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
                    print(f"{gender} participants: {len(gender_participants)}")
                    total_participants += len(gender_participants)
                    
                    # Get custom group name and image link from config if available
                    group_key = str(f"{distance}_{gender}")
                    group_config = self.group_configs.get(group_key, {})
                    custom_name = group_config.get('name', group_key)
                    image_path = group_config.get('image', '')
                    
                    # Create a single object for all participants in this distance+gender
                    group_data = {
                        'Group1': custom_name,
                        'Gender1': gender
                    }
                    
                    # Add up to 60 participants per group
                    for i in range(1, 61):
                        if i <= len(gender_participants):
                            participant = gender_participants[i-1]
                            group_data[f'Name{i}'] = str(participant.get('full_name', ''))
                            group_data[f'Image{i}'] = image_path
                            group_data[f'Number{i}'] = str(participant.get('dal_id', ''))
                            group_data[f'Subgroup{i}'] = str(participant.get('grupa', ''))
                            # Add sequential start number with dot
                            group_data[f'StartaNr{i}'] = f"{i}"
                        else:
                            # Fill empty slots if we don't have enough participants
                            group_data[f'Name{i}'] = ''
                            group_data[f'Image{i}'] = ''
                            group_data[f'Number{i}'] = ''
                            group_data[f'Subgroup{i}'] = ''
                            group_data[f'StartaNr{i}'] = ''
                    
                    result.append(group_data)

        print(f"\nTotal participants processed and saved to JSON: {total_participants}")
        
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            filepath = os.path.join(self.output_dir, "all_participants.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({"teams": result}, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error in save/verify process: {str(e)}")