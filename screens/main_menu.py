import pygame
import os

class MainMenuScreen:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("Segoe UI", 24)
        self.title_font = pygame.font.SysFont("Segoe UI", 40, bold=True)
        self.desc_font = pygame.font.SysFont("Segoe UI", 22)

        self.next_screen = None

        # Load and scale background
        base_path = os.path.dirname(os.path.dirname(__file__))  # Project root
        img_path = os.path.join(base_path, "assets", "background.jpg")
        raw_bg = pygame.image.load(img_path)
        self.background, self.bg_offset = self.scale_and_center(
            raw_bg, screen.get_width(), screen.get_height()
        )

        # GreenWave theme
        self.button_color = (34, 139, 34)
        self.button_hover = (60, 179, 113)
        self.frame_fill = (220, 245, 220)
        self.frame_border = (100, 180, 100)
        self.screen.fill((255, 255, 255))  # soft greenish white or any background color

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

    def scale_and_center(self, img, target_width, target_height):
        img_width, img_height = img.get_size()
        scale_factor = min(target_width / img_width, target_height / img_height)
        new_width = int(img_width * scale_factor)
        new_height = int(img_height * scale_factor)
        scaled_img = pygame.transform.smoothscale(img, (new_width, new_height))
        offset = ((target_width - new_width) // 2, (target_height - new_height) // 2)
        return scaled_img, offset

    def handle_events(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.buttons["Start Simulation"].collidepoint(event.pos):
                print("Go to Simulation screen")
                self.next_screen = "simulation"
                # self.next_screen = "simulation"  # for future
            elif self.buttons["Change Parameters"].collidepoint(event.pos):
                print("Go to Settings screen")
                self.next_screen = "settings"

    def update(self, time_delta):
        pass  # or update logic later if needed

    def draw(self):
        self.screen.blit(self.background, self.bg_offset)

        # Title
        title = self.title_font.render("GreenWave Project", True, (20, 60, 20))
        self.screen.blit(title, (self.center_x(title), 20))

        # Description box
        frame_rect = pygame.Rect(150, 140, 600, 150)
        pygame.draw.rect(self.screen, self.frame_fill, frame_rect, border_radius=12)
        pygame.draw.rect(self.screen, self.frame_border, frame_rect, width=2, border_radius=12)

        desc_lines = [
            "A smart traffic light simulation designed to reduce",
            "traffic jams, fuel consumption, and travel time.",
            "Powered by adaptive algorithms and real-time logic."
        ]

        for i, line in enumerate(desc_lines):
            desc = self.desc_font.render(line, True, (30, 60, 30))
            self.screen.blit(desc, (self.center_x(desc), 160 + i * 30))

        # Buttons
        mouse_pos = pygame.mouse.get_pos()
        for text, rect in self.buttons.items():
            is_hovered = rect.collidepoint(mouse_pos)
            color = self.button_hover if is_hovered else self.button_color
            pygame.draw.rect(self.screen, color, rect, border_radius=10)

            label = self.font.render(text, True, (255, 255, 255))
            label_pos = (rect.x + (rect.width - label.get_width()) // 2, rect.y + 12)
            self.screen.blit(label, label_pos)

    def center_x(self, surface):
        return (self.screen.get_width() - surface.get_width()) // 2

    def get_next_screen(self):
        return self.next_screen
