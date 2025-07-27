"""
Main Menu Screen Module

This module contains the MainMenuScreen class for the main menu interface of the
GreenWave traffic simulation system. The main menu provides navigation to different
sections of the application including simulation, settings, and help.

Classes:
    MainMenuScreen: Main menu interface with navigation buttons and help system.
"""

import pygame
import os
from screens.help import HelpScreen, open_help_window


def scale_and_center(img, target_width, target_height):
    """
    Scale and center an image to fit the target dimensions.

    Args:
        img: Pygame image surface to scale
        target_width (int): Target width
        target_height (int): Target height

    Returns:
        tuple: (scaled_image, (offset_x, offset_y))
    """
    # Calculate scaling factor to cover the entire screen while maintaining aspect ratio
    img_width, img_height = img.get_size()
    width_ratio = target_width / img_width
    height_ratio = target_height / img_height
    scale_factor = max(width_ratio, height_ratio)  # Use max to ensure full coverage

    # Calculate new dimensions
    new_width = int(img_width * scale_factor)
    new_height = int(img_height * scale_factor)

    # Scale the image smoothly
    scaled_img = pygame.transform.smoothscale(img, (new_width, new_height))

    # Calculate offset to center and ensure full coverage
    offset_x = (target_width - new_width) // 2
    offset_y = (target_height - new_height) // 2

    return scaled_img, (offset_x, offset_y)


