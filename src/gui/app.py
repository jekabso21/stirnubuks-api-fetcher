import tkinter as tk
from tkinter import ttk
from api.startlist import StartListAPI
from api.summary import SummaryAPI
from api.awarding import AwardingAPI
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
        
        # Initialize distances_vars
        self.distances_vars = {key: tk.BooleanVar() for key in self.DISTANCES.keys()}
        
        self._create_widgets()
        
    def _create_widgets(self):
        # Main container
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)

        # Parameters Frame
        params_frame = ttk.LabelFrame(main_container, text="API Parameters", padding=10)
        params_frame.pack(fill="x", pady=5)
        
        # Auth Key Entry
        ttk.Label(params_frame, text="Auth Key:").grid(row=0, column=0, padx=5, pady=5)
        self.auth_key_var = tk.StringVar()
        self.auth_key_entry = ttk.Entry(params_frame, textvariable=self.auth_key_var, width=30)
        self.auth_key_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Posms Dropdown
        ttk.Label(params_frame, text="Posms:").grid(row=1, column=0, padx=5, pady=5)
        self.posms_var = tk.StringVar()
        self.posms_dropdown = ttk.Combobox(
            params_frame, 
            textvariable=self.posms_var, 
            values=list(self.POSMI.keys()), 
            state="readonly",
            width=30
        )
        self.posms_dropdown.grid(row=1, column=1, padx=5, pady=5)
        
        # Distances Checkboxes
        ttk.Label(params_frame, text="Distances:").grid(row=2, column=0, padx=5, pady=5)
        distances_frame = ttk.Frame(params_frame)
        distances_frame.grid(row=2, column=1, sticky='w')
        
        # Create checkboxes in two rows
        for index, (key, value) in enumerate(self.DISTANCES.items()):
            row = index // 5
            col = index % 5
            ttk.Checkbutton(
                distances_frame,
                text=f"{key} - {value}",
                variable=self.distances_vars[key]
            ).grid(row=row, column=col, padx=5, pady=2, sticky='w')

        # Update Interval
        ttk.Label(params_frame, text="Update Interval (sec):").grid(row=4, column=0, padx=5, pady=5)
        self.update_interval_var = tk.StringVar(value="30")
        ttk.Entry(params_frame, textvariable=self.update_interval_var, width=10).grid(row=4, column=1, sticky='w', padx=5, pady=5)

        # Test Mode Checkbox
        self.test_mode_var = tk.BooleanVar()
        ttk.Checkbutton(params_frame, text="Test Mode", variable=self.test_mode_var).grid(row=5, column=0, columnspan=2, pady=5)

        # Control Buttons Frame
        control_frame = ttk.LabelFrame(main_container, text="Controls", padding=10)
        control_frame.pack(fill="x", pady=5)

        # Start List Button
        self.startlist_button = ttk.Button(control_frame, text="Fetch Start List", command=self._fetch_data)
        self.startlist_button.pack(side=tk.LEFT, padx=5)

        # Summary Controls
        summary_frame = ttk.Frame(control_frame)
        summary_frame.pack(side=tk.LEFT, padx=20)
        
        self.summary_status_var = tk.StringVar(value="Summary: Stopped")
        ttk.Label(summary_frame, textvariable=self.summary_status_var).pack(side=tk.LEFT, padx=5)
        
        self.start_summary_button = ttk.Button(
            summary_frame, 
            text="Start Summary", 
            command=lambda: print("Start Summary clicked") or self._start_summary_updates()
        )
        self.start_summary_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_summary_button = ttk.Button(
            summary_frame, 
            text="Stop Summary", 
            command=lambda: print("Stop Summary clicked") or self._stop_summary_updates(),
            state=tk.DISABLED
        )
        self.stop_summary_button.pack(side=tk.LEFT, padx=5)

        # Awarding Button
        self.awarding_button = ttk.Button(
            control_frame, 
            text="Fetch Awarding", 
            command=lambda: print("Awarding clicked") or self._fetch_awarding_results()
        )
        self.awarding_button.pack(side=tk.LEFT, padx=5)

        # Status Label
        self.status_label = ttk.Label(main_container, text="")
        self.status_label.pack(fill="x", pady=5)
        
        # Results Display
        results_frame = ttk.LabelFrame(main_container, text="Results", padding=10)
        results_frame.pack(fill="both", expand=True)
        
        self.results_text = tk.Text(results_frame, wrap=tk.WORD)
        self.results_text.pack(fill="both", expand=True)

    def _fetch_data(self):
        # Get selected values
        posms = self.posms_var.get()
        auth_token = self.auth_key_var.get()
        
        # Get selected distances
        selected_distances = [key for key, var in self.distances_vars.items() if var.get()]
        if not posms or not selected_distances or not auth_token:
            self.status_label.config(text="Please select Posms, at least one Distance, and enter Auth Key", foreground="red")
            return
        
        # Reset results text
        self.results_text.delete(1.0, tk.END)
        
        # Create API instance with all selected distances
        api = StartListAPI(posms, selected_distances, auth_token, self.test_mode_var.get())
        
        try:
            # Fetch all data
            all_data = api.fetch_data()
            
            if all_data:
                # Process and save all data
                api.process_data(all_data)
                
                # Display results preview
                try:
                    output_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'output'))
                    filepath = os.path.join(output_dir, 'all_participants.json')
                    
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Show preview of data for each distance
                        for distance in selected_distances:
                            if distance in data:
                                self.results_text.insert(tk.END, f"\nDistance: {distance} - {self.DISTANCES[distance]}\n")
                                self.results_text.insert(tk.END, f"Participants: {len(data[distance])}\n")
                                if data[distance]:  # Show first participant as example
                                    self.results_text.insert(tk.END, "Example participant:\n")
                                    self.results_text.insert(tk.END, 
                                        json.dumps(data[distance][0], indent=2, ensure_ascii=False) + "\n")
                
                    self.status_label.config(
                        text=f"Data saved successfully in: {filepath}\n" + 
                             f"Posms: {self.POSMI.get(posms, posms)} | " + 
                             f"Total distances processed: {len(selected_distances)}",
                        foreground="green"
                    )
                except Exception as e:
                    self.results_text.insert(tk.END, f"Error reading saved file: {str(e)}\n")
            else:
                self.status_label.config(
                    text="No data could be fetched for the selected distances",
                    foreground="red"
                )
        except Exception as e:
            self.status_label.config(
                text=f"Error during data fetch: {str(e)}",
                foreground="red"
            )

    def _start_summary_updates(self):
        try:
            interval = int(self.update_interval_var.get())
            if interval < 5:
                raise ValueError("Update interval must be at least 5 seconds")

            posms = self.posms_var.get()
            auth_token = self.auth_key_var.get()
            selected_distances = [key for key, var in self.distances_vars.items() if var.get()]

            print(f"Starting summary updates with:")  # Debug print
            print(f"Posms: {posms}")  # Debug print
            print(f"Selected distances: {selected_distances}")  # Debug print
            print(f"Interval: {interval}")  # Debug print

            if not posms or not selected_distances or not auth_token:
                self.status_label.config(text="Please select Posms, at least one Distance, and enter Auth Key", foreground="red")
                return

            self.summary_api = SummaryAPI(
                posms=posms,
                distances=selected_distances,
                auth_token=auth_token,
                update_interval=interval,
                test_mode=self.test_mode_var.get()
            )
            
            print("Created SummaryAPI instance")  # Debug print
            self.summary_api.start_updates()
            print("Started updates")  # Debug print

            self.summary_status_var.set("Running")
            self.start_summary_button.config(state=tk.DISABLED)
            self.stop_summary_button.config(state=tk.NORMAL)
            self.status_label.config(text=f"Summary updates started - Updating {SummaryAPI.SUMMARY_FILE}", foreground="green")

        except ValueError as e:
            print(f"ValueError: {str(e)}")  # Debug print
            self.status_label.config(text=str(e), foreground="red")
        except Exception as e:
            print(f"Exception in _start_summary_updates: {str(e)}")  # Debug print
            self.status_label.config(text=f"Error starting summary updates: {str(e)}", foreground="red")

    def _stop_summary_updates(self):
        if hasattr(self, 'summary_api'):
            self.summary_api.stop_updates()
            self.summary_status_var.set("Stopped")
            self.start_summary_button.config(state=tk.NORMAL)
            self.stop_summary_button.config(state=tk.DISABLED)
            self.status_label.config(text="Summary updates stopped", foreground="green")

    def _fetch_awarding_results(self):
        try:
            posms = self.posms_var.get()
            auth_token = self.auth_key_var.get()
            selected_distances = [key for key, var in self.distances_vars.items() if var.get()]

            print(f"Fetching awarding results with:")
            print(f"Posms: {posms}")
            print(f"Selected distances: {selected_distances}")

            if not posms or not selected_distances or not auth_token:
                self.status_label.config(text="Please select Posms, at least one Distance, and enter Auth Key", foreground="red")
                return

            awarding_api = AwardingAPI(
                posms=posms,
                distances=selected_distances,
                auth_token=auth_token,
                test_mode=self.test_mode_var.get()
            )
            
            print("Created AwardingAPI instance")
            all_data = awarding_api.fetch_data()  # Use the new fetch_data method

            if all_data:
                print("Processing awarding data")
                awarding_api.process_data(all_data)
                self.status_label.config(text=f"Awarding results updated in {AwardingAPI.AWARDING_FILE}", foreground="green")
            else:
                print("No awarding data received")
                self.status_label.config(text="No awarding data could be fetched", foreground="red")

        except Exception as e:
            print(f"Exception in _fetch_awarding_results: {str(e)}")
            self.status_label.config(text=f"Error fetching awarding results: {str(e)}", foreground="red")