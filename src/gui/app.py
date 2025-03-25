import tkinter as tk
from tkinter import ttk
from api.startlist import StartListAPI
import os
import json

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("API Fetcher")
        self.root.geometry("800x600")
        
        self._create_widgets()
        
    def _create_widgets(self):
        # Parameters Frame
        params_frame = ttk.LabelFrame(self.root, text="API Parameters", padding=10)
        params_frame.pack(fill="x", padx=10, pady=5)
        
        # Posms Entry
        ttk.Label(params_frame, text="Posms:").grid(row=0, column=0, padx=5, pady=5)
        self.posms_entry = ttk.Entry(params_frame)
        self.posms_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Distance Entry
        ttk.Label(params_frame, text="Distance:").grid(row=1, column=0, padx=5, pady=5)
        self.distance_entry = ttk.Entry(params_frame)
        self.distance_entry.grid(row=1, column=1, padx=5, pady=5)
        
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
        posms = self.posms_entry.get()
        distance = self.distance_entry.get()
        test_mode = self.test_mode_var.get()
        
        if not posms or not distance:
            self.status_label.config(text="Please fill in both Posms and Distance fields", foreground="red")
            return
        
        api = StartListAPI(posms, distance, test_mode)
        data = api.fetch_data()
        api.process_data(data)
        
        # Update status and display results
        output_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'output'))
        self.status_label.config(
            text=f"Data saved successfully in: {output_dir}",
            foreground="green"
        )
        
        # Display preview of saved files
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Saved files preview:\n\n")
        
        try:
            # Read and display teams_startlist.json
            with open(os.path.join(output_dir, 'teams_startlist.json'), 'r', encoding='utf-8') as f:
                teams_data = json.load(f)
                self.results_text.insert(tk.END, "teams_startlist.json:\n")
                self.results_text.insert(tk.END, json.dumps(teams_data, indent=2, ensure_ascii=False)[:500] + "...\n\n")
            
            # Read and display subteams_startlist.json
            with open(os.path.join(output_dir, 'subteams_startlist.json'), 'r', encoding='utf-8') as f:
                subteams_data = json.load(f)
                self.results_text.insert(tk.END, "subteams_startlist.json:\n")
                self.results_text.insert(tk.END, json.dumps(subteams_data, indent=2, ensure_ascii=False)[:500] + "...")
        except Exception as e:
            self.results_text.insert(tk.END, f"Error reading saved files: {str(e)}") 