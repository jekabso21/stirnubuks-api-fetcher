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
            'skola': 'Skolu čempionāts',
            'lusis': 'Lusis'
        }
        
        # Initialize distances_vars
        self.distances_vars = {key: tk.BooleanVar() for key in self.DISTANCES.keys()}
        
        # Initialize group configs and active distance configs
        self.group_configs = {}
        self.active_distance_configs = {}  # Initialize active_distance_configs
        
        # Create presets directory if it doesn't exist
        self.presets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'presets')
        os.makedirs(self.presets_dir, exist_ok=True)
        
        self._create_widgets()
        
    def _create_widgets(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Main tab
        main_tab = ttk.Frame(self.notebook)
        self.notebook.add(main_tab, text="Main")

        # Group Config tab
        config_tab = ttk.Frame(self.notebook)
        self.notebook.add(config_tab, text="Group Config")

        # Main container for main tab
        main_container = ttk.Frame(main_tab, padding="10")
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

        # All Settings Frame
        all_settings_frame = ttk.LabelFrame(main_container, text="Save/Load All Settings", padding=10)
        all_settings_frame.pack(fill="x", pady=5)

        # Settings name entry
        ttk.Label(all_settings_frame, text="Settings Name:").pack(side=tk.LEFT, padx=5)
        self.all_settings_name_var = tk.StringVar()
        ttk.Entry(all_settings_frame, textvariable=self.all_settings_name_var, width=20).pack(side=tk.LEFT, padx=5)

        # Save/Load buttons
        ttk.Button(all_settings_frame, text="Save All Settings", command=self._save_all_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(all_settings_frame, text="Load Settings", command=self._load_all_settings).pack(side=tk.LEFT, padx=5)

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

        # Group Config tab content
        config_container = ttk.Frame(config_tab, padding="10")
        config_container.pack(fill=tk.BOTH, expand=True)

        # Preset controls frame
        preset_frame = ttk.LabelFrame(config_container, text="Preset Controls", padding=10)
        preset_frame.pack(fill="x", pady=5)

        # Preset name entry
        ttk.Label(preset_frame, text="Preset Name:").pack(side=tk.LEFT, padx=5)
        self.preset_name_var = tk.StringVar()
        ttk.Entry(preset_frame, textvariable=self.preset_name_var, width=20).pack(side=tk.LEFT, padx=5)

        # Preset buttons
        ttk.Button(preset_frame, text="Save Preset", command=self._save_preset).pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_frame, text="Load Preset", command=self._load_preset).pack(side=tk.LEFT, padx=5)

        # Group configurations frame
        group_frame = ttk.LabelFrame(config_container, text="Group Configurations", padding=10)
        group_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Create scrollable frame for group configs
        canvas = tk.Canvas(group_frame)
        scrollbar = ttk.Scrollbar(group_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Store group config entries
        self.group_config_entries = {}

        # Create entries for each possible group
        row = 0
        for distance in self.DISTANCES:
            for gender in ['Vīrieši', 'Sievietes']:
                group_key = f"{distance}_{gender}"
                group_frame = ttk.LabelFrame(scrollable_frame, text=f"{self.DISTANCES[distance]} - {gender}", padding=5)
                group_frame.pack(fill="x", pady=2)

                # Group name entry
                ttk.Label(group_frame, text="Group Name:").grid(row=0, column=0, padx=5, pady=2)
                name_var = tk.StringVar(value=group_key)
                name_entry = ttk.Entry(group_frame, textvariable=name_var, width=30)
                name_entry.grid(row=0, column=1, padx=5, pady=2)

                # Image selection frame
                image_frame = ttk.Frame(group_frame)
                image_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=2)
                
                ttk.Label(image_frame, text="Image:").pack(side=tk.LEFT)
                image_var = tk.StringVar()
                image_entry = ttk.Entry(image_frame, textvariable=image_var, width=30)
                image_entry.pack(side=tk.LEFT, padx=5)
                
                # Add radio buttons for image type
                image_type_var = tk.StringVar(value="web")
                ttk.Radiobutton(image_frame, text="Web Link", variable=image_type_var, value="web").pack(side=tk.LEFT)
                ttk.Radiobutton(image_frame, text="Local File", variable=image_type_var, value="local").pack(side=tk.LEFT)
                
                # Browse button
                ttk.Button(
                    image_frame, 
                    text="Browse", 
                    command=lambda var=image_var, type_var=image_type_var: self._browse_image(var, type_var)
                ).pack(side=tk.LEFT)

                self.group_config_entries[group_key] = {
                    'name': name_var,
                    'image': image_var,
                    'image_type': image_type_var
                }
                row += 1

        # Save button
        save_button = ttk.Button(config_container, text="Save Configurations", command=self._save_group_configs)
        save_button.pack(pady=10)

        # Add Distance Configuration tab
        distance_config_tab = ttk.Frame(self.notebook)
        self.notebook.add(distance_config_tab, text="Distance Config")

        # Distance configuration container
        config_container = ttk.Frame(distance_config_tab, padding="10")
        config_container.pack(fill=tk.BOTH, expand=True)

        # Create scrollable frame for configurations
        canvas = tk.Canvas(config_container)
        scrollbar = ttk.Scrollbar(config_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Store distance config entries
        self.distance_configs = {}

        # Create configuration for each distance
        for distance in self.DISTANCES:
            frame = ttk.LabelFrame(scrollable_frame, text=f"{self.DISTANCES[distance]}", padding=5)
            frame.pack(fill="x", pady=5, padx=5)

            # Grouping method
            ttk.Label(frame, text="Group By:").grid(row=0, column=0, padx=5, pady=2)
            group_var = tk.StringVar(value="distance")
            group_combo = ttk.Combobox(
                frame, 
                textvariable=group_var,
                values=["distance", "classgroups"],
                state="readonly",
                width=20
            )
            group_combo.grid(row=0, column=1, padx=5, pady=2)

            # Top players count
            ttk.Label(frame, text="Top Players:").grid(row=1, column=0, padx=5, pady=2)
            top_count_var = tk.StringVar(value="3")
            top_count_entry = ttk.Entry(frame, textvariable=top_count_var, width=5)
            top_count_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)

            # Store the configuration variables
            self.distance_configs[distance] = {
                'group_by': group_var,
                'top_count': top_count_var
            }

        # Save button
        save_button = ttk.Button(
            config_container, 
            text="Save Distance Configurations", 
            command=self._save_distance_configs
        )
        save_button.pack(pady=10)

        # Preset controls for distance configs
        preset_frame = ttk.LabelFrame(config_container, text="Distance Config Presets", padding=5)
        preset_frame.pack(fill="x", pady=5)

        ttk.Label(preset_frame, text="Preset Name:").pack(side=tk.LEFT, padx=5)
        self.distance_preset_name = tk.StringVar()
        ttk.Entry(preset_frame, textvariable=self.distance_preset_name, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_frame, text="Save Preset", command=self._save_distance_preset).pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_frame, text="Load Preset", command=self._load_distance_preset).pack(side=tk.LEFT, padx=5)

    def _browse_image(self, image_var, type_var):
        """Open file dialog to select an image file or handle web link"""
        if type_var.get() == "local":
            from tkinter import filedialog
            filetypes = (
                ('Image files', '*.png;*.jpg;*.jpeg;*.gif;*.bmp'),
                ('All files', '*.*')
            )
            filename = filedialog.askopenfilename(
                title='Select an image',
                filetypes=filetypes
            )
            if filename:
                image_var.set(filename)
        else:
            # For web links, just let the user type in the entry field
            pass

    def _save_preset(self):
        """Save current configurations as a preset"""
        preset_name = self.preset_name_var.get().strip()
        if not preset_name:
            self.status_label.config(text="Please enter a preset name", foreground="red")
            return

        preset_data = {}
        for group_key, entries in self.group_config_entries.items():
            if entries['name'].get() or entries['image'].get():
                preset_data[group_key] = {
                    'name': entries['name'].get(),
                    'image': entries['image'].get()
                }

        if not preset_data:
            self.status_label.config(text="No configurations to save", foreground="red")
            return

        try:
            preset_file = os.path.join(self.presets_dir, f"{preset_name}.json")
            with open(preset_file, 'w', encoding='utf-8') as f:
                json.dump(preset_data, f, ensure_ascii=False, indent=2)
            self.status_label.config(text=f"Preset '{preset_name}' saved successfully", foreground="green")
        except Exception as e:
            self.status_label.config(text=f"Error saving preset: {str(e)}", foreground="red")

    def _load_preset(self):
        """Load configurations from a preset"""
        from tkinter import filedialog
        preset_file = filedialog.askopenfilename(
            title='Select a preset file',
            initialdir=self.presets_dir,
            filetypes=[('JSON files', '*.json')]
        )
        
        if not preset_file:
            return

        try:
            with open(preset_file, 'r', encoding='utf-8') as f:
                preset_data = json.load(f)
            
            # Update entries with preset data
            for group_key, data in preset_data.items():
                if group_key in self.group_config_entries:
                    self.group_config_entries[group_key]['name'].set(data.get('name', ''))
                    self.group_config_entries[group_key]['image'].set(data.get('image', ''))
            
            self.status_label.config(text=f"Preset loaded successfully", foreground="green")
        except Exception as e:
            self.status_label.config(text=f"Error loading preset: {str(e)}", foreground="red")

    def _save_group_configs(self):
        """Save group configurations and update the API"""
        group_configs = {}
        for group_key, entries in self.group_config_entries.items():
            if entries['name'].get() or entries['image'].get():
                group_configs[group_key] = {
                    'name': entries['name'].get(),
                    'image': entries['image'].get()
                }
        
        # Store the configurations and update all APIs
        self.group_configs = group_configs
        
        # If summary API is running, update its configs
        if hasattr(self, 'summary_api') and self.summary_api:
            self.summary_api.group_configs = group_configs
        
        self.status_label.config(text="Group configurations saved", foreground="green")

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
        
        # Create API instance with all selected distances and group configs
        api = StartListAPI(
            posms, 
            selected_distances, 
            auth_token, 
            self.test_mode_var.get(),
            self.group_configs
        )
        
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

            if not posms or not selected_distances or not auth_token:
                self.status_label.config(text="Please select Posms, at least one Distance, and enter Auth Key", foreground="red")
                return

            self.summary_api = SummaryAPI(
                posms=posms,
                distances=selected_distances,
                auth_token=auth_token,
                update_interval=interval,
                test_mode=self.test_mode_var.get(),
                group_configs=self.group_configs
            )
            
            self.summary_api.start_updates()
            self.summary_status_var.set("Running")
            self.start_summary_button.config(state=tk.DISABLED)
            self.stop_summary_button.config(state=tk.NORMAL)
            self.status_label.config(text=f"Summary updates started - Updating summary_results.json", foreground="green")

        except ValueError as e:
            self.status_label.config(text=str(e), foreground="red")
        except Exception as e:
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

            if not posms or not selected_distances or not auth_token:
                self.status_label.config(text="Please select Posms, at least one Distance, and enter Auth Key", foreground="red")
                return

            awarding_api = AwardingAPI(
                posms=posms,
                distances=selected_distances,
                auth_token=auth_token,
                test_mode=self.test_mode_var.get(),
                group_configs=self.group_configs,
                distance_configs=self.active_distance_configs
            )
            
            all_data = awarding_api.fetch_data()

            if all_data:
                awarding_api.process_data(all_data)
                self.status_label.config(text=f"Awarding results updated in awarding_results.json", foreground="green")
            else:
                self.status_label.config(text="No awarding data could be fetched", foreground="red")

        except Exception as e:
            self.status_label.config(text=f"Error fetching awarding results: {str(e)}", foreground="red")

    def _save_distance_configs(self):
        """Save distance configurations"""
        configs = {}
        for distance, vars in self.distance_configs.items():
            try:
                top_count = int(vars['top_count'].get())
                if top_count < 1:
                    raise ValueError
            except ValueError:
                self.status_label.config(
                    text=f"Invalid top count for {self.DISTANCES[distance]}", 
                    foreground="red"
                )
                return

            configs[distance] = {
                'group_by': vars['group_by'].get(),
                'top_count': top_count,
                'name': self.DISTANCES[distance]  # Add the distance name from DISTANCES dictionary
            }
        
        self.active_distance_configs = configs  # Update active_distance_configs
        self.status_label.config(text="Distance configurations saved", foreground="green")

    def _save_distance_preset(self):
        """Save current distance configurations as a preset"""
        name = self.distance_preset_name.get().strip()
        if not name:
            self.status_label.config(text="Please enter a preset name", foreground="red")
            return

        configs = {}
        for distance, vars in self.distance_configs.items():
            configs[distance] = {
                'group_by': vars['group_by'].get(),
                'top_count': vars['top_count'].get()
            }

        try:
            preset_file = os.path.join(self.presets_dir, f"distance_config_{name}.json")
            with open(preset_file, 'w', encoding='utf-8') as f:
                json.dump(configs, f, ensure_ascii=False, indent=2)
            self.status_label.config(text=f"Distance config preset '{name}' saved", foreground="green")
        except Exception as e:
            self.status_label.config(text=f"Error saving preset: {str(e)}", foreground="red")

    def _load_distance_preset(self):
        """Load distance configurations from a preset"""
        from tkinter import filedialog
        preset_file = filedialog.askopenfilename(
            title='Select a distance config preset',
            initialdir=self.presets_dir,
            filetypes=[('JSON files', '*.json')]
        )
        
        if not preset_file:
            return

        try:
            with open(preset_file, 'r', encoding='utf-8') as f:
                configs = json.load(f)
            
            for distance, config in configs.items():
                if distance in self.distance_configs:
                    self.distance_configs[distance]['group_by'].set(config['group_by'])
                    self.distance_configs[distance]['top_count'].set(str(config['top_count']))
            
            self.status_label.config(text="Distance config preset loaded", foreground="green")
        except Exception as e:
            self.status_label.config(text=f"Error loading preset: {str(e)}", foreground="red")

    def _save_all_settings(self):
        """Save all current settings including selections, configs, and parameters"""
        try:
            # Get all current settings
            settings = {
                'posms': self.posms_var.get(),
                'auth_key': self.auth_key_var.get(),
                'test_mode': self.test_mode_var.get(),
                'update_interval': self.update_interval_var.get(),
                'selected_distances': {
                    distance: var.get() 
                    for distance, var in self.distances_vars.items()
                },
                'group_configs': self.group_configs,
                'distance_configs': self.active_distance_configs
            }

            # Get settings name
            name = self.all_settings_name_var.get().strip()
            if not name:
                self.status_label.config(text="Please enter a name for the settings", foreground="red")
                return

            # Save to file
            settings_file = os.path.join(self.presets_dir, f"all_settings_{name}.json")
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            self.status_label.config(text=f"All settings saved as '{name}'", foreground="green")
        except Exception as e:
            self.status_label.config(text=f"Error saving settings: {str(e)}", foreground="red")

    def _load_all_settings(self):
        """Load all settings from a saved file"""
        from tkinter import filedialog
        
        settings_file = filedialog.askopenfilename(
            title='Select settings file',
            initialdir=self.presets_dir,
            filetypes=[('JSON files', '*.json')]
        )
        
        if not settings_file:
            return

        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            # Apply loaded settings
            self.posms_var.set(settings.get('posms', ''))
            self.auth_key_var.set(settings.get('auth_key', ''))
            self.test_mode_var.set(settings.get('test_mode', False))
            self.update_interval_var.set(settings.get('update_interval', '30'))

            # Set selected distances
            for distance, selected in settings.get('selected_distances', {}).items():
                if distance in self.distances_vars:
                    self.distances_vars[distance].set(selected)

            # Set group configs
            self.group_configs = settings.get('group_configs', {})
            # Update group config entries if they exist
            for group_key, config in self.group_configs.items():
                if group_key in self.group_config_entries:
                    self.group_config_entries[group_key]['name'].set(config.get('name', ''))
                    self.group_config_entries[group_key]['image'].set(config.get('image', ''))

            # Set distance configs
            self.active_distance_configs = settings.get('distance_configs', {})
            # Update distance config entries
            for distance, config in self.active_distance_configs.items():
                if distance in self.distance_configs:
                    self.distance_configs[distance]['group_by'].set(config.get('group_by', 'distance'))
                    self.distance_configs[distance]['top_count'].set(str(config.get('top_count', 3)))

            self.status_label.config(text="All settings loaded successfully", foreground="green")
        except Exception as e:
            self.status_label.config(text=f"Error loading settings: {str(e)}", foreground="red")