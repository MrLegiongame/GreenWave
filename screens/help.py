"""
Help Screen Module

This module contains the HelpScreen class and related functions for providing
user help and documentation within the GreenWave traffic simulation system.
The help system includes both overlay and standalone window modes.

Classes:
    HelpScreen: Help screen interface with scrolling text and navigation.

Functions:
    run_help_window: Runs a standalone help window process.
    open_help_window: Opens a standalone help window.
"""

import pygame
import multiprocessing

class HelpScreen:
    """
    Help screen interface for the GreenWave traffic simulation system.
    
    This class provides a comprehensive help interface with scrolling text,
    navigation controls, and both overlay and standalone window modes.
    The help screen displays user guidance, controls, and support information.
    
    Attributes:
        font: Font for help text
        button_font: Font for buttons
        screen: Pygame screen surface
        on_close: Callback function for closing the help screen
        width (int): Screen width
        height (int): Screen height
        help_text (list): List of help text lines
        button_rect: Rectangle for close button
        line_height (int): Height of each text line
        text_margin (int): Margin around text
        scroll_y (int): Current scroll position
        max_scroll (int): Maximum scroll position
        scrollbar_width (int): Width of scrollbar
        scrollbar_color: Color of scrollbar
        scrollbar_drag (bool): Flag for scrollbar dragging
        scrollbar_rect: Rectangle for scrollbar
    """

    def __init__(self, screen, on_close=None):
        """
        Initialize the help screen.
        
        Args:
            screen: Pygame screen surface to render on
            on_close (callable, optional): Callback function when help is closed
        """
        # In __init__, use a monospace font for proper alignment:
        self.font        = pygame.font.SysFont('Consolas', 20)
        self.button_font = pygame.font.SysFont('Consolas', 22)

        self.drag_offset = 0

        self.screen = screen
        self.on_close = on_close
        self.width, self.height = screen.get_size()
        self.help_text = [
            "╔════════════════════════════════════╗",
            "║        GreenWave User Help        ║",
            "╚════════════════════════════════════╝",
            "",
            " Welcome to GreenWave!",
            "",
            " ■ NAVIGATION",
            "   • Simulation    • Settings    • Statistics",
            "",
            " ■ SIMULATION",
            "   › Control flow and watch vehicles",
            "   › Click a vehicle for details",
            "",
            " ■ SETTINGS",
            "   • Number of cars     • Map choice   • Algorithms control",
            "",
            " ■ CONTROLS",
            "   • Drag window by title bar",
            "   • Click buttons & icons",
            "   • Mouse Wheel: scroll help text",
            "   • ESC / Close: exit help",
            "",
            " ■ SUPPORT",
            "   GitHub: https://github.com/MrLegiongame/GreenWave",
            "",
            " ── Thank you for using GreenWave! ──",
        ]
        self.button_rect = pygame.Rect(20, self.height - 60, 120, 40)
        # Scrolling
        self.line_height = 32
        self.text_margin = 40
        self.scroll_y = 0
        self.max_scroll = 0
        self.scrollbar_width = 16
        self.scrollbar_color = (180, 180, 180)
        self.scrollbar_drag = False
        self.scrollbar_rect = pygame.Rect(self.width - self.scrollbar_width - 8, 0, self.scrollbar_width, 100)
        self.update_scrollbar()

    def update_scrollbar(self):
        """
        Update the scrollbar position and size based on content.
        
        This method calculates the scrollbar dimensions and position
        based on the content height and current scroll position.
        """
        content_height = len(self.help_text) * self.line_height + self.text_margin * 2
        visible_height = self.height - 80
        if content_height > visible_height:
            self.max_scroll = content_height - visible_height
            bar_height = max(40, int(visible_height * visible_height / content_height))
            bar_y = int((self.scroll_y / self.max_scroll) * (visible_height - bar_height)) if self.max_scroll > 0 else 0
            self.scrollbar_rect = pygame.Rect(self.width - self.scrollbar_width - 8, 40 + bar_y, self.scrollbar_width, bar_height)
        else:
            self.max_scroll = 0
            self.scrollbar_rect = pygame.Rect(self.width - self.scrollbar_width - 8, 40, self.scrollbar_width, visible_height)

    def draw(self):
        """
        Draw the help screen interface.
        
        This method renders the help text, close button, and scrollbar
        with proper positioning and styling.
        """
        self.screen.fill((240, 240, 240))
        # Draw help text with scrolling
        y = 40 - self.scroll_y
        for line in self.help_text:
            text_surf = self.font.render(line, True, (30, 30, 30))
            self.screen.blit(text_surf, (self.text_margin, y))
            y += self.line_height
        # Draw Close button
        pygame.draw.rect(self.screen, (100, 180, 100), self.button_rect)
        btn_text = self.button_font.render('Close', True, (255, 255, 255))
        self.screen.blit(btn_text, (self.button_rect.x + 20, self.button_rect.y + 8))
        # Draw scrollbar if needed
        if self.max_scroll > 0:
            pygame.draw.rect(self.screen, (220, 220, 220), (self.width - self.scrollbar_width - 8, 40, self.scrollbar_width, self.height - 80), border_radius=8)
            pygame.draw.rect(self.screen, self.scrollbar_color, self.scrollbar_rect, border_radius=8)

    def handle_event(self, event):
        """
        Handle pygame events for the help screen.
        
        Args:
            event: Pygame event to handle
        """
        if event.type == pygame.QUIT:
            if self.on_close:
                self.on_close()
            pygame.quit()
            exit()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.button_rect.collidepoint(event.pos):
                if self.on_close:
                    self.on_close()
                pygame.quit()
                exit()
            elif self.max_scroll > 0 and self.scrollbar_rect.collidepoint(event.pos):
                self.scrollbar_drag = True
                self.drag_offset = event.pos[1] - self.scrollbar_rect.y
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.scrollbar_drag = False
        elif event.type == pygame.MOUSEMOTION and self.scrollbar_drag:
            visible_height = self.height - 80
            bar_height = self.scrollbar_rect.height
            bar_y = min(max(event.pos[1] - self.drag_offset, 40), 40 + visible_height - bar_height)
            scroll_ratio = (bar_y - 40) / (visible_height - bar_height)
            self.scroll_y = int(scroll_ratio * self.max_scroll)
            self.update_scrollbar()
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_y -= event.y * 40
            self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
            self.update_scrollbar()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.on_close:
                    self.on_close()
                pygame.quit()
                exit()


def run_help_window():
    """
    Run a standalone help window process.
    
    This function creates and runs a standalone help window with its own
    pygame display and event loop. It's designed to be run in a separate
    process for independent help window functionality.
    """
    pygame.init()
    width, height = 770, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption('User Help')
    help_screen = HelpScreen(screen)
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            help_screen.handle_event(event)
        help_screen.draw()
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()

def open_help_window():
    """
    Open a standalone help window in a separate process.
    
    This function creates a new process to run the help window independently
    of the main application, allowing users to access help while keeping
    the main application running.
    
    Returns:
        multiprocessing.Process: The process running the help window
    """
    p = multiprocessing.Process(target=run_help_window)
    p.start()
    return p 