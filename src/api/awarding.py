from .base import BaseAPIHandler
from typing import Dict, Any, List, Tuple
import requests
import logging
import os
import json

class AwardingAPI(BaseAPIHandler):
    BASE_URL = "https://www.stirnubuks.lv/api/"
    AWARDING_FILE = "awarding_results.json"  # Single file for all awarding results
    
    def __init__(self, posms: str, distances: List[str], auth_token: str, test_mode: bool = False, group_configs: Dict[str, Dict[str, Any]] = None, distance_configs: Dict[str, Dict[str, Any]] = None):
        super().__init__()
        self.posms = posms
        self.distances = distances
        self.AUTH_TOKEN = auth_token
        self.test_mode = test_mode
        self.group_configs = group_configs or {}
        self.distance_configs = distance_configs or {}  # Initialize distance_configs

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
        }
        
        # Only add posms if it's not empty
        if self.posms:
            params["posms"] = self.posms
        
        if self.test_mode:
            params["gads"] = "2024"
            
        try:
            print(f"\nFetching data for distance: {distance}")
            print(f"Request parameters: {params}")
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            # Check if the data is a list
            if isinstance(data, list):
                print(f"Received {len(data)} participants")
                course_classes = set(p.get('CourseClass', 'Unknown') for p in data)
                print(f"Found course classes: {', '.join(sorted(course_classes))}")
                for cc in course_classes:
                    count = len([p for p in data if p.get('CourseClass') == cc])
                    print(f"  {cc}: {count} participants")
                return distance, data
            else:
                print(f"Unexpected data format: {type(data)}")
                return distance, []

        except Exception as e:
            self.logger.error(f"Error fetching awarding data for distance {distance}: {str(e)}")
            print(f"Error in _fetch_single_distance: {str(e)}")
            return distance, []

    def _parse_course_class(self, course_class: str, participants: List[Dict[str, Any]]) -> Tuple[str, str]:
        if not course_class:
            # Check participant genders if course_class is unknown
            genders = [self._translate_gender(p.get('dzimums', '')) for p in participants[:3]]
            if len(set(genders)) == 1 and genders[0] in ['Vīrieši', 'Sievietes']:
                return ('Unknown', genders[0])
            return ('Unknown', 'Unknown')
        
        # Handle U-groups with gender suffix
        if course_class.startswith('U'):
            if course_class.endswith('V'):
                return (course_class[:-1], 'Vīrieši')
            elif course_class.endswith('S'):
                return (course_class[:-1], 'Sievietes')
        
        # Handle V and S groups
        if course_class.startswith('V'):
            return (course_class, 'Vīrieši')
        elif course_class.startswith('S'):
            return (course_class, 'Sievietes')
        
        # If course_class exists but pattern is unknown, check participant genders
        genders = [self._translate_gender(p.get('dzimums', '')) for p in participants[:3]]
        if len(set(genders)) == 1 and genders[0] in ['Vīrieši', 'Sievietes']:
            return (course_class, genders[0])
        
        return (course_class, 'Unknown')

    def process_data(self, all_data: Dict[str, List[Dict[str, Any]]]) -> None:
        """Process all fetched data into the required format"""
        if not all_data:
            self.logger.warning("No data to process")
            return

        result = {"teams": []}
        
        for distance, participants in all_data.items():
            if not participants:
                continue

            # Get distance configuration
            distance_config = self.distance_configs.get(distance, {
                'group_by': 'distance',
                'top_count': 3
            })
            group_by = distance_config['group_by']
            top_count = distance_config['top_count']

            print(f"\nProcessing {distance} with config: {distance_config}")

            if group_by == "distance":
                # First, group participants by gender
                gender_groups = self._group_by_gender(participants)
                
                # Process females first, then males
                gender_order = ['Sievietes', 'Vīrieši']
                for gender in gender_order:
                    if gender in gender_groups:
                        sorted_participants = self._sort_participants(gender_groups[gender])
                        # Use the same group key pattern as StartListAPI
                        group_key = f"{distance}_{gender}"
                        group_config = self.group_configs.get(group_key, {})
                        custom_name = group_config.get('name', group_key)  # Fixed: use group_key as default
                        print(f"Using group key: {group_key}, config: {group_config}, name: {custom_name}")  # Debug print
                        
                        result['teams'].append(self._create_group_data(
                            custom_name,  # Use custom name from group config
                            gender,  # Just use gender for course class in distance mode
                            gender,  # Use actual gender
                            sorted_participants,
                            top_count,
                            distance
                        ))

            elif group_by == "classgroups":
                # Group by CourseClass only
                class_groups = self._group_by_courseclass(participants)
                # Sort class groups to ensure consistent order
                sorted_class_groups = sorted(class_groups.items())
                
                for course_class, class_participants in sorted_class_groups:
                    sorted_participants = self._sort_participants(class_participants)
                    group, gender = self._parse_course_class(course_class, class_participants)
                    
                    # Use the same group key pattern as StartListAPI for the base distance
                    group_key = f"{distance}_{gender}"
                    group_config = self.group_configs.get(group_key, {})
                    custom_name = group_config.get('name', group_key)  # Fixed: use group_key as default
                    print(f"Using group key: {group_key}, config: {group_config}, name: {custom_name}")  # Debug print
                    
                    result['teams'].append(self._create_group_data(
                        custom_name,  # Use custom name from group config
                        f"{group} - {gender}",  # Combine group and gender for course class
                        group,  # Use group as gender field
                        sorted_participants,
                        top_count,
                        distance
                    ))

        try:
            os.makedirs(self.output_dir, exist_ok=True)
            filepath = os.path.join(self.output_dir, self.AWARDING_FILE)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error in save/verify process: {str(e)}")

    def _sort_participants(self, participants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort participants by position and race time"""
        return sorted(
            participants,
            key=lambda x: (
                float(x.get('Position', '999999')) if x.get('Position') and str(x.get('Position')).isdigit() else float('inf'),
                float(x.get('RaceTime', '999999')) if x.get('RaceTime') and x.get('RaceTime').replace('.','',1).isdigit() else float('inf')
            )
        )

    def _group_by_gender(self, participants: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group participants by gender"""
        groups = {}
        for participant in participants:
            gender = self._translate_gender(participant.get('dzimums', ''))
            if gender not in groups:
                groups[gender] = []
            groups[gender].append(participant)
        return groups

    def _group_by_courseclass(self, participants: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group participants by CourseClass"""
        groups = {}
        for participant in participants:
            course_class = participant.get('CourseClass', 'Unknown')
            if course_class not in groups:
                groups[course_class] = []
            groups[course_class].append(participant)
        return groups

    def _create_group_data(self, group_name: str, course_class: str, gender: str, participants: List[Dict[str, Any]], top_count: int, distance: str) -> Dict[str, Any]:
        """Create a group data entry with specified number of top participants"""
        group_key = f"{distance}_{course_class}"
        group_config = self.group_configs.get(group_key, {})
        custom_name = group_config.get('name', group_name)
        print(f"Creating group data for {custom_name} with gender {gender} and group name: {group_name}")

        group_data = {
            'group1': custom_name,
            'subgroup1': course_class
        }

        for i in range(1, top_count + 1):
            if i <= len(participants):
                participant = participants[i-1]
                group_data[f'name{i}'] = str(participant.get('Name', ''))
                group_data[f'image{i}'] = ''
                group_data[f'laiks{i}'] = str(participant.get('RaceTime', ''))
                group_data[f'number{i}'] = str(participant.get('dal_id', ''))
                group_data[f'club{i}'] = str(participant.get('Club', ''))
                group_data[f'position{i}'] = str(participant.get('Position', ''))
            else:
                group_data[f'name{i}'] = ''
                group_data[f'image{i}'] = ''
                group_data[f'laiks{i}'] = ''
                group_data[f'number{i}'] = ''
                group_data[f'club{i}'] = ''
                group_data[f'position{i}'] = ''

        return group_data
