import pygame
import pygame_gui
import os
import json
import tkinter as tk
from tkinter import filedialog
from classes.Enums.Alg import Alg


def get_available_maps():
    """Get list of available maps from the maps folder."""
    maps_dir = "maps"
    available_maps = []

    # Create maps directory if it doesn't exist
    if not os.path.exists(maps_dir):
        os.makedirs(maps_dir)

    # Get all JSON files in the maps directory
    for file in os.listdir(maps_dir):
        if file.endswith('.json'):
            # Remove .json extension to get map name
            map_name = os.path.splitext(file)[0]
            available_maps.append(map_name)

    return available_maps


class SettingsScreen:
    def __init__(self, screen, ui_manager):
        # Resize window to 900x700 for settings screen
        self.screen = screen
        self.ui_manager = ui_manager
        self.next_screen = None
        self._cleaned_up = False  # Flag to track if cleanup has been called

        self.bg_color = (230, 255, 230)
        self.elements = []
        self.loaded_from_file = False

        # Get available maps
        self.available_maps = get_available_maps()
        # Get available algorithms from Alg enum
        self.available_algorithms = [alg.name for alg in Alg]

        # Title
        self.title_label = pygame_gui.elements.UILabel(
            pygame.Rect((350, 10), (350, 30)),
            text="Simulation Settings",
            manager=self.ui_manager,
            object_id="#title_label"
        )
        self.elements.append(self.title_label)

        # Labels
        labels = [
            ("Map for simulation", (40, 100)),
            ("Private car amount", (40, 250)),
            ("Buses amount", (40, 300)),
            ("Trucks amount", (40, 350)),
            ("Type:", (40, 400)),
            ("Display algorithm", (600, 50)),
            ("Compared algorithm", (600, 100))
        ]
        for text, pos in labels:
            label = pygame_gui.elements.UILabel(
                pygame.Rect(pos, (200, 25)),
                text=text,
                manager=self.ui_manager,
                object_id="#black_label"
            )
            self.elements.append(label)

        icon_size = (24, 24)

        # Load and place icons
        self.electric_icon = pygame_gui.elements.UIImage(
            pygame.Rect((210, 400), icon_size),
            pygame.image.load(os.path.join("assets", "electric.png")).convert_alpha(),
            manager=self.ui_manager
        )

        self.gasoline_icon = pygame_gui.elements.UIImage(
            pygame.Rect((210, 425), icon_size),
            pygame.image.load(os.path.join("assets", "gasoline.png")).convert_alpha(),
            manager=self.ui_manager
        )

        self.gas_icon = pygame_gui.elements.UIImage(
            pygame.Rect((210, 450), icon_size),
            pygame.image.load(os.path.join("assets", "gas.png")).convert_alpha(),
            manager=self.ui_manager
        )

        self.electric_percent = pygame_gui.elements.UILabel(
            pygame.Rect((320, 400), (20, 30)),
            text="%",
            manager=self.ui_manager
        )

        self.gasoline_percent = pygame_gui.elements.UILabel(
            pygame.Rect((320, 425), (20, 30)),
            text="%",
            manager=self.ui_manager
        )

        self.gas_percent = pygame_gui.elements.UILabel(
            pygame.Rect((320, 450), (20, 30)),
            text="%",
            manager=self.ui_manager
        )

        # Inputs
        # Remove time_input, random_checkbox, density_slider, density_label
        # Initialize dropdown with available maps

        self.map_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=self.available_maps,
            starting_option=self.available_maps[0] if self.available_maps else "",
            relative_rect=pygame.Rect((240, 100), (200, 30)),
            manager=self.ui_manager,
            object_id='#map_dropdown'
        )

        # Algorithm dropdowns
        self.display_alg_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=self.available_algorithms,
            starting_option=self.available_algorithms[0] if self.available_algorithms else "",
            relative_rect=pygame.Rect((800, 50), (250, 30)),
            manager=self.ui_manager,
            object_id='#display_alg_dropdown'
        )
        self.compared_alg_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=self.available_algorithms,
            starting_option=self.available_algorithms[0] if self.available_algorithms else "",
            relative_rect=pygame.Rect((800, 100), (250, 30)),
            manager=self.ui_manager,
            object_id='#compared_alg_dropdown'
        )

        self.car_input = pygame_gui.elements.UITextEntryLine(pygame.Rect((240, 250), (200, 30)), self.ui_manager)
        self.bus_input = pygame_gui.elements.UITextEntryLine(pygame.Rect((240, 300), (200, 30)), self.ui_manager)
        self.truck_input = pygame_gui.elements.UITextEntryLine(pygame.Rect((240, 350), (200, 30)), self.ui_manager)

        for inp in [self.car_input, self.bus_input, self.truck_input]:
            inp.set_allowed_characters("numbers")
            inp.set_text_length_limit(3)

        # Renamed hybrid to gas
        self.electric_input = pygame_gui.elements.UITextEntryLine(pygame.Rect((240, 400), (80, 30)), self.ui_manager)
        self.gasoline_input = pygame_gui.elements.UITextEntryLine(pygame.Rect((240, 425), (80, 30)), self.ui_manager)
        self.gas_input = pygame_gui.elements.UITextEntryLine(pygame.Rect((240, 450), (80, 30)), self.ui_manager)

        for inp in [self.electric_input, self.gasoline_input, self.gas_input]:
            inp.set_allowed_characters("numbers")
            inp.set_text_length_limit(3)

        self.upload_button = pygame_gui.elements.UIButton(pygame.Rect((800, 500), (150, 30)), "Upload JSON", self.ui_manager)
        self.save_button = pygame_gui.elements.UIButton(pygame.Rect((100, 500), (200, 50)), "Save", self.ui_manager)
        self.cancel_button = pygame_gui.elements.UIButton(pygame.Rect((850, 10), (30, 30)), "X", self.ui_manager)
        self.error_label = pygame_gui.elements.UILabel(pygame.Rect((300, 560), (400, 30)), "", self.ui_manager, object_id="#error_label")

        self.elements.extend([
            self.map_dropdown, self.display_alg_dropdown, self.compared_alg_dropdown,
            self.car_input, self.bus_input, self.truck_input,
            self.electric_input, self.gasoline_input, self.gas_input,
            self.upload_button, self.save_button, self.cancel_button, self.error_label,
            self.electric_icon, self.gasoline_icon, self.gas_icon,
            self.electric_percent, self.gasoline_percent, self.gas_percent
        ])

        if os.path.exists("settings.json"):
            self.load_from_json("settings.json")
            # Refresh all UI fields to reflect loaded values

    def handle_events(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.upload_button:
                self.upload_json()
            elif event.ui_element == self.save_button:
                self.save_to_json()
            elif event.ui_element == self.cancel_button:
                self.next_screen = "main_menu"

    def cleanup(self):
        """Clean up UI elements before switching screens"""
        if self._cleaned_up:
            return  # Already cleaned up
            
        for element in self.elements:
            element.kill()
        self.elements.clear()
        self.ui_manager.clear_and_reset()
        
        self._cleaned_up = True

    def update(self, time_delta):
        self.ui_manager.update(time_delta)
        # Remove density_label and density_slider logic
        # Remove random_checkbox logic
        # Only keep the check for algorithms and energy percentages
        display_alg = self.display_alg_dropdown.selected_option
        compared_alg = self.compared_alg_dropdown.selected_option
        if display_alg == compared_alg:
            self.save_button.disable()
            self.error_label.set_text("Display and Compared algorithm must be different")
            return
        try:
            total = int(self.electric_input.get_text() or 0) + \
                    int(self.gasoline_input.get_text() or 0) + \
                    int(self.gas_input.get_text() or 0)
            if total != 100:
                self.save_button.disable()
                self.error_label.set_text("Energy percentages must sum to 100%")
            else:
                self.save_button.enable()
                self.error_label.set_text("")
        except ValueError:
            self.save_button.disable()
            self.error_label.set_text("Percentages must be numeric")

    def draw(self):
        self.screen.fill(self.bg_color)
        self.ui_manager.draw_ui(self.screen)

    def get_next_screen(self):
        return self.next_screen

    def upload_json(self):
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            self.loaded_from_file = True
            self.load_from_json(file_path)

    def save_to_json(self):
        if self.loaded_from_file:
            return  # Do not overwrite manually loaded settings
        
        # Get the selected map and ensure it's a single value
        selected_map = self.map_dropdown.selected_option
        # Handle different types of selected_map
        if isinstance(selected_map, tuple):
            selected_map = selected_map[0]  # Take first value from tuple
        elif isinstance(selected_map, list):
            selected_map = selected_map[0] if selected_map else ""
        
        # Get selected algorithms
        selected_display_alg = self.display_alg_dropdown.selected_option
        selected_compared_alg = self.compared_alg_dropdown.selected_option
        # Handle different types of selected_display_alg
        if isinstance(selected_display_alg, tuple):
            selected_display_alg = selected_display_alg[0]
        elif isinstance(selected_display_alg, list):
            selected_display_alg = selected_display_alg[0] if selected_display_alg else ""
        # Handle different types of selected_compared_alg
        if isinstance(selected_compared_alg, tuple):
            selected_compared_alg = selected_compared_alg[0]
        elif isinstance(selected_compared_alg, list):
            selected_compared_alg = selected_compared_alg[0] if selected_compared_alg else ""
        
        data = {
            "Map for simulation": {"value": selected_map},
            "Private car amount": {"value": self.car_input.get_text()},
            "Buses amount": {"value": self.bus_input.get_text()},
            "Trucks amount": {"value": self.truck_input.get_text()},
            "Electric": {"value": self.electric_input.get_text()},
            "Gasoline": {"value": self.gasoline_input.get_text()},
            "Gas": {"value": self.gas_input.get_text()},
            "Display algorithm": {"value": selected_display_alg},
            "Compared algorithm": {"value": selected_compared_alg}
        }
        # Clear the file by opening in 'w' mode and then write new data
        with open("settings.json", "w") as f:
            json.dump(data, f, indent=4)

    def load_from_json(self, file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

                # Get the map value from JSON and ensure it's a string
                map_value = data.get("Map for simulation", {}).get("value", "")
                # Handle case where map_value might be a list
                if isinstance(map_value, list) and map_value:
                    map_value = map_value[0]  # Take the first map from the list
                
                # Check if the map exists in available maps
                if map_value in self.available_maps:
                    select_map = map_value
                elif self.available_maps:  # If map not found but we have other maps
                    select_map = self.available_maps[0]
                else:
                    # No maps available
                    select_map = None
                
                self.car_input.set_text(data.get("Private car amount", {}).get("value", ""))
                self.bus_input.set_text(data.get("Buses amount", {}).get("value", ""))
                self.truck_input.set_text(data.get("Trucks amount", {}).get("value", ""))
                self.electric_input.set_text(data.get("Electric", {}).get("value", ""))
                self.gasoline_input.set_text(data.get("Gasoline", {}).get("value", ""))
                self.gas_input.set_text(data.get("Gas", {}).get("value", ""))
                # Set default algorithms from json file
                display_alg_value = data.get("Display algorithm", {}).get("value", self.available_algorithms[0])
                compared_alg_value = data.get("Compared algorithm", {}).get("value", self.available_algorithms[0])
                if display_alg_value in self.available_algorithms:
                    display_alg = display_alg_value
                else:
                    display_alg = self.available_algorithms[1]
                if compared_alg_value in self.available_algorithms:
                    compared_alg = compared_alg_value
                else:
                    compared_alg = self.available_algorithms[0]

                self.map_dropdown = pygame_gui.elements.UIDropDownMenu(
                    options_list=self.available_maps,
                    starting_option= select_map,
                    relative_rect=pygame.Rect((240, 100), (200, 30)),
                    manager=self.ui_manager,
                    object_id='#map_dropdown'
                )

                # Algorithm dropdowns
                self.display_alg_dropdown = pygame_gui.elements.UIDropDownMenu(
                    options_list=self.available_algorithms,
                    starting_option= display_alg,
                    relative_rect=pygame.Rect((800, 50), (250, 30)),
                    manager=self.ui_manager,
                    object_id='#display_alg_dropdown'
                )
                self.compared_alg_dropdown = pygame_gui.elements.UIDropDownMenu(
                    options_list=self.available_algorithms,
                    starting_option=compared_alg,
                    relative_rect=pygame.Rect((800, 100), (250, 30)),
                    manager=self.ui_manager,
                    object_id='#compared_alg_dropdown'
                )
        except Exception:
            # Failed to load JSON
            pass
