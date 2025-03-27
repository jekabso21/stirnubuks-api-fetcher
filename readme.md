# Stirnu Buks API Client

This application fetches and processes data from the Stirnu Buks API, including start lists, summary results, and awarding data.

## Setup Instructions

### 1. Python Virtual Environment

First, create and activate a virtual environment:

#### Windows
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate
```

#### macOS/Linux
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate
```

### 2. Install Dependencies

With the virtual environment activated, install the required packages:
```bash
pip install -r requirements.txt
```

### 3. Running the Application

Start the application by running:
```bash
python src/main.py
```

## Usage

1. Enter your API authentication key in the "Auth Key" field
2. Select the "Posms" (event) from the dropdown
3. Select one or more distances using the checkboxes
4. Set the update interval (in seconds) for summary results
5. Choose operations:
   - "Fetch Start List": Get the start list data
   - "Start Summary": Begin fetching live summary results
   - "Stop Summary": Stop fetching live summary results
   - "Fetch Awarding": Get the awarding results

### Test Mode

If you want to test the application with 2024 data:
1. Check the "Test Mode" checkbox before fetching data
2. This will use the 2024 dataset for testing purposes

## Output Files

The application saves JSON files in the `output` directory (created automatically in the project root):

- `teams_startlist.json`: Start list data grouped by teams
- `subteams_startlist.json`: Start list data grouped by subteams
- `summary_results.json`: Live summary results
- `awarding_results.json`: Awarding results

## File Structure

## Important Notes

- The minimum update interval for summary results is 5 seconds
- All output files are saved in UTF-8 encoding
- Make sure you have a valid authentication key before using the application
- The application requires an active internet connection to fetch data from the API

## Troubleshooting

If you encounter any issues:
1. Ensure your authentication key is valid
2. Check your internet connection
3. Verify that you have selected at least one distance
4. Make sure the selected "Posms" is valid for the current season

For testing purposes, enable "Test Mode" to use 2024 data, which is guaranteed to be available.