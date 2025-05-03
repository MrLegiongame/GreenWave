import pygame
import pygame_gui
import os
from screens.main_menu import MainMenuScreen
from screens.settings import SettingsScreen
from screens.simulation import SimulationScreen

pygame.init()
screen = pygame.display.set_mode((900, 600))
pygame.display.set_caption("GreenWave Simulation")

theme_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "theme.json"))
ui_manager = pygame_gui.UIManager((900, 600), theme_path)

print("Theme path:", theme_path)
print("Theme loaded:", os.path.exists(theme_path))

#print("Theme loaded from:", ui_manager.ui_theme.theme_file_path)
current_screen = MainMenuScreen(screen)
clock = pygame.time.Clock()
running = True

while running:
    time_delta = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
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
            current_screen = SimulationScreen(screen, ui_manager)

