import os
from abc import ABC, abstractmethod
import requests
import json
import logging
from typing import Dict, Any

class BaseAPIHandler(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        # Ensure output directory exists
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'output')
        os.makedirs(self.output_dir, exist_ok=True)
        
    @abstractmethod
    def fetch_data(self) -> Dict[str, Any]:
        """Fetch data from the API"""
        pass
    
    @abstractmethod
    def process_data(self, data: Dict[str, Any]) -> None:
        """Process the fetched data"""
        pass
    
    def save_json(self, data: Dict[str, Any], filename: str) -> None:
        """Save data to a JSON file in the output directory"""
        try:
            filepath = os.path.join(self.output_dir, filename)
            
            # Debug print before JSON conversion
            first_distance = next(iter(data))
            print(f"\nBefore JSON conversion:")
            print(f"Sample data: {data[first_distance][:2]}")
            
            # Convert to JSON string first to check the conversion
            json_string = json.dumps(data, indent=4, ensure_ascii=False)
            
            # Debug print after JSON conversion
            print(f"\nAfter JSON conversion (before saving):")
            print(f"Sample from JSON string: {json_string[:500]}")
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_string)
            
            # Verify saved data
            with open(filepath, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                print(f"\nAfter reading saved file:")
                print(f"Sample from saved file: {saved_data[first_distance][:2]}")
                
            self.logger.info(f"Successfully saved data to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving JSON file {filename}: {str(e)}") 