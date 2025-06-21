import pygame
import pygame_gui
from classes.Enums.Color import Color

class StatisticsScreen:
    def __init__(self, screen, ui_manager, total_vehicles, simulation_time, vehicle_stats):
        self.screen = screen
        self.ui_manager = ui_manager
        self.next_screen = None
        self.total_vehicles = total_vehicles
        self.simulation_time = simulation_time
        self.vehicle_stats = vehicle_stats
        
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
        self.card_height = int(140 * self.scale_factor)
        self.margin = int(20 * self.scale_factor)
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

    def handle_resize(self, new_width, new_height):
        """Handle window resize"""
        self.WINDOW_WIDTH = new_width
        self.WINDOW_HEIGHT = new_height
        
        # Recalculate scale factor
        self.scale_factor = self.WINDOW_WIDTH / self.base_width
        
        # Update card dimensions
        self.card_width = int(280 * self.scale_factor)
        self.card_height = int(140 * self.scale_factor)
        self.margin = int(20 * self.scale_factor)
        
        # Recalculate total width and starting position
        total_cards_width = (self.card_width * self.cards_per_row) + (self.margin * (self.cards_per_row - 1))
        self.start_x = (self.WINDOW_WIDTH - total_cards_width) // 2
        
        # Update button position and size
        button_width = int(200 * self.scale_factor)
        button_height = int(50 * self.scale_factor)
        self.back_button.set_relative_position(
            (self.WINDOW_WIDTH//2 - button_width//2,
             self.WINDOW_HEIGHT - int(80 * self.scale_factor))
        )
        self.back_button.set_dimensions((button_width, button_height))

    def draw_card(self, x, y, width, height, title, content_items):
        # Draw card background with shadow
        card_rect = pygame.Rect(x, y, width, height)
        shadow_rect = pygame.Rect(x + int(2 * self.scale_factor), y + int(2 * self.scale_factor), width, height)
        pygame.draw.rect(self.screen, (200, 200, 200), shadow_rect, border_radius=int(8 * self.scale_factor))
        pygame.draw.rect(self.screen, self.CARD_COLOR, card_rect, border_radius=int(8 * self.scale_factor))
        pygame.draw.rect(self.screen, (220, 220, 220), card_rect, width=1, border_radius=int(8 * self.scale_factor))
        
        # Draw title
        title_font = pygame.font.SysFont("Arial", int(18 * self.scale_factor), bold=True)
        title_surface = title_font.render(title, True, self.TITLE_COLOR)
        title_rect = title_surface.get_rect(midtop=(x + width//2, y + int(10 * self.scale_factor)))
        self.screen.blit(title_surface, title_rect)
        
        # Draw content
        content_font = pygame.font.SysFont("Arial", int(16 * self.scale_factor))
        y_offset = y + int(40 * self.scale_factor)
        for label, value in content_items:
            text = f"{label}: {value}"
            text_surface = content_font.render(text, True, self.TEXT_COLOR)
            text_rect = text_surface.get_rect(midleft=(x + int(15 * self.scale_factor), y_offset))
            self.screen.blit(text_surface, text_rect)
            y_offset += int(25 * self.scale_factor)

    def draw_section_title(self, x, y, title):
        title_font = pygame.font.SysFont("Arial", int(24 * self.scale_factor), bold=True)
        title_surface = title_font.render(title, True, self.SECTION_TITLE_COLOR)
        title_rect = title_surface.get_rect(midleft=(x, y))
        self.screen.blit(title_surface, title_rect)

    def handle_events(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.back_button:
                self.next_screen = "main_menu"
        elif event.type == pygame.VIDEORESIZE:
            self.handle_resize(event.w, event.h)

    def update(self, time_delta):
        self.ui_manager.update(time_delta)

    def draw(self):
        # Draw background
        self.screen.fill(self.BACKGROUND_COLOR)
        
        # Draw main title with shadow
        title_font = pygame.font.SysFont("Arial", int(40 * self.scale_factor), bold=True)
        title = title_font.render("Simulation Statistics", True, self.TITLE_COLOR)
        title_shadow = title_font.render("Simulation Statistics", True, (200, 200, 200))
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH//2, int(40 * self.scale_factor)))
        self.screen.blit(title_shadow, (title_rect.x + int(2 * self.scale_factor), title_rect.y + int(2 * self.scale_factor)))
        self.screen.blit(title, title_rect)
        
        # Draw Simulation Overview section
        self.draw_section_title(self.start_x, int(100 * self.scale_factor), "Simulation Overview")
        
        # Draw Overview Cards
        overview_items = [
            ("Total Vehicles", self.total_vehicles),
            ("Simulation Time", f"{self.simulation_time:.2f} seconds")
        ]
        self.draw_card(
            self.start_x,
            int(130 * self.scale_factor),
            self.card_width,
            self.card_height,
            "General Info",
            overview_items
        )
        
        # Draw Vehicle Types Card
        vehicle_items = [
            ("Private Cars", self.vehicle_stats["Private car amount"]),
            ("Buses", self.vehicle_stats["Buses amount"]),
            ("Trucks", self.vehicle_stats["Trucks amount"])
        ]
        self.draw_card(
            self.start_x + self.card_width + self.margin,
            int(130 * self.scale_factor),
            self.card_width,
            self.card_height,
            "Vehicle Types",
            vehicle_items
        )
        
        # Draw Energy Distribution Card
        energy_items = [
            ("Electric", f"{self.vehicle_stats['Electric']}%"),
            ("Gasoline", f"{self.vehicle_stats['Gasoline']}%"),
            ("Gas", f"{self.vehicle_stats['Gas']}%")
        ]
        self.draw_card(
            self.start_x + (self.card_width + self.margin) * 2,
            int(130 * self.scale_factor),
            self.card_width,
            self.card_height,
            "Energy Distribution",
            energy_items
        )
        
        # Draw UI elements
        self.ui_manager.draw_ui(self.screen)

    def get_next_screen(self):
        return self.next_screen
