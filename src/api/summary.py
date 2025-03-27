from .base import BaseAPIHandler
from typing import Dict, Any, List, Tuple
import requests
import logging
from datetime import datetime
import time
import threading

class SummaryAPI(BaseAPIHandler):  # Renamed from LiveResultsAPI to SummaryAPI
    BASE_URL = "https://www.stirnubuks.lv/api/"
    
    def __init__(self, posms: str, distances: List[str], auth_token: str, update_interval: int = 30, test_mode: bool = False):
        super().__init__()
        self.posms = posms
        self.distances = distances
        self.AUTH_TOKEN = auth_token
        self.update_interval = update_interval
        self.test_mode = test_mode
        self.is_running = False
        self.thread = None

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
        if not all_data:
            self.logger.warning("No data to process")
            return

        processed_data = {}
        
        for distance, participants in all_data.items():
            processed_data[distance] = []
            
            for participant in participants:
                processed_participant = {
                    'ImagePath1': "",
                    'Gender1': self._translate_gender(participant.get('dzimums', '')),
                    'Number1': participant.get('dal_id', ''),
                    'Name1': participant.get('Name', ''),
                    'Time1': participant.get('RaceTime', '')
                }
                processed_data[distance].append(processed_participant)

        # Save to JSON file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"summary_results_{timestamp}.json"
        self.save_json(processed_data, filename)
        
        # Also save to a fixed filename for latest results
        self.save_json(processed_data, "latest_summary_results.json")

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