"""
GreenWave Traffic Simulation - Main Application Entry Point

This module serves as the main entry point for the GreenWave traffic simulation system.
It initializes the pygame application, manages screen transitions, handles user events,
and coordinates the overall application flow between different screens.

The application follows a screen-based architecture where different screens (main menu,
settings, simulation, statistics) are managed through a central main loop. Each screen
is responsible for its own rendering and event handling, while the main loop coordinates
transitions between screens.

Key Features:
    - Pygame-based graphical user interface
    - Screen management system with smooth transitions
    - Dynamic window resizing support
    - Settings-based algorithm configuration
    - Modular screen architecture

Screens:
    - MainMenuScreen: Application main menu and navigation
    - SettingsScreen: Configuration and parameter settings
    - SimulationScreen: Traffic simulation visualization and control
    - StatisticsScreen: Results analysis and data visualization

Dependencies:
    - pygame: Graphics and event handling
    - pygame_gui: User interface components
    - classes.Enums.Alg: Algorithm enumeration
    - screens.*: Screen implementations
"""

import pygame
import pygame_gui
import os
import json

from classes.Enums.Alg import Alg
from screens.main_menu import MainMenuScreen
from screens.settings import SettingsScreen
from screens.simulation import SimulationScreen
from screens.statistics import StatisticsScreen

def main():
    """
    Main application entry point and event loop.
    
    This function initializes the pygame application, sets up the main window,
    loads the UI theme, and runs the main event loop that manages screen transitions
    and user interactions. The function handles window resizing, screen switching,
    and proper cleanup of resources.
    
    The main loop performs the following operations:
    1. Initialize pygame and create the main window
    2. Load the UI theme and create the UI manager
    3. Start with the main menu screen
    4. Process events and handle screen transitions
    5. Update and render the current screen
    6. Manage screen switching based on user navigation
    
    Screen Transition Logic:
        - "settings" -> SettingsScreen
        - "main_menu" -> MainMenuScreen  
        - "simulation" -> SimulationScreen (with algorithm configuration)
        - StatisticsScreen instance -> Direct screen instance
    
    Algorithm Configuration:
        The simulation screen is configured with algorithms from settings.json:
        - Display algorithm: Primary algorithm for visualization
        - Compare algorithm: Secondary algorithm for comparison
        
    Window Management:
        - Supports dynamic window resizing
        - Notifies screens of resize events
        - Updates UI manager for new window dimensions
        
    Returns:
        None
        
    Raises:
        FileNotFoundError: If theme.json or settings.json cannot be loaded
        KeyError: If algorithm settings are invalid
        Exception: For other initialization or runtime errors
    """
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((1100, 600), pygame.RESIZABLE)
    pygame.display.set_caption("GreenWave Simulation")

    # Load and scale the theme
    theme_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "theme.json"))
    ui_manager = pygame_gui.UIManager((1100, 600), theme_path=theme_path)

    current_screen = MainMenuScreen(screen)
    clock = pygame.time.Clock()
    running = True


    while running:
        time_delta = clock.tick(60) / 1000.0  # in seconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                # Update screen and UI manager for new size
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                ui_manager.set_window_resolution((event.w, event.h))
                # Notify current screen of resize if it has the method
                if hasattr(current_screen, 'handle_resize'):
                    current_screen.handle_resize(event.w, event.h)
            elif hasattr(current_screen, 'handle_events'):
                current_screen.handle_events(event)
                if hasattr(current_screen, 'ui_manager'):
                    current_screen.ui_manager.process_events(event)

        # These should be called ONCE per frame, not per event:
        if hasattr(current_screen, 'update'):
            current_screen.update(time_delta)
        if hasattr(current_screen, 'draw'):
            current_screen.draw()
        pygame.display.flip()

        # Screen switching logic
        next_screen = current_screen.get_next_screen()
        if next_screen:
            # Clean up current screen if it has a cleanup method
            if hasattr(current_screen, 'cleanup'):
                current_screen.cleanup()
            
            if next_screen == "settings":
                current_screen = SettingsScreen(screen, ui_manager)
            elif next_screen == "main_menu":
                current_screen = MainMenuScreen(screen)
            elif next_screen == "simulation":
                # Read algorithms from settings.json
                display_alg = Alg.ADAPTIVE_ALG
                compare_alg = Alg.FIXED_TIMING_CYCLE
                try:
                    with open("settings.json", "r") as f:
                        settings = json.load(f)
                        display_alg_str = settings.get("Display algorithm", {}).get("value", "ADAPTIVE_ALG")
                        compare_alg_str = settings.get("Compared algorithm", {}).get("value", "FIXED_TIMING_CYCLE")
                        display_alg = Alg[display_alg_str] if display_alg_str in Alg.__members__ else Alg.ADAPTIVE_ALG
                        compare_alg = Alg[compare_alg_str] if compare_alg_str in Alg.__members__ else Alg.FIXED_TIMING_CYCLE
                except Exception:
                    # Failed to read algorithms from settings.json
                    pass

                # Create the simulation screen
                current_screen = SimulationScreen(screen, ui_manager, display_alg, compare_alg)
            elif isinstance(next_screen, StatisticsScreen):
                current_screen = next_screen

if __name__ == "__main__":
    main()

