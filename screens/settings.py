import pygame
import pygame_gui
import os
import json
import tkinter as tk
from tkinter import filedialog

class SettingsScreen:
    def __init__(self, screen, ui_manager):
        self.screen = screen
        self.ui_manager = ui_manager
        self.next_screen = None

        self.bg_color = (230, 255, 230)
        self.elements = []
        self.loaded_from_file = False


        # Title
        self.title_label = pygame_gui.elements.UILabel(
            pygame.Rect((350, 10), (250, 30)),
            text="Simulation Settings",
            manager=self.ui_manager,
            object_id="#title_label"
        )
        self.elements.append(self.title_label)

        # Labels
        labels = [
            ("Time to shutdown simulation", (40, 50)),
            ("Map for simulation", (40, 100)),
            ("Private car amount", (40, 250)),
            ("Buses amount", (40, 300)),
            ("Trucks amount", (40, 350)),
            ("Type:", (40, 400)),
            ("Display algorithm", (500, 50)),
            ("Random vehicles JSON", (500, 180)),
            ("Density", (500, 250))
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
        self.time_input = pygame_gui.elements.UITextEntryLine(pygame.Rect((240, 50), (200, 30)), self.ui_manager)
        self.time_input.set_text("2")
        self.time_input.set_allowed_characters("numbers")

        self.map_dropdown = pygame_gui.elements.UIDropDownMenu(["map1", "map2", "map3"], "map1", pygame.Rect((240, 100), (200, 30)), self.ui_manager)

        self.algorithm_checklist = pygame_gui.elements.UISelectionList(
            pygame.Rect((700, 50), (150, 120)),
            ["alg1", "alg2", "alg3", "alg4"],
            manager=self.ui_manager,
            allow_multi_select=True
        )

        self.random_checkbox = pygame_gui.elements.UISelectionList(pygame.Rect((700, 180), (30, 30)), ["✔"], self.ui_manager)
        self.density_slider = pygame_gui.elements.UIHorizontalSlider(pygame.Rect((700, 250), (150, 30)), start_value=3, value_range=(1, 5), manager=self.ui_manager)

        self.density_label = pygame_gui.elements.UILabel(pygame.Rect((860, 250), (30, 30)), "3", self.ui_manager, object_id="#black_label")

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

        self.upload_button = pygame_gui.elements.UIButton(pygame.Rect((700, 500), (150, 30)), "Upload JSON", self.ui_manager)
        self.save_button = pygame_gui.elements.UIButton(pygame.Rect((100, 500), (200, 50)), "Save", self.ui_manager)
        self.cancel_button = pygame_gui.elements.UIButton(pygame.Rect((850, 10), (30, 30)), "X", self.ui_manager)
        self.error_label = pygame_gui.elements.UILabel(pygame.Rect((300, 560), (400, 30)), "", self.ui_manager, object_id="#error_label")

        self.elements.extend([
            self.time_input, self.map_dropdown, self.algorithm_checklist,
            self.random_checkbox, self.density_slider, self.density_label,
            self.car_input, self.bus_input, self.truck_input,
            self.electric_input, self.gasoline_input, self.gas_input,
            self.upload_button, self.save_button, self.cancel_button, self.error_label , self.electric_icon, self.gasoline_icon, self.gas_icon,
    self.electric_percent, self.gasoline_percent, self.gas_percent
        ])
        if os.path.exists("settings.json"):
            self.load_from_json("settings.json")

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
                self.next_screen = "main_menu"  # This returns to main screen

    def update(self, time_delta):
        self.ui_manager.update(time_delta)
        self.density_label.set_text(str(int(self.density_slider.get_current_value())))
        active = self.random_checkbox.get_single_selection() not in (None, "")
        for field in [self.car_input, self.bus_input, self.truck_input, self.electric_input, self.gasoline_input, self.gas_input]:
            if active:
                field.disable()
            else:
                field.enable()
        self.density_slider.disable() if active else self.density_slider.enable()

        if not active:
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
            self.load_from_json(file_path)

    def save_to_json(self):
        if self.loaded_from_file:
            return  # Do not overwrite manually loaded settings
        data = {
            "Time to shutdown simulation": {"value": self.time_input.get_text()},
            "Map for simulation": {"value": self.map_dropdown.selected_option},
            "Private car amount": {"value": self.car_input.get_text()},
            "Buses amount": {"value": self.bus_input.get_text()},
            "Trucks amount": {"value": self.truck_input.get_text()},
            "Electric": {"value": self.electric_input.get_text()},
            "Gasoline": {"value": self.gasoline_input.get_text()},
            "Gas": {"value": self.gas_input.get_text()}
        }
        with open("settings.json", "w") as f:
            json.dump(data, f, indent=4)

    def load_from_json(self, file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                self.time_input.set_text(data.get("Time to shutdown simulation", {}).get("value", ""))
                self.map_dropdown.selected_option = data.get("Map for simulation", {}).get("value", "map1")
                self.car_input.set_text(data.get("Private car amount", {}).get("value", ""))
                self.bus_input.set_text(data.get("Buses amount", {}).get("value", ""))
                self.truck_input.set_text(data.get("Trucks amount", {}).get("value", ""))
                self.electric_input.set_text(data.get("Electric", {}).get("value", ""))
                self.gasoline_input.set_text(data.get("Gasoline", {}).get("value", ""))
                self.gas_input.set_text(data.get("Gas", {}).get("value", ""))
                self.loaded_from_file = True
                print(f"[DEBUG] Loaded settings from {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to load JSON: {e}")
