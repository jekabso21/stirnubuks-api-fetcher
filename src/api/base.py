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
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Successfully saved data to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving JSON file {filename}: {str(e)}") 