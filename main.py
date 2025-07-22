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
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((1100, 600), pygame.RESIZABLE)
    pygame.display.set_caption("GreenWave Simulation")

    # Load and scale the theme
    theme_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "theme.json"))
    ui_manager = pygame_gui.UIManager((1100, 600), theme_path=theme_path)

    print("Theme path:", theme_path)
    print("Theme loaded:", os.path.exists(theme_path))

    current_screen = MainMenuScreen(screen)
    clock = pygame.time.Clock()
    running = True

while running:
    time_delta = clock.tick(60) / 1000.0  # / 1000000.0
    
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
        
        if hasattr(current_screen, 'update'):
            current_screen.update(time_delta)
            
        if hasattr(current_screen, 'draw'):
            current_screen.draw()
        
        pygame.display.flip()
        
        # Screen switching logic
        next_screen = current_screen.get_next_screen()
        if next_screen:
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
                except Exception as e:
                    print(f"[ERROR] Failed to read algorithms from settings.json: {e}")

                # Create the simulation screen
                current_screen = SimulationScreen(screen, ui_manager, display_alg, compare_alg)
            elif isinstance(next_screen, StatisticsScreen):
                current_screen = next_screen

if __name__ == "__main__":
    main()

