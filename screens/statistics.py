import pygame
import pygame_gui
import csv
import os
from datetime import datetime
from classes.Enums.Color import Color

def format_algorithm_name(alg_name):
    """Convert algorithm enum name to a more readable display name."""
    name_mapping = {
        'FIXED_TIMING_CYCLE': 'Fixed Timing Cycle',
        'ADAPTIVE_ALG': 'Adaptive Algorithm',
        'GREEN_WAVE_ENERGY': 'Green Wave (Energy)',
        'GREEN_WAVE_POLLUTION': 'Green Wave (Pollution)'
    }
    return name_mapping.get(alg_name, alg_name.replace('_', ' ').title())


def wrap_text(text, font, max_width):
    """Wrap text to fit within a given width when rendered with the specified font."""
    words = text.split(' ')
    lines = []
    current_line = ''
    for word in words:
        test_line = current_line + (' ' if current_line else '') + word
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


class StatisticsScreen:
    def __init__(self, screen, ui_manager, total_vehicles, main_simulation_time, compare_simulation_time, vehicle_stats, display_stats=None, compare_stats=None, display_alg_name=None, compare_alg_name=None):
        self.screen = screen
        self.ui_manager = ui_manager
        self.next_screen = None
        self.total_vehicles = total_vehicles
        self.main_simulation_time = main_simulation_time
        self.compare_simulation_time = compare_simulation_time
        self.vehicle_stats = vehicle_stats
        self.display_stats = display_stats or {}
        self.compare_stats = compare_stats or {}
        self.display_alg_name = format_algorithm_name(display_alg_name) if display_alg_name else 'Display Algorithm'
        self.compare_alg_name = format_algorithm_name(compare_alg_name) if compare_alg_name else 'Compare Algorithm'
        self._cleaned_up = False  # Flag to track if cleanup has been called
        
        # Scroll state
        self.scroll_offset = 0
        self.max_scroll = 0
        self.SCROLL_SPEED = 40  # pixels per wheel event

        # Screen dimensions
        self.WINDOW_WIDTH, self.WINDOW_HEIGHT = self.screen.get_size()
        
        # Colors
        self.BACKGROUND_COLOR = (240, 240, 240)  # Light gray background
        self.CARD_COLOR = (255, 255, 255)  # White cards
        self.TITLE_COLOR = (50, 50, 50)  # Dark gray for titles
        self.TEXT_COLOR = (70, 70, 70)  # Slightly lighter gray for text
        self.ACCENT_COLOR = (0, 120, 0)  # Green accent color
        self.SECTION_TITLE_COLOR = (0, 100, 0)  # Dark green for section titles
        
        # Calculate dynamic dimensions based on screen size
        self.base_width = 900  # Base width for scaling
        self.scale_factor = self.WINDOW_WIDTH / self.base_width
        
        # Card dimensions (scaled)
        self.card_width = int(280 * self.scale_factor)
        self.card_height = int(280 * 0.8 * self.scale_factor)  # 20% smaller
        self.margin = int(20 * 1.15 * self.scale_factor)  # 15% more space
        self.cards_per_row = 3
        
        # Calculate total width of cards in a row
        total_cards_width = (self.card_width * self.cards_per_row) + (self.margin * (self.cards_per_row - 1))
        
        # Calculate starting x position to center the cards
        self.start_x = (self.WINDOW_WIDTH - total_cards_width) // 2

        # Create back button with better styling
        button_width = int(200 * self.scale_factor)
        button_height = int(50 * self.scale_factor)
        self.back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (self.WINDOW_WIDTH//2 - button_width//2, 
                 self.WINDOW_HEIGHT - int(80 * self.scale_factor)),
                (button_width, button_height)
            ),
            text='Back to Main Menu',
            manager=self.ui_manager,
            object_id='#main_menu_button'
        )

        # Create save to CSV button
        self.save_csv_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (self.WINDOW_WIDTH//2 - button_width//2 - button_width - int(20 * self.scale_factor), 
                 self.WINDOW_HEIGHT - int(80 * self.scale_factor)),
                (button_width, button_height)
            ),
            text='Save to CSV',
            manager=self.ui_manager,
            object_id='#save_csv_button'
        )

    def handle_resize(self, new_width, new_height):
        """Handle window resize"""
        self.WINDOW_WIDTH = new_width
        self.WINDOW_HEIGHT = new_height
        
        # Recalculate scale factor
        self.scale_factor = self.WINDOW_WIDTH / self.base_width
        
        # Update card dimensions
        self.card_width = int(280 * self.scale_factor)
        self.card_height = int(280 * 0.8 * self.scale_factor)
        self.margin = int(20 * 1.15 * self.scale_factor)
        
        # Recalculate total width and starting position
        total_cards_width = (self.card_width * self.cards_per_row) + (self.margin * (self.cards_per_row - 1))
        self.start_x = (self.WINDOW_WIDTH - total_cards_width) // 2
        
        # Update button positions and sizes
        button_width = int(200 * self.scale_factor)
        button_height = int(50 * self.scale_factor)
        self.back_button.set_relative_position(
            (self.WINDOW_WIDTH//2 - button_width//2,
             self.WINDOW_HEIGHT - int(80 * self.scale_factor))
        )
        self.back_button.set_dimensions((button_width, button_height))
        
        # Update save CSV button position and size
        self.save_csv_button.set_relative_position(
            (self.WINDOW_WIDTH//2 - button_width//2 - button_width - int(20 * self.scale_factor),
             self.WINDOW_HEIGHT - int(80 * self.scale_factor))
        )
        self.save_csv_button.set_dimensions((button_width, button_height))

    def draw_card(self, x, y, width, height, title, content_items, surface=None):
        if surface is None:
            surface = self.screen
        # Draw card background with shadow
        card_rect = pygame.Rect(x, y, width, height)
        shadow_rect = pygame.Rect(x + int(2 * self.scale_factor), y + int(2 * self.scale_factor), width, height)
        pygame.draw.rect(surface, (200, 200, 200), shadow_rect, border_radius=int(8 * self.scale_factor))
        pygame.draw.rect(surface, self.CARD_COLOR, card_rect, border_radius=int(8 * self.scale_factor))
        pygame.draw.rect(surface, (220, 220, 220), card_rect, width=1, border_radius=int(8 * self.scale_factor))
        
        # Draw title
        title_font = pygame.font.SysFont("Arial", int(18 * self.scale_factor), bold=True)
        title_surface = title_font.render(title, True, self.TITLE_COLOR)
        # Move the title further down to fit the taller card
        title_rect = title_surface.get_rect(midtop=(x + width//2, y + int(24 * self.scale_factor)))
        surface.blit(title_surface, title_rect)
        
        # Draw content
        content_font = pygame.font.SysFont("Arial", int(16 * self.scale_factor))
        y_offset = y + int(64 * self.scale_factor)
        max_text_width = width - int(30 * self.scale_factor)
        for label, value in content_items:
            text = f"{label}: {value}" if label else f"{value}"
            wrapped_lines = wrap_text(text, content_font, max_text_width)
            for line in wrapped_lines:
                text_surface = content_font.render(line, True, self.TEXT_COLOR)
                text_rect = text_surface.get_rect(midleft=(x + int(15 * self.scale_factor), y_offset))
                surface.blit(text_surface, text_rect)
                y_offset += int(22 * self.scale_factor)

    def draw_section_title(self, x, y, title, surface=None):
        if surface is None:
            surface = self.screen
        title_font = pygame.font.SysFont("Arial", int(24 * self.scale_factor), bold=True)
        title_surface = title_font.render(title, True, self.SECTION_TITLE_COLOR)
        # Move section titles further down for better spacing with larger cards
        title_rect = title_surface.get_rect(midleft=(x, y + int(16 * self.scale_factor)))
        surface.blit(title_surface, title_rect)

    def handle_events(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.back_button:
                self.next_screen = "main_menu"
            elif event.ui_element == self.save_csv_button:
                self.save_statistics_to_csv()
        elif event.type == pygame.VIDEORESIZE:
            self.handle_resize(event.w, event.h)
        elif event.type == pygame.MOUSEWHEEL:
            # Scroll up/down
            self.scroll_offset -= event.y * self.SCROLL_SPEED
            self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))

    def update(self, time_delta):
        self.ui_manager.update(time_delta)

    def save_statistics_to_csv(self):
        """
        Save all displayed statistics to a CSV file in the results' folder.
        The filename will be: display_alg_name + compare_alg_name + current_date_time.csv
        """
        # Create results folder if it doesn't exist
        results_folder = "results"
        if not os.path.exists(results_folder):
            os.makedirs(results_folder)
        
        # Generate filename with current date and time
        current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Clean algorithm names for filename (remove special characters)
        display_alg_clean = self.display_alg_name.replace(" ", "_").replace("(", "").replace(")", "").replace(":", "")
        compare_alg_clean = self.compare_alg_name.replace(" ", "_").replace("(", "").replace(")", "").replace(":", "")
        filename = f"{display_alg_clean}_{compare_alg_clean}_{current_datetime}.csv"
        filepath = os.path.join(results_folder, filename)
        
        # Prepare data for CSV
        # Add algorithm names as rows
        # Add simulation overview data
        # Add vehicle types data
        # Add energy distribution data
        csv_data = [["Algorithm", self.display_alg_name], ["Algorithm", self.compare_alg_name],
                    ["Total Vehicles", self.total_vehicles, self.total_vehicles],
                    ["Simulation Time (seconds)", f"{self.main_simulation_time:.2f}",
                     f"{self.compare_simulation_time:.2f}"], ["Private Cars", self.vehicle_stats["Private car amount"],
                                                              self.vehicle_stats["Private car amount"]],
                    ["Buses", self.vehicle_stats["Buses amount"], self.vehicle_stats["Buses amount"]],
                    ["Trucks", self.vehicle_stats["Trucks amount"], self.vehicle_stats["Trucks amount"]],
                    ["Electric (%)", self.vehicle_stats["Electric"], self.vehicle_stats["Electric"]],
                    ["Gasoline (%)", self.vehicle_stats["Gasoline"], self.vehicle_stats["Gasoline"]],
                    ["Gas (%)", self.vehicle_stats["Gas"], self.vehicle_stats["Gas"]]]

        # Add energy consumption data
        if self.display_stats and self.compare_stats:
            display_total_consumption = self.display_stats.get("total_energy_consumed", 0)
            compare_total_consumption = self.compare_stats.get("total_energy_consumed", 0)
            csv_data.append(["Total Energy (Megajoule)", f"{display_total_consumption:.2f}", f"{compare_total_consumption:.2f}"])
            
            csv_data.append(["Total Distance (Km)", f"{self.display_stats.get('total_distance', 0):.1f}", f"{self.compare_stats.get('total_distance', 0):.1f}"])
            csv_data.append(["Average Energy Efficiency", f"{self.display_stats.get('average_energy_efficiency', 0):.3f}", f"{self.compare_stats.get('average_energy_efficiency', 0):.3f}"])
            
            # Add pollution data
            display_total_pollution = self.display_stats.get("total_pollution", 0)
            compare_total_pollution = self.compare_stats.get("total_pollution", 0)
            csv_data.append(["Total CO2 (Kg)", f"{display_total_pollution:.1f}", f"{compare_total_pollution:.1f}"])
            csv_data.append(["Average Emission (Kg/km)", f"{self.display_stats.get('average_pollution_efficiency', 0):.1f}", f"{self.compare_stats.get('average_pollution_efficiency', 0):.1f}"])
            csv_data.append(["Stops Count", self.display_stats.get("total_stops", 0), self.compare_stats.get("total_stops", 0)])
            
            # Add traffic behavior data
            display_idle_time = self.display_stats.get("total_idle_time", 0)
            compare_idle_time = self.compare_stats.get("total_idle_time", 0)
            csv_data.append(["Idle Time (seconds)", f"{display_idle_time:.1f}", f"{compare_idle_time:.1f}"])
            
            # Calculate average speeds
            display_total_distance = self.display_stats.get("total_distance", 0)
            display_total_time = self.display_stats.get("total_time", self.main_simulation_time)
            display_avg_speed = (display_total_distance / display_total_time * 3.6) if display_total_time > 0 else 0
            compare_total_distance = self.compare_stats.get("total_distance", 0)
            compare_total_time = self.compare_stats.get("total_time", self.compare_simulation_time)
            compare_avg_speed = (compare_total_distance / compare_total_time * 3.6) if compare_total_time > 0 else 0
            csv_data.append(["Average Speed (km/h)", f"{display_avg_speed:.1f}", f"{compare_avg_speed:.1f}"])
            
            # Add energy consumption by type
            display_energy_consumption = self.display_stats.get("energy_consumption", {})
            compare_energy_consumption = self.compare_stats.get("energy_consumption", {})
            csv_data.append(["Electric Energy (Megajoule)", f"{display_energy_consumption.get('Electric', 0):.2f}", f"{compare_energy_consumption.get('Electric', 0):.2f}"])
            csv_data.append(["Gasoline Energy (Megajoule)", f"{display_energy_consumption.get('Gasoline', 0):.2f}", f"{compare_energy_consumption.get('Gasoline', 0):.2f}"])
            csv_data.append(["Gas Energy (Megajoule)", f"{display_energy_consumption.get('Gas', 0):.2f}", f"{compare_energy_consumption.get('Gas', 0):.2f}"])
            
            # Add pollution by energy type
            display_energy_pollution = self.display_stats.get("energy_pollution", {})
            compare_energy_pollution = self.compare_stats.get("energy_pollution", {})
            csv_data.append(["Electric CO2 (Kg)", f"{display_energy_pollution.get('Electric', 0):.1f}", f"{compare_energy_pollution.get('Electric', 0):.1f}"])
            csv_data.append(["Gasoline CO2 (Kg)", f"{display_energy_pollution.get('Gasoline', 0):.1f}", f"{compare_energy_pollution.get('Gasoline', 0):.1f}"])
            csv_data.append(["Gas CO2 (Kg)", f"{display_energy_pollution.get('Gas', 0):.1f}", f"{compare_energy_pollution.get('Gas', 0):.1f}"])
            
            # Add consumption by vehicle type
            display_vehicle_consumption = self.display_stats.get("vehicle_consumption", {})
            compare_vehicle_consumption = self.compare_stats.get("vehicle_consumption", {})
            csv_data.append(["Car Consumption", f"{display_vehicle_consumption.get('Car', 0):.2f}", f"{compare_vehicle_consumption.get('Car', 0):.2f}"])
            csv_data.append(["Bus Consumption", f"{display_vehicle_consumption.get('Bus', 0):.2f}", f"{compare_vehicle_consumption.get('Bus', 0):.2f}"])
            csv_data.append(["Truck Consumption", f"{display_vehicle_consumption.get('Truck', 0):.2f}", f"{compare_vehicle_consumption.get('Truck', 0):.2f}"])
            
            # Add final scores
            display_score = display_total_consumption + display_total_pollution
            compare_score = compare_total_consumption + compare_total_pollution
            csv_data.append(["Final Score (Lower = Better)", f"{display_score:.1f}", f"{compare_score:.1f}"])
        
        # Write to CSV file
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Write header
                writer.writerow(["Metric", "Display Algorithm", "Compare Algorithm"])
                # Write data
                writer.writerows(csv_data)

            return filepath
        except Exception:
            # Failed to save statistics to CSV
            return None

    def draw(self):
        # Calculate total content height (estimate based on cards/sections)
        content_height = int(700 * self.scale_factor)
        if self.display_stats or self.compare_stats:
            content_height = int(1200 * self.scale_factor)
        # Add extra height for the new score row
        content_height += self.card_height + self.margin
        self.max_scroll = max(0, content_height - self.WINDOW_HEIGHT + 100)

        # Create a scrollable surface
        scroll_surface = pygame.Surface((self.WINDOW_WIDTH, content_height))
        scroll_surface.fill(self.BACKGROUND_COLOR)

        # Draw everything on scroll_surface instead of self.screen
        # --- BEGIN DRAWING ON scroll_surface ---
        # Draw main title with shadow
        title_font = pygame.font.SysFont("Arial", int(40 * self.scale_factor), bold=True)
        title = title_font.render("Simulation Statistics", True, self.TITLE_COLOR)
        title_shadow = title_font.render("Simulation Statistics", True, (200, 200, 200))
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH//2, int(40 * self.scale_factor)))
        scroll_surface.blit(title_shadow, (title_rect.x + int(2 * self.scale_factor), title_rect.y + int(2 * self.scale_factor)))
        scroll_surface.blit(title, title_rect)

        # --- NEW: Draw Algorithm Score Row ---
        score_y = int(80 * self.scale_factor)
        score_card_width = int((self.card_width * 1.2))
        score_margin = int(self.margin * 2)
        # Calculate x positions for two cards centered
        total_score_width = score_card_width * 2 + score_margin
        score_start_x = (self.WINDOW_WIDTH - total_score_width) // 2

        # Calculate scores (lower is better)
        def calc_score(stats):
            if not stats:
                return 0
            return stats.get('total_pollution', 0) + stats.get('total_energy_consumed', 0)

        display_score = calc_score(self.display_stats)
        compare_score = calc_score(self.compare_stats)

        # Get algorithm names from instance variables
        display_alg_name = self.display_alg_name
        compare_alg_name = self.compare_alg_name

        self.draw_card(
            score_start_x,
            score_y,
            score_card_width,
            self.card_height,
            "Display Algorithm",
            [("Final Score", f"{display_score:.1f}"), ("Goal", "Lower = Better") , ("Name", f"{display_alg_name}")],
            surface=scroll_surface
        )
        self.draw_card(
            score_start_x + score_card_width + score_margin,
            score_y,
            score_card_width,
            self.card_height,
            "Compare Algorithm",
            [("Final Score", f"{compare_score:.1f}"), ("Goal", "Lower = Better"), ("Name", f"{compare_alg_name}")],
            surface=scroll_surface
        )

        # Y positions for each row
        y_row1 = int(130 * self.scale_factor) + self.card_height + self.margin
        y_row2 = y_row1 + self.card_height + self.margin
        y_row3 = y_row2 + self.card_height + self.margin

        # Draw Simulation Overview section
        self.draw_section_title(self.start_x, int(340 * self.scale_factor), "Simulation Overview", surface=scroll_surface)
        
        # Draw Overview Cards
        overview_items = [
            ("Total Vehicles", self.total_vehicles),
            ("Simulation Time", f"{self.main_simulation_time:.2f} seconds"),
        ]
        if self.display_stats and self.compare_stats:
            overview_items.append(("", "--- Compare Algorithm ---"))
            overview_items.append(("Simulation Time", f"{self.compare_simulation_time:.2f} seconds"))
        self.draw_card(
            self.start_x,
            y_row1,
            self.card_width,
            self.card_height,
            "General Info",
            overview_items,
            surface=scroll_surface
        )
        
        # Draw Vehicle Types Card
        vehicle_items = [
            ("Private Cars", self.vehicle_stats["Private car amount"]),
            ("Buses", self.vehicle_stats["Buses amount"]),
            ("Trucks", self.vehicle_stats["Trucks amount"])
        ]
        self.draw_card(
            self.start_x + self.card_width + self.margin,
            y_row1,
            self.card_width,
            self.card_height,
            "Vehicle Types",
            vehicle_items,
            surface=scroll_surface
        )
        
        # Draw Energy Distribution Card
        energy_items = [
            ("Electric", f"{self.vehicle_stats['Electric']}%"),
            ("Gasoline", f"{self.vehicle_stats['Gasoline']}%"),
            ("Gas", f"{self.vehicle_stats['Gas']}%")
        ]
        self.draw_card(
            self.start_x + (self.card_width + self.margin) * 2,
            y_row1,
            self.card_width,
            self.card_height,
            "Energy Distribution",
            energy_items,
            surface=scroll_surface
        )
        
        # Draw Consumption and Pollution section if data is available
        if self.display_stats and self.compare_stats:
            self.draw_section_title(self.start_x, y_row2 - int(30 * self.scale_factor), "Consumption & Pollution Analysis", surface=scroll_surface)
            
            # Draw Total Consumption Card
            display_total_consumption = self.display_stats.get("total_energy_consumed", 0)
            compare_total_consumption = self.compare_stats.get("total_energy_consumed", 0)
            energy_unit = "Megajoule" #  if any("Electric" in str(v) for v in self.vehicle_stats.values()) else "L"
            consumption_items = [
                ("Total Energy", f"{display_total_consumption:.2f} {energy_unit}"),
                ("Total Distance", f"{self.display_stats.get('total_distance', 0):.1f} Km"),
                ("Avg Efficiency", f"{self.display_stats.get('average_energy_efficiency', 0):.3f}"),
                ("", "--- Compare Algorithm ---"),
                ("Total Energy", f"{compare_total_consumption:.2f} {energy_unit}"),
                ("Total Distance", f"{self.compare_stats.get('total_distance', 0):.1f} Km"),
                ("Avg Efficiency", f"{self.compare_stats.get('average_energy_efficiency', 0):.3f}")
            ]
            self.draw_card(
                self.start_x,
                y_row2,
                self.card_width,
                self.card_height,
                "Energy Consumption",
                consumption_items,
                surface=scroll_surface
            )
            
            # Draw Total Pollution Card
            display_total_pollution = self.display_stats.get("total_pollution", 0)
            compare_total_pollution = self.compare_stats.get("total_pollution", 0)
            pollution_items = [
                ("Total CO2", f"{display_total_pollution:.1f} Kg"),
                ("Avg Emission", f"{self.display_stats.get('average_pollution_efficiency', 0):.1f} Kg/km"),
                ("Stops Count", self.display_stats.get("total_stops", 0)),
                ("", "--- Compare Algorithm ---"),
                ("Total CO2", f"{compare_total_pollution:.1f} Kg"),
                ("Avg Emission", f"{self.compare_stats.get('average_pollution_efficiency', 0):.1f} Kg/km"),
                ("Stops Count", self.compare_stats.get("total_stops", 0))
            ]
            self.draw_card(
                self.start_x + self.card_width + self.margin,
                y_row2,
                self.card_width,
                self.card_height,
                "Pollution Emissions",
                pollution_items,
                surface=scroll_surface
            )
            
            # Draw Traffic Behavior Card
            display_idle_time = self.display_stats.get("total_idle_time", 0)
            display_total_distance = self.display_stats.get("total_distance", 0)
            display_total_time = self.display_stats.get("total_time", self.main_simulation_time)
            display_avg_speed = (display_total_distance / display_total_time * 3.6) if display_total_time > 0 else 0
            compare_idle_time = self.compare_stats.get("total_idle_time", 0)
            compare_total_distance = self.compare_stats.get("total_distance", 0)
            compare_total_time = self.compare_stats.get("total_time", self.compare_simulation_time)
            compare_avg_speed = (compare_total_distance / compare_total_time * 3.6) if compare_total_time > 0 else 0
            behavior_items = [
                ("Idle Time", f"{display_idle_time:.1f} s"),
                ("Avg Speed", f"{display_avg_speed:.1f} km/h"),
                ("", "--- Compare Algorithm ---"),
                ("Idle Time", f"{compare_idle_time:.1f} s"),
                ("Avg Speed", f"{compare_avg_speed:.1f} km/h")
            ]
            self.draw_card(
                self.start_x + (self.card_width + self.margin) * 2,
                y_row2,
                self.card_width,
                self.card_height,
                "Traffic Behavior",
                behavior_items,
                surface=scroll_surface
            )
            
            # Draw Energy Type Breakdown section
            self.draw_section_title(self.start_x, y_row3 - int(30 * self.scale_factor), "Energy Type Breakdown", surface=scroll_surface)
            
            # Draw Energy Consumption by Type
            display_energy_consumption = self.display_stats.get("energy_consumption", {})
            compare_energy_consumption = self.compare_stats.get("energy_consumption", {})
            energy_consumption_items = [
                ("Electric", f"{display_energy_consumption.get('Electric', 0):.2f} Megajoule"),
                ("Gasoline", f"{display_energy_consumption.get('Gasoline', 0):.2f} Megajoule"),
                ("Gas", f"{display_energy_consumption.get('Gas', 0):.2f} Megajoule"),
                ("", "--- Compare Algorithm ---"),
                ("Electric", f"{compare_energy_consumption.get('Electric', 0):.2f} Megajoule"),
                ("Gasoline", f"{compare_energy_consumption.get('Gasoline', 0):.2f} Megajoule"),
                ("Gas", f"{compare_energy_consumption.get('Gas', 0):.2f} Megajoule")
            ]
            self.draw_card(
                self.start_x,
                y_row3,
                self.card_width,
                self.card_height,
                "Energy by Type",
                energy_consumption_items,
                surface=scroll_surface
            )
            
            # Draw Pollution by Energy Type
            display_energy_pollution = self.display_stats.get("energy_pollution", {})
            compare_energy_pollution = self.compare_stats.get("energy_pollution", {})
            energy_pollution_items = [
                ("Electric", f"{display_energy_pollution.get('Electric', 0):.1f} CO2 Kg"),
                ("Gasoline", f"{display_energy_pollution.get('Gasoline', 0):.1f} CO2 Kg"),
                ("Gas", f"{display_energy_pollution.get('Gas', 0):.1f} g CO2"),
                ("", "--- Compare Algorithm ---"),
                ("Electric", f"{compare_energy_pollution.get('Electric', 0):.1f} CO2 Kg"),
                ("Gasoline", f"{compare_energy_pollution.get('Gasoline', 0):.1f} CO2 Kg"),
                ("Gas", f"{compare_energy_pollution.get('Gas', 0):.1f} CO2 Kg")
            ]
            self.draw_card(
                self.start_x + self.card_width + self.margin,
                y_row3,
                self.card_width,
                self.card_height,
                "Pollution by Type",
                energy_pollution_items,
                surface=scroll_surface
            )
            
            # Draw Vehicle Type Impact
            display_vehicle_consumption = self.display_stats.get("vehicle_consumption", {})
            compare_vehicle_consumption = self.compare_stats.get("vehicle_consumption", {})
            vehicle_impact_items = [
                ("Cars", f"{display_vehicle_consumption.get('Car', 0):.2f}"),
                ("Buses", f"{display_vehicle_consumption.get('Bus', 0):.2f}"),
                ("Trucks", f"{display_vehicle_consumption.get('Truck', 0):.2f}"),
                ("", "--- Compare Algorithm ---"),
                ("Cars", f"{compare_vehicle_consumption.get('Car', 0):.2f}"),
                ("Buses", f"{compare_vehicle_consumption.get('Bus', 0):.2f}"),
                ("Trucks", f"{compare_vehicle_consumption.get('Truck', 0):.2f}")
            ]
            self.draw_card(
                self.start_x + (self.card_width + self.margin) * 2,
                y_row3,
                self.card_width,
                self.card_height,
                "Consumption by Vehicle",
                vehicle_impact_items,
                surface=scroll_surface
            )
        # --- END DRAWING ON scroll_surface ---

        # Blit the visible part of scroll_surface to the main screen
        self.screen.fill(self.BACKGROUND_COLOR)
        self.screen.blit(scroll_surface, (0, -self.scroll_offset))
        self.ui_manager.draw_ui(self.screen)

    def get_next_screen(self):
        return self.next_screen

    def cleanup(self):
        """Clean up UI elements when transitioning away from this screen"""
        if self._cleaned_up:
            return  # Already cleaned up
        
        if hasattr(self, 'back_button') and self.back_button:
            self.back_button.kill()
        if hasattr(self, 'save_csv_button') and self.save_csv_button:
            self.save_csv_button.kill()
        # Clear the UI manager to ensure no leftover elements
        if hasattr(self, 'ui_manager'):
            self.ui_manager.clear_and_reset()
        
        self._cleaned_up = True
