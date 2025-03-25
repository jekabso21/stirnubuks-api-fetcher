import tkinter as tk
from tkinter import ttk
from api.startlist import StartListAPI
import os
import json

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Stirnu Buks API Fetcher")
        self.root.geometry("1000x700")
        
        # Define available posmi and distances
        self.POSMI = {
            'veveri': 'Veveri',
            'piejuras': 'Piejuras',
            'sveikuli': 'Sveikuli',
            'smeceres': 'Smeceres'
        }
        
        self.DISTANCES = {
            'vavere': 'Vāvere',
            'zakis': 'Zaķis',
            'susurs': 'Susurs',
            'pzakis': 'Zaķis (pārgājiens)',
            'vilks': 'Vilks',
            'pvavere': 'Vāvere (pārgājiens)',
            'buks': 'Stirnu buks',
            'pbuks': 'Stirnu buks (pārgājiens)',
            'skola': 'Skolu čempionāts'
        }
        
        self._create_widgets()
        
    def _create_widgets(self):
        # Parameters Frame
        params_frame = ttk.LabelFrame(self.root, text="API Parameters", padding=10)
        params_frame.pack(fill="x", padx=10, pady=5)
        
        # Posms Dropdown
        ttk.Label(params_frame, text="Posms:").grid(row=0, column=0, padx=5, pady=5)
        self.posms_var = tk.StringVar()
        self.posms_dropdown = ttk.Combobox(
            params_frame, 
            textvariable=self.posms_var, 
            values=list(self.POSMI.keys()), 
            state="readonly",
            width=30
        )
        self.posms_dropdown.grid(row=0, column=1, padx=5, pady=5)
        
        # Distances Listbox (Multi-select)
        ttk.Label(params_frame, text="Distances:").grid(row=1, column=0, padx=5, pady=5)
        self.distances_frame = ttk.Frame(params_frame)
        self.distances_frame.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        
        self.distances_listbox = tk.Listbox(
            self.distances_frame, 
            selectmode=tk.MULTIPLE, 
            exportselection=0,
            width=40, 
            height=5
        )
        for distance_key in self.DISTANCES.keys():
            self.distances_listbox.insert(tk.END, f"{distance_key} - {self.DISTANCES[distance_key]}")
        
        self.distances_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Scrollbar for Distances Listbox
        distances_scrollbar = ttk.Scrollbar(
            self.distances_frame, 
            orient=tk.VERTICAL, 
            command=self.distances_listbox.yview
        )
        distances_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.distances_listbox.config(yscrollcommand=distances_scrollbar.set)
        
        # Test Mode Checkbox
        self.test_mode_var = tk.BooleanVar()
        ttk.Checkbutton(params_frame, text="Test Mode", variable=self.test_mode_var).grid(row=2, column=0, columnspan=2, pady=5)
        
        # Fetch Button
        ttk.Button(params_frame, text="Fetch Data", command=self._fetch_data).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Status Label
        self.status_label = ttk.Label(params_frame, text="")
        self.status_label.grid(row=4, column=0, columnspan=2, pady=5)
        
        # Results Display
        results_frame = ttk.LabelFrame(self.root, text="Results", padding=10)
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.results_text = tk.Text(results_frame, wrap=tk.WORD)
        self.results_text.pack(fill="both", expand=True)
        
    def _fetch_data(self):
        # Get selected values
        posms = self.posms_var.get()
        
        # Get selected distances
        selected_indices = self.distances_listbox.curselection()
        if not posms or not selected_indices:
            self.status_label.config(text="Please select Posms and at least one Distance", foreground="red")
            return
        
        # Reset results text
        self.results_text.delete(1.0, tk.END)
        
        # Fetch data for each selected distance
        output_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'output'))
        test_mode = self.test_mode_var.get()
        
        # Store results for status and display
        processed_distances = []
        
        for index in selected_indices:
            # Extract distance from listbox (format: "key - full name")
            full_distance_text = self.distances_listbox.get(index)
            distance_key = full_distance_text.split(' - ')[0]
            
            # Create API instance and fetch data
            api = StartListAPI(posms, distance_key, test_mode)
            data = api.fetch_data()
            
            if data:
                api.process_data(data)
                processed_distances.append(full_distance_text)
                
                # Add to results text
                try:
                    # Read and display teams_startlist.json
                    with open(os.path.join(output_dir, 'teams_startlist.json'), 'r', encoding='utf-8') as f:
                        teams_data = json.load(f)
                        self.results_text.insert(tk.END, f"Teams for {full_distance_text}:\n")
                        self.results_text.insert(tk.END, json.dumps(teams_data, indent=2, ensure_ascii=False)[:500] + "...\n\n")
                    
                    # Read and display subteams_startlist.json
                    with open(os.path.join(output_dir, 'subteams_startlist.json'), 'r', encoding='utf-8') as f:
                        subteams_data = json.load(f)
                        self.results_text.insert(tk.END, f"Subteams for {full_distance_text}:\n")
                        self.results_text.insert(tk.END, json.dumps(subteams_data, indent=2, ensure_ascii=False)[:500] + "...\n\n")
                except Exception as e:
                    self.results_text.insert(tk.END, f"Error reading saved files for {full_distance_text}: {str(e)}\n\n")
        
        # Update status
        if processed_distances:
            self.status_label.config(
                text=f"Data saved successfully in: {output_dir}\n" + 
                     f"Posms: {self.POSMI.get(posms, posms)} | " + 
                     f"Distances: {', '.join(processed_distances)}",
                foreground="green"
            )
        else:
            self.status_label.config(
                text="No data could be fetched for the selected distances",
                foreground="red"
            )