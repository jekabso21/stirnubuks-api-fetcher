from .base import BaseAPIHandler
from typing import Dict, Any, List, Tuple
import requests
import logging

class AwardingAPI(BaseAPIHandler):
    BASE_URL = "https://www.stirnubuks.lv/api/"
    AWARDING_FILE = "awarding_results.json"  # Single file for all awarding results
    
    def __init__(self, posms: str, distances: List[str], auth_token: str, test_mode: bool = False):
        super().__init__()
        self.posms = posms
        self.distances = distances
        self.AUTH_TOKEN = auth_token
        self.test_mode = test_mode

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
        if not all_data:
            self.logger.warning("No data to process")
            return

        processed_data = {}
        
        for distance, participants in all_data.items():
            # Group by CourseClass first
            course_classes = {}
            for participant in participants:
                course_class = participant.get('CourseClass', 'Unknown')
                gender = participant.get('dzimums', 'Unknown')
                
                if course_class not in course_classes:
                    course_classes[course_class] = {'S': [], 'V': []}
                
                processed_participant = {
                    'ImagePath1': "",
                    'Gender1': self._translate_gender(gender),
                    'Number1': participant.get('dal_id', ''),
                    'Name1': participant.get('Name', ''),
                    'Time1': participant.get('RaceTime', ''),
                    'Position': participant.get('Position', ''),
                    'Club': participant.get('Club', '')
                }
                
                course_classes[course_class][gender].append(processed_participant)
            
            processed_data[distance] = course_classes

        # Save to single JSON file
        self.save_json(processed_data, self.AWARDING_FILE) 