class MainMenuScreen:
    """
    Main menu screen for the GreenWave traffic simulation system.
    
    This class manages the main menu interface, including background rendering,
    button layout, help system integration, and navigation to other screens.
    The menu provides a clean, professional interface with GreenWave branding.
    
    Attributes:
        screen: Pygame screen surface
        font: Font for regular text
        title_font: Font for title text
        desc_font: Font for description text
        next_screen: Next screen to navigate to
        show_help: Flag indicating if help is being shown
        help_overlay: Help screen overlay
        help_button_rect: Rectangle for help button
        help_window_process: Process for help window
        background: Background image surface
        bg_offset: Background offset for centering
        button_color: Primary button color
        button_hover: Button hover color
        frame_fill: Frame background color
        frame_border: Frame border color
        buttons: Dictionary of button rectangles
        frame_rect: Rectangle for description frame
    """

    def __init__(self, screen):
        """
        Initialize the main menu screen.
        
        Args:
            screen: Pygame screen surface to render on
        """
        self.screen = screen
        self.buttons = None
        self.frame_rect = None
        self.font = pygame.font.SysFont("Segoe UI", 24)
        self.title_font = pygame.font.SysFont("Segoe UI", 40, bold=True)
        self.desc_font = pygame.font.SysFont("Segoe UI", 22)

        self.next_screen = None
        self.show_help = False
        self.help_overlay = HelpScreen(screen, self.close_help)
        # Add Help button at bottom left
        help_button_width, help_button_height = 120, 40
        self.help_button_rect = pygame.Rect(20, self.screen.get_height() - help_button_height - 20, help_button_width, help_button_height)
        # Track help window process if needed
        self.help_window_process = None

        # Load and scale background
        base_path = os.path.dirname(os.path.dirname(__file__))  # Project root
        img_path = os.path.join(base_path, "assets", "background.jpg")
        raw_bg = pygame.image.load(img_path)
        self.background, self.bg_offset = scale_and_center(raw_bg, screen.get_width(), screen.get_height())

        # GreenWave theme
        self.button_color = (34, 139, 34)
        self.button_hover = (60, 179, 113)
        self.frame_fill = (220, 245, 220)
        self.frame_border = (100, 180, 100)
        self.screen.fill((255, 255, 255))  # soft greenish white or any background color

        # Update button positions
        self.update_button_positions()

    def update_button_positions(self):
        """
        Update button positions based on current window size.
        
        This method recalculates the positions of all UI elements to ensure
        proper layout regardless of window size changes.
        """
        # Button layout
        button_width = 220
        button_height = 50
        spacing = 40
        bottom_y = self.screen.get_height() - 100
        center_x = self.screen.get_width() // 2

        self.buttons = {
            "Change Parameters": pygame.Rect(center_x - button_width - spacing // 2, bottom_y, button_width, button_height),
            "Start Simulation": pygame.Rect(center_x + spacing // 2, bottom_y, button_width, button_height),
        }

        # Description frame layout
        frame_width = min(600, self.screen.get_width() - 100)  # Max width of 600 or screen width - 100
        frame_height = 150
        frame_x = (self.screen.get_width() - frame_width) // 2
        frame_y = 140
        self.frame_rect = pygame.Rect(frame_x, frame_y, frame_width, frame_height)

        # Update Help button position on resize
        self.help_button_rect = pygame.Rect(20, self.screen.get_height() - 60, 120, 40)

    def handle_resize(self, new_width, new_height):
        """
        Handle window resize events.
        
        Args:
            new_width (int): New window width
            new_height (int): New window height
        """
        # Update background scaling
        try:
            raw_bg = pygame.image.load(os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "background.jpg"))
            self.background, self.bg_offset = scale_and_center(raw_bg, new_width, new_height)
        except Exception as e:
            # Fallback to solid color if image loading fails
            self.background = pygame.Surface((new_width, new_height))
            self.background.fill((255, 255, 255))
            self.bg_offset = (0, 0)
        
        # Update button positions
        self.update_button_positions()


    def handle_events(self, event):
        """
        Handle pygame events for the main menu.
        
        Args:
            event: Pygame event to handle
        """
        if self.show_help:
            self.help_overlay.handle_event(event)
            return
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.buttons["Start Simulation"].collidepoint(event.pos):
                self.next_screen = "simulation"
            elif self.buttons["Change Parameters"].collidepoint(event.pos):
                self.next_screen = "settings"
            elif self.help_button_rect.collidepoint(event.pos):
                if self.help_window_process is None or not self.help_window_process.is_alive():
                    self.help_window_process = open_help_window()

    def close_help(self):
        self.show_help = False

    def update(self, time_delta):
        pass

    def draw(self):
        # Draw background
        self.screen.fill((255, 255, 255))  # Fill with white first to prevent black lines
        self.screen.blit(self.background, self.bg_offset)

        # Title
        title = self.title_font.render("GreenWave Project", True, (20, 60, 20))
        self.screen.blit(title, (self.center_x(title), 20))

        # Description box
        pygame.draw.rect(self.screen, self.frame_fill, self.frame_rect, border_radius=12)
        pygame.draw.rect(self.screen, self.frame_border, self.frame_rect, width=2, border_radius=12)

        desc_lines = [
            "A smart traffic light simulation designed to reduce",
            "traffic jams, fuel consumption, and travel time.",
            "Powered by adaptive algorithms and real-time logic."
        ]

        for i, line in enumerate(desc_lines):
            desc = self.desc_font.render(line, True, (30, 60, 30))
            self.screen.blit(desc, (self.center_x(desc), self.frame_rect.y + 20 + i * 30))

        # Buttons
        mouse_pos = pygame.mouse.get_pos()
        for text, rect in self.buttons.items():
            is_hovered = rect.collidepoint(mouse_pos)
            color = self.button_hover if is_hovered else self.button_color
            pygame.draw.rect(self.screen, color, rect, border_radius=10)

            label = self.font.render(text, True, (255, 255, 255))
            label_pos = (rect.x + (rect.width - label.get_width()) // 2, rect.y + 12)
            self.screen.blit(label, label_pos)

        # Draw Help button at bottom left
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = self.help_button_rect.collidepoint(mouse_pos)
        color = self.button_hover if is_hovered else self.button_color
        pygame.draw.rect(self.screen, color, self.help_button_rect, border_radius=8)
        help_label = self.font.render('Help', True, (255, 255, 255))
        self.screen.blit(help_label, (self.help_button_rect.x + 20, self.help_button_rect.y + 8))

    def center_x(self, surface):
        return (self.screen.get_width() - surface.get_width()) // 2

    def get_next_screen(self):
        return self.next_screen